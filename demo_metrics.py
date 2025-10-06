#!/usr/bin/env python3
"""
Demo script to show the performance metrics functionality
Run this after starting the server with: uvicorn app.main:app --reload
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api"


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def demo_metrics():
    """Demonstrate the metrics functionality"""
    
    print_section("Recipe Explorer - Performance Metrics Demo")
    
    # Clear existing metrics
    print("1. Clearing existing metrics...")
    response = requests.delete(f"{BASE_URL}/metrics")
    print(f"   Status: {response.status_code}")
    
    # Make some API calls to generate metrics
    print("\n2. Making API calls to generate metrics...")
    
    # Get all recipes (internal query)
    print("   - Getting all recipes (internal query)...")
    response = requests.get(f"{BASE_URL}/recipes")
    if response.status_code == 200:
        data = response.json()
        print(f"     Found {data['meta']['count']} recipes")
        if 'performance' in data['meta']:
            perf = data['meta']['performance']
            print(f"     Performance: {json.dumps(perf, indent=2)}")
    
    time.sleep(0.5)
    
    # Search for recipes (combines internal + external)
    print("\n   - Searching for 'chicken' (internal + external)...")
    response = requests.get(f"{BASE_URL}/recipes?search=chicken")
    if response.status_code == 200:
        data = response.json()
        print(f"     Found {data['meta']['count']} recipes")
        print(f"     Internal: {data['meta']['internal_count']}, External: {data['meta']['external_count']}")
        if 'performance' in data['meta']:
            perf = data['meta']['performance']
            print(f"     Performance metrics:")
            for key, value in perf.items():
                print(f"       - {key}: {value}ms")
    
    time.sleep(0.5)
    
    # Get metrics summary
    print_section("3. Performance Metrics Summary")
    response = requests.get(f"{BASE_URL}/metrics")
    if response.status_code == 200:
        data = response.json()
        stats = data['data']['statistics']
        
        print(f"   Total Operations: {stats['total_operations']}")
        print(f"\n   Internal Queries:")
        print(f"     - Count: {stats['internal_count']}")
        print(f"     - Average: {stats['internal_avg_ms']}ms")
        
        print(f"\n   External API Calls:")
        print(f"     - Count: {stats['external_count']}")
        print(f"     - Average: {stats['external_avg_ms']}ms")
        
        if 'performance_comparison' in data['data'] and data['data']['performance_comparison']:
            comparison = data['data']['performance_comparison']
            print(f"\n   Performance Comparison:")
            print(f"     {comparison['message']}")
        
        # Show per-operation details
        if stats['operations']:
            print(f"\n   Per-Operation Statistics:")
            for op_name, op_stats in stats['operations'].items():
                print(f"     {op_name}:")
                print(f"       - Count: {op_stats['count']}")
                print(f"       - Avg: {op_stats['avg_ms']}ms")
                print(f"       - Min: {op_stats['min_ms']}ms")
                print(f"       - Max: {op_stats['max_ms']}ms")
    
    print_section("Demo Complete!")
    print("Key Takeaways:")
    print("  ✓ All operations are automatically timed")
    print("  ✓ API responses include performance data")
    print("  ✓ Metrics endpoint provides aggregated statistics")
    print("  ✓ Can easily compare internal vs external performance")
    print("\nAccess metrics anytime at: GET /api/metrics")


if __name__ == "__main__":
    try:
        demo_metrics()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the server.")
        print("Please start the server first with:")
        print("  uvicorn app.main:app --reload")
        print("\nThen run this demo script again.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
