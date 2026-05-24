from django.contrib import admin

from .models import (
    Transaction, Category,
    Room, RoomMembership, RoomExpense, ExpenseShare,
)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'room_code', 'created_by', 'created_at')
    search_fields = ('name', 'room_code')


@admin.register(RoomMembership)
class RoomMembershipAdmin(admin.ModelAdmin):
    list_display = ('room', 'user', 'joined_at')


@admin.register(RoomExpense)
class RoomExpenseAdmin(admin.ModelAdmin):
    list_display = ('room', 'paid_by', 'amount', 'description', 'created_at')


@admin.register(ExpenseShare)
class ExpenseShareAdmin(admin.ModelAdmin):
    list_display = ('expense', 'user', 'share_amount')


admin.site.register(Transaction)
admin.site.register(Category)
