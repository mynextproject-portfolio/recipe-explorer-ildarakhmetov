"""
Performance metrics and timing utilities for measuring API response times
"""

import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict
from functools import wraps

logger = logging.getLogger(__name__)


class PerformanceTimer:
    """Context manager and decorator for measuring execution time"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
        self.duration_ms = None
    
    def __enter__(self):
        """Start timing when entering context"""
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing when exiting context"""
        self.end_time = time.perf_counter()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        logger.info(f"{self.operation_name} took {self.duration_ms:.2f}ms")
        return False
    
    def get_duration_ms(self) -> float:
        """Get the duration in milliseconds"""
        if self.duration_ms is None:
            return 0.0
        return round(self.duration_ms, 2)


class MetricsCollector:
    """Collects and stores performance metrics"""
    
    def __init__(self):
        self.metrics: List[Dict[str, Any]] = []
        self.operation_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "total_ms": 0, "min_ms": float('inf'), "max_ms": 0}
        )
        self.max_metrics = 1000  # Keep last 1000 metrics
    
    def record(self, operation_type: str, operation_name: str, duration_ms: float, 
               metadata: Optional[Dict[str, Any]] = None):
        """Record a performance metric"""
        metric = {
            "timestamp": datetime.now().isoformat(),
            "operation_type": operation_type,  # 'internal' or 'external'
            "operation_name": operation_name,
            "duration_ms": round(duration_ms, 2),
            "metadata": metadata or {}
        }
        
        self.metrics.append(metric)
        
        # Update statistics
        stats = self.operation_stats[operation_name]
        stats["count"] += 1
        stats["total_ms"] += duration_ms
        stats["min_ms"] = min(stats["min_ms"], duration_ms)
        stats["max_ms"] = max(stats["max_ms"], duration_ms)
        stats["avg_ms"] = round(stats["total_ms"] / stats["count"], 2)
        
        # Trim old metrics if needed
        if len(self.metrics) > self.max_metrics:
            self.metrics = self.metrics[-self.max_metrics:]
        
        logger.debug(f"Recorded metric: {operation_type}/{operation_name} - {duration_ms:.2f}ms")
    
    def get_recent_metrics(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent metrics"""
        return self.metrics[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregated statistics"""
        stats = {}
        
        # Calculate internal vs external averages
        internal_metrics = [m for m in self.metrics if m["operation_type"] == "internal"]
        external_metrics = [m for m in self.metrics if m["operation_type"] == "external"]
        
        if internal_metrics:
            internal_avg = sum(m["duration_ms"] for m in internal_metrics) / len(internal_metrics)
            stats["internal_avg_ms"] = round(internal_avg, 2)
            stats["internal_count"] = len(internal_metrics)
        else:
            stats["internal_avg_ms"] = 0
            stats["internal_count"] = 0
        
        if external_metrics:
            external_avg = sum(m["duration_ms"] for m in external_metrics) / len(external_metrics)
            stats["external_avg_ms"] = round(external_avg, 2)
            stats["external_count"] = len(external_metrics)
        else:
            stats["external_avg_ms"] = 0
            stats["external_count"] = 0
        
        # Add per-operation statistics
        stats["operations"] = dict(self.operation_stats)
        stats["total_operations"] = len(self.metrics)
        
        return stats
    
    def clear(self):
        """Clear all metrics"""
        self.metrics.clear()
        self.operation_stats.clear()
        logger.info("Cleared all metrics")


# Global metrics collector instance
metrics_collector = MetricsCollector()


def timed_operation(operation_type: str, operation_name: str):
    """Decorator for timing async or sync functions"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            timer = PerformanceTimer(f"{operation_type}/{operation_name}")
            with timer:
                result = await func(*args, **kwargs)
            metrics_collector.record(operation_type, operation_name, timer.get_duration_ms())
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            timer = PerformanceTimer(f"{operation_type}/{operation_name}")
            with timer:
                result = func(*args, **kwargs)
            metrics_collector.record(operation_type, operation_name, timer.get_duration_ms())
            return result
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
