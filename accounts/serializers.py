from rest_framework import serializers
from .models import User , Notification

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone', 'gender', 'date_of_birth', 'state', 'location', 'latitude', 'longitude', 'address', 'password']
        extra_kwargs = {
            'password': {'write_only': True},  
        }

    def create(self, validated_data):
        user = User(
            full_name=validated_data['full_name'],
            email=validated_data['email'],
            phone=validated_data['phone'],
            gender=validated_data['gender'],
            date_of_birth=validated_data['date_of_birth'],
            state=validated_data['state'],
            address=validated_data['address'],
        )
        user.set_password(validated_data['password']) 
        user.save()
        return user


class AllUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'phone', 'state', 'is_active']
        



class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'doctor', 'type', 'message', 'is_read', 'created_at']
