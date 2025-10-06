"""
TheMealDB API Adapter
Handles communication with TheMealDB API and transforms data to match internal schema
"""

import httpx
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.services.metrics import PerformanceTimer, metrics_collector

logger = logging.getLogger(__name__)

class TheMealDBAdapter:
    """Adapter for TheMealDB API with error handling and data transformation"""
    
    BASE_URL = "https://www.themealdb.com/api/json/v1/1"
    TIMEOUT = 5.0  # 5 second timeout for external API calls
    
    def __init__(self):
        self.client = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create an async HTTP client"""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=self.TIMEOUT)
        return self.client
    
    async def close(self):
        """Close the HTTP client"""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def search_meals(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for meals by name in TheMealDB API
        
        Args:
            query: Search query string
            
        Returns:
            List of transformed recipe dictionaries
        """
        if not query or not query.strip():
            logger.warning("Empty search query provided to TheMealDB adapter")
            return []
        
        with PerformanceTimer("external/search_meals") as timer:
            try:
                client = await self._get_client()
                url = f"{self.BASE_URL}/search.php"
                params = {"s": query.strip()}
                
                logger.info(f"Searching TheMealDB API with query: {query}")
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                meals = data.get("meals", [])
                
                if not meals:
                    logger.info(f"No meals found in TheMealDB for query: {query}")
                    result = []
                else:
                    # Transform each meal to our internal schema
                    transformed_recipes = []
                    for meal in meals:
                        try:
                            recipe = self._transform_meal_to_recipe(meal)
                            transformed_recipes.append(recipe)
                        except Exception as e:
                            logger.error(f"Error transforming meal {meal.get('idMeal')}: {str(e)}")
                            continue
                    
                    logger.info(f"Successfully transformed {len(transformed_recipes)} meals from TheMealDB")
                    result = transformed_recipes
                
            except httpx.TimeoutException:
                logger.error(f"Timeout while searching TheMealDB for query: {query}")
                result = []
            except httpx.HTTPError as e:
                logger.error(f"HTTP error while searching TheMealDB: {str(e)}")
                result = []
            except Exception as e:
                logger.error(f"Unexpected error searching TheMealDB: {str(e)}")
                result = []
        
        metrics_collector.record("external", "search_meals", timer.get_duration_ms(),
                                {"query": query, "result_count": len(result)})
        return result
    
    async def get_meal_by_id(self, meal_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific meal by ID from TheMealDB API
        
        Args:
            meal_id: TheMealDB meal ID
            
        Returns:
            Transformed recipe dictionary or None if not found
        """
        if not meal_id:
            logger.warning("Empty meal_id provided to TheMealDB adapter")
            return None
        
        with PerformanceTimer("external/get_meal_by_id") as timer:
            try:
                client = await self._get_client()
                url = f"{self.BASE_URL}/lookup.php"
                params = {"i": meal_id}
                
                logger.info(f"Fetching meal {meal_id} from TheMealDB API")
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                meals = data.get("meals", [])
                
                if not meals or len(meals) == 0:
                    logger.warning(f"Meal {meal_id} not found in TheMealDB")
                    result = None
                else:
                    meal = meals[0]
                    recipe = self._transform_meal_to_recipe(meal)
                    
                    logger.info(f"Successfully retrieved and transformed meal {meal_id}")
                    result = recipe
                
            except httpx.TimeoutException:
                logger.error(f"Timeout while fetching meal {meal_id} from TheMealDB")
                result = None
            except httpx.HTTPError as e:
                logger.error(f"HTTP error while fetching meal {meal_id}: {str(e)}")
                result = None
            except Exception as e:
                logger.error(f"Unexpected error fetching meal {meal_id}: {str(e)}")
                result = None
        
        metrics_collector.record("external", "get_meal_by_id", timer.get_duration_ms(),
                                {"meal_id": meal_id, "found": result is not None})
        return result
    
    def _transform_meal_to_recipe(self, meal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform TheMealDB meal format to our internal Recipe schema
        
        TheMealDB format example:
        {
            "idMeal": "52772",
            "strMeal": "Teriyaki Chicken Casserole",
            "strCategory": "Chicken",
            "strArea": "Japanese",
            "strInstructions": "Preheat oven to 350°...",
            "strMealThumb": "https://...",
            "strTags": "Meat,Casserole",
            "strIngredient1": "soy sauce",
            "strMeasure1": "3/4 cup",
            ...
        }
        
        Args:
            meal: Raw meal data from TheMealDB
            
        Returns:
            Dictionary matching our Recipe schema
        """
        # Extract basic info
        meal_id = meal.get("idMeal", "")
        title = meal.get("strMeal", "Unknown Recipe")
        category = meal.get("strCategory", "")
        area = meal.get("strArea", "International")
        instructions_text = meal.get("strInstructions", "")
        tags_text = meal.get("strTags", "")
        
        # Parse ingredients and measurements
        ingredients = self._extract_ingredients(meal)
        
        # Parse instructions (split by period or newline)
        instructions = self._parse_instructions(instructions_text)
        
        # Parse tags
        tags = []
        if tags_text:
            tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
        if category and category not in tags:
            tags.append(category)
        
        # Create description from category and area
        description = self._create_description(meal)
        
        # Transform to our schema
        recipe = {
            "id": meal_id,
            "title": title,
            "description": description,
            "ingredients": ingredients,
            "instructions": instructions,
            "tags": tags[:20],  # Limit to MAX_TAGS
            "region": area if area else "International",
            "cuisine": area if area else "International",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "source": "external"
        }
        
        return recipe
    
    def _extract_ingredients(self, meal: Dict[str, Any]) -> List[str]:
        """
        Extract ingredients and measurements from TheMealDB meal data
        
        TheMealDB stores ingredients as strIngredient1-20 and strMeasure1-20
        """
        ingredients = []
        
        for i in range(1, 21):  # TheMealDB has up to 20 ingredients
            ingredient = meal.get(f"strIngredient{i}", "")
            measure = meal.get(f"strMeasure{i}", "")
            
            # Skip if ingredient is empty or None
            if not ingredient or ingredient.strip() == "":
                continue
            
            # Combine measure and ingredient
            if measure and measure.strip():
                combined = f"{measure.strip()} {ingredient.strip()}"
            else:
                combined = ingredient.strip()
            
            ingredients.append(combined)
        
        # Ensure at least one ingredient
        if not ingredients:
            ingredients = ["No ingredients listed"]
        
        return ingredients
    
    def _parse_instructions(self, instructions_text: str) -> List[str]:
        """
        Parse instruction text into a list of steps
        
        TheMealDB provides instructions as a single text block
        """
        if not instructions_text or not instructions_text.strip():
            return ["No instructions provided"]
        
        # Try to split by newlines first
        steps = []
        lines = instructions_text.split("\n")
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 5:  # Skip very short lines
                # Remove "STEP X:" prefixes if present
                line = line.replace("STEP", "").strip()
                if line.startswith(":"):
                    line = line[1:].strip()
                # Remove leading numbers and dots
                if line and line[0].isdigit():
                    line = line.lstrip("0123456789.:) ").strip()
                
                if line:
                    steps.append(line)
        
        # If we didn't get good steps from newlines, try splitting by periods
        if len(steps) < 2 and "." in instructions_text:
            sentences = instructions_text.split(".")
            steps = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        
        # If still no good steps, use the whole text as one step
        if not steps:
            steps = [instructions_text.strip()]
        
        return steps
    
    def _create_description(self, meal: Dict[str, Any]) -> str:
        """Create a description from available meal data"""
        category = meal.get("strCategory", "")
        area = meal.get("strArea", "")
        
        description_parts = []
        
        if area:
            description_parts.append(f"A delicious {area} dish")
        else:
            description_parts.append("A delicious recipe")
        
        if category:
            description_parts.append(f"from the {category} category")
        
        description_parts.append(f"This {meal.get('strMeal', 'recipe')} is sourced from TheMealDB community database.")
        
        description = " ".join(description_parts)
        
        # Ensure minimum length
        if len(description) < 10:
            description = f"This is a traditional recipe for {meal.get('strMeal', 'this dish')} from TheMealDB."
        
        return description


# Global adapter instance
themealdb_adapter = TheMealDBAdapter()
