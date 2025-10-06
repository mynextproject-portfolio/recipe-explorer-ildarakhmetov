from fastapi import APIRouter, HTTPException, UploadFile, File, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from typing import List, Optional, Dict, Any
import json
import logging
from datetime import datetime

from app.models import Recipe, RecipeCreate, RecipeUpdate
from app.services.storage import recipe_storage
from app.services.themealdb_adapter import themealdb_adapter
from app.validation import (
    RecipeValidator, validate_recipe_id, validate_search_query, validate_import_data
)
from app.error_handlers import (
    create_error_response, create_validation_error_response, 
    create_not_found_error_response, create_bad_request_error_response,
    create_server_error_response, handle_pydantic_validation_error,
    create_success_response, create_file_error_response, StatusCodes
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


@router.get("/recipes")
async def get_recipes(search: Optional[str] = None):
    """Get all recipes or search by title with validation - combines internal and external sources"""
    try:
        # Validate search query if provided
        if search is not None:
            validation_result = validate_search_query(search)
            if not validation_result.is_valid:
                return create_validation_error_response(validation_result)
        
        # Execute search or get all from internal storage
        if search:
            internal_recipes = recipe_storage.search_recipes(search)
            logger.info(f"Search query '{search}' returned {len(internal_recipes)} internal recipes")
            
            # Also search external API
            external_recipes_data = await themealdb_adapter.search_meals(search)
            external_recipes = []
            
            # Convert external recipe dicts to Recipe objects
            for recipe_data in external_recipes_data:
                try:
                    recipe = Recipe(**recipe_data)
                    external_recipes.append(recipe)
                except Exception as e:
                    logger.error(f"Error creating Recipe from external data: {str(e)}")
                    continue
            
            logger.info(f"Search query '{search}' returned {len(external_recipes)} external recipes")
            
            # Combine results
            all_recipes = internal_recipes + external_recipes
        else:
            # For non-search requests, only return internal recipes
            all_recipes = recipe_storage.get_all_recipes()
            logger.info(f"Retrieved all internal recipes: {len(all_recipes)} found")
        
        # Count by source
        internal_count = sum(1 for r in all_recipes if r.source == "internal")
        external_count = sum(1 for r in all_recipes if r.source == "external")
        
        return create_success_response(
            data={"recipes": all_recipes},
            message=f"Successfully retrieved {len(all_recipes)} recipes",
            meta={
                "count": len(all_recipes),
                "internal_count": internal_count,
                "external_count": external_count,
                "search_query": search if search else None,
                "has_search": search is not None
            }
        )
    
    except Exception as e:
        logger.error(f"Error retrieving recipes: {str(e)}")
        return create_server_error_response("Failed to retrieve recipes")


@router.get("/recipes/export")
def export_recipes():
    """Export all recipes as JSON with proper response handling"""
    try:
        recipes = recipe_storage.get_all_recipes()
        
        if not recipes:
            return create_success_response(
                data=[],
                message="No recipes found to export",
                meta={"count": 0, "action": "export"}
            )
        
        # Convert to dict for JSON serialization
        try:
            recipes_dict = [recipe.model_dump() for recipe in recipes]
        except AttributeError:
            # Fallback for older Pydantic versions
            recipes_dict = [recipe.dict() for recipe in recipes]
        logger.info(f"Exported {len(recipes)} recipes")
        
        return JSONResponse(
            content={
                "success": True,
                "message": f"Successfully exported {len(recipes)} recipes",
                "data": recipes_dict,
                "meta": {
                    "count": len(recipes),
                    "export_timestamp": str(datetime.now().isoformat()),
                    "action": "export"
                }
            },
            headers={
                "Content-Disposition": "attachment; filename=recipes_export.json",
                "Content-Type": "application/json"
            }
        )
    
    except Exception as e:
        logger.error(f"Error exporting recipes: {str(e)}")
        return create_server_error_response("Failed to export recipes")


@router.get("/recipes/internal/{recipe_id}")
def get_internal_recipe(recipe_id: str):
    """Get a specific internal recipe by ID with validation"""
    try:
        # Validate recipe ID format
        validation_result = validate_recipe_id(recipe_id)
        if not validation_result.is_valid:
            return create_validation_error_response(validation_result)
        
        # Get recipe from storage
        recipe = recipe_storage.get_recipe(recipe_id)
        if not recipe:
            return create_not_found_error_response("Internal recipe", recipe_id)
        
        logger.info(f"Retrieved internal recipe: {recipe_id}")
        
        return create_success_response(
            data=recipe,
            message="Internal recipe retrieved successfully",
            meta={"recipe_id": recipe_id, "source": "internal"}
        )
    
    except Exception as e:
        logger.error(f"Error retrieving internal recipe {recipe_id}: {str(e)}")
        return create_server_error_response("Failed to retrieve internal recipe")


@router.get("/recipes/external/{recipe_id}")
async def get_external_recipe(recipe_id: str):
    """Get a specific external recipe by ID from TheMealDB"""
    try:
        # Validate recipe ID format
        validation_result = validate_recipe_id(recipe_id)
        if not validation_result.is_valid:
            return create_validation_error_response(validation_result)
        
        # Get recipe from external API
        recipe_data = await themealdb_adapter.get_meal_by_id(recipe_id)
        
        if not recipe_data:
            return create_not_found_error_response("External recipe", recipe_id)
        
        # Convert to Recipe object
        try:
            recipe = Recipe(**recipe_data)
        except Exception as e:
            logger.error(f"Error creating Recipe from external data: {str(e)}")
            return create_server_error_response("Failed to process external recipe data")
        
        logger.info(f"Retrieved external recipe: {recipe_id}")
        
        return create_success_response(
            data=recipe,
            message="External recipe retrieved successfully",
            meta={"recipe_id": recipe_id, "source": "external"}
        )
    
    except Exception as e:
        logger.error(f"Error retrieving external recipe {recipe_id}: {str(e)}")
        return create_server_error_response("Failed to retrieve external recipe")


@router.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: str):
    """Get a specific recipe by ID with validation (deprecated - use /internal or /external endpoints)"""
    try:
        # Validate recipe ID format
        validation_result = validate_recipe_id(recipe_id)
        if not validation_result.is_valid:
            return create_validation_error_response(validation_result)
        
        # Get recipe from storage
        recipe = recipe_storage.get_recipe(recipe_id)
        if not recipe:
            return create_not_found_error_response("Recipe", recipe_id)
        
        logger.info(f"Retrieved recipe: {recipe_id}")
        
        return create_success_response(
            data=recipe,
            message="Recipe retrieved successfully",
            meta={"recipe_id": recipe_id}
        )
    
    except Exception as e:
        logger.error(f"Error retrieving recipe {recipe_id}: {str(e)}")
        return create_server_error_response("Failed to retrieve recipe")


