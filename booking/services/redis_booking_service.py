from django.db import transaction
from django.db.models import Q

from booking.constants import Constants
from booking.models import Booking, Room, TimeSlot, Team, TeamMember
from datetime import date, time, datetime

from booking.redis_config import redis_client



class RedisBookingService:
    @staticmethod
    def _key(date_str, slot_time_str, room_type, room_name):
        return f"room_availability/{date_str}/{slot_time_str}/{room_type}/{room_name}"

    @staticmethod
    def _validate_booking_request(user, data):
        date_str = data.get("date")
        slot_id = data.get("slot_id")
        room_type = data.get("room_type")
        room_name = data.get("room_name")
        team_name = data.get("team_name")

        if not all([date_str, slot_id, room_type, room_name]):
            raise Exception("Missing required booking fields")

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise Exception("Invalid date format. Expected YYYY-MM-DD")

        try:
            slot = TimeSlot.objects.get(id=slot_id)
        except TimeSlot.DoesNotExist:
            raise Exception("Invalid slot ID")

        if date_obj < date.today():
            raise Exception("Cannot book a past date")

        if date_obj == date.today():
            now = datetime.now().time()
            if slot.start_time < now < slot.end_time or slot.end_time < now:
                raise Exception("Booking is only allowed for future time slots")

        team = None
        if team_name:
            try:
                team = Team.objects.prefetch_related("members__user").get(name=team_name)
            except Team.DoesNotExist:
                raise Exception("Invalid team name")
            if user not in team.members.all():
                raise Exception("You are not a member of the team")

        if not team and user.age is not None and user.age < 10:
            raise Exception("Children under 10 cannot book individually")

        return date_obj, slot, room_type, room_name, team

    @staticmethod
    def _get_or_create_redis_key(date_str, slot_time_str, room_type, room_name, query):
        key = RedisBookingService._key(date_str, slot_time_str, room_type, room_name)

        if not redis_client.exists(key):
            room_capacity_mapping = Constants.ROOM_CAPACITY_MAPPING
            new_query = query & Q(room__room_type=room_type, room__name=room_name)
            count = room_capacity_mapping.get(room_type) - Booking.objects.filter(new_query).count()
            redis_client.set(key, count)

        return key

    @staticmethod
    def book_room(*, user, data):
        date_obj, slot, room_type, room_name, team = RedisBookingService._validate_booking_request(user, data)

        query = Q(time_slot=slot, date=date_obj, status='ACTIVE')

        if team:
            if room_type != 'conference':
                raise Exception("Only conference rooms can be booked by teams.")

            team_members = TeamMember.objects.select_related('user').filter(team=team)
            team_size = team_members.count()
            seat_needed = sum(1 for m in team_members if not m.user.age or m.user.age >= 10)

            if team_size < 3:
                raise Exception("Conference rooms require at least 3 team members")

            if Booking.objects.filter(Q(booked_by_team=team) & query).exists():
                raise Exception("This team already has a booking for the selected slot")

        else:
            seat_needed = 1
            if Booking.objects.filter(Q(booked_by_user=user) & query).exists():
                raise Exception("You already have a booking for the selected slot")

        if room_type == 'shared' and team:
            raise Exception("Teams cannot book shared desks")

        slot_time_str = f"{slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}"
        date_str = date_obj.isoformat()

        key = RedisBookingService._get_or_create_redis_key(date_str, slot_time_str, room_type, room_name, query)

        try:
            with transaction.atomic():
                available = redis_client.get(key) or 0
                if available is None or int(available) < seat_needed:
                    raise Exception("No available room for the selected slot and type")

                val = redis_client.decrby(key, seat_needed)
                if val < 0:
                    raise Exception("No available room for the selected slot and type")

                booked_ids = Booking.objects.filter(
                    room__room_type=room_type,
                    room__name=room_name,
                    date=date_obj,
                    time_slot=slot,
                    status='ACTIVE'
                ).values_list('room_id', flat=True)

                candidate_rooms = Room.objects.filter(room_type=room_type, name=room_name).exclude(id__in=booked_ids)
                assigned_room = None

                if room_type == 'shared':
                    for room in Room.objects.filter(room_type='shared'):
                        count = Booking.objects.filter(
                            room=room,
                            time_slot=slot,
                            date=date_obj,
                            status='ACTIVE'
                        ).count()
                        if count + seat_needed <= 4:
                            assigned_room = room
                            break
                else:
                    assigned_room = candidate_rooms.first()

                if not assigned_room:
                    redis_client.incrby(key, seat_needed)
                    return None, "No available room for the selected slot and type"

                booking = Booking.objects.create(
                    room=assigned_room,
                    booked_by_user=user if not team else None,
                    booked_by_team=team if team else None,
                    time_slot=slot,
                    date=date_obj,
                    status='ACTIVE'
                )
                return booking.id, "Booking is successful"

        except Exception as err:
            redis_client.incrby(key, seat_needed)
            raise Exception(str(err))
