from rest_framework import generics, permissions, status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q, Avg
from django.shortcuts import get_object_or_404
import django_filters

from .models import (
    MealCategory, Meal, MealLike, MealSave, MealComment,
    MealRating, MealCollection, MealCollectionItem
)
from .serializers import (
    MealCategorySerializer, MealListSerializer, MealDetailSerializer,
    MealCreateUpdateSerializer, MealCommentSerializer, MealRatingSerializer,
    MealCollectionSerializer, MealLikeSerializer, MealSaveSerializer
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
        queryset = Meal.objects.all()
        
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
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_meals(self, request):
        """Get current user's meals"""
        meals = self.queryset.filter(creator=request.user)
        page = self.paginate_queryset(meals)
        if page is not None:
            serializer = MealListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = MealListSerializer(meals, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def saved_meals(self, request):
        """Get user's saved meals"""
        saved = MealSave.objects.filter(user=request.user).values_list('meal', flat=True)
        meals = self.queryset.filter(id__in=saved)
        page = self.paginate_queryset(meals)
        if page is not None:
            serializer = MealListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = MealListSerializer(meals, many=True, context={'request': request})
        return Response(serializer.data)


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
