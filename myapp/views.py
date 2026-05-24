from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction as db_transaction
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .Serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from .Serializers import TransactionSerializer
from .Serializers import CategorySerializer, ChangePasswordSerializer
from .Serializers import (
    RoomCreateSerializer,
    RoomSerializer,
    RoomExpenseSerializer,
    CreateRoomExpenseSerializer,
)

from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Transaction
from .models import Category
from .models import Room, RoomMembership, RoomExpense, ExpenseShare


class RegisterUserAPIView(generics.GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            # Serialize user data without the password
            user_data = UserSerializer(user, context=self.get_serializer_context()).data
            return Response({
                "user": user_data,
                "token": token.key
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class LoginAPIView(generics.GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({"token": token.key})
        return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

class ProtectedExampleView(APIView):
    permission_classes = [IsAuthenticated]
    print('hel')
    def get(self, request, *args, **kwargs):
        user = request.user
        transactions = Transaction.objects.filter(UserID=user).select_related('CategoryID')
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    def post(self, request, format=None):
        print('data is coming')
        print(request.data)
        user = request.user
        data = request.data
        category_id = data.get('CategoryID')

        # Ensure the Category exists and belongs to the user
        category = get_object_or_404(Category, id=category_id, UserID=user)
        serializer = TransactionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            print('data is com')
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk=None):
        print(f"Received pk: {request.data.get('id')}")
        instance = get_object_or_404(Transaction, pk=request.data.get('id'))
        print(f"Found instance: {instance}")

        serializer = TransactionSerializer(instance=instance, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk, *args, **kwargs):
        print(f"Received delete request for pk: {pk}")
        print(f"User: {request.user}")
        transaction = get_object_or_404(Transaction, pk=pk, UserID=request.user)
        print(f"Found transaction: {transaction}")
        transaction.delete()
        return Response({"detail": "Transaction deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    
    
class CategoryView(APIView):
    permission_classes = [IsAuthenticated]
    print('hel')
    def get(self, request, *args, **kwargs):
        user = request.user
        transactions = Category.objects.filter(UserID=user)
        serializer = CategorySerializer(transactions, many=True)
        return Response(serializer.data)
    
    def post(self, request, format=None):
        serializer = CategorySerializer(data=request.data, context={'request': request})
        print('data is coming')
        if serializer.is_valid():
            print('data is com')
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk=None):
        print(f"Received pk: {request.data.get('id')}")
        instance = get_object_or_404(Category, pk=request.data.get('id'))
        print(f"Found instance: {instance}")

        serializer = CategorySerializer(instance=instance, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk, *args, **kwargs):
        print(f"Received delete request for pk: {pk}")
        print(f"User: {request.user}")
        transaction = get_object_or_404(Category, pk=pk, UserID=request.user)
        print(f"Found transaction: {transaction}")
        transaction.delete()
        return Response({"detail": "Transaction deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    
      
class UserView(APIView):
    permission_classes = [IsAuthenticated]
    print('hel')
    def get(self, request, *args, **kwargs):
        user = request.user
        return Response({
            'username': user.username,
            'email': user.email
        }, status=200)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            # Assuming token authentication is used
            token = Token.objects.get(user=request.user)
            token.delete()
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Token.DoesNotExist:
            return Response({"detail": "Token not found."}, status=status.HTTP_400_BAD_REQUEST)
        

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']
            
            # Check old password
            if not user.check_password(old_password):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            
            # Set the new password
            user.set_password(new_password)
            user.save()
            
            return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def _get_member_room_or_403(room_code, user):
    """Return room if `user` is a member, else raise PermissionDenied / 404."""
    room = get_object_or_404(Room, room_code=room_code.upper())
    if not RoomMembership.objects.filter(room=room, user=user).exists():
        raise PermissionDenied("You are not a member of this room. Join it first.")
    return room


class RoomCreateView(APIView):
    """POST /api/rooms/create/  ->  create a new shared room."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = RoomCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            room = serializer.save()
            return Response(RoomSerializer(room).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoomJoinView(APIView):
    """POST /api/rooms/join/  ->  join an existing room with code + password."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        room_code = (request.data.get('room_code') or '').strip().upper()
        password = request.data.get('password') or ''
        if not room_code or not password:
            return Response(
                {"detail": "room_code and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        room = Room.objects.filter(room_code=room_code).first()
        if not room or not room.check_password(password):
            return Response(
                {"detail": "Invalid room code or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        _, created = RoomMembership.objects.get_or_create(room=room, user=request.user)
        data = RoomSerializer(room).data
        data['joined'] = created
        return Response(data, status=status.HTTP_200_OK)


class RoomListView(APIView):
    """GET /api/rooms/  ->  list rooms the current user is a member of."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        rooms = Room.objects.filter(memberships__user=request.user).distinct()
        return Response(RoomSerializer(rooms, many=True).data)


class RoomDetailView(APIView):
    """GET /api/rooms/<room_code>/  ->  details for a single room."""
    permission_classes = [IsAuthenticated]

    def get(self, request, room_code, *args, **kwargs):
        room = _get_member_room_or_403(room_code, request.user)
        return Response(RoomSerializer(room).data)


class RoomLeaveView(APIView):
    """POST /api/rooms/<room_code>/leave/  ->  leave a room."""
    permission_classes = [IsAuthenticated]

    def post(self, request, room_code, *args, **kwargs):
        room = get_object_or_404(Room, room_code=room_code.upper())
        deleted, _ = RoomMembership.objects.filter(room=room, user=request.user).delete()
        if not deleted:
            return Response(
                {"detail": "You are not a member of this room."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"detail": "Left the room."}, status=status.HTTP_200_OK)


class RoomExpenseView(APIView):
    """
    GET  /api/rooms/<room_code>/expenses/  -> list expenses in the room
    POST /api/rooms/<room_code>/expenses/  -> add a new expense (auto split)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, room_code, *args, **kwargs):
        room = _get_member_room_or_403(room_code, request.user)
        expenses = room.expenses.all().order_by('-created_at').prefetch_related('shares__user')
        return Response(RoomExpenseSerializer(expenses, many=True).data)

    def post(self, request, room_code, *args, **kwargs):
        room = _get_member_room_or_403(room_code, request.user)
        serializer = CreateRoomExpenseSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        amount = float(data['amount'])
        description = data.get('description', '')
        member_ids = set(
            RoomMembership.objects.filter(room=room).values_list('user_id', flat=True)
        )

        # Determine share map {user_id: share_amount}
        share_map = {}
        if data.get('shares'):
            # Custom shares - keys are user_id strings
            try:
                raw = {int(k): float(v) for k, v in data['shares'].items()}
            except (TypeError, ValueError):
                return Response(
                    {"shares": "Keys must be user IDs and values must be numbers."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            bad = [uid for uid in raw if uid not in member_ids]
            if bad:
                return Response(
                    {"shares": f"Users {bad} are not members of this room."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if abs(sum(raw.values()) - amount) > 0.01:
                return Response(
                    {"shares": "Sum of shares must equal the total amount."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            share_map = raw
        else:
            split_ids = data.get('split_among') or list(member_ids)
            split_ids = list({int(x) for x in split_ids})
            bad = [uid for uid in split_ids if uid not in member_ids]
            if bad:
                return Response(
                    {"split_among": f"Users {bad} are not members of this room."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not split_ids:
                return Response(
                    {"split_among": "No users to split between."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            per_head = round(amount / len(split_ids), 2)
            share_map = {uid: per_head for uid in split_ids}
            # Adjust last share to absorb rounding so totals match exactly
            diff = round(amount - per_head * len(split_ids), 2)
            if diff:
                last_uid = split_ids[-1]
                share_map[last_uid] = round(share_map[last_uid] + diff, 2)

        with db_transaction.atomic():
            expense = RoomExpense.objects.create(
                room=room,
                paid_by=request.user,
                amount=amount,
                description=description,
            )
            ExpenseShare.objects.bulk_create([
                ExpenseShare(expense=expense, user_id=uid, share_amount=amt)
                for uid, amt in share_map.items()
            ])

        expense = RoomExpense.objects.prefetch_related('shares__user').get(pk=expense.pk)
        return Response(RoomExpenseSerializer(expense).data, status=status.HTTP_201_CREATED)


class RoomBalanceView(APIView):
    """
    GET /api/rooms/<room_code>/balances/

    Returns each member's totals:
      - paid:  amount this user has paid for the room
      - owed:  sum of this user's shares across expenses
      - net:   paid - owed  (positive => is owed money, negative => owes money)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, room_code, *args, **kwargs):
        room = _get_member_room_or_403(room_code, request.user)

        memberships = RoomMembership.objects.filter(room=room).select_related('user')
        paid_totals = {}
        owed_totals = {}

        for exp in room.expenses.all().prefetch_related('shares'):
            paid_totals[exp.paid_by_id] = paid_totals.get(exp.paid_by_id, 0.0) + float(exp.amount)
            for share in exp.shares.all():
                owed_totals[share.user_id] = owed_totals.get(share.user_id, 0.0) + float(share.share_amount)

        balances = []
        for m in memberships:
            paid = round(paid_totals.get(m.user_id, 0.0), 2)
            owed = round(owed_totals.get(m.user_id, 0.0), 2)
            balances.append({
                'user_id': m.user_id,
                'username': m.user.username,
                'paid': paid,
                'owed': owed,
                'net': round(paid - owed, 2),
            })

        total_spent = round(sum(paid_totals.values()), 2)
        return Response({
            'room_code': room.room_code,
            'total_spent': total_spent,
            'balances': balances,
        })