# booking/urls.py
from django.urls import path

from .api_views import AvailableSlotsView, CreateBookingView, CustomTokenView, CustomTokenRefreshView, LogoutView, \
    UserCreateView, TeamCreateView, AddUserToTeamView, RemoveUserFromTeamView, DeactivateUserView, ActivateUserView, \
    BookingHistoryView, CancelBookingView, AllBookingsView

urlpatterns = [
    path('login/', CustomTokenView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='token_logout'),

    path('book-room/', CreateBookingView.as_view(), name='book-room'),
    path('bookings-available/', AvailableSlotsView.as_view(), name='bookings-available'),
    path('bookings/history/', BookingHistoryView.as_view(), name='booking-history'),
    path('bookings/all/', AllBookingsView.as_view(), name='all-bookings'),
    path('cancel/<int:booking_id>/', CancelBookingView.as_view(), name='cancel-booking'),

    path('users/add/', UserCreateView.as_view(), name='add-user'),
    path('teams/add/', TeamCreateView.as_view(), name='add-team'),
    path('teams/add-user/', AddUserToTeamView.as_view(), name='add-user-to-team'),
    path('teams/remove-user/', RemoveUserFromTeamView.as_view(), name='remove-user-from-team'),
    path('users/deactivate/', DeactivateUserView.as_view(), name='deactivate-user'),
    path('users/activate/', ActivateUserView.as_view(), name='activate-user'),
]
