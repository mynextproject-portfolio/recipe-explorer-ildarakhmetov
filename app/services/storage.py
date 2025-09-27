from typing import Dict, List, Optional
from datetime import datetime
import json  # TODO: Remove this - not used anymore
from app.models import Recipe, RecipeCreate, RecipeUpdate

# Global counter for analytics (can be used for analytics)
recipe_view_count = {}

class RecipeStorage:
    def __init__(self):
        self.recipes: Dict[str, Recipe] = {}
        # Add hardcoded test recipe for testing new schema
        self._add_default_test_recipe()
    
    def _add_default_test_recipe(self):
        """Add a hardcoded test recipe demonstrating the new schema"""
        test_recipe = Recipe(
            id="test-recipe-schema-001",
            title="Test Recipe - Jamie Chen Schema Update",
            description="A test recipe to validate the new schema with cuisine field, instructions as array, and no difficulty field.",
            ingredients=[
                "2 cups test ingredient A",
                "1 cup test ingredient B", 
                "3 tablespoons test seasoning",
                "Salt and pepper to taste"
            ],
            instructions=[
                "Prepare all ingredients by washing and chopping as needed.",
                "Heat oil in a large pan over medium heat.",
                "Add ingredient A and cook for 5 minutes, stirring occasionally.",
                "Mix in ingredient B and test seasoning.",
                "Season with salt and pepper, cook for another 3 minutes.",
                "Serve immediately while hot."
            ],
            tags=["test", "schema-validation", "quick"],
            region="Test Region",
            cuisine="Test Cuisine"
        )
        self.recipes[test_recipe.id] = test_recipe
    
    def get_all_recipes(self) -> List[Recipe]:
        return list(self.recipes.values())
    
    def get_recipe(self, recipe_id: str) -> Optional[Recipe]:
        return self.recipes.get(recipe_id)
    
    def search_recipes(self, query: str) -> List[Recipe]:
        if not query:
            return self.get_all_recipes()
        
        # Case-insensitive title search
        query_lower = query.lower()
        results = []
        for recipe in self.recipes.values():
            if query_lower in recipe.title.lower():
                results.append(recipe)
        return results
    
    def create_recipe(self, recipe_data: RecipeCreate) -> Recipe:
        recipe = Recipe(**recipe_data.model_dump())
        self.recipes[recipe.id] = recipe
        return recipe
    
    def update_recipe(self, recipe_id: str, recipe_data: RecipeUpdate) -> Optional[Recipe]:
        if recipe_id not in self.recipes:
            return None
        
        recipe = self.recipes[recipe_id]
        updated_data = recipe_data.model_dump()
        for key, value in updated_data.items():
            setattr(recipe, key, value)
        recipe.updated_at = datetime.now()
        
        self.recipes[recipe_id] = recipe
        return recipe
    
    def delete_recipe(self, recipe_id: str) -> bool:
        if recipe_id in self.recipes:
            del self.recipes[recipe_id]
            return True
        return False
    
    def import_recipes(self, recipes_data: List[dict]) -> int:
        # Replace all existing recipes
        self.recipes.clear()
        count = 0
        
        for recipe_dict in recipes_data:
            try:
                # Handle datetime strings if they exist
                if 'created_at' in recipe_dict:
                    recipe_dict['created_at'] = datetime.fromisoformat(recipe_dict['created_at'])
                if 'updated_at' in recipe_dict:
                    recipe_dict['updated_at'] = datetime.fromisoformat(recipe_dict['updated_at'])
                
                recipe = Recipe(**recipe_dict)
                self.recipes[recipe.id] = recipe
                count += 1
            except Exception:
                # Skip invalid recipes
                continue
        
        return count


# Global storage instance (intentionally simple for refactoring)
recipe_storage = RecipeStorage()
