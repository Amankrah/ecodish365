from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    MealCategory, Meal, MealLike, MealSave, MealComment,
    MealRating, MealCollection, MealCollectionItem
)
from .services import MealCalculationService

User = get_user_model()


class MealCategorySerializer(serializers.ModelSerializer):
    """Serializer for meal categories"""
    class Meta:
        model = MealCategory
        fields = ('id', 'name', 'description', 'icon', 'color')


class MealListSerializer(serializers.ModelSerializer):
    """Serializer for meal list view"""
    creator = serializers.StringRelatedField(read_only=True)
    category = MealCategorySerializer(read_only=True)
    likes_count = serializers.ReadOnlyField()
    saves_count = serializers.ReadOnlyField()
    comments_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    
    class Meta:
        model = Meal
        fields = (
            'id', 'name', 'description', 'creator', 'category', 'meal_type',
            'is_public', 'is_featured', 'total_calories', 'sustainability_score',
            'preparation_time', 'cooking_time', 'servings', 'difficulty_level',
            'image', 'likes_count', 'saves_count', 'comments_count', 'views_count',
            'average_rating', 'tags', 'created_at', 'is_liked', 'is_saved'
        )
    
    def get_comments_count(self, obj):
        return obj.comments.count()
    
    def get_average_rating(self, obj):
        ratings = obj.ratings.all()
        if ratings:
            return sum(r.overall_rating for r in ratings) / len(ratings)
        return None
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
    
    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.saves.filter(user=request.user).exists()
        return False


class MealDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed meal view"""
    creator = serializers.StringRelatedField(read_only=True)
    category = MealCategorySerializer(read_only=True)
    likes_count = serializers.ReadOnlyField()
    saves_count = serializers.ReadOnlyField()
    comments_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    health_score_average = serializers.SerializerMethodField()
    overall_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Meal
        fields = (
            'id', 'name', 'description', 'creator', 'category', 'meal_type',
            'is_public', 'is_featured', 'food_items', 'total_calories',
            'total_weight_grams', 'nutrient_profile', 'fcs_score', 'hefi_score',
            'hsr_score', 'heni_score', 'environmental_impact', 'sustainability_score',
            'carbon_footprint', 'preparation_time', 'cooking_time', 'servings',
            'difficulty_level', 'instructions', 'tips', 'image', 'likes_count',
            'saves_count', 'comments_count', 'views_count', 'average_rating',
            'tags', 'created_at', 'updated_at', 'is_liked', 'is_saved',
            'health_score_average', 'overall_rating'
        )
    
    def get_comments_count(self, obj):
        return obj.comments.count()
    
    def get_average_rating(self, obj):
        ratings = obj.ratings.all()
        if ratings:
            return sum(r.overall_rating for r in ratings) / len(ratings)
        return None
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
    
    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.saves.filter(user=request.user).exists()
        return False
    
    def get_health_score_average(self, obj):
        return obj.get_health_score_average()
    
    def get_overall_rating(self, obj):
        return obj.get_overall_rating()


class MealCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating meals"""
    class Meta:
        model = Meal
        fields = (
            'name', 'description', 'category', 'meal_type', 'is_public',
            'food_items', 'preparation_time', 'cooking_time', 'servings',
            'difficulty_level', 'instructions', 'tips', 'image', 'tags'
        )
    
    def validate_food_items(self, value):
        """Validate food items format and existence"""
        if not value or not isinstance(value, list):
            raise serializers.ValidationError("Food items must be a non-empty list")
        
        required_fields = ['food_id', 'quantity', 'unit']
        for item in value:
            if not all(field in item for field in required_fields):
                raise serializers.ValidationError(
                    f"Each food item must have: {required_fields}"
                )
            
            if not isinstance(item['food_id'], int) or item['food_id'] <= 0:
                raise serializers.ValidationError("food_id must be a positive integer")
            
            if not isinstance(item['quantity'], (int, float)) or item['quantity'] <= 0:
                raise serializers.ValidationError("quantity must be a positive number")
        
        # Validate using the calculation service
        try:
            calculation_service = MealCalculationService()
            calculation_service.validate_food_items(value)
        except Exception as e:
            raise serializers.ValidationError(f"Food validation error: {str(e)}")
        
        return value
    
    def create(self, validated_data):
        """Create meal with calculated health and environmental scores"""
        meal = super().create(validated_data)
        self._calculate_and_save_scores(meal)
        return meal
    
    def update(self, instance, validated_data):
        """Update meal and recalculate scores if food items changed"""
        old_food_items = instance.food_items
        meal = super().update(instance, validated_data)
        
        # Recalculate scores if food items changed
        if meal.food_items != old_food_items:
            self._calculate_and_save_scores(meal)
        
        return meal
    
    def _calculate_and_save_scores(self, meal):
        """Calculate and save all health and environmental scores"""
        try:
            calculation_service = MealCalculationService()
            scores_data = calculation_service.calculate_all_scores(meal.food_items)
            
            # Update meal with calculated data
            meal.nutrient_profile = scores_data['nutritional_profile']
            meal.total_calories = scores_data['total_calories']
            meal.total_weight_grams = scores_data['total_weight_grams']
            
            # Health scores
            health_scores = scores_data['health_scores']
            meal.fcs_score = health_scores.get('fcs_score')
            meal.hefi_score = health_scores.get('hefi_score')
            meal.heni_score = health_scores.get('heni_score')
            meal.hsr_score = health_scores.get('hsr_score')
            
            # Environmental data
            env_data = scores_data['environmental_data']
            meal.environmental_impact = env_data.get('environmental_impacts', {})
            meal.sustainability_score = env_data.get('sustainability_score')
            
            meal.save(update_fields=[
                'nutrient_profile', 'total_calories', 'total_weight_grams',
                'fcs_score', 'hefi_score', 'heni_score', 'hsr_score',
                'environmental_impact', 'sustainability_score'
            ])
            
        except Exception as e:
            # Log the error but don't fail meal creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to calculate meal scores for meal {meal.id}: {str(e)}")


class MealCommentSerializer(serializers.ModelSerializer):
    """Serializer for meal comments"""
    user = serializers.StringRelatedField(read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = MealComment
        fields = (
            'id', 'user', 'content', 'parent_comment', 'replies',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_replies(self, obj):
        if obj.replies.exists():
            return MealCommentSerializer(obj.replies.all(), many=True).data
        return []


class MealRatingSerializer(serializers.ModelSerializer):
    """Serializer for meal ratings"""
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = MealRating
        fields = (
            'id', 'user', 'taste_rating', 'health_rating', 'ease_rating',
            'sustainability_rating', 'overall_rating', 'review',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class MealCollectionSerializer(serializers.ModelSerializer):
    """Serializer for meal collections"""
    creator = serializers.StringRelatedField(read_only=True)
    meals_count = serializers.SerializerMethodField()
    meals = MealListSerializer(many=True, read_only=True)
    
    class Meta:
        model = MealCollection
        fields = (
            'id', 'name', 'description', 'creator', 'is_public',
            'cover_image', 'meals_count', 'meals', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_meals_count(self, obj):
        return obj.meals.count()


class MealLikeSerializer(serializers.ModelSerializer):
    """Serializer for meal likes"""
    class Meta:
        model = MealLike
        fields = ('id', 'created_at')
        read_only_fields = ('id', 'created_at')


class MealSaveSerializer(serializers.ModelSerializer):
    """Serializer for meal saves"""
    class Meta:
        model = MealSave
        fields = ('id', 'created_at')
        read_only_fields = ('id', 'created_at')