@router.post("/recipes", status_code=StatusCodes.CREATED)
def create_recipe(recipe_data: Dict[str, Any]):
    """Create a new recipe with comprehensive validation"""
    try:
        # Additional business validation
        validation_result = RecipeValidator.validate_recipe_create(recipe_data)
        if not validation_result.is_valid:
            return create_validation_error_response(validation_result)
        
        # Create Pydantic model (this will also validate)
        try:
            recipe_create = RecipeCreate(**recipe_data)
        except ValidationError as e:
            return handle_pydantic_validation_error(e)
        
        # Create recipe in storage
        new_recipe = recipe_storage.create_recipe(recipe_create)
        logger.info(f"Created new recipe: {new_recipe.id}")
        
        return create_success_response(
            data=new_recipe,
            message="Recipe created successfully",
            meta={"recipe_id": new_recipe.id, "action": "create"}
        )
    
    except Exception as e:
        logger.error(f"Error creating recipe: {str(e)}")
        return create_server_error_response("Failed to create recipe")


@router.put("/recipes/{recipe_id}")
def update_recipe(recipe_id: str, recipe_data: Dict[str, Any]):
    """Update an existing recipe with comprehensive validation"""
    try:
        # Validate recipe ID format
        id_validation = validate_recipe_id(recipe_id)
        if not id_validation.is_valid:
            return create_validation_error_response(id_validation)
        
        # Check if recipe exists
        existing_recipe = recipe_storage.get_recipe(recipe_id)
        if not existing_recipe:
            return create_not_found_error_response("Recipe", recipe_id)
        
        # Additional business validation
        validation_result = RecipeValidator.validate_recipe_update(recipe_data)
        if not validation_result.is_valid:
            return create_validation_error_response(validation_result)
        
        # Create Pydantic model (this will also validate)
        try:
            recipe_update = RecipeUpdate(**recipe_data)
        except ValidationError as e:
            return handle_pydantic_validation_error(e)
        
        # Update recipe in storage
        updated_recipe = recipe_storage.update_recipe(recipe_id, recipe_update)
        logger.info(f"Updated recipe: {recipe_id}")
        
        return create_success_response(
            data=updated_recipe,
            message="Recipe updated successfully",
            meta={"recipe_id": recipe_id, "action": "update"}
        )
    
    except Exception as e:
        logger.error(f"Error updating recipe {recipe_id}: {str(e)}")
        return create_server_error_response("Failed to update recipe")


