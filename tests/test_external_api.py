"""
Tests for external API integration with TheMealDB.
Tests the adapter, data transformation, and combined search functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.themealdb_adapter import TheMealDBAdapter
from app.models import Recipe


# Sample TheMealDB API response
SAMPLE_THEMEALDB_MEAL = {
    "idMeal": "52772",
    "strMeal": "Teriyaki Chicken Casserole",
    "strCategory": "Chicken",
    "strArea": "Japanese",
    "strInstructions": "Preheat oven to 350°F. Cook rice according to package directions.\nMix chicken with vegetables.\nCombine sauce ingredients.\nLayer rice and chicken in casserole dish.\nBake for 30 minutes.",
    "strMealThumb": "https://www.themealdb.com/images/media/meals/wvpsxx1468256321.jpg",
    "strTags": "Meat,Casserole",
    "strIngredient1": "soy sauce",
    "strMeasure1": "3/4 cup",
    "strIngredient2": "water",
    "strMeasure2": "1/2 cup",
    "strIngredient3": "brown sugar",
    "strMeasure3": "1/4 cup",
    "strIngredient4": "chicken breasts",
    "strMeasure4": "2 pieces",
    "strIngredient5": "",
    "strMeasure5": "",
}


class TestTheMealDBAdapter:
    """Test the TheMealDB adapter functionality"""
    
    @pytest.mark.asyncio
    async def test_search_meals_success(self):
        """Test successful meal search"""
        adapter = TheMealDBAdapter()
        
        # Mock the HTTP client response
        mock_response = MagicMock()
        mock_response.json.return_value = {"meals": [SAMPLE_THEMEALDB_MEAL]}
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        
        with patch.object(adapter, '_get_client', return_value=mock_client):
            results = await adapter.search_meals("chicken")
            
            assert len(results) == 1
            recipe = results[0]
            assert recipe["id"] == "52772"
            assert recipe["title"] == "Teriyaki Chicken Casserole"
            assert recipe["source"] == "external"
            assert recipe["region"] == "Japanese"
            assert recipe["cuisine"] == "Japanese"
            assert len(recipe["ingredients"]) == 4
            assert "3/4 cup soy sauce" in recipe["ingredients"]
    
    @pytest.mark.asyncio
    async def test_search_meals_empty_query(self):
        """Test search with empty query"""
        adapter = TheMealDBAdapter()
        results = await adapter.search_meals("")
        assert results == []
    
    @pytest.mark.asyncio
    async def test_search_meals_no_results(self):
        """Test search with no results"""
        adapter = TheMealDBAdapter()
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"meals": None}
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        
        with patch.object(adapter, '_get_client', return_value=mock_client):
            results = await adapter.search_meals("nonexistent")
            assert results == []
    
    @pytest.mark.asyncio
    async def test_search_meals_api_error(self):
        """Test handling of API errors"""
        adapter = TheMealDBAdapter()
        
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("API Error")
        
        with patch.object(adapter, '_get_client', return_value=mock_client):
            results = await adapter.search_meals("chicken")
            assert results == []
    
    @pytest.mark.asyncio
    async def test_get_meal_by_id_success(self):
        """Test successful meal retrieval by ID"""
        adapter = TheMealDBAdapter()
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"meals": [SAMPLE_THEMEALDB_MEAL]}
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        
        with patch.object(adapter, '_get_client', return_value=mock_client):
            recipe = await adapter.get_meal_by_id("52772")
            
            assert recipe is not None
            assert recipe["id"] == "52772"
            assert recipe["title"] == "Teriyaki Chicken Casserole"
            assert recipe["source"] == "external"
    
    @pytest.mark.asyncio
    async def test_get_meal_by_id_not_found(self):
        """Test meal not found"""
        adapter = TheMealDBAdapter()
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"meals": None}
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        
        with patch.object(adapter, '_get_client', return_value=mock_client):
            recipe = await adapter.get_meal_by_id("99999")
            assert recipe is None
    
    @pytest.mark.asyncio
    async def test_get_meal_by_id_empty_id(self):
        """Test with empty ID"""
        adapter = TheMealDBAdapter()
        recipe = await adapter.get_meal_by_id("")
        assert recipe is None
    
    def test_transform_meal_to_recipe(self):
        """Test meal data transformation"""
        adapter = TheMealDBAdapter()
        recipe = adapter._transform_meal_to_recipe(SAMPLE_THEMEALDB_MEAL)
        
        assert recipe["id"] == "52772"
        assert recipe["title"] == "Teriyaki Chicken Casserole"
        assert recipe["source"] == "external"
        assert recipe["region"] == "Japanese"
        assert recipe["cuisine"] == "Japanese"
        assert len(recipe["ingredients"]) > 0
        assert len(recipe["instructions"]) > 0
        assert "Chicken" in recipe["tags"]
        assert len(recipe["description"]) >= 10
    
    def test_extract_ingredients(self):
        """Test ingredient extraction"""
        adapter = TheMealDBAdapter()
        ingredients = adapter._extract_ingredients(SAMPLE_THEMEALDB_MEAL)
        
        assert len(ingredients) == 4
        assert "3/4 cup soy sauce" in ingredients
        assert "1/2 cup water" in ingredients
        assert "1/4 cup brown sugar" in ingredients
        assert "2 pieces chicken breasts" in ingredients
    
    def test_parse_instructions(self):
        """Test instruction parsing"""
        adapter = TheMealDBAdapter()
        instructions_text = "Preheat oven to 350°F. Cook rice according to package directions.\nMix chicken with vegetables."
        instructions = adapter._parse_instructions(instructions_text)
        
        assert len(instructions) >= 2
        assert all(len(step) >= 5 for step in instructions)
    
    def test_parse_instructions_empty(self):
        """Test instruction parsing with empty text"""
        adapter = TheMealDBAdapter()
        instructions = adapter._parse_instructions("")
        
        assert len(instructions) == 1
        assert instructions[0] == "No instructions provided"


class TestExternalAPIEndpoints:
    """Test API endpoints for external recipe integration"""
    
    @pytest.mark.asyncio
    async def test_search_combines_internal_and_external(self, client, clean_storage, sample_recipe_data):
        """Test that search endpoint combines internal and external results"""
        # Create an internal recipe first
        client.post("/api/recipes", json=sample_recipe_data)
        
        # Mock the external API
        mock_external_recipes = [{
            "id": "52772",
            "title": "External Recipe",
            "description": "An external test recipe from TheMealDB",
            "ingredients": ["ingredient 1", "ingredient 2"],
            "instructions": ["step 1", "step 2"],
            "tags": ["external"],
            "region": "Japanese",
            "cuisine": "Japanese",
            "source": "external",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }]
        
        with patch('app.routes.api.themealdb_adapter.search_meals', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_external_recipes
            
            response = client.get("/api/recipes?search=test")
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            recipes = data["data"]["recipes"]
            
            # Should have both internal and external recipes
            assert len(recipes) >= 1  # At least one recipe
            assert data["meta"]["internal_count"] >= 1
            
            # Check if external count is included when external recipes are present
            if len(mock_external_recipes) > 0:
                assert "external_count" in data["meta"]
    
    def test_get_internal_recipe_endpoint(self, client, clean_storage, sample_recipe_data):
        """Test the /api/recipes/internal/{id} endpoint"""
        # Create a recipe
        create_response = client.post("/api/recipes", json=sample_recipe_data)
        recipe_id = create_response.json()["data"]["id"]
        
        # Get internal recipe
        response = client.get(f"/api/recipes/internal/{recipe_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == recipe_id
        assert data["meta"]["source"] == "internal"
    
    def test_get_internal_recipe_not_found(self, client, clean_storage):
        """Test internal recipe endpoint with non-existent ID"""
        response = client.get("/api/recipes/internal/nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
    
    @pytest.mark.asyncio
    async def test_get_external_recipe_endpoint(self, client):
        """Test the /api/recipes/external/{id} endpoint"""
        mock_recipe = {
            "id": "52772",
            "title": "External Recipe",
            "description": "An external test recipe from TheMealDB",
            "ingredients": ["ingredient 1", "ingredient 2"],
            "instructions": ["step 1", "step 2"],
            "tags": ["external"],
            "region": "Japanese",
            "cuisine": "Japanese",
            "source": "external",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        with patch('app.routes.api.themealdb_adapter.get_meal_by_id', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_recipe
            
            response = client.get("/api/recipes/external/52772")
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["data"]["id"] == "52772"
            assert data["data"]["source"] == "external"
            assert data["meta"]["source"] == "external"
    
    @pytest.mark.asyncio
    async def test_get_external_recipe_not_found(self, client):
        """Test external recipe endpoint with non-existent ID"""
        with patch('app.routes.api.themealdb_adapter.get_meal_by_id', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            response = client.get("/api/recipes/external/99999")
            assert response.status_code == 404
            data = response.json()
            assert data["error"] is True


class TestRecipeModelWithSource:
    """Test that Recipe model properly handles source field"""
    
    def test_recipe_with_internal_source(self, sample_recipe_data):
        """Test creating recipe with internal source"""
        recipe_data = {**sample_recipe_data, "source": "internal"}
        recipe = Recipe(**recipe_data)
        assert recipe.source == "internal"
    
    def test_recipe_with_external_source(self, sample_recipe_data):
        """Test creating recipe with external source"""
        recipe_data = {**sample_recipe_data, "source": "external"}
        recipe = Recipe(**recipe_data)
        assert recipe.source == "external"
    
    def test_recipe_default_source(self, sample_recipe_data):
        """Test that recipe defaults to internal source"""
        recipe = Recipe(**sample_recipe_data)
        assert recipe.source == "internal"
    
    def test_recipe_invalid_source(self, sample_recipe_data):
        """Test that invalid source value is rejected"""
        recipe_data = {**sample_recipe_data, "source": "invalid"}
        with pytest.raises(Exception):  # Pydantic validation error
            Recipe(**recipe_data)


class TestDataTransformationEdgeCases:
    """Test edge cases in data transformation"""
    
    def test_transform_meal_with_minimal_data(self):
        """Test transformation with minimal meal data"""
        adapter = TheMealDBAdapter()
        minimal_meal = {
            "idMeal": "12345",
            "strMeal": "Minimal Recipe",
            "strArea": "",
            "strInstructions": "",
            "strTags": "",
        }
        
        recipe = adapter._transform_meal_to_recipe(minimal_meal)
        
        assert recipe["id"] == "12345"
        assert recipe["title"] == "Minimal Recipe"
        assert len(recipe["ingredients"]) >= 1  # Should have default
        assert len(recipe["instructions"]) >= 1  # Should have default
        assert len(recipe["description"]) >= 10
    
    def test_transform_meal_with_many_ingredients(self):
        """Test transformation with maximum ingredients"""
        adapter = TheMealDBAdapter()
        meal = {"idMeal": "123", "strMeal": "Test", "strArea": "Test", "strInstructions": "Test instructions"}
        
        # Add 20 ingredients (TheMealDB maximum)
        for i in range(1, 21):
            meal[f"strIngredient{i}"] = f"ingredient {i}"
            meal[f"strMeasure{i}"] = f"{i} cup"
        
        recipe = adapter._transform_meal_to_recipe(meal)
        assert len(recipe["ingredients"]) == 20
    
    def test_extract_ingredients_with_empty_measures(self):
        """Test ingredient extraction when measures are empty"""
        adapter = TheMealDBAdapter()
        meal = {
            "strIngredient1": "salt",
            "strMeasure1": "",
            "strIngredient2": "pepper",
            "strMeasure2": None,
        }
        
        ingredients = adapter._extract_ingredients(meal)
        assert "salt" in ingredients
        assert "pepper" in ingredients
