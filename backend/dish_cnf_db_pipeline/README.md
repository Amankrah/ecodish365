# Canadian Nutrient File (CNF) Data Pipeline

A comprehensive, well-engineered system for exploring and managing Canadian Nutrient File data with advanced search, comparison, and analytics capabilities.

## 🚀 Key Features

### Data Exploration & Search
- **Advanced Text Search**: Intelligent search with relevance scoring and pagination
- **Nutrient-Based Search**: Find foods by nutrient content with min/max value filters
- **Food Group Exploration**: Browse foods by category
- **Food Comparison**: Compare nutritional content of multiple foods side-by-side
- **Database Analytics**: Comprehensive statistics and insights

### Data Management
- **CRUD Operations**: Full create, read, update, delete functionality for foods
- **Batch Operations**: Efficient bulk food import/export
- **Transaction Support**: Atomic operations with rollback capability
- **Data Validation**: Comprehensive input validation and error handling
- **Data Integrity Checks**: Automated quality assurance

### Performance & Reliability
- **Caching**: Intelligent caching for improved performance
- **Search Indexing**: Optimized search performance
- **Error Handling**: Robust error handling with proper logging
- **Transaction Management**: Database-like transaction support

## 📚 API Endpoints

### Food Management
```
POST   /api/cnf/foods/                    # Add single food
POST   /api/cnf/foods/batch/             # Batch add foods
GET    /api/cnf/foods/{id}/              # Get food details
PUT    /api/cnf/foods/{id}/              # Update food
DELETE /api/cnf/foods/{id}/              # Delete food
```

### Search & Exploration
```
GET    /api/cnf/search/?q={query}&limit={limit}&offset={offset}
GET    /api/cnf/search/by-nutrient/?nutrient_id={id}&min_value={min}&max_value={max}
GET    /api/cnf/groups/{group_id}/foods/
POST   /api/cnf/compare/                 # Compare multiple foods
```

### Reference Data
```
GET    /api/cnf/food-groups/
GET    /api/cnf/food-sources/
GET    /api/cnf/nutrient-sources/
GET    /api/cnf/nutrients/
GET    /api/cnf/measures/
```

### Analytics & Quality
```
GET    /api/cnf/statistics/              # Database statistics
GET    /api/cnf/integrity-check/         # Data integrity check
POST   /api/cnf/export/                  # Export food data
```

## 🏗️ Architecture

### Core Components

1. **CNFDataPipeline** - Main orchestrator
   - Coordinates all operations
   - Provides clean API interface
   - Manages search indexing

2. **CNFDataLoader** - Data loading and persistence
   - CSV file management
   - Encoding detection
   - Data type validation

3. **CNFDataProcessor** - Data manipulation
   - CRUD operations
   - Transaction management
   - Data validation

4. **FoodInputValidator** - Input validation
   - Data structure validation
   - Business rule enforcement
   - Error message generation

### Key Improvements Made

#### 🔧 Eliminated Code Duplication
- Unified food creation logic between single and batch operations
- Centralized validation logic
- Shared error handling patterns

#### ⚡ Performance Enhancements
- Added search indexing for faster text searches
- Implemented intelligent caching with `@lru_cache`
- Optimized batch operations for large datasets

#### 🛡️ Robust Error Handling
- Transaction support with automatic rollback
- Comprehensive error logging
- Consistent API error responses

#### 🔍 Enhanced User Exploration
- **Relevance-scored search** with pagination
- **Nutrient-based filtering** for dietary analysis
- **Food comparison tools** for nutritional analysis
- **Advanced analytics** with database insights

#### 📊 Data Quality Assurance
- Automated integrity checks
- Orphaned record detection
- Duplicate data identification
- Comprehensive validation

## 💡 Usage Examples

### Search Foods
```python
# Text search with pagination
results = cnf_pipeline.search_foods("apple", limit=20, offset=0)

# Search by nutrient content (e.g., high protein foods)
protein_foods = cnf_pipeline.search_foods_by_nutrient(
    nutrient_id=203,  # Protein
    min_value=20.0,   # At least 20g protein
    limit=50
)
```

### Compare Foods
```python
# Compare nutritional content
comparison = cnf_pipeline.compare_foods(
    food_ids=[1234, 5678, 9012],
    nutrient_ids=[203, 204, 205]  # Protein, Fat, Carbs
)
```

### Data Management
```python
# Add single food with validation
food_id = cnf_pipeline.add_food(food_data, validate=True)

# Batch add foods efficiently
food_ids = cnf_pipeline.add_foods_batch(foods_list, validate=True)

# Update food with transaction support
updated_food = cnf_pipeline.update_food(food_id, updated_data)
```

### Analytics
```python
# Get database statistics
stats = cnf_pipeline.get_database_statistics()

# Check data integrity
integrity_report = cnf_pipeline.check_data_integrity()
```

## 🔧 Configuration

### Environment Variables
- `DJANGO_ENV=development` - Enables development mode with debug features
- `DJANGO_SECRET_KEY` - Django secret key for production

### Settings
- `CNF_FOLDER` - Path to CNF CSV data files
- Logging configuration for different environments
- Caching settings for performance optimization

## 🧪 Testing

The system includes comprehensive error handling and validation:

```python
# All operations include proper error handling
try:
    food_id = cnf_pipeline.add_food(food_data)
except ValidationError as e:
    # Handle validation errors
    print(f"Validation failed: {e}")
except Exception as e:
    # Handle unexpected errors
    print(f"Operation failed: {e}")
```

## 📈 Performance Considerations

1. **Search Performance**: Uses indexed search for O(log n) lookup
2. **Batch Operations**: Optimized for large datasets (up to 100 foods per batch)
3. **Caching**: Intelligent caching reduces database hits
4. **Memory Management**: Efficient pandas operations for large datasets

## 🔄 Migration Guide

### From Legacy API
The system maintains backward compatibility with old endpoints:

- `/cnf/add-food-to-cnf/` → `/cnf/foods/`
- `/cnf/food/{id}/` → `/cnf/foods/{id}/`
- Basic search → Advanced search with pagination

### New Features Available
- Food comparison functionality
- Nutrient-based search
- Comprehensive analytics
- Data export capabilities
- Enhanced error handling

## 🎯 Best Practices

1. **Always validate input** when adding/updating foods
2. **Use batch operations** for multiple foods
3. **Implement proper error handling** in your applications
4. **Cache results** where appropriate
5. **Monitor data integrity** regularly

This refactored system provides a solid foundation for nutritional data exploration while maintaining clean, maintainable code that follows best practices for enterprise-level applications. 