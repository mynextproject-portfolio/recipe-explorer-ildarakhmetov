from typing import Dict, List, Optional
from datetime import datetime
import json  # TODO: Remove this - not used anymore
from app.models import Recipe, RecipeCreate, RecipeUpdate
from app.services.metrics import PerformanceTimer, metrics_collector

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
        with PerformanceTimer("internal/get_all_recipes") as timer:
            result = list(self.recipes.values())
        metrics_collector.record("internal", "get_all_recipes", timer.get_duration_ms(), 
                                {"result_count": len(result)})
        return result
    
    def get_recipe(self, recipe_id: str) -> Optional[Recipe]:
        with PerformanceTimer("internal/get_recipe") as timer:
            result = self.recipes.get(recipe_id)
        metrics_collector.record("internal", "get_recipe", timer.get_duration_ms(),
                                {"recipe_id": recipe_id, "found": result is not None})
        return result
    
    def search_recipes(self, query: str) -> List[Recipe]:
        with PerformanceTimer("internal/search_recipes") as timer:
            if not query:
                return self.get_all_recipes()
            
            # Case-insensitive title search
            query_lower = query.lower()
            results = []
            for recipe in self.recipes.values():
                if query_lower in recipe.title.lower():
                    results.append(recipe)
        
        metrics_collector.record("internal", "search_recipes", timer.get_duration_ms(),
                                {"query": query, "result_count": len(results)})
        return results
    
    def create_recipe(self, recipe_data: RecipeCreate) -> Recipe:
        with PerformanceTimer("internal/create_recipe") as timer:
            recipe = Recipe(**recipe_data.model_dump())
            self.recipes[recipe.id] = recipe
        metrics_collector.record("internal", "create_recipe", timer.get_duration_ms(),
                                {"recipe_id": recipe.id})
        return recipe
    
    def update_recipe(self, recipe_id: str, recipe_data: RecipeUpdate) -> Optional[Recipe]:
        with PerformanceTimer("internal/update_recipe") as timer:
            if recipe_id not in self.recipes:
                result = None
            else:
                recipe = self.recipes[recipe_id]
                updated_data = recipe_data.model_dump()
                for key, value in updated_data.items():
                    setattr(recipe, key, value)
                recipe.updated_at = datetime.now()
                
                self.recipes[recipe_id] = recipe
                result = recipe
        
        metrics_collector.record("internal", "update_recipe", timer.get_duration_ms(),
                                {"recipe_id": recipe_id, "success": result is not None})
        return result
    
    def delete_recipe(self, recipe_id: str) -> bool:
        with PerformanceTimer("internal/delete_recipe") as timer:
            if recipe_id in self.recipes:
                del self.recipes[recipe_id]
                success = True
            else:
                success = False
        
        metrics_collector.record("internal", "delete_recipe", timer.get_duration_ms(),
                                {"recipe_id": recipe_id, "success": success})
        return success
    
    def import_recipes(self, recipes_data: List[dict]) -> int:
        with PerformanceTimer("internal/import_recipes") as timer:
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
        
        metrics_collector.record("internal", "import_recipes", timer.get_duration_ms(),
                                {"total_recipes": len(recipes_data), "imported_count": count})
        return count


# Global storage instance (intentionally simple for refactoring)
recipe_storage = RecipeStorage()
