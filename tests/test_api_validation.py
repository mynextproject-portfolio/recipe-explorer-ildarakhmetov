"""
Comprehensive contract tests for Recipe API validation and error handling.
Tests all endpoints with various validation scenarios and HTTP status codes.
"""
import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock
from io import BytesIO

from app.main import app
from app.services.storage import recipe_storage


class TestRecipeAPIValidation:
    """Test suite for API validation and error handling"""

    def setup_method(self):
        """Clean storage before each test and ensure test recipe is available"""
        recipe_storage.recipes.clear()
        # Re-add the default test recipe that gets added on storage initialization
        recipe_storage._add_default_test_recipe()

    # ===== GET /recipes Tests =====
    
    def test_get_recipes_success_no_search(self):
        """Test successful retrieval of all recipes"""
        client = TestClient(app)
        response = client.get("/api/recipes")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "recipes" in data["data"]
        assert isinstance(data["data"]["recipes"], list)
        assert data["meta"]["count"] >= 1  # Should have test recipe
        
    def test_get_recipes_success_with_search(self):
        """Test successful search with valid query"""
        client = TestClient(app)
        response = client.get("/api/recipes?search=test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["meta"]["search_query"] == "test"
        assert data["meta"]["has_search"] is True
        
    def test_get_recipes_validation_error_empty_search(self):
        """Test 422 error for empty search query"""
        client = TestClient(app)
        response = client.get("/api/recipes?search=")
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
        assert data["error_code"] == "validation_failed"
        assert "validation_errors" in data
        
    def test_get_recipes_validation_error_long_search(self):
        """Test 422 error for search query too long"""
        client = TestClient(app)
        long_search = "x" * 101  # Exceeds 100 char limit
        response = client.get(f"/api/recipes?search={long_search}")
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
        assert "too_long" in str(data["validation_errors"]).lower()

    # ===== GET /recipes/{recipe_id} Tests =====
    
    def test_get_recipe_success(self):
        """Test successful retrieval of specific recipe"""
        client = TestClient(app)
        # Get the test recipe ID
        recipes_response = client.get("/api/recipes")
        recipe_id = recipes_response.json()["data"]["recipes"][0]["id"]
        
        response = client.get(f"/api/recipes/{recipe_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == recipe_id
        assert data["meta"]["recipe_id"] == recipe_id
        
    def test_get_recipe_not_found(self):
        """Test 404 error for non-existent recipe"""
        client = TestClient(app)
        fake_id = "550e8400-e29b-41d4-a716-446655440000"
        response = client.get(f"/api/recipes/{fake_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert data["error_code"] == "not_found"
        assert data["details"]["requested_id"] == fake_id
        
    def test_get_recipe_invalid_id_format(self):
        """Test 422 error for invalid recipe ID format"""
        client = TestClient(app)
        invalid_id = "invalid@id#format!"  # Contains invalid characters
        response = client.get(f"/api/recipes/{invalid_id}")
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
        assert "invalid" in str(data["validation_errors"]).lower()

    # ===== POST /recipes Tests =====
    
    def test_create_recipe_success(self):
        """Test successful recipe creation"""
        client = TestClient(app)
        recipe_data = {
            "title": "Test Recipe Creation",
            "description": "A test recipe for validation testing with sufficient length",
            "ingredients": ["ingredient 1", "ingredient 2"],
            "instructions": ["step 1 with enough characters", "step 2 with enough characters"],
            "tags": ["test", "validation"],
            "region": "Test Region",
            "cuisine": "Test Cuisine"
        }
        
        response = client.post("/api/recipes", json=recipe_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == recipe_data["title"]
        assert "recipe_id" in data["meta"]
        
    def test_create_recipe_validation_title_too_short(self):
        """Test 422 error for title too short"""
        client = TestClient(app)
        recipe_data = {
            "title": "AB",  # Too short
            "description": "A test recipe description that meets minimum length",
            "ingredients": ["ingredient 1"],
            "instructions": ["instruction step with enough characters"],
            "region": "Test Region",
            "cuisine": "Test Cuisine"
        }
        
        response = client.post("/api/recipes", json=recipe_data)
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
        assert any("title" in error["field"].lower() for error in data["validation_errors"])
        
    def test_create_recipe_validation_description_too_short(self):
        """Test 422 error for description too short"""
        client = TestClient(app)
        recipe_data = {
            "title": "Valid Recipe Title",
            "description": "Too short",  # Too short
            "ingredients": ["ingredient 1"],
            "instructions": ["instruction step with enough characters"],
            "region": "Test Region", 
            "cuisine": "Test Cuisine"
        }
        
        response = client.post("/api/recipes", json=recipe_data)
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
        assert any("description" in error["field"].lower() for error in data["validation_errors"])
        
    def test_create_recipe_validation_no_ingredients(self):
        """Test 422 error for missing ingredients"""
        client = TestClient(app)
        recipe_data = {
            "title": "Valid Recipe Title",
            "description": "A test recipe description that meets minimum length",
            "ingredients": [],  # Empty ingredients
            "instructions": ["instruction step with enough characters"],
            "region": "Test Region",
            "cuisine": "Test Cuisine"
        }
        
        response = client.post("/api/recipes", json=recipe_data)
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
        assert any("ingredient" in error["field"].lower() for error in data["validation_errors"])
        
    def test_create_recipe_validation_instructions_too_short(self):
        """Test 422 error for instruction steps too short"""
        client = TestClient(app)
        recipe_data = {
            "title": "Valid Recipe Title",
            "description": "A test recipe description that meets minimum length",
            "ingredients": ["ingredient 1"],
            "instructions": ["Hi"],  # Too short
            "region": "Test Region",
            "cuisine": "Test Cuisine"
        }
        
        response = client.post("/api/recipes", json=recipe_data)
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
        assert any("instruction" in error["field"].lower() for error in data["validation_errors"])
        
    def test_create_recipe_validation_missing_fields(self):
        """Test 422 error for missing required fields"""
        client = TestClient(app)
        recipe_data = {
            "title": "Valid Recipe Title"
            # Missing required fields
        }
        
        response = client.post("/api/recipes", json=recipe_data)
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
        assert len(data["validation_errors"]) > 0

    # ===== PUT /recipes/{recipe_id} Tests =====
    
    def test_update_recipe_success(self):
        """Test successful recipe update"""
        client = TestClient(app)
        # Get existing recipe ID
        recipes_response = client.get("/api/recipes")
        recipe_id = recipes_response.json()["data"]["recipes"][0]["id"]
        
        update_data = {
            "title": "Updated Recipe Title",
            "description": "Updated description with sufficient length for validation",
            "ingredients": ["updated ingredient 1", "updated ingredient 2"],
            "instructions": ["updated step 1 with enough characters", "updated step 2 with enough characters"],
            "tags": ["updated", "test"],
            "region": "Updated Region",
            "cuisine": "Updated Cuisine"
        }
        
        response = client.put(f"/api/recipes/{recipe_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == update_data["title"]
        assert data["meta"]["recipe_id"] == recipe_id
        
    def test_update_recipe_not_found(self):
        """Test 404 error for updating non-existent recipe"""
        client = TestClient(app)
        fake_id = "550e8400-e29b-41d4-a716-446655440000"
        
        update_data = {
            "title": "Updated Recipe Title",
            "description": "Updated description with sufficient length",
            "ingredients": ["ingredient 1"],
            "instructions": ["step 1 with enough characters"],
            "region": "Updated Region",
            "cuisine": "Updated Cuisine"
        }
        
        response = client.put(f"/api/recipes/{fake_id}", json=update_data)
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert data["error_code"] == "not_found"

    # ===== DELETE /recipes/{recipe_id} Tests =====
    
    def test_delete_recipe_success(self):
        """Test successful recipe deletion"""
        client = TestClient(app)
        # Create a recipe to delete
        create_data = {
            "title": "Recipe to Delete",
            "description": "A recipe that will be deleted for testing purposes",
            "ingredients": ["ingredient 1"],
            "instructions": ["step 1 with enough characters"],
            "region": "Test Region",
            "cuisine": "Test Cuisine"
        }
        
        create_response = client.post("/api/recipes", json=create_data)
        recipe_id = create_response.json()["data"]["id"]
        
        # Delete the recipe
        response = client.delete(f"/api/recipes/{recipe_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["deleted_recipe_id"] == recipe_id
        
        # Verify recipe is gone
        get_response = client.get(f"/api/recipes/{recipe_id}")
        assert get_response.status_code == 404
        
    def test_delete_recipe_not_found(self):
        """Test 404 error for deleting non-existent recipe"""
        client = TestClient(app)
        fake_id = "550e8400-e29b-41d4-a716-446655440000"
        
        response = client.delete(f"/api/recipes/{fake_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert data["error_code"] == "not_found"

    # ===== POST /recipes/import Tests =====
    
    def test_import_recipes_success(self):
        """Test successful recipe import"""
        client = TestClient(app)
        
        import_data = [
            {
                "title": "Imported Recipe 1",
                "description": "First imported recipe with sufficient description length",
                "ingredients": ["imported ingredient 1", "imported ingredient 2"],
                "instructions": ["imported step 1 with enough characters", "imported step 2 with enough characters"],
                "tags": ["imported"],
                "region": "Import Region",
                "cuisine": "Import Cuisine"
            }
        ]
        
        json_content = json.dumps(import_data)
        files = {"file": ("test_recipes.json", BytesIO(json_content.encode()), "application/json")}
        
        response = client.post("/api/recipes/import", files=files)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["imported_count"] == 1
        
    def test_import_recipes_invalid_file_type(self):
        """Test 400 error for non-JSON file"""
        client = TestClient(app)
        
        files = {"file": ("test.txt", BytesIO(b"not json content"), "text/plain")}
        response = client.post("/api/recipes/import", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True
        assert data["error_code"] == "file_error"
        
    def test_import_recipes_invalid_json(self):
        """Test 400 error for invalid JSON"""
        client = TestClient(app)
        
        invalid_json = "{'invalid': json}"
        files = {"file": ("invalid.json", BytesIO(invalid_json.encode()), "application/json")}
        
        response = client.post("/api/recipes/import", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True
        assert "Invalid JSON format" in data["message"]
        
    def test_import_recipes_validation_errors(self):
        """Test 422 error for recipes with validation issues"""
        client = TestClient(app)
        
        import_data = [
            {
                "title": "AB",  # Too short
                "description": "Short",  # Too short
                "ingredients": [],  # Empty
                "instructions": [],  # Empty
                "region": "",  # Empty
                "cuisine": ""  # Empty
            }
        ]
        
        json_content = json.dumps(import_data)
        files = {"file": ("invalid_recipes.json", BytesIO(json_content.encode()), "application/json")}
        
        response = client.post("/api/recipes/import", files=files)
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
        assert len(data["validation_errors"]) > 0

    # ===== GET /recipes/export Tests =====
    
    def test_export_recipes_success(self):
        """Test successful recipe export"""
        client = TestClient(app)
        
        response = client.get("/api/recipes/export")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        assert data["meta"]["count"] >= 1  # Should have test recipe
        assert "export_timestamp" in data["meta"]
        
    def test_export_recipes_headers(self):
        """Test export response has proper headers"""
        client = TestClient(app)
        
        response = client.get("/api/recipes/export")
        
        assert response.status_code == 200
        assert "Content-Disposition" in response.headers
        assert "recipes_export.json" in response.headers["Content-Disposition"]
        assert response.headers["Content-Type"] == "application/json"

    # ===== HTTP Status Code Validation Tests =====
    
    def test_status_codes_consistency(self):
        """Test that all endpoints return consistent HTTP status codes"""
        client = TestClient(app)
        
        # Test various scenarios and expected status codes
        test_cases = [
            ("GET", "/api/recipes", None, 200),
            ("GET", "/api/recipes/550e8400-e29b-41d4-a716-446655440000", None, 404),  # Valid UUID but nonexistent
            ("POST", "/api/recipes", {"title": "A"}, 422),  # Invalid data
            ("PUT", "/api/recipes/550e8400-e29b-41d4-a716-446655440000", {"title": "Valid Title"}, 404),  # Valid UUID but nonexistent
            ("DELETE", "/api/recipes/550e8400-e29b-41d4-a716-446655440000", None, 404),  # Valid UUID but nonexistent
            ("GET", "/api/recipes/export", None, 200),
        ]
        
        for method, url, data, expected_status in test_cases:
            if method == "GET":
                response = client.get(url)
            elif method == "POST":
                response = client.post(url, json=data)
            elif method == "PUT":
                response = client.put(url, json=data)
            elif method == "DELETE":
                response = client.delete(url)
            
            assert response.status_code == expected_status, f"{method} {url} returned {response.status_code}, expected {expected_status}"

    # ===== Edge Cases and Boundary Tests =====
    
    def test_max_length_validations(self):
        """Test maximum length validations"""
        client = TestClient(app)
        
        # Test maximum allowed values
        max_recipe_data = {
            "title": "A" * 200,  # Max title length
            "description": "A" * 2000,  # Max description length
            "ingredients": [f"ingredient {i}" for i in range(50)],  # Max ingredients
            "instructions": [f"instruction step {i} with enough characters" for i in range(50)],  # Max instructions
            "tags": [f"tag{i}" for i in range(20)],  # Max tags
            "region": "A" * 100,  # Max region length
            "cuisine": "A" * 100   # Max cuisine length
        }
        
        response = client.post("/api/recipes", json=max_recipe_data)
        assert response.status_code == 201
        
        # Test exceeding maximum values
        over_max_recipe_data = {
            "title": "A" * 201,  # Over max title length
            "description": "Valid description with sufficient length for testing",
            "ingredients": ["valid ingredient"],
            "instructions": ["valid instruction step with enough characters"],
            "region": "Valid Region",
            "cuisine": "Valid Cuisine"
        }
        
        response = client.post("/api/recipes", json=over_max_recipe_data)
        assert response.status_code == 422
        
    def test_empty_and_whitespace_handling(self):
        """Test handling of empty strings and whitespace-only values"""
        client = TestClient(app)
        
        whitespace_recipe = {
            "title": "   ",  # Whitespace only
            "description": "\\t\\n   \\t",  # Whitespace only
            "ingredients": ["   ", "\\t\\n"],  # Whitespace ingredients
            "instructions": ["   ", "\\t\\n"],  # Whitespace instructions
            "region": "   ",
            "cuisine": "   "
        }
        
        response = client.post("/api/recipes", json=whitespace_recipe)
        assert response.status_code == 422
        data = response.json()
        assert len(data["validation_errors"]) > 0
