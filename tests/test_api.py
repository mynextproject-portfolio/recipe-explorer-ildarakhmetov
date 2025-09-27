"""
Basic smoke and contract tests for Recipe Explorer API.
These tests verify that endpoints exist and return expected status codes.
"""

def test_health_check(client):
    """Smoke test: API is running and responding"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_home_page_loads(client):
    """Smoke test: Home page renders without error"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Recipe Explorer" in response.text


def test_get_all_recipes(client, clean_storage):
    """Contract test: GET /api/recipes returns correct structure"""
    response = client.get("/api/recipes")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "recipes" in data["data"]
    assert isinstance(data["data"]["recipes"], list)


def test_create_and_get_recipe(client, clean_storage, sample_recipe_data):
    """Contract test: Create recipe and verify response structure"""
    # Create recipe
    create_response = client.post("/api/recipes", json=sample_recipe_data)
    assert create_response.status_code == 201
    
    create_data = create_response.json()
    assert create_data["success"] is True
    recipe = create_data["data"]
    assert "id" in recipe
    assert "title" in recipe
    assert "created_at" in recipe
    assert recipe["title"] == sample_recipe_data["title"]
    
    # Get recipe
    get_response = client.get(f"/api/recipes/{recipe['id']}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["success"] is True
    assert get_data["data"]["id"] == recipe["id"]


def test_recipe_not_found(client, clean_storage):
    """Contract test: Non-existent recipe returns 404"""
    response = client.get("/api/recipes/550e8400-e29b-41d4-a716-446655440000")
    assert response.status_code == 404
    data = response.json()
    assert data["error"] is True


def test_recipe_pages_load(client, clean_storage, sample_recipe_data):
    """Smoke test: Recipe HTML pages load without error"""
    # Create a recipe first
    create_response = client.post("/api/recipes", json=sample_recipe_data)
    create_data = create_response.json()
    recipe_id = create_data["data"]["id"]
    
    # Test recipe detail page
    response = client.get(f"/recipes/{recipe_id}")
    assert response.status_code == 200
    
    # Test new recipe form
    response = client.get("/recipes/new")
    assert response.status_code == 200
    
    # Test import page
    response = client.get("/import")
    assert response.status_code == 200
