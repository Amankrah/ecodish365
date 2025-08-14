from django.contrib import admin
from .models import (
    MealCategory, Meal, MealLike, MealSave, MealComment,
    MealRating, MealCollection, MealCollectionItem
)


@admin.register(MealCategory)
class MealCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'color')
    list_filter = ('color',)
    search_fields = ('name', 'description')


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'creator', 'category', 'meal_type', 'is_public', 
        'total_calories', 'sustainability_score', 'likes_count', 'created_at'
    )
    list_filter = ('meal_type', 'difficulty_level', 'is_public', 'is_featured', 'category')
    search_fields = ('name', 'description', 'tags')
    readonly_fields = ('likes_count', 'saves_count', 'views_count', 'created_at', 'updated_at')
    filter_horizontal = ()


@admin.register(MealComment)
class MealCommentAdmin(admin.ModelAdmin):
    list_display = ('meal', 'user', 'content', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content', 'meal__name', 'user__username')


@admin.register(MealRating)
class MealRatingAdmin(admin.ModelAdmin):
    list_display = ('meal', 'user', 'overall_rating', 'created_at')
    list_filter = ('overall_rating', 'created_at')
    search_fields = ('meal__name', 'user__username')


@admin.register(MealCollection)
class MealCollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'is_public', 'created_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('name', 'description')


# Register the relationship models
admin.site.register(MealLike)
admin.site.register(MealSave)
admin.site.register(MealCollectionItem)
