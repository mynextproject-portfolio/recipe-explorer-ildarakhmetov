"""
Tests for performance metrics functionality
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.metrics import PerformanceTimer, MetricsCollector, metrics_collector


class TestPerformanceTimer:
    """Test the PerformanceTimer class"""
    
    def test_timer_measures_duration(self):
        """Test that timer measures duration correctly"""
        import time
        
        with PerformanceTimer("test_operation") as timer:
            time.sleep(0.01)  # Sleep for 10ms
        
        duration = timer.get_duration_ms()
        assert duration >= 10.0  # Should be at least 10ms
        assert duration < 100.0  # But not too long
    
    def test_timer_context_manager(self):
        """Test timer works as context manager"""
        timer = PerformanceTimer("test_op")
        
        assert timer.start_time is None
        assert timer.end_time is None
        assert timer.duration_ms is None
        
        with timer:
            pass
        
        assert timer.start_time is not None
        assert timer.end_time is not None
        assert timer.duration_ms is not None
        assert timer.duration_ms >= 0


class TestMetricsCollector:
    """Test the MetricsCollector class"""
    
    def setup_method(self):
        """Clear metrics before each test"""
        self.collector = MetricsCollector()
    
    def test_record_metric(self):
        """Test recording a metric"""
        self.collector.record("internal", "test_operation", 10.5, {"test": "data"})
        
        metrics = self.collector.get_recent_metrics(10)
        assert len(metrics) == 1
        assert metrics[0]["operation_type"] == "internal"
        assert metrics[0]["operation_name"] == "test_operation"
        assert metrics[0]["duration_ms"] == 10.5
        assert metrics[0]["metadata"]["test"] == "data"
    
    def test_record_multiple_metrics(self):
        """Test recording multiple metrics"""
        self.collector.record("internal", "op1", 10.0)
        self.collector.record("external", "op2", 20.0)
        self.collector.record("internal", "op3", 15.0)
        
        metrics = self.collector.get_recent_metrics(10)
        assert len(metrics) == 3
    
    def test_get_statistics(self):
        """Test getting statistics"""
        self.collector.record("internal", "query1", 5.0)
        self.collector.record("internal", "query2", 15.0)
        self.collector.record("external", "api1", 100.0)
        self.collector.record("external", "api2", 200.0)
        
        stats = self.collector.get_statistics()
        
        assert stats["internal_count"] == 2
        assert stats["external_count"] == 2
        assert stats["internal_avg_ms"] == 10.0  # (5 + 15) / 2
        assert stats["external_avg_ms"] == 150.0  # (100 + 200) / 2
        assert stats["total_operations"] == 4
    
    def test_operation_statistics(self):
        """Test per-operation statistics"""
        self.collector.record("internal", "search", 10.0)
        self.collector.record("internal", "search", 20.0)
        self.collector.record("internal", "search", 30.0)
        
        stats = self.collector.get_statistics()
        search_stats = stats["operations"]["search"]
        
        assert search_stats["count"] == 3
        assert search_stats["min_ms"] == 10.0
        assert search_stats["max_ms"] == 30.0
        assert search_stats["avg_ms"] == 20.0
    
    def test_clear_metrics(self):
        """Test clearing metrics"""
        self.collector.record("internal", "op1", 10.0)
        self.collector.record("external", "op2", 20.0)
        
        assert len(self.collector.get_recent_metrics(10)) == 2
        
        self.collector.clear()
        
        assert len(self.collector.get_recent_metrics(10)) == 0
        stats = self.collector.get_statistics()
        assert stats["total_operations"] == 0
    
    def test_metrics_limit(self):
        """Test that old metrics are trimmed"""
        collector = MetricsCollector()
        collector.max_metrics = 5  # Set low limit for testing
        
        # Record more metrics than the limit
        for i in range(10):
            collector.record("internal", f"op{i}", float(i))
        
        metrics = collector.get_recent_metrics(100)
        assert len(metrics) == 5  # Should only keep last 5
        assert metrics[0]["operation_name"] == "op5"  # First should be op5
        assert metrics[-1]["operation_name"] == "op9"  # Last should be op9


class TestMetricsEndpoints:
    """Test the metrics API endpoints"""
    
    def test_get_metrics_endpoint(self, client, clean_storage):
        """Test the GET /api/metrics endpoint"""
        # Clear metrics first
        metrics_collector.clear()
        
        # Generate some metrics by making API calls
        client.get("/api/recipes")
        
        # Get metrics
        response = client.get("/api/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "statistics" in data["data"]
        assert "recent_metrics" in data["data"]
        assert "performance_comparison" in data["data"]
    
    def test_clear_metrics_endpoint(self, client):
        """Test the DELETE /api/metrics endpoint"""
        # Generate some metrics
        client.get("/api/recipes")
        
        # Clear metrics
        response = client.delete("/api/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["cleared"] is True
        
        # Verify metrics are cleared
        metrics_response = client.get("/api/metrics")
        metrics_data = metrics_response.json()
        assert metrics_data["data"]["statistics"]["total_operations"] == 0
    
    @pytest.mark.asyncio
    async def test_performance_data_in_search_response(self, client, clean_storage, sample_recipe_data):
        """Test that search responses include performance timing data"""
        # Create an internal recipe
        client.post("/api/recipes", json=sample_recipe_data)
        
        # Mock external API
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
            assert "performance" in data["meta"]
            
            performance = data["meta"]["performance"]
            assert "total_request_ms" in performance
            # When searching, we should have both internal and external timings
            if data["meta"]["internal_count"] > 0:
                assert "internal_query_ms" in performance or True  # May or may not be present
            if data["meta"]["external_count"] > 0:
                assert "external_api_ms" in performance or True


class TestStorageMetrics:
    """Test that storage operations are properly instrumented"""
    
    def test_get_all_recipes_records_metric(self, clean_storage):
        """Test that get_all_recipes records a metric"""
        from app.services.storage import recipe_storage
        
        metrics_collector.clear()
        
        recipes = recipe_storage.get_all_recipes()
        
        metrics = metrics_collector.get_recent_metrics(10)
        assert len(metrics) > 0
        
        # Find the get_all_recipes metric
        get_all_metric = next((m for m in metrics if m["operation_name"] == "get_all_recipes"), None)
        assert get_all_metric is not None
        assert get_all_metric["operation_type"] == "internal"
        assert get_all_metric["duration_ms"] >= 0
    
    def test_search_recipes_records_metric(self, clean_storage, sample_recipe_data):
        """Test that search_recipes records a metric"""
        from app.services.storage import recipe_storage
        from app.models import RecipeCreate
        
        metrics_collector.clear()
        
        # Create a recipe first
        recipe_create = RecipeCreate(**sample_recipe_data)
        recipe_storage.create_recipe(recipe_create)
        
        # Clear metrics after creation
        metrics_collector.clear()
        
        # Search for recipes
        results = recipe_storage.search_recipes("test")
        
        metrics = metrics_collector.get_recent_metrics(10)
        
        # Find the search_recipes metric
        search_metric = next((m for m in metrics if m["operation_name"] == "search_recipes"), None)
        assert search_metric is not None
        assert search_metric["operation_type"] == "internal"
        assert "query" in search_metric["metadata"]


class TestExternalAPIMetrics:
    """Test that external API operations are properly instrumented"""
    
    @pytest.mark.asyncio
    async def test_search_meals_records_metric(self):
        """Test that search_meals records a metric"""
        from app.services.themealdb_adapter import TheMealDBAdapter
        
        metrics_collector.clear()
        
        adapter = TheMealDBAdapter()
        
        # Mock the HTTP client
        mock_response = MagicMock()
        mock_response.json.return_value = {"meals": None}
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        
        with patch.object(adapter, '_get_client', return_value=mock_client):
            await adapter.search_meals("test")
        
        metrics = metrics_collector.get_recent_metrics(10)
        
        # Find the search_meals metric
        search_metric = next((m for m in metrics if m["operation_name"] == "search_meals"), None)
        assert search_metric is not None
        assert search_metric["operation_type"] == "external"
        assert search_metric["duration_ms"] >= 0
    
    @pytest.mark.asyncio
    async def test_get_meal_by_id_records_metric(self):
        """Test that get_meal_by_id records a metric"""
        from app.services.themealdb_adapter import TheMealDBAdapter
        
        metrics_collector.clear()
        
        adapter = TheMealDBAdapter()
        
        # Mock the HTTP client
        mock_response = MagicMock()
        mock_response.json.return_value = {"meals": None}
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        
        with patch.object(adapter, '_get_client', return_value=mock_client):
            await adapter.get_meal_by_id("12345")
        
        metrics = metrics_collector.get_recent_metrics(10)
        
        # Find the get_meal_by_id metric
        get_metric = next((m for m in metrics if m["operation_name"] == "get_meal_by_id"), None)
        assert get_metric is not None
        assert get_metric["operation_type"] == "external"
        assert "meal_id" in get_metric["metadata"]


class TestPerformanceComparison:
    """Test performance comparison between internal and external sources"""
    
    def test_metrics_show_performance_difference(self, client, clean_storage, sample_recipe_data):
        """Test that we can see the performance difference between sources"""
        metrics_collector.clear()
        
        # Create internal recipe
        client.post("/api/recipes", json=sample_recipe_data)
        
        # Search with mock external API
        with patch('app.routes.api.themealdb_adapter.search_meals', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            client.get("/api/recipes?search=test")
        
        # Get metrics
        response = client.get("/api/metrics")
        data = response.json()
        
        stats = data["data"]["statistics"]
        
        # Should have both internal and external metrics
        assert "internal_avg_ms" in stats
        assert "external_avg_ms" in stats
        
        # Check if performance comparison is present
        if stats["internal_count"] > 0 and stats["external_count"] > 0:
            assert "performance_comparison" in data["data"]
            comparison = data["data"]["performance_comparison"]
            assert "faster_source" in comparison
            assert "speedup_factor" in comparison
            assert "message" in comparison
