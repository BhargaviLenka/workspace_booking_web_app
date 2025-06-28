from datetime import datetime, timedelta
from django.db import migrations
from booking.constants import Constants
from booking.redis_config import redis_client


def create_or_update_initial_edis_data(apps, schema_editor):
    Room = apps.get_model('booking', 'Room')
    TimeSlot = apps.get_model('booking', 'TimeSlot')
    room_name_mapping = {}
    rooms = Room.objects.all()
    for each in rooms:
        if each.room_type in room_name_mapping:
            room_name_mapping[each.room_type].append(each.name)
        else:
            room_name_mapping[each.room_type] = [each.name]
    room_capacity = Constants.ROOM_CAPACITY_MAPPING
    slot_times = [
        f"{slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}"
        for slot in TimeSlot.objects.all()
    ]

    # Generate keys for the next 7 days
    today = datetime.today()

    # delete previous days data
    all_keys = redis_client.keys("room_availability/*")
    for key in all_keys:
        try:
            parts = key.decode().split("/")
            key_date = datetime.strptime(parts[1], "%Y-%m-%d").date()
            if key_date < today:
                redis_client.delete(key)
                print(f"Deleted past key: {key.decode()}")
        except Exception as e:
            print(f"Could not parse or delete key: {key.decode()} — {e}")

    # Create availability keys for next 7 days
    for offset in range(0, 7):
        booking_date = today + timedelta(days=offset)
        date_str = datetime.strftime(booking_date, '%Y-%m-%d')

        for slot in slot_times:
            for room_type, count in room_capacity.items():
                for room_name in room_name_mapping.get(room_type):
                    redis_key = f"room_availability/{date_str}/{slot}/{room_type}/{room_name}"
                    if not redis_client.exists(redis_key):
                        redis_client.set(redis_key, count)
                        print(f"Created key: {redis_key} -> {count}")
                    else:
                        print(f"Key exists: {redis_key}")


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0002_seed_initial_db_data'),
    ]

    operations = [
        migrations.RunPython(create_or_update_initial_edis_data),
    ]
