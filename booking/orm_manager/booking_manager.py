from collections import defaultdict
from django.utils.timezone import now
from django.db.models import Q
from datetime import date
from booking.constants import Constants
from booking.models import Booking, TimeSlot, Room, TeamMember


class BookingManager:
    @staticmethod
    def get_available_slots_for_date(query_date: date):
        # Fetch all rooms and timeslots
        rooms = Room.objects.values('id', 'name', 'room_type', 'capacity')
        slots = TimeSlot.objects.values('id', 'start_time', 'end_time', 'id')

        # Get count of bookings grouped by (room_id, slot_id)
        booking_counts = defaultdict(int)
        for booking in Booking.objects.filter(date=query_date, status='ACTIVE').values('room_id', 'time_slot_id'):
            booking_counts[(booking['room_id'], booking['time_slot_id'])] += 1

        # Prepare structured output grouped by slot
        grouped = defaultdict(lambda: defaultdict(list))

        for slot in slots:
            slot_id = slot['id']
            slot_label = f"{slot['start_time']} - {slot['end_time']}"

            for room in rooms:
                key = (room['id'], slot_id)
                booked_count = booking_counts.get(key, 0)
                room_type = room['room_type']

                if room_type == 'private' and booked_count == 0:
                    grouped[(slot_label, slot_id)]['private'].append(room['name'])

                elif room_type == 'shared':
                    available_seats = room['capacity'] - booked_count
                    if available_seats > 0:
                        grouped[(slot_label, slot_id)]['shared'].append({
                            "name": room['name'],
                            "seats_available": available_seats
                        })

                elif room_type == 'conference':
                    grouped[(slot_label, slot_id)]['conference'].append(room['name'])

        # Final structured list
        response = []
        for (slot_label, slot_id), roomtypes in grouped.items():
            response.append({
                "date": query_date,
                "slot_id": slot_id,
                "slot": slot_label,
                "room_types": [
                    {
                        "type": room_type,
                        "available_rooms": rooms,
                        "count": (
                            sum(r['seats_available'] for r in rooms)
                            if room_type == 'shared' else len(rooms)
                        )
                    }
                    for room_type, rooms in roomtypes.items()
                ]
            })

        return response

    @staticmethod
    def create_rooms():
        if Room.objects.count() == 0:
            rooms_to_create = []
            for room_type, count in Constants.ROOM_TYPES.items():
                capacity = 1 if room_type != "conference" else None
                for i in range(1, count+1):
                    rooms = Room(name=room_type[0].capitalize() +str(i), room_type=room_type, capacity=capacity)
                    rooms_to_create.append(rooms)
            Room.objects.bulk_create(rooms_to_create)

    @staticmethod
    def get_user_and_team_bookings(user):
        if getattr(user, 'is_admin', False):
            return Booking.objects.all()

        user_teams = TeamMember.objects.filter(user=user).values_list('team_id', flat=True)
        return Booking.objects.filter(
            Q(booked_by_user=user) | Q(booked_by_team__in=user_teams)
        )

    @staticmethod
    def cancel_booking(booking_id, user):
        try:
            booking = Booking.objects.get(id=booking_id)

            if booking.booked_by_user != user:
                return {"error": "You are not authorized to cancel this booking."}

            if booking.status == "CANCELLED":
                return {"error": "Booking is already cancelled."}

            booking.status = "CANCELLED"
            booking.cancelled_at = now()
            booking.save()

            return {"success": "Booking cancelled successfully."}

        except Booking.DoesNotExist:
            return {"error": "Booking not found."}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_user_bookings(user):
        return Booking.objects.select_related(
            'room', 'time_slot', 'booked_by_user', 'booked_by_team'
        ).filter(booked_by_user=user).order_by('-booked_at')

    @staticmethod
    def get_all_bookings():
        return Booking.objects.select_related(
            'room', 'time_slot', 'booked_by_user', 'booked_by_team'
        ).all().order_by('-booked_at')

    @staticmethod
    def get_booking_by_id(booking_id):
        return Booking.objects.select_related(
            'room', 'time_slot', 'booked_by_user', 'booked_by_team'
        ).filter(id=booking_id).first()