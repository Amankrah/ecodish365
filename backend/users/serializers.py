from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import UserFollowing, UserActivityLog

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = (
            'email', 'username', 'password', 'password_confirm',
            'first_name', 'last_name', 'date_of_birth', 'bio',
            'activity_level', 'dietary_preferences', 'allergies',
            'health_goals', 'daily_calorie_target'
        )
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    full_name = serializers.ReadOnlyField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    meals_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'date_of_birth', 'bio', 'profile_picture', 'activity_level',
            'dietary_preferences', 'allergies', 'health_goals', 'daily_calorie_target',
            'profile_public', 'meals_public_by_default', 'created_at', 'last_active',
            'followers_count', 'following_count', 'meals_count'
        )
        read_only_fields = ('id', 'created_at', 'last_active')
    
    def get_followers_count(self, obj):
        return obj.followers.count()
    
    def get_following_count(self, obj):
        return obj.following.count()
    
    def get_meals_count(self, obj):
        return obj.created_meals.count()


class UserPublicSerializer(serializers.ModelSerializer):
    """Serializer for public user information"""
    full_name = serializers.ReadOnlyField()
    meals_count = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'full_name', 'bio', 'profile_picture',
            'dietary_preferences', 'created_at', 'meals_count', 'followers_count'
        )
    
    def get_meals_count(self, obj):
        return obj.created_meals.filter(is_public=True).count()
    
    def get_followers_count(self, obj):
        return obj.followers.count()


class UserFollowingSerializer(serializers.ModelSerializer):
    """Serializer for user following relationships"""
    follower = UserPublicSerializer(read_only=True)
    following = UserPublicSerializer(read_only=True)
    
    class Meta:
        model = UserFollowing
        fields = ('id', 'follower', 'following', 'created_at')


class UserActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for user activity logs"""
    user = UserPublicSerializer(read_only=True)
    
    class Meta:
        model = UserActivityLog
        fields = ('id', 'user', 'activity_type', 'details', 'timestamp')