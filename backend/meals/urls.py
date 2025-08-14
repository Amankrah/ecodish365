from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MealCategoryViewSet, MealViewSet, MealCollectionViewSet, MealRecommendationView,
    MealCommentViewSet, MealRatingViewSet
)

router = DefaultRouter()
router.register(r'categories', MealCategoryViewSet, basename='mealcategory')
router.register(r'meals', MealViewSet, basename='meal')
router.register(r'collections', MealCollectionViewSet, basename='mealcollection')

app_name = 'meals'

urlpatterns = [
    path('recommendations/', MealRecommendationView.as_view(), name='recommendations'),
    path('comments/', MealCommentViewSet.as_view({'get': 'list', 'post': 'create'}), name='comments'),
    path('ratings/', MealRatingViewSet.as_view({'get': 'list', 'post': 'create'}), name='ratings'),
    path('', include(router.urls)),
]