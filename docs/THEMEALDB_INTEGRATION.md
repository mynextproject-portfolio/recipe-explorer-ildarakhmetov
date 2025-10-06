# TheMealDB API Integration

## Overview

This document describes the integration of TheMealDB API into the Recipe Explorer application, enabling users to search and view thousands of additional recipes from an external source alongside internal recipes.

## Features

### 1. **TheMealDB API Adapter**
- Located in `app/services/themealdb_adapter.py`
- Handles all communication with TheMealDB API
- Implements comprehensive error handling for API failures
- Uses async HTTP client with configurable timeout (5 seconds)
- Gracefully handles timeouts, HTTP errors, and network issues

### 2. **Source Field**
- All recipes now include a `source` field with values:
  - `"internal"` - Recipes created and stored in the application
  - `"external"` - Recipes from TheMealDB API
- The field uses Pydantic's `Literal` type for validation
- Defaults to `"internal"` for backward compatibility

### 3. **Enhanced Search Endpoint**
- `GET /api/recipes?search={query}`
- Searches both internal database AND TheMealDB API simultaneously
- Combines results from both sources
- Returns metadata with counts for internal and external recipes
- Without search query, returns only internal recipes

### 4. **New Source-Specific Endpoints**

#### Get Internal Recipe
```
GET /api/recipes/internal/{recipe_id}
```
Retrieves a recipe from the internal database by ID.

#### Get External Recipe
```
GET /api/recipes/external/{recipe_id}
```
Retrieves a recipe from TheMealDB API by ID.

### 5. **Data Transformation**
- Transforms TheMealDB format to internal Recipe schema
- Maps 20 ingredient/measure pairs to ingredient list
- Splits instructions text into structured steps
- Extracts tags from categories and tags field
- Generates descriptions from available data
- Handles edge cases and missing data gracefully

## API Response Format

### Search Response
```json
{
  "success": true,
  "message": "Successfully retrieved X recipes",
  "data": {
    "recipes": [
      {
        "id": "52772",
        "title": "Teriyaki Chicken Casserole",
        "description": "A delicious Japanese dish from the Chicken category...",
        "ingredients": ["3/4 cup soy sauce", "1/2 cup water", ...],
        "instructions": ["Preheat oven to 350°F", "Cook rice...", ...],
        "tags": ["Meat", "Casserole", "Chicken"],
        "region": "Japanese",
        "cuisine": "Japanese",
        "source": "external",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
      }
    ]
  },
  "meta": {
    "count": 15,
    "internal_count": 5,
    "external_count": 10,
    "search_query": "chicken",
    "has_search": true
  }
}
```

## Error Handling

### External API Failures
- API timeouts return empty results instead of crashing
- HTTP errors are logged and return empty results
- Invalid data is skipped with error logging
- Internal recipes always returned even if external API fails

### Validation
- All external recipe data validated against Recipe schema
- Invalid recipes skipped with logging
- Ensures data consistency across sources

## TheMealDB Data Mapping

| TheMealDB Field | Internal Field | Notes |
|----------------|----------------|-------|
| `idMeal` | `id` | Direct mapping |
| `strMeal` | `title` | Direct mapping |
| `strCategory` | `tags` | Added as tag |
| `strArea` | `region`, `cuisine` | Used for both fields |
| `strInstructions` | `instructions` | Split into steps |
| `strIngredient1-20` + `strMeasure1-20` | `ingredients` | Combined as "measure ingredient" |
| `strTags` | `tags` | Split by comma |
| Generated | `description` | Created from category and area |
| Generated | `source` | Always "external" |

## Testing

### Test Coverage
- **23 new tests** in `tests/test_external_api.py`
- Tests adapter functionality
- Tests data transformation
- Tests API endpoint integration
- Tests error handling scenarios
- Tests edge cases (minimal data, empty fields, etc.)

### Running Tests
```bash
source .venv/bin/activate
python -m pytest tests/test_external_api.py -v
```

### Test Categories
1. **Adapter Tests**: API communication, error handling
2. **Endpoint Tests**: Combined search, source-specific endpoints
3. **Model Tests**: Source field validation
4. **Transformation Tests**: Edge cases, data mapping

## Dependencies

Added to `requirements.txt`:
- `pytest-asyncio==0.23.3` - For testing async functions
- `httpx==0.26.0` - Already present, used for HTTP requests

## Usage Examples

### Search Combined Results
```python
# Search both internal and external sources
response = await client.get("/api/recipes?search=chicken")
recipes = response.json()["data"]["recipes"]

# Filter by source
internal = [r for r in recipes if r["source"] == "internal"]
external = [r for r in recipes if r["source"] == "external"]
```

### Get Internal Recipe
```python
response = await client.get("/api/recipes/internal/my-recipe-id")
recipe = response.json()["data"]
```

### Get External Recipe
```python
response = await client.get("/api/recipes/external/52772")
recipe = response.json()["data"]
```

## Future Enhancements

The following features are planned for future milestones:
- **Caching**: Cache external API responses to reduce API calls
- **Rate Limiting**: Implement rate limiting for external API calls
- **Pagination**: Add pagination for large result sets
- **Favorites**: Allow users to favorite external recipes
- **Import External**: Import external recipes to internal database

## Architecture Decisions

### Real-Time API Calls
- Current implementation uses real-time API calls (no caching)
- Ensures fresh data from TheMealDB
- Caching planned for next milestone

### Async HTTP Client
- Uses `httpx.AsyncClient` for non-blocking requests
- Allows concurrent internal and external searches
- Improves response time for combined queries

### Error Resilience
- External API failures don't crash the application
- Internal recipes always available
- Graceful degradation when external API unavailable

## Troubleshooting

### External Recipes Not Showing
1. Check network connectivity
2. Verify TheMealDB API is accessible: `https://www.themealdb.com/api/json/v1/1/search.php?s=chicken`
3. Check logs for error messages
4. Increase timeout if needed in `themealdb_adapter.py`

### Validation Errors
- External recipes must meet internal schema requirements
- Check logs for specific validation errors
- Invalid recipes are skipped automatically

### Performance Issues
- External API calls add latency (5s timeout)
- Consider implementing caching (future milestone)
- Use source-specific endpoints when source is known
