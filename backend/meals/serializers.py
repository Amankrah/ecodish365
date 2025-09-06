from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    MealCategory, Meal, MealLike, MealSave, MealComment,
    MealRating, MealCollection, MealCollectionItem, MealMedia
)
from .services import MealCalculationService

User = get_user_model()


class MealMediaSerializer(serializers.ModelSerializer):
    """Serializer for meal media files"""
    file_size_mb = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    
    class Meta:
        model = MealMedia
        fields = (
            'id', 'media_type', 'file', 'thumbnail', 'caption', 'order',
            'is_primary', 'file_size', 'file_size_mb', 'duration', 'width', 'height',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'file_size', 'width', 'height')
    
    def get_file_size_mb(self, obj):
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return None
    
    def get_file(self, obj):
        """Return the full URL for the media file"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_thumbnail(self, obj):
        """Return the full URL for the thumbnail"""
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None


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
    health_score_average = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    primary_media = serializers.SerializerMethodField()
    media_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Meal
        fields = (
            'id', 'name', 'description', 'creator', 'category', 'meal_type',
            'is_public', 'is_featured', 'total_calories', 'sustainability_score',
            'preparation_time', 'cooking_time', 'servings', 'difficulty_level',
            'image', 'primary_media', 'media_count', 'likes_count', 'saves_count', 
            'comments_count', 'views_count', 'average_rating', 'health_score_average',
            'tags', 'created_at', 'is_liked', 'is_saved'
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
    
    def get_primary_media(self, obj):
        """Get the primary media file for this meal"""
        # Try to get from prefetched media_files first
        if hasattr(obj, '_prefetched_objects_cache') and 'media_files' in obj._prefetched_objects_cache:
            for media in obj._prefetched_objects_cache['media_files']:
                if media.is_primary:
                    return MealMediaSerializer(media, context=self.context).data
        else:
            # Fallback to database query
            primary = obj.media_files.filter(is_primary=True).first()
            if primary:
                return MealMediaSerializer(primary, context=self.context).data
        return None
    
    def get_media_count(self, obj):
        """Get the count of media files for this meal"""
        # Try to get from prefetched media_files first
        if hasattr(obj, '_prefetched_objects_cache') and 'media_files' in obj._prefetched_objects_cache:
            return len(obj._prefetched_objects_cache['media_files'])
        else:
            # Fallback to database query
            return obj.media_files.count()


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
    primary_media = serializers.SerializerMethodField()
    media_files = serializers.SerializerMethodField()
    media_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Meal
        fields = (
            'id', 'name', 'description', 'creator', 'category', 'meal_type',
            'is_public', 'is_featured', 'food_items', 'food_items_with_details', 'total_calories',
            'total_weight_grams', 'nutrient_profile', 'fcs_score', 'hefi_score',
            'hsr_score', 'heni_score', 'heni_total_score', 'environmental_impact', 'sustainability_score',
            'carbon_footprint', 'preparation_time', 'cooking_time', 'servings',
            'difficulty_level', 'instructions', 'tips', 'image', 'primary_media', 
            'media_files', 'media_count', 'likes_count', 'saves_count', 'comments_count', 
            'views_count', 'average_rating', 'tags', 'created_at', 'updated_at', 
            'is_liked', 'is_saved', 'health_score_average', 'overall_rating'
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
    
    def get_primary_media(self, obj):
        """Get the primary media file for this meal"""
        # Try to get from prefetched media_files first
        if hasattr(obj, '_prefetched_objects_cache') and 'media_files' in obj._prefetched_objects_cache:
            for media in obj._prefetched_objects_cache['media_files']:
                if media.is_primary:
                    return MealMediaSerializer(media, context=self.context).data
        else:
            # Fallback to database query
            primary = obj.media_files.filter(is_primary=True).first()
            if primary:
                return MealMediaSerializer(primary, context=self.context).data
        return None
    
    def get_media_files(self, obj):
        """Get all media files for this meal"""
        # Try to get from prefetched media_files first
        if hasattr(obj, '_prefetched_objects_cache') and 'media_files' in obj._prefetched_objects_cache:
            # Sort the prefetched media files
            media = sorted(obj._prefetched_objects_cache['media_files'], 
                         key=lambda x: (x.order, x.created_at))
        else:
            # Fallback to database query
            media = obj.media_files.all().order_by('order', 'created_at')
        return MealMediaSerializer(media, many=True, context=self.context).data
    
    def get_media_count(self, obj):
        """Get the count of media files for this meal"""
        # Try to get from prefetched media_files first
        if hasattr(obj, '_prefetched_objects_cache') and 'media_files' in obj._prefetched_objects_cache:
            return len(obj._prefetched_objects_cache['media_files'])
        else:
            # Fallback to database query
            return obj.media_files.count()


class MealCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating meals"""
    media_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    media_captions = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True
    )
    
    class Meta:
        model = Meal
        fields = (
            'id', 'name', 'description', 'category', 'meal_type', 'is_public',
            'food_items', 'preparation_time', 'cooking_time', 'servings',
            'difficulty_level', 'instructions', 'tips', 'image', 'tags',
            'media_files', 'media_captions'
        )
        read_only_fields = ('id',)
    
    def validate_food_items(self, value):
        """Validate food items format and existence"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Validating food items: {value}")
        
        if not value or not isinstance(value, list):
            raise serializers.ValidationError("Food items must be a non-empty list")
        
        required_fields = ['food_id', 'quantity', 'unit']
        for item in value:
            if not all(field in item for field in required_fields):
                logger.error(f"Food item missing fields: {item}, required: {required_fields}")
                raise serializers.ValidationError(
                    f"Each food item must have: {required_fields}"
                )
            
            if not isinstance(item['food_id'], int) or item['food_id'] <= 0:
                logger.error(f"Invalid food_id: {item['food_id']}")
                raise serializers.ValidationError("food_id must be a positive integer")
            
            if not isinstance(item['quantity'], (int, float)) or item['quantity'] <= 0:
                logger.error(f"Invalid quantity: {item['quantity']}")
                raise serializers.ValidationError("quantity must be a positive number")
        
        # Validate using the calculation service
        try:
            calculation_service = MealCalculationService()
            calculation_service.validate_food_items(value)
        except Exception as e:
            logger.error(f"Food validation service error: {str(e)}")
            raise serializers.ValidationError(f"Food validation error: {str(e)}")
        
        logger.info(f"Food items validation passed: {len(value)} items")
        return value
    
    def create(self, validated_data):
        """Create meal with calculated health and environmental scores"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Creating meal with validated_data keys: {list(validated_data.keys())}")
        
        # Extract media files data before creating meal
        media_files = validated_data.pop('media_files', [])
        media_captions_raw = validated_data.pop('media_captions', '')
        
        logger.info(f"Media files count: {len(media_files) if media_files else 0}")
        logger.info(f"Media captions raw: {media_captions_raw}")
        
        # Handle media_captions that might come as JSON string from FormData
        media_captions = []
        if media_captions_raw:
            if isinstance(media_captions_raw, str):
                try:
                    import json
                    media_captions = json.loads(media_captions_raw)
                    logger.info(f"Parsed media captions: {media_captions}")
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse media captions JSON: {media_captions_raw}")
                    media_captions = []
            elif isinstance(media_captions_raw, list):
                media_captions = media_captions_raw
        
        try:
            meal = super().create(validated_data)
            logger.info(f"Meal basic creation successful")
            
            self._calculate_and_save_scores(meal)
            
            # Create media files
            if media_files:
                logger.info(f"Creating {len(media_files)} media files")
                self._create_media_files(meal, media_files, media_captions)
            
            logger.info(f"Meal creation completed successfully")
            return meal
        except Exception as e:
            logger.error(f"Error during meal creation: {str(e)}")
            raise
    
    def update(self, instance, validated_data):
        """Update meal and recalculate scores if food items changed"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Updating meal {instance.id} with validated_data keys: {list(validated_data.keys())}")
        
        # Extract media files data before updating meal
        media_files = validated_data.pop('media_files', None)
        media_captions_raw = validated_data.pop('media_captions', None)
        
        logger.info(f"Media files count: {len(media_files) if media_files else 0}")
        logger.info(f"Media captions raw: {media_captions_raw}")
        
        # Handle media_captions that might come as JSON string from FormData
        media_captions = []
        if media_captions_raw:
            if isinstance(media_captions_raw, str):
                try:
                    import json
                    media_captions = json.loads(media_captions_raw)
                    logger.info(f"Parsed media captions: {media_captions}")
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse media captions JSON: {media_captions_raw}")
                    media_captions = []
            elif isinstance(media_captions_raw, list):
                media_captions = media_captions_raw
        
        old_food_items = instance.food_items
        
        try:
            meal = super().update(instance, validated_data)
            logger.info(f"Meal basic update successful")
            
            # Recalculate scores if food items changed
            if meal.food_items != old_food_items:
                logger.info(f"Food items changed, recalculating scores")
                self._calculate_and_save_scores(meal)
            
            # Update media files if provided and not empty
            if media_files is not None and len(media_files) > 0:
                logger.info(f"Creating {len(media_files)} new media files")
                # Clear existing media files and create new ones
                meal.media_files.all().delete()
                self._create_media_files(meal, media_files, media_captions)
            
            logger.info(f"Meal update completed successfully")
            return meal
        except Exception as e:
            logger.error(f"Error during meal update: {str(e)}")
            raise
    
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
    
    def _create_media_files(self, meal, media_files, media_captions):
        """Create media files for the meal"""
        try:
            import os
            from PIL import Image as PILImage
            
            for i, media_file in enumerate(media_files):
                # Determine media type
                media_type = 'image' if media_file.content_type.startswith('image/') else 'video'
                
                # Get caption (use empty string if not provided or index out of range)
                caption = media_captions[i] if i < len(media_captions) else ''
                
                # Create MealMedia instance
                meal_media = MealMedia(
                    meal=meal,
                    media_type=media_type,
                    file=media_file,
                    caption=caption,
                    order=i,
                    is_primary=(i == 0),  # First file is primary
                    file_size=media_file.size
                )
                
                # For images, try to get dimensions
                if media_type == 'image':
                    try:
                        with PILImage.open(media_file) as img:
                            meal_media.width = img.width
                            meal_media.height = img.height
                    except Exception:
                        pass  # Don't fail if we can't get dimensions
                
                meal_media.save()
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create media files for meal {meal.id}: {str(e)}")


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