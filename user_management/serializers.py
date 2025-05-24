from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import xx_User as User, xx_UserLevel, xx_notification as Notification

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'role', 'can_transfer_budget']
        extra_kwargs = {'password': {'write_only': True}}
 
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
 
    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid credentials")

class UserLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = xx_UserLevel
        fields = ['id', 'name', 'description', 'level_order']

class NotificationSerializer(serializers.Serializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'message', 'is_read','is_shown','is_system_read', 'created_at']