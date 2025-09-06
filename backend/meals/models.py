from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
import uuid
import json

User = get_user_model()


class MealCategory(models.Model):
    """Categories for different meal types"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # For frontend icons
    color = models.CharField(max_length=7, default='#007bff')  # Hex color code
    
    class Meta:
        db_table = 'meals_category'
        verbose_name_plural = 'Meal Categories'
    
    def __str__(self):
        return self.name


class Meal(models.Model):
    """Main meal model that integrates with existing food calculation systems"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic info
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_meals')
    category = models.ForeignKey(MealCategory, on_delete=models.CASCADE, related_name='meals')
    
    # Meal timing
    meal_type = models.CharField(
        max_length=20,
        choices=[
            ('breakfast', 'Breakfast'),
            ('lunch', 'Lunch'),
            ('dinner', 'Dinner'),
            ('snack', 'Snack'),
            ('dessert', 'Dessert'),
            ('beverage', 'Beverage'),
        ]
    )
    
    # Privacy settings
    is_public = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)  # For admin-curated content
    
    # Meal composition - stores food IDs and quantities
    food_items = models.JSONField(
        default=list,
        help_text="List of dicts with food_id, quantity, and unit"
    )  # [{"food_id": 123, "quantity": 100, "unit": "g"}, ...]
    
    # Calculated nutritional data (cached from your existing calculators)
    total_calories = models.FloatField(null=True, blank=True)
    total_weight_grams = models.FloatField(null=True, blank=True)
    nutrient_profile = models.JSONField(default=dict, blank=True)
    
    # Health scores (from your existing calculation systems)
    fcs_score = models.FloatField(null=True, blank=True)  # Food Choice Score
    hefi_score = models.FloatField(null=True, blank=True)  # Healthy Eating Food Index
    hsr_score = models.FloatField(null=True, blank=True)  # Health Star Rating
    heni_score = models.FloatField(null=True, blank=True)  # Health and Nutrition Index (per 100kcal)
    heni_total_score = models.FloatField(null=True, blank=True)  # Total HENI score (for minutes calculation)
    
    # Environmental impact scores
    environmental_impact = models.JSONField(default=dict, blank=True)
    sustainability_score = models.FloatField(null=True, blank=True)
    carbon_footprint = models.FloatField(null=True, blank=True)
    
    # Recipe information
    preparation_time = models.PositiveIntegerField(null=True, blank=True, help_text="Minutes")
    cooking_time = models.PositiveIntegerField(null=True, blank=True, help_text="Minutes")
    servings = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard'),
        ],
        default='easy'
    )
    
    instructions = models.TextField(blank=True)
    tips = models.TextField(blank=True)
    
    # Media
    image = models.ImageField(upload_to='meal_images/', null=True, blank=True)
    
    # Engagement metrics
    likes_count = models.PositiveIntegerField(default=0)
    saves_count = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Tags
    tags = models.JSONField(default=list, blank=True)  # ['healthy', 'quick', 'vegetarian']
    
    class Meta:
        db_table = 'meals_meal'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['creator', 'is_public']),
            models.Index(fields=['meal_type']),
            models.Index(fields=['category']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} by {self.creator.username}"
    
    def get_total_prep_time(self):
        """Get total preparation and cooking time"""
        prep = self.preparation_time or 0
        cook = self.cooking_time or 0
        return prep + cook
    
    def get_health_score_average(self):
        """Calculate average of all available health scores"""
        scores = [
            self.fcs_score, self.hefi_score, 
            self.hsr_score, self.heni_score
        ]
        valid_scores = [s for s in scores if s is not None]
        return sum(valid_scores) / len(valid_scores) if valid_scores else None
    
    def get_overall_rating(self):
        """Get overall meal rating combining health and sustainability"""
        health = self.get_health_score_average()
        sustainability = self.sustainability_score
        
        if health is not None and sustainability is not None:
            return (health + sustainability) / 2
        return health or sustainability or 50  # Default neutral score
    
    def get_primary_media(self):
        """Get the primary media file for this meal"""
        return self.media_files.filter(is_primary=True).first()
    
    def get_all_media(self):
        """Get all media files ordered by order and creation date"""
        return self.media_files.all()
    
    def get_images(self):
        """Get all image files for this meal"""
        return self.media_files.filter(media_type='image')
    
    def get_videos(self):
        """Get all video files for this meal"""
        return self.media_files.filter(media_type='video')


class MealLike(models.Model):
    """Track meal likes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'meal')
        db_table = 'meals_like'


class MealSave(models.Model):
    """Track saved meals"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='saves')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'meal')
        db_table = 'meals_save'


class MealComment(models.Model):
    """Comments on meals"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    parent_comment = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'meals_comment'
        ordering = ['-created_at']


class MealRating(models.Model):
    """User ratings for meals"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Different rating categories
    taste_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    health_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    ease_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    sustainability_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    
    overall_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'meal')
        db_table = 'meals_rating'


class MealCollection(models.Model):
    """User-created collections of meals"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_collections')
    meals = models.ManyToManyField(Meal, through='MealCollectionItem')
    
    is_public = models.BooleanField(default=False)
    cover_image = models.ImageField(upload_to='collection_covers/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'meals_collection'
        unique_together = ('creator', 'name')


class MealCollectionItem(models.Model):
    """Items in meal collections with ordering"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    collection = models.ForeignKey(MealCollection, on_delete=models.CASCADE)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'meals_collection_item'
        ordering = ['order']


class MealMedia(models.Model):
    """Media files (images/videos) associated with meals"""
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='media_files')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    file = models.FileField(upload_to='meal_media/')
    thumbnail = models.ImageField(upload_to='meal_media/thumbnails/', null=True, blank=True)
    caption = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)  # For ordering multiple media files
    is_primary = models.BooleanField(default=False)  # Primary image/video for the meal
    
    # File metadata
    file_size = models.PositiveIntegerField(null=True, blank=True)  # Size in bytes
    duration = models.FloatField(null=True, blank=True)  # For videos, duration in seconds
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'meals_media'
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['meal', 'order']),
            models.Index(fields=['meal', 'is_primary']),
        ]
    
    def __str__(self):
        return f"{self.meal.name} - {self.media_type} ({self.order})"
    
    def get_file_extension(self):
        """Get file extension from the file name"""
        if self.file:
            return self.file.name.split('.')[-1].lower()
        return None
    
    def is_image(self):
        """Check if this is an image file"""
        return self.media_type == 'image'
    
    def is_video(self):
        """Check if this is a video file"""
        return self.media_type == 'video'