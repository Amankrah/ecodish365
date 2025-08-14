from django.core.management.base import BaseCommand
from meals.models import MealCategory


class Command(BaseCommand):
    help = 'Create initial meal categories'

    def handle(self, *args, **options):
        categories_data = [
            {
                'name': 'Healthy',
                'description': 'Nutritious meals focused on health and wellness',
                'icon': 'heart',
                'color': '#10b981'  # Green
            },
            {
                'name': 'Quick & Easy',
                'description': 'Simple meals that can be prepared quickly',
                'icon': 'clock',
                'color': '#f59e0b'  # Amber
            },
            {
                'name': 'Traditional',
                'description': 'Classic recipes and traditional dishes',
                'icon': 'home',
                'color': '#8b5cf6'  # Purple
            },
            {
                'name': 'International',
                'description': 'Cuisines from around the world',
                'icon': 'globe',
                'color': '#ef4444'  # Red
            },
            {
                'name': 'Vegetarian',
                'description': 'Plant-based meals without meat',
                'icon': 'leaf',
                'color': '#22c55e'  # Green
            },
            {
                'name': 'Vegan',
                'description': 'Completely plant-based meals',
                'icon': 'sprout',
                'color': '#16a34a'  # Dark green
            },
            {
                'name': 'Low Carb',
                'description': 'Meals with reduced carbohydrate content',
                'icon': 'chart-down',
                'color': '#3b82f6'  # Blue
            },
            {
                'name': 'High Protein',
                'description': 'Protein-rich meals for fitness and muscle building',
                'icon': 'muscle',
                'color': '#dc2626'  # Red
            },
            {
                'name': 'Comfort Food',
                'description': 'Hearty, satisfying meals that provide comfort',
                'icon': 'heart-filled',
                'color': '#f97316'  # Orange
            },
            {
                'name': 'Seasonal',
                'description': 'Meals featuring seasonal ingredients',
                'icon': 'sun',
                'color': '#fbbf24'  # Yellow
            }
        ]

        created_count = 0
        for category_data in categories_data:
            category, created = MealCategory.objects.get_or_create(
                name=category_data['name'],
                defaults=category_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Category already exists: {category.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} new meal categories. '
                f'Total categories: {MealCategory.objects.count()}'
            )
        )