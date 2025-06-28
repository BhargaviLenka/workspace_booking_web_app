from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from datetime import datetime, date
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from booking.orm_manager.booking_manager import BookingManager
from booking.orm_manager.team_manager import TeamManager
from booking.orm_manager.user_manager import UserManager
from booking.permissions import IsAdminUserCustom
from booking.serializers import BookingSerializer, AdminBookingSerializer, TeamSerializer, UserSerializer, \
    CustomTokenObtainPairSerializer
from booking.services.redis_booking_service import RedisBookingService
from booking.utils import StandardResultsSetPagination



class AvailableSlotsView(APIView):
    """
       Retrieve available slots for a specific date.

       GET Params:
           - date (optional): Date in 'YYYY-MM-DD' format. Defaults to today's date.

       Response:
           A structured list of available rooms and types per time slot.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_str = request.data.get("date")
        query_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()
        available_slots = BookingManager.get_available_slots_for_date(query_date)
        return Response(available_slots)

class CreateBookingView(APIView):
    """
       Create a booking for a selected room and time slot.

       Request body:
           {
               "slot_id": int,
               "date": "YYYY-MM-DD",
               "team_name": "Team Alpha",
               "room_type": "private",
               "room_name": "p1"
           }

       Response:
           - booking_id: ID of the created booking.
           - message: Confirmation or error message.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            data = request.data
            BookingManager.create_rooms()
            booking_id, message = RedisBookingService.book_room(user=user, data=data)
            return Response({'booking_id': booking_id, 'message': message})

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class BookingHistoryView(APIView):
    """
    Retrieve paginated booking history for the logged-in user.

    Response:
        - Paginated list of past bookings (individual or team).
    """
    permission_classes = [IsAuthenticated]


    def get(self, request):
        try:
            bookings = BookingManager.get_user_bookings(request.user)
            paginator = StandardResultsSetPagination()
            result_page = paginator.paginate_queryset(bookings, request)
            serializer = BookingSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AllBookingsView(APIView):
    """
    Admin only: Retrieve paginated list of all bookings in the system.

    Requires:
        - Admin permissions.

    Response:
        - Paginated list of all bookings with user/team details.
    """
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def get(self, request):
        try:
            bookings = BookingManager.get_all_bookings()
            paginator = StandardResultsSetPagination()
            result_page = paginator.paginate_queryset(bookings, request)
            serializer = AdminBookingSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomTokenView(TokenObtainPairView):
    """
    Refresh the access token using the refresh token.

    Request body:
        {
            "refresh": "JWT refresh token"
        }

    Response:
        {
            "access": "new JWT access token"
        }
    """
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshView(TokenRefreshView):
    pass

class CancelBookingView(APIView):
    """
    Cancel a booking by booking ID.

    URL Param:
        - booking_id: ID of the booking to cancel.

    Response:
        - Success or error message.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        result = BookingManager.cancel_booking(booking_id, request.user)

        if "error" in result:
            return Response({"detail": result["error"]}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": result["success"]}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Logout user by blacklisting their refresh token.

    Request body:
        {
            "refresh": "<refresh_token>"
        }

    Response:
        - Confirmation of logout or error if token is invalid.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response({"detail": "refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logout successful."}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"detail": "Invalid refresh token."}, status=status.HTTP_400_BAD_REQUEST)


class UserCreateView(APIView):
    """
    Admin only: Create a new user account.

    Request body:
        {
            "username": str,
            "email": str,
            "password": str,
            ...
        }

    Response:
        - Created user details or validation errors.
    """
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = UserManager.create_user(serializer.validated_data)
                return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeamCreateView(APIView):
    """
    Admin only: Create a new team.

    Request body:
        {
            "name": str,
            ...
        }

    Response:
        - Created team details.
    """
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def post(self, request):
        serializer = TeamSerializer(data=request.data)
        if serializer.is_valid():
            try:
                team = TeamManager.create_team(serializer.validated_data)
                return Response(TeamSerializer(team).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddUserToTeamView(APIView):
    """
    Admin only: Add a user to a team.

    Request body:
        {
            "user_id": int,
            "team_id": int
        }

    Response:
        - Success or error message.
    """

    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def post(self, request):
        team_id = request.data.get('team_id')
        user_id = request.data.get('user_id')

        if not team_id or not user_id:
            return Response({"detail": "team_id and user_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        result = TeamManager.add_user_to_team(team_id, user_id)

        if "error" in result:
            return Response({"detail": result["error"]}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": result["success"]}, status=status.HTTP_201_CREATED)


class RemoveUserFromTeamView(APIView):
    """
    Admin only: Remove a user from a team.

    Request body:
        {
            "user_id": int,
            "team_id": int
        }

    Response:
        - Success or error message.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        team_id = request.data.get('team_id')
        user_id = request.data.get('user_id')

        if not team_id or not user_id:
            return Response({"detail": "team_id and user_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        result = TeamManager.remove_user_from_team(team_id, user_id)

        if "error" in result:
            return Response({"detail": result["error"]}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": result["success"]}, status=status.HTTP_200_OK)


class DeactivateUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def post(self, request):
        user_id = request.data.get('user_id')

        if not user_id:
            return Response({"detail": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        result = UserManager.deactivate_user(user_id)

        if "error" in result:
            return Response({"detail": result["error"]}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": result["success"]}, status=status.HTTP_200_OK)


class ActivateUserView(APIView):
    """
    Admin only: Reactivate a deactivated user account.

    Request body:
        {
            "user_id": int
        }

    Response:
        - Success or error message.
    """
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def post(self, request):
        user_id = request.data.get('user_id')

        if not user_id:
            return Response({"detail": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        result = UserManager.activate_user(user_id)

        if "error" in result:
            return Response({"detail": result["error"]}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": result["success"]}, status=status.HTTP_200_OK)