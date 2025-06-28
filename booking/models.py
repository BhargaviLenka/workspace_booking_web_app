from datetime import date

from django.db import models
from django.contrib.auth.models import AbstractUser



class User(AbstractUser):
    is_admin = models.BooleanField(default=False)
    dob = models.DateField("Date of Birth", null=True, blank=True)

    class Meta:
        db_table = "auth_custom_user"


    @property
    def age(self):
        """
        Compute age in years from self.dob.
        Returns None if dob is not set.
        """
        if not self.dob:
            return None

        today = date.today()
        years = today.year - self.dob.year
        if (today.month, today.day) < (self.dob.month, self.dob.day):
            years -= 1
        return years


class Team(models.Model):
    name = models.CharField(max_length=100)
    team_lead = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_lead')

    def __str__(self):
        return self.name

    class Meta:
        db_table = "team_info"


class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = "team_members"
        unique_together = ('team', 'user')

class Room(models.Model):
    PRIVATE = 'private'
    CONFERENCE = 'conference'
    SHARED = 'shared'

    ROOM_TYPES = [
        (PRIVATE, 'Private'),
        (CONFERENCE, 'Conference'),
        (SHARED, 'Shared'),
    ]
    name = models.CharField(max_length=100, unique=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    capacity = models.PositiveIntegerField(null=True, blank=True, help_text="Leave blank for unlimited capacity")

    class Meta:
        db_table = "rooms"


class TimeSlot(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        db_table = 'time_slot'


class Booking(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('CANCELLED', 'Cancelled'),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    booked_by_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_bookings")
    booked_by_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team_booking", null=True, blank=True)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    date = models.DateField()
    booked_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    cancelled_at = models.DateTimeField(null=True, blank=True)


    class Meta:
        db_table = "booking_data"
        unique_together = ('room', 'date', 'time_slot')
