from rest_framework import generics, permissions, status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q, Avg
from django.shortcuts import get_object_or_404
import django_filters

from .models import (
    MealCategory, Meal, MealLike, MealSave, MealComment,
    MealRating, MealCollection, MealCollectionItem, MealMedia
)
from .serializers import (
    MealCategorySerializer, MealListSerializer, MealDetailSerializer,
    MealCreateUpdateSerializer, MealCommentSerializer, MealRatingSerializer,
    MealCollectionSerializer, MealLikeSerializer, MealSaveSerializer, MealMediaSerializer
)
from .services import MealRecommendationService

User = get_user_model()


class MealFilter(django_filters.FilterSet):
    """Filter for meals"""
    meal_type = django_filters.CharFilter()
    difficulty_level = django_filters.CharFilter()
    is_public = django_filters.BooleanFilter()
    tags = django_filters.CharFilter(method='filter_tags')
    min_calories = django_filters.NumberFilter(field_name='total_calories', lookup_expr='gte')
    max_calories = django_filters.NumberFilter(field_name='total_calories', lookup_expr='lte')
    min_prep_time = django_filters.NumberFilter(field_name='preparation_time', lookup_expr='gte')
    max_prep_time = django_filters.NumberFilter(field_name='preparation_time', lookup_expr='lte')
    
    class Meta:
        model = Meal
        fields = ['meal_type', 'difficulty_level', 'is_public']
    
    def filter_tags(self, queryset, name, value):
        """Filter by tags"""
        if value:
            tag_list = [tag.strip() for tag in value.split(',')]
            for tag in tag_list:
                queryset = queryset.filter(tags__contains=tag)
        return queryset


class MealCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for meal categories"""
    queryset = MealCategory.objects.all()
    serializer_class = MealCategorySerializer
    permission_classes = [permissions.AllowAny]


class MealViewSet(viewsets.ModelViewSet):
    """ViewSet for meals"""
    queryset = Meal.objects.all()
    filterset_class = MealFilter
    search_fields = ['name', 'description', 'tags']
    ordering_fields = ['created_at', 'likes_count', 'views_count', 'sustainability_score']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action in ['list']:
            return MealListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return MealCreateUpdateSerializer
        return MealDetailSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = Meal.objects.select_related('creator', 'category').prefetch_related('media_files', 'likes', 'saves', 'comments', 'ratings')
        
        # Filter public meals for anonymous users
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_public=True)
        elif self.action == 'list':
            # Show public meals + user's own meals
            queryset = queryset.filter(
                Q(is_public=True) | Q(creator=self.request.user)
            )
        
        # Filter by creator
        creator = self.request.query_params.get('creator', None)
        if creator:
            queryset = queryset.filter(creator__username=creator)
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve meal and increment view count"""
        meal = self.get_object()
        
        # Check permissions for private meals
        if not meal.is_public and meal.creator != request.user:
            return Response(
                {'error': 'This meal is private'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Increment view count
        meal.views_count += 1
        meal.save(update_fields=['views_count'])
        
        return super().retrieve(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def recalculate(self, request, pk=None):
        """Recalculate nutrition and environmental metrics for a meal"""
        meal = self.get_object()
        
        # Check if user can edit this meal
        if meal.creator != request.user:
            return Response(
                {'error': 'Only meal creator can recalculate metrics'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Use the calculation service to recalculate all metrics
            from .services import MealCalculationService
            calculation_service = MealCalculationService()
            scores_data = calculation_service.calculate_all_scores(meal.food_items)
            
            # Update meal with new calculated data
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
            safe_np = safe_np if safe_np else {}
            
            meal.nutrient_profile = safe_np
            meal.total_calories = scores_data['total_calories']
            meal.total_weight_grams = scores_data['total_weight_grams']
            
            # Health scores
            health_scores = scores_data['health_scores']
            meal.fcs_score = health_scores.get('fcs_score')
            meal.hefi_score = health_scores.get('hefi_score')
            meal.heni_score = health_scores.get('heni_score')
            meal.heni_total_score = health_scores.get('heni_total_score')
            meal.hsr_score = health_scores.get('hsr_score')
            
            # Environmental data
            env_data = scores_data['environmental_data']
            env_impacts = env_data.get('environmental_impacts', {})
            env_impacts_with_costs = {
                **env_impacts,
                '_monetized_total_cad': env_data.get('environmental_cost_total_cad'),
                '_monetized_per_100g_cad': env_data.get('environmental_cost_per_100g_cad'),
                '_monetized_per_calorie_cad': env_data.get('environmental_cost_per_calorie_cad'),
            }
            meal.environmental_impact = env_impacts_with_costs
            meal.sustainability_score = env_data.get('sustainability_score')
            meal.carbon_footprint = env_impacts.get('Global warming') if isinstance(env_impacts, dict) else None
            
            meal.save(update_fields=[
                'nutrient_profile', 'total_calories', 'total_weight_grams',
                'fcs_score', 'hefi_score', 'heni_score', 'heni_total_score', 'hsr_score',
                'environmental_impact', 'sustainability_score', 'carbon_footprint'
            ])
            
            # Return updated meal data
            serializer = self.get_serializer(meal)
            return Response({
                'message': 'Meal metrics recalculated successfully',
                'meal': serializer.data
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to recalculate metrics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def perform_create(self, serializer):
        """Create meal with current user as creator"""
        # Use user's default privacy setting if not specified
        if 'is_public' not in serializer.validated_data:
            serializer.validated_data['is_public'] = self.request.user.meals_public_by_default
        
        serializer.save(creator=self.request.user)
        
        # Log activity
        from users.models import UserActivityLog
        UserActivityLog.objects.create(
            user=self.request.user,
            activity_type='meal_created',
            details={'meal_id': str(serializer.instance.id), 'meal_name': serializer.instance.name}
        )
    
    def perform_update(self, serializer):
        """Update meal - only creator can update"""
        if serializer.instance.creator != self.request.user:
            raise PermissionError("Only meal creator can update")
        serializer.save()
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        """Like a meal"""
        meal = self.get_object()
        like, created = MealLike.objects.get_or_create(user=request.user, meal=meal)
        
        if created:
            # Update likes count
            meal.likes_count += 1
            meal.save(update_fields=['likes_count'])
            
            # Log activity
            from users.models import UserActivityLog
            UserActivityLog.objects.create(
                user=request.user,
                activity_type='meal_liked',
                details={'meal_id': str(meal.id), 'meal_name': meal.name}
            )
            
            return Response({'message': 'Meal liked'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'Already liked'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def unlike(self, request, pk=None):
        """Unlike a meal"""
        meal = self.get_object()
        try:
            like = MealLike.objects.get(user=request.user, meal=meal)
            like.delete()
            
            # Update likes count
            meal.likes_count = max(0, meal.likes_count - 1)
            meal.save(update_fields=['likes_count'])
            
            return Response({'message': 'Meal unliked'})
        except MealLike.DoesNotExist:
            return Response({'error': 'Not liked'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def save(self, request, pk=None):
        """Save a meal"""
        meal = self.get_object()
        save, created = MealSave.objects.get_or_create(user=request.user, meal=meal)
        
        if created:
            # Update saves count
            meal.saves_count += 1
            meal.save(update_fields=['saves_count'])
            
            # Log activity
            from users.models import UserActivityLog
            UserActivityLog.objects.create(
                user=request.user,
                activity_type='meal_saved',
                details={'meal_id': str(meal.id), 'meal_name': meal.name}
            )
            
            return Response({'message': 'Meal saved'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'Already saved'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def unsave(self, request, pk=None):
        """Unsave a meal"""
        meal = self.get_object()
        try:
            save = MealSave.objects.get(user=request.user, meal=meal)
            save.delete()
            
            # Update saves count
            meal.saves_count = max(0, meal.saves_count - 1)
            meal.save(update_fields=['saves_count'])
            
            return Response({'message': 'Meal unsaved'})
        except MealSave.DoesNotExist:
            return Response({'error': 'Not saved'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated], url_path=r'my[-_]meals')
    def my_meals(self, request):
        """Get current user's meals"""
        meals = self.get_queryset().filter(creator=request.user)
        # Optional ordering (e.g., -created_at, -likes_count)
        ordering = request.query_params.get('ordering')
        if ordering:
            meals = meals.order_by(ordering)
        page = self.paginate_queryset(meals)
        if page is not None:
            serializer = MealListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = MealListSerializer(meals, many=True, context={'request': request})
        # Return a consistent paginated-like shape when pagination is not applied
        return Response({'results': serializer.data})
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated], url_path=r'saved[-_]meals')
    def saved_meals(self, request):
        """Get user's saved meals"""
        saved = MealSave.objects.filter(user=request.user).values_list('meal', flat=True)
        meals = self.get_queryset().filter(id__in=saved)
        # Optional ordering (e.g., -created_at, -likes_count, -saves_count)
        ordering = request.query_params.get('ordering')
        if ordering:
            meals = meals.order_by(ordering)
        page = self.paginate_queryset(meals)
        if page is not None:
            serializer = MealListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = MealListSerializer(meals, many=True, context={'request': request})
        # Return a consistent paginated-like shape when pagination is not applied
        return Response({'results': serializer.data})


class MealCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for meal comments"""
    serializer_class = MealCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        meal_id = self.request.query_params.get('meal_id')
        if meal_id:
            return MealComment.objects.filter(meal_id=meal_id)
        return MealComment.objects.none()
    
    def perform_create(self, serializer):
        meal_id = self.request.data.get('meal')
        meal = get_object_or_404(Meal, pk=meal_id)
        serializer.save(user=self.request.user, meal=meal)


class MealRatingViewSet(viewsets.ModelViewSet):
    """ViewSet for meal ratings"""
    serializer_class = MealRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        meal_id = self.request.query_params.get('meal_id')
        if meal_id:
            return MealRating.objects.filter(meal_id=meal_id)
        return MealRating.objects.none()
    
    def perform_create(self, serializer):
        meal_id = self.request.data.get('meal')
        meal = get_object_or_404(Meal, pk=meal_id)
        serializer.save(user=self.request.user, meal=meal)


class MealCollectionViewSet(viewsets.ModelViewSet):
    """ViewSet for meal collections"""
    serializer_class = MealCollectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.action == 'list':
            # Show public collections + user's own collections
            return MealCollection.objects.filter(
                Q(is_public=True) | Q(creator=self.request.user)
            )
        return MealCollection.objects.all()
    
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_meal(self, request, pk=None):
        """Add meal to collection"""
        collection = self.get_object()
        if collection.creator != request.user:
            return Response({'error': 'Not your collection'}, status=status.HTTP_403_FORBIDDEN)
        
        meal_id = request.data.get('meal_id')
        if not meal_id:
            return Response({'error': 'meal_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            meal = Meal.objects.get(id=meal_id)
            collection.meals.add(meal)
            return Response({'message': 'Meal added to collection'})
        except Meal.DoesNotExist:
            return Response({'error': 'Meal not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['delete'])
    def remove_meal(self, request, pk=None):
        """Remove meal from collection"""
        collection = self.get_object()
        if collection.creator != request.user:
            return Response({'error': 'Not your collection'}, status=status.HTTP_403_FORBIDDEN)
        
        meal_id = request.data.get('meal_id')
        if not meal_id:
            return Response({'error': 'meal_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            meal = Meal.objects.get(id=meal_id)
            collection.meals.remove(meal)
            return Response({'message': 'Meal removed from collection'})
        except Meal.DoesNotExist:
            return Response({'error': 'Meal not found'}, status=status.HTTP_404_NOT_FOUND)


class MealRecommendationView(generics.ListAPIView):
    """Get personalized meal recommendations"""
    serializer_class = MealListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        meal_type = self.request.query_params.get('meal_type')
        limit = int(self.request.query_params.get('limit', 10))
        
        recommendation_service = MealRecommendationService()
        recommendations = recommendation_service.get_recommendations_for_user(
            self.request.user if self.request.user.is_authenticated else None,
            meal_type=meal_type,
            limit=limit
        )
        
        # Extract meal objects from recommendations
        return [rec['meal'] for rec in recommendations]
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class MealMediaViewSet(viewsets.ModelViewSet):
    """ViewSet for meal media files"""
    serializer_class = MealMediaSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        meal_id = self.kwargs.get('meal_pk') or self.request.query_params.get('meal_id')
        if meal_id:
            return MealMedia.objects.filter(meal_id=meal_id)
        return MealMedia.objects.none()
    
    def perform_create(self, serializer):
        meal_id = self.kwargs.get('meal_pk') or self.request.data.get('meal')
        meal = get_object_or_404(Meal, pk=meal_id)
        
        # Check if user can add media to this meal
        if meal.creator != self.request.user:
            raise PermissionError("Only meal creator can add media")
        
        # If this is the first media file, make it primary
        is_primary = not meal.media_files.exists()
        
        serializer.save(meal=meal, is_primary=is_primary)
    
    def perform_update(self, serializer):
        # Check if user can update this media
        if serializer.instance.meal.creator != self.request.user:
            raise PermissionError("Only meal creator can update media")
        serializer.save()
    
    def perform_destroy(self, instance):
        # Check if user can delete this media
        if instance.meal.creator != self.request.user:
            raise PermissionError("Only meal creator can delete media")
        
        # If deleting primary media, make another media primary
        meal = instance.meal
        was_primary = instance.is_primary
        instance.delete()
        
        if was_primary:
            next_media = meal.media_files.first()
            if next_media:
                next_media.is_primary = True
                next_media.save()
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def set_primary(self, request, pk=None, meal_pk=None):
        """Set this media file as primary"""
        media = self.get_object()
        
        # Check permissions
        if media.meal.creator != request.user:
            return Response(
                {'error': 'Only meal creator can set primary media'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Unset current primary and set this one as primary
        MealMedia.objects.filter(meal=media.meal, is_primary=True).update(is_primary=False)
        media.is_primary = True
        media.save()
        
        return Response({'message': 'Primary media updated'}, status=status.HTTP_200_OK)
