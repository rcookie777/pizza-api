#!/usr/bin/env python3
"""
Test script for the Restaurant Popular Times API
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API base URL (change this to your deployed API URL)
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed")
            print(f"   Status: {data['status']}")
            print(f"   Database connected: {data['database_connected']}")
            print(f"   Restaurants count: {data['restaurants_count']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_restaurants_list():
    """Test the restaurants list endpoint"""
    print("\nTesting restaurants list...")
    try:
        response = requests.get(f"{API_BASE_URL}/restaurants")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Restaurants list retrieved")
            print(f"   Count: {data['count']}")
            for restaurant_id, info in data['restaurants'].items():
                print(f"   - {restaurant_id}: {info['name']}")
            return True
        else:
            print(f"❌ Restaurants list failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Restaurants list error: {e}")
        return False

def test_pizza_index_live():
    """Test the pizza index live endpoint"""
    print("\nTesting pizza index live...")
    try:
        response = requests.get(f"{API_BASE_URL}/pizza-index/live")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Pizza index live data retrieved")
            print(f"   Index: {data['index']['name']}")
            print(f"   Value: {data['index']['value']}")
            print(f"   Symbol: {data['index']['symbol']}")
            print(f"   Active restaurants: {data['metadata']['active_restaurants']}/{data['metadata']['total_restaurants']}")
            print(f"   Average popularity: {data['metadata']['avg_popularity']}")
            return True
        else:
            print(f"❌ Pizza index live failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Pizza index live error: {e}")
        return False

def test_pizza_index_chart_data():
    """Test the pizza index chart data endpoint"""
    print("\nTesting pizza index chart data...")
    try:
        response = requests.get(f"{API_BASE_URL}/pizza-index/chart-data?days=7&interval=hour")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Pizza index chart data retrieved")
            print(f"   Data points: {len(data['chart_data'])}")
            print(f"   Period: {data['period_days']} days")
            print(f"   Interval: {data['interval']}")
            if data['chart_data']:
                latest = data['chart_data'][-1]
                print(f"   Latest value: {latest['value']}")
            return True
        else:
            print(f"❌ Pizza index chart data failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Pizza index chart data error: {e}")
        return False

def test_restaurant_data(restaurant_id):
    """Test getting data for a specific restaurant"""
    print(f"\nTesting restaurant data for {restaurant_id}...")
    try:
        response = requests.get(f"{API_BASE_URL}/restaurant/{restaurant_id}/data?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Restaurant data retrieved")
            print(f"   Records: {len(data)}")
            if data:
                latest = data[0]
                print(f"   Latest timestamp: {latest.get('timestamp')}")
                print(f"   Current popularity: {latest.get('current_popularity')}")
                print(f"   Rating: {latest.get('rating')}")
            return True
        elif response.status_code == 404:
            print(f"⚠️  No data available for {restaurant_id}")
            return True
        else:
            print(f"❌ Restaurant data failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Restaurant data error: {e}")
        return False

def test_restaurant_latest(restaurant_id):
    """Test getting latest data for a specific restaurant"""
    print(f"\nTesting latest data for {restaurant_id}...")
    try:
        response = requests.get(f"{API_BASE_URL}/restaurant/{restaurant_id}/latest")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Latest data retrieved")
            print(f"   Timestamp: {data.get('timestamp')}")
            print(f"   Current popularity: {data.get('current_popularity')}")
            print(f"   Rating: {data.get('rating')}")
            return True
        elif response.status_code == 404:
            print(f"⚠️  No latest data available for {restaurant_id}")
            return True
        else:
            print(f"❌ Latest data failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Latest data error: {e}")
        return False

def test_restaurant_stats(restaurant_id):
    """Test getting statistics for a restaurant"""
    print(f"\nTesting stats for {restaurant_id}...")
    try:
        response = requests.get(f"{API_BASE_URL}/restaurant/{restaurant_id}/stats?days=7")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stats retrieved")
            print(f"   Data points: {data.get('data_points')}")
            if data.get('current_popularity'):
                pop = data['current_popularity']
                print(f"   Popularity - Latest: {pop.get('latest')}, Avg: {pop.get('average')}")
            if data.get('rating'):
                rating = data['rating']
                print(f"   Rating - Latest: {rating.get('latest')}, Avg: {rating.get('average')}")
            return True
        else:
            print(f"❌ Stats failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Stats error: {e}")
        return False

def test_all_latest():
    """Test getting latest data for all restaurants"""
    print("\nTesting all latest data...")
    try:
        response = requests.get(f"{API_BASE_URL}/data/latest")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ All latest data retrieved")
            print(f"   Timestamp: {data.get('timestamp')}")
            for restaurant_id, info in data['restaurants'].items():
                if info.get('latest_data'):
                    latest = info['latest_data']
                    print(f"   {restaurant_id}: {latest.get('current_popularity')}% busy")
                else:
                    print(f"   {restaurant_id}: No data")
            return True
        else:
            print(f"❌ All latest data failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ All latest data error: {e}")
        return False

def test_data_summary():
    """Test getting data summary"""
    print("\nTesting data summary...")
    try:
        response = requests.get(f"{API_BASE_URL}/data/summary?days=7")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Data summary retrieved")
            print(f"   Period: {data.get('period_days')} days")
            print(f"   Total data points: {data.get('total_data_points')}")
            for restaurant_id, info in data['restaurants'].items():
                print(f"   {restaurant_id}: {info.get('data_points')} data points")
            return True
        else:
            print(f"❌ Data summary failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Data summary error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Restaurant Popular Times API Test Suite")
    print("=" * 50)
    
    # Define all restaurant IDs
    restaurant_ids = [
        "extreme_pizza",
        "colony_grill", 
        "wise_guy",
        "night_hawk",
        "district_pizza",
        "we_the_pizza",
        "dominos_1",
        "dominos_2"
    ]
    
    tests = [
        test_health_check,
        test_restaurants_list,
        test_pizza_index_live,
        test_pizza_index_chart_data,
        test_all_latest,
        test_data_summary
    ]
    
    # Add restaurant-specific tests
    for restaurant_id in restaurant_ids:
        tests.extend([
            lambda rid=restaurant_id: test_restaurant_data(rid),
            lambda rid=restaurant_id: test_restaurant_latest(rid),
            lambda rid=restaurant_id: test_restaurant_stats(rid)
        ])
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check your configuration and data.")

if __name__ == "__main__":
    main() 