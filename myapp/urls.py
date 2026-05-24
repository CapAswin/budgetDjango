from django.urls import path
from .views import (
    RegisterUserAPIView, LoginAPIView, ProtectedExampleView, UserView,
    LogoutAPIView, CategoryView, ChangePasswordView,
    RoomCreateView, RoomJoinView, RoomListView, RoomDetailView,
    RoomLeaveView, RoomExpenseView, RoomBalanceView,
)

urlpatterns = [
    path('register/', RegisterUserAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('transactions/', ProtectedExampleView.as_view(), name='protected'),
    path('insert/', ProtectedExampleView.as_view(), name='protected'),
    path('update/', ProtectedExampleView.as_view(), name='protected'),
    path('remove/<int:pk>/', ProtectedExampleView.as_view(), name='protected-delete'),
    path('user/', UserView.as_view(), name='userView'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('categories/', CategoryView.as_view(), name='protected'),
    path('insertCategory/', CategoryView.as_view(), name='protected'),
    path('updateCategory/', CategoryView.as_view(), name='protected'),
    path('removeCategory/<int:pk>/', CategoryView.as_view(), name='protected-delete'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),

    # Shared expense rooms
    path('rooms/', RoomListView.as_view(), name='room-list'),
    path('rooms/create/', RoomCreateView.as_view(), name='room-create'),
    path('rooms/join/', RoomJoinView.as_view(), name='room-join'),
    path('rooms/<str:room_code>/', RoomDetailView.as_view(), name='room-detail'),
    path('rooms/<str:room_code>/leave/', RoomLeaveView.as_view(), name='room-leave'),
    path('rooms/<str:room_code>/expenses/', RoomExpenseView.as_view(), name='room-expenses'),
    path('rooms/<str:room_code>/balances/', RoomBalanceView.as_view(), name='room-balances'),
]
