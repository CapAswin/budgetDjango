from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Transaction
from .models import Category
from .models import Room, RoomMembership, RoomExpense, ExpenseShare



class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)  # Add password as write-only field

    class Meta:
        model = User
        fields = ['username', 'email', 'password']  # Include password here for validation

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def create(self, validated_data):
        # Create user with hashed password
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ('UserID',)


    def create(self, validated_data):
        validated_data['UserID'] = self.context['request'].user

        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        instance.Name = validated_data.get('Name', instance.Name)
        instance.Description = validated_data.get('Description', instance.Description)
        instance.TransactionDate = validated_data.get('TransactionDate', instance.TransactionDate)
        instance.save()
        return instance

class TransactionSerializer(serializers.ModelSerializer):
    CategoryID = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all()) 


    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ('UserID',)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['CategoryID'] = CategorySerializer(instance.CategoryID).data
        return representation
    
    def create(self, validated_data):
        validated_data['UserID'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        instance.Amount = validated_data.get('Amount', instance.Amount)
        instance.CategoryID = validated_data.get('CategoryID', instance.CategoryID)
        instance.Description = validated_data.get('Description', instance.Description)
        instance.TransactionDate = validated_data.get('TransactionDate', instance.TransactionDate)
        instance.TransactionType = validated_data.get('TransactionType', instance.TransactionType)
        instance.save()
        return instance
    


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        # Add any additional password validations here
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value


class RoomMemberSerializer(serializers.ModelSerializer):
    """Lightweight member representation used inside room responses."""
    id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    joined_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = RoomMembership
        fields = ['id', 'username', 'email', 'joined_at']


class RoomCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=4)
    room_code = serializers.CharField(required=False, allow_blank=True, max_length=12)

    class Meta:
        model = Room
        fields = ['id', 'name', 'room_code', 'password', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_room_code(self, value):
        if not value:
            return value
        value = value.strip().upper()
        if Room.objects.filter(room_code=value).exists():
            raise serializers.ValidationError("This room code is already taken.")
        return value

    def create(self, validated_data):
        raw_password = validated_data.pop('password')
        request = self.context['request']
        room = Room(
            name=validated_data['name'],
            room_code=validated_data.get('room_code') or '',
            created_by=request.user,
        )
        room.set_password(raw_password)
        room.save()
        RoomMembership.objects.create(room=room, user=request.user)
        return room


class RoomSerializer(serializers.ModelSerializer):
    members = RoomMemberSerializer(source='memberships', many=True, read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = [
            'id', 'name', 'room_code', 'created_by_username',
            'created_at', 'members', 'member_count',
        ]

    def get_member_count(self, obj):
        return obj.memberships.count()


class ExpenseShareSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ExpenseShare
        fields = ['user_id', 'username', 'share_amount']


class RoomExpenseSerializer(serializers.ModelSerializer):
    paid_by_id = serializers.IntegerField(source='paid_by.id', read_only=True)
    paid_by_username = serializers.CharField(source='paid_by.username', read_only=True)
    shares = ExpenseShareSerializer(many=True, read_only=True)

    class Meta:
        model = RoomExpense
        fields = [
            'id', 'amount', 'description', 'created_at',
            'paid_by_id', 'paid_by_username', 'shares',
        ]


class CreateRoomExpenseSerializer(serializers.Serializer):
    """Input for adding a new expense.

    - `amount`: total amount paid
    - `description`: optional label
    - `paid_by`: optional user ID who paid (defaults to current user)
    - `split_among`: optional list of user IDs to split among (defaults to all members)
    - `shares`: optional {user_id: amount} dict for custom splits; sum must equal amount
    """
    amount = serializers.FloatField(min_value=0.01)
    description = serializers.CharField(required=False, allow_blank=True, max_length=255)
    paid_by = serializers.IntegerField(required=False)
    split_among = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )
    shares = serializers.DictField(
        child=serializers.FloatField(min_value=0), required=False
    )