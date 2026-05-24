import secrets
import string

from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password


class Transaction(models.Model):
    UserID = models.ForeignKey(User, on_delete=models.CASCADE)
    Amount = models.FloatField()  # Field for the amount of the transaction
    CategoryID = models.ForeignKey('Category', on_delete=models.CASCADE)   # Field for the category ID of the transaction
    Description = models.CharField(max_length=255)  # Field for the description of the transaction
    TransactionDate = models.DateTimeField()  # Field for the date of the transaction
    TransactionType = models.CharField(max_length=50)  # Field for the type of the transaction (e.g., 'credit', 'debit')

    def __str__(self):
        return self.Description


class Category(models.Model):
    UserID = models.ForeignKey(User, on_delete=models.CASCADE)
    Name = models.CharField(max_length=255)  # Field for the amount of the transaction
    Description = models.CharField(max_length=255)  # Field for the description of the transaction
    TransactionDate = models.DateTimeField()  # Field for the date of the transaction


def _generate_room_code(length=6):
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(secrets.choice(alphabet) for _ in range(length))
        if not Room.objects.filter(room_code=code).exists():
            return code


class Room(models.Model):
    """A shared expense room. Anyone with room_code + password can join."""
    name = models.CharField(max_length=120)
    room_code = models.CharField(max_length=12, unique=True, db_index=True)
    password_hash = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='rooms_created'
    )
    members = models.ManyToManyField(
        User, through='RoomMembership', related_name='rooms_joined'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    def save(self, *args, **kwargs):
        if not self.room_code:
            self.room_code = _generate_room_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.room_code})"


class RoomMembership(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='room_memberships')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('room', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.room.room_code}"


class RoomExpense(models.Model):
    """An expense logged inside a room, paid by one user and split among others."""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='expenses')
    paid_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='room_expenses_paid')
    amount = models.FloatField()
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description or 'Expense'} - {self.amount} by {self.paid_by.username}"


class ExpenseShare(models.Model):
    """Each user's share of a single RoomExpense (what they owe)."""
    expense = models.ForeignKey(RoomExpense, on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expense_shares')
    share_amount = models.FloatField()

    class Meta:
        unique_together = ('expense', 'user')

    def __str__(self):
        return f"{self.user.username} owes {self.share_amount} for expense {self.expense_id}"


