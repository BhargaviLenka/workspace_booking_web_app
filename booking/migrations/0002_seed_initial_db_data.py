from django.db import migrations
from datetime import time
from django.contrib.auth.hashers import make_password

def seed_initial_data(apps, schema_editor):
    User = apps.get_model('booking', 'User')
    Team = apps.get_model('booking', 'Team')
    TeamMember = apps.get_model('booking', 'TeamMember')
    Room = apps.get_model('booking', 'Room')
    TimeSlot = apps.get_model('booking', 'TimeSlot')

    # Admin
    if not User.objects.filter(is_admin=False).exists():
        User.objects.create(username='admin', email='admin@example.com', password=make_password('admin123'),
                            is_admin=True, dob="1999-01-01")


    # Regular users
    for i in range(1, 10):
        User.objects.get_or_create(
            username=f'user{i}',
            defaults={
                'email': f'user{i}@example.com',
                'dob': '2000-01-01',
                'password': make_password(f'user{i}@123')
            }
        )

    # Time slots
    for hour in range(9, 18):
        TimeSlot.objects.get_or_create(
            start_time=time(hour, 0),
            end_time=time(hour + 1, 0)
        )

    # Rooms
    if not Room.objects.exists():
        for i in range(8):
            Room.objects.create(name=f'P{i+1}', room_type='private', capacity=1)
        for i in range(4):
            Room.objects.create(name=f'C{i+1}', room_type='conference', capacity=1)
        for i in range(3):
            Room.objects.create(name=f'S{i+1}', room_type='shared', capacity=4)

    # Teams
    user1 = User.objects.get(username='user1')
    team, _ = Team.objects.get_or_create(name='Team Alpha', team_lead=user1)
    for i in range(1, 4):
        u = User.objects.get(username=f'user{i}')
        TeamMember.objects.get_or_create(team=team, user=u)

    user5 = User.objects.get(username='user5')
    team, _ = Team.objects.get_or_create(name='Team Beta', team_lead=user5)
    for i in range(5, 10):
        u = User.objects.get(username=f'user{i}')
        TeamMember.objects.get_or_create(team=team, user=u)


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_initial_data),
    ]
