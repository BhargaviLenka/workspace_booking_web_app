from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from booking.models import User, Team, TeamMember, Booking


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['is_admin'] = user.is_admin
        return token

class BookingSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(source='room.name', read_only=True)
    room_type = serializers.CharField(source='room.room_type', read_only=True)
    start_time = serializers.TimeField(source='time_slot.start_time', read_only=True)
    end_time = serializers.TimeField(source='time_slot.end_time', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    booked_at = serializers.DateTimeField(read_only=True)
    cancelled_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'room_name', 'room_type', 'date', 'start_time', 'end_time', 'status', 'status_display',
                  'booked_at', 'cancelled_at']


class AdminBookingSerializer(BookingSerializer):
    booked_by_username = serializers.CharField(source='booked_by_user.username', read_only=True)
    team_name = serializers.CharField(source='booked_by_team.name', read_only=True, default=None)

    class Meta(BookingSerializer.Meta):
        fields = BookingSerializer.Meta.fields + ['booked_by_username', 'team_name']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'dob', 'is_admin']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'name', 'team_lead']


class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        fields = ['id', 'team', 'user']