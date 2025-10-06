# Recipe Explorer

A simple FastAPI web application for managing recipes. Features CRUD operations, search, file uploads, and a Bootstrap frontend.

**Tech Stack:** FastAPI, Jinja2, Bootstrap 5, pytest

## Quick Start

### Run Locally

```bash
# Clone and setup
git clone <repository-url>
cd recipe-explorer-template
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install and run
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Visit **http://localhost:8000**

### Run with Docker

```bash
docker build -t recipe-explorer .
docker run -p 8000:8000 recipe-explorer
```

Visit **http://localhost:8000**

## Sample Data

Upload the `sample-recipes.json` file using the "Import Recipes" page to get started with 3 example recipes (Poutine, Shuba, Guo Bao Rou).

## Testing

```bash
pytest           # Run all tests
pytest -v        # Verbose output
```

## Performance Metrics

The API automatically measures and reports response times for internal database queries vs external TheMealDB API calls.

### Features

- **Automatic Timing**: All database queries and external API calls are automatically timed
- **Performance Metadata**: API responses include timing data in the `meta.performance` field
- **Metrics Endpoint**: Access aggregated statistics at `GET /api/metrics`
- **Performance Comparison**: See which data source (internal/external) is faster

### Example Response with Metrics

```json
{
  "success": true,
  "data": {
    "recipes": [...]
  },
  "meta": {
    "count": 5,
    "internal_count": 2,
    "external_count": 3,
    "performance": {
      "internal_query_ms": 0.25,
      "external_api_ms": 145.32,
      "total_request_ms": 156.78
    }
  }
}
```

### Viewing Metrics

Access the metrics endpoint to see aggregated statistics:

```bash
curl http://localhost:8000/api/metrics
```

This shows:
- Average response times for internal vs external sources
- Per-operation statistics (min/max/avg)
- Performance comparison and speedup factors
- Recent operation history

## API Endpoints

**Pages:**
- `/` - Home page with recipe list
- `/recipes/new` - Add recipe form  
- `/recipes/{id}` - Recipe detail page
- `/import` - Import recipes

**API:**
- `GET /api/recipes` - List/search recipes (includes performance metrics in response)
- `POST /api/recipes` - Create recipe
- `GET /api/recipes/{id}` - Get recipe
- `PUT /api/recipes/{id}` - Update recipe
- `DELETE /api/recipes/{id}` - Delete recipe
- `POST /api/recipes/import` - Import JSON
- `GET /api/recipes/export` - Export JSON
- `GET /api/metrics` - View performance metrics
- `DELETE /api/metrics` - Clear performance metrics

---

*Part of [mynextproject.dev](https://mynextproject.dev) - Learn to code like a professional*
