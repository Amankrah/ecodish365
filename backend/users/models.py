from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class CustomUser(AbstractUser):
    """Extended user model with additional profile fields"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    
    # Profile fields
    date_of_birth = models.DateField(null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    
    # Health & preferences
    activity_level = models.CharField(
        max_length=20,
        choices=[
            ('sedentary', 'Sedentary'),
            ('light', 'Lightly Active'),
            ('moderate', 'Moderately Active'),
            ('very_active', 'Very Active'),
            ('extra_active', 'Extra Active'),
        ],
        default='moderate'
    )
    
    dietary_preferences = models.JSONField(default=list, blank=True)  # ['vegetarian', 'gluten_free', etc.]
    allergies = models.JSONField(default=list, blank=True)  # ['nuts', 'dairy', etc.]
    
    # Goals
    health_goals = models.JSONField(default=list, blank=True)  # ['weight_loss', 'muscle_gain', 'sustainability', etc.]
    daily_calorie_target = models.PositiveIntegerField(null=True, blank=True)
    
    # Privacy settings
    profile_public = models.BooleanField(default=False)
    meals_public_by_default = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_active = models.DateTimeField(default=timezone.now)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    class Meta:
        db_table = 'users_customuser'


class UserFollowing(models.Model):
    """Track user following relationships"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    follower = models.ForeignKey(CustomUser, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(CustomUser, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'following')
        db_table = 'users_following'
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class UserActivityLog(models.Model):
    """Track user activity for analytics and engagement"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activity_logs')
    
    activity_type = models.CharField(
        max_length=50,
        choices=[
            ('meal_created', 'Meal Created'),
            ('meal_shared', 'Meal Shared'),
            ('meal_liked', 'Meal Liked'),
            ('meal_saved', 'Meal Saved'),
            ('profile_updated', 'Profile Updated'),
            ('user_followed', 'User Followed'),
        ]
    )
    
    details = models.JSONField(default=dict, blank=True)  # Store additional activity details
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'users_activity_log'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_type} at {self.timestamp}"