@router.delete("/recipes/{recipe_id}", status_code=StatusCodes.OK)
def delete_recipe(recipe_id: str):
    """Delete a recipe with proper validation and error handling"""
    try:
        # Validate recipe ID format
        validation_result = validate_recipe_id(recipe_id)
        if not validation_result.is_valid:
            return create_validation_error_response(validation_result)
        
        # Check if recipe exists before deletion
        existing_recipe = recipe_storage.get_recipe(recipe_id)
        if not existing_recipe:
            return create_not_found_error_response("Recipe", recipe_id)
        
        # Delete recipe from storage
        success = recipe_storage.delete_recipe(recipe_id)
        if not success:
            return create_server_error_response("Failed to delete recipe")
        
        logger.info(f"Deleted recipe: {recipe_id}")
        
        return create_success_response(
            data={"deleted_recipe_id": recipe_id},
            message="Recipe deleted successfully",
            meta={"recipe_id": recipe_id, "action": "delete"}
        )
    
    except Exception as e:
        logger.error(f"Error deleting recipe {recipe_id}: {str(e)}")
        return create_server_error_response("Failed to delete recipe")


@router.post("/recipes/import", status_code=StatusCodes.CREATED)
async def import_recipes(file: UploadFile = File(...)):
    """Import recipes from JSON file with comprehensive validation"""
    try:
        # Validate file type
        if not file.filename.endswith('.json'):
            return create_file_error_response(
                "Invalid file type. Only JSON files are allowed",
                {"filename": file.filename, "expected_extension": ".json"}
            )
        
        # Read and validate file size
        content = await file.read()
        max_size = 2 * 1024 * 1024  # 2MB limit
        
        if len(content) > max_size:
            return create_file_error_response(
                f"File too large. Maximum size is {max_size/1024/1024}MB",
                {
                    "file_size": len(content),
                    "max_size": max_size,
                    "filename": file.filename
                }
            )
        
        # Parse JSON
        try:
            recipes_data = json.loads(content)
        except json.JSONDecodeError as e:
            return create_bad_request_error_response(
                "Invalid JSON format in uploaded file",
                {"json_error": str(e), "filename": file.filename}
            )
        
        # Validate import data structure
        validation_result = validate_import_data(recipes_data)
        if not validation_result.is_valid:
            return create_validation_error_response(validation_result)
        
        # Import recipes
        count = recipe_storage.import_recipes(recipes_data)
        logger.info(f"Imported {count} recipes from {file.filename}")
        
        return create_success_response(
            data={"imported_count": count, "filename": file.filename},
            message=f"Successfully imported {count} recipes",
            meta={
                "total_recipes_in_file": len(recipes_data),
                "successfully_imported": count,
                "filename": file.filename,
                "action": "import"
            }
        )
    
    except Exception as e:
        logger.error(f"Error importing recipes from {file.filename}: {str(e)}")
        return create_server_error_response("Failed to import recipes")
