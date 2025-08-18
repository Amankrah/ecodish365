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
    creator = serializers.SerializerMethodField()
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
    
    def get_creator(self, obj):
        return obj.creator.username


class MealDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed meal view"""
    creator = serializers.SerializerMethodField()
    category = MealCategorySerializer(read_only=True)
    likes_count = serializers.ReadOnlyField()
    saves_count = serializers.ReadOnlyField()
    comments_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    health_score_average = serializers.SerializerMethodField()
    overall_rating = serializers.SerializerMethodField()
    food_items_with_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Meal
        fields = (
            'id', 'name', 'description', 'creator', 'category', 'meal_type',
            'is_public', 'is_featured', 'food_items', 'food_items_with_details', 'total_calories',
            'total_weight_grams', 'nutrient_profile', 'fcs_score', 'hefi_score',
            'hsr_score', 'heni_score', 'heni_total_score', 'environmental_impact', 'sustainability_score',
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
    
    def get_creator(self, obj):
        return obj.creator.username
    
    def get_health_score_average(self, obj):
        return obj.get_health_score_average()
    
    def get_overall_rating(self, obj):
        return obj.get_overall_rating()
    
    def get_food_items_with_details(self, obj):
        """Get food items with their descriptions from CNF database"""
        from api.food_id_finder import load_food_data
        try:
            food_df = load_food_data()
            if food_df is None:
                return obj.food_items
            
            food_items_with_details = []
            for item in obj.food_items:
                food_row = food_df[food_df['FoodID'] == item['food_id']]
                if not food_row.empty:
                    food_description = food_row.iloc[0]['FoodDescription']
                    food_items_with_details.append({
                        **item,
                        'food_description': food_description
                    })
                else:
                    food_items_with_details.append({
                        **item,
                        'food_description': f"Food ID {item['food_id']}"
                    })
            
            return food_items_with_details
        except Exception as e:
            # Fallback to original food items if there's an error
            return obj.food_items


class MealCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating meals"""
    class Meta:
        model = Meal
        fields = (
            'id', 'name', 'description', 'category', 'meal_type', 'is_public',
            'food_items', 'preparation_time', 'cooking_time', 'servings',
            'difficulty_level', 'instructions', 'tips', 'image', 'tags'
        )
        read_only_fields = ('id',)
    
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
            
            # Update meal with calculated data (ensure JSON-serializable dict)
            np = scores_data.get('nutritional_profile', {})
            if not np or not isinstance(np, dict):
                np = {}
            
            # Ensure the nutrient profile is valid JSON by creating clean dict
            safe_np = {}
            for k, v in np.items():
                try:
                    # Skip None, NaN, Inf values and ensure the key is a string
                    if (v is not None and 
                        str(v).lower() not in ['nan', 'inf', '-inf', 'none'] and
                        not (isinstance(v, float) and not (v == v))):  # Check for NaN
                        clean_value = float(v)
                        # Only include if it's a finite number
                        if isinstance(clean_value, float) and clean_value != float('inf') and clean_value != float('-inf'):
                            safe_np[str(k)] = clean_value
                except (ValueError, TypeError, OverflowError):
                    continue
            
            # Set to empty dict if nothing valid was found
            meal.nutrient_profile = safe_np if safe_np else {}
            
            # Safely set basic metrics
            meal.total_calories = scores_data.get('total_calories', 0) or 0
            meal.total_weight_grams = scores_data.get('total_weight_grams', 0) or 0
            
            # Health scores - safely extract values
            health_scores = scores_data.get('health_scores', {}) or {}
            meal.fcs_score = health_scores.get('fcs_score') if isinstance(health_scores.get('fcs_score'), (int, float)) else None
            meal.hefi_score = health_scores.get('hefi_score') if isinstance(health_scores.get('hefi_score'), (int, float)) else None
            meal.heni_score = health_scores.get('heni_score') if isinstance(health_scores.get('heni_score'), (int, float)) else None
            meal.heni_total_score = health_scores.get('heni_total_score') if isinstance(health_scores.get('heni_total_score'), (int, float)) else None
            meal.hsr_score = health_scores.get('hsr_score') if isinstance(health_scores.get('hsr_score'), (int, float)) else None
            
            # Environmental data (include monetized costs and carbon footprint)
            env_data = scores_data.get('environmental_data', {}) or {}
            env_impacts = env_data.get('environmental_impacts', {}) or {}
            
            # Build environmental impacts with costs
            env_impacts_with_costs = {}
            if isinstance(env_impacts, dict):
                env_impacts_with_costs.update(env_impacts)
            
            # Add monetization data safely
            env_cost_total = env_data.get('environmental_cost_total_cad')
            env_cost_per_100g = env_data.get('environmental_cost_per_100g_cad')
            env_cost_per_calorie = env_data.get('environmental_cost_per_calorie_cad')
            
            if isinstance(env_cost_total, (int, float)):
                env_impacts_with_costs['_monetized_total_cad'] = env_cost_total
            if isinstance(env_cost_per_100g, (int, float)):
                env_impacts_with_costs['_monetized_per_100g_cad'] = env_cost_per_100g
            if isinstance(env_cost_per_calorie, (int, float)):
                env_impacts_with_costs['_monetized_per_calorie_cad'] = env_cost_per_calorie
            
            meal.environmental_impact = env_impacts_with_costs
            
            # Sustainability score and carbon footprint
            sustainability_score = env_data.get('sustainability_score')
            meal.sustainability_score = sustainability_score if isinstance(sustainability_score, (int, float)) else None
            
            # Populate carbon_footprint if available in impacts (kg CO2-eq over analyzed weight)
            carbon_footprint = None
            if isinstance(env_impacts, dict) and 'Global warming' in env_impacts:
                gw_value = env_impacts['Global warming']
                if isinstance(gw_value, (int, float)):
                    carbon_footprint = gw_value
            meal.carbon_footprint = carbon_footprint
            
            meal.save(update_fields=[
                'nutrient_profile', 'total_calories', 'total_weight_grams',
                'fcs_score', 'hefi_score', 'heni_score', 'heni_total_score', 'hsr_score',
                'environmental_impact', 'sustainability_score', 'carbon_footprint'
            ])
            
        except Exception as e:
            # Log the error but don't fail meal creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to calculate meal scores for meal {meal.id}: {str(e)}")


class MealCommentSerializer(serializers.ModelSerializer):
    """Serializer for meal comments"""
    user = serializers.SerializerMethodField()
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
    
    def get_user(self, obj):
        return obj.user.username


class MealRatingSerializer(serializers.ModelSerializer):
    """Serializer for meal ratings"""
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = MealRating
        fields = (
            'id', 'user', 'taste_rating', 'health_rating', 'ease_rating',
            'sustainability_rating', 'overall_rating', 'review',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_user(self, obj):
        return obj.user.username


class MealCollectionSerializer(serializers.ModelSerializer):
    """Serializer for meal collections"""
    creator = serializers.SerializerMethodField()
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
    
    def get_creator(self, obj):
        return obj.creator.username


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