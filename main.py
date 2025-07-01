#!/usr/bin/env python3
"""
Restaurant Popular Times API
FastAPI service to interact with restaurant data stored in Supabase
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Restaurant Popular Times API",
    description="API for accessing restaurant popular times data from Supabase",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Restaurant configurations - Updated to match data_collector.py
RESTAURANTS = {
    "extreme_pizza": {
        "name": "Extreme Pizza",
        "address": "1419 S Fern St, Arlington, VA 22202"
    },
    "colony_grill": {
        "name": "Colony Grill",
        "address": "2800 Clarendon Blvd, Arlington, VA 22201"
    },
    "wise_guy": {
        "name": "Wise Guy Pizza",
        "address": "1735 North Lynn St, Arlington, VA 22209"
    },
    "night_hawk": {
        "name": "Night Hawk Brewery & Pizza",
        "address": "1201 S Joyce St, Ste C10, Arlington, VA 22202"
    },
    "district_pizza": {
        "name": "District Pizza Palace",
        "address": "2325 S Eads St, Arlington, VA 22202"
    }
}

# Pydantic models for request/response validation
class RestaurantData(BaseModel):
    id: int
    restaurant_id: str
    restaurant_name: str
    restaurant_address: str
    timestamp: str
    rating: Optional[float]
    rating_count: Optional[int]
    current_popularity: Optional[int]
    time_spent_min: Optional[int]
    time_spent_max: Optional[int]
    popular_times: Optional[Dict[str, Any]]
    created_at: str

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
    database_connected: bool
    restaurants_count: int

class PizzaIndexData(BaseModel):
    timestamp: str
    value: float
    change: float
    changePercent: float
    total_popularity: int
    avg_popularity: float
    active_restaurants: int
    total_restaurants: int
    restaurant_data: Dict[str, Any]

def get_supabase_headers(use_service_role: bool = False) -> Dict[str, str]:
    """Get headers for Supabase API requests"""
    key = SUPABASE_SERVICE_ROLE_KEY if use_service_role else SUPABASE_ANON_KEY
    return {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json'
    }

def validate_supabase_connection() -> bool:
    """Validate Supabase connection"""
    try:
        headers = get_supabase_headers(use_service_role=True)
        response = requests.get(f"{SUPABASE_URL}/rest/v1/", headers=headers)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Supabase connection error: {e}")
        return False

def calculate_pizza_index(latest_data: Dict[str, Any]) -> PizzaIndexData:
    """Calculate the Pentagon Pizza Index from latest restaurant data"""
    current_time = datetime.utcnow()
    
    # Filter restaurants with valid popularity data
    valid_restaurants = {}
    total_popularity = 0
    active_count = 0
    
    for restaurant_id, data in latest_data['restaurants'].items():
        if data.get('latest_data') and data['latest_data'].get('current_popularity') is not None:
            popularity = data['latest_data']['current_popularity']
            valid_restaurants[restaurant_id] = {
                'restaurant': data['restaurant'],
                'popularity': popularity,
                'rating': data['latest_data'].get('rating'),
                'timestamp': data['latest_data'].get('timestamp')
            }
            total_popularity += popularity
            active_count += 1
    
    # Calculate index value (normalized to 100-200 range like stock indices)
    if active_count > 0:
        avg_popularity = total_popularity / active_count
        # Convert popularity (0-100) to index value (100-200)
        index_value = 100 + (avg_popularity * 0.8)  # Scale factor to keep reasonable range
    else:
        index_value = 100.0
        avg_popularity = 0.0
    
    # For demo purposes, calculate a simple change (in real app, compare with previous period)
    # This would typically compare with data from 24 hours ago
    change = 0.0  # Placeholder - would calculate actual change
    change_percent = 0.0  # Placeholder - would calculate actual change percent
    
    return PizzaIndexData(
        timestamp=current_time.isoformat(),
        value=round(index_value, 1),
        change=change,
        changePercent=change_percent,
        total_popularity=total_popularity,
        avg_popularity=round(avg_popularity, 1),
        active_restaurants=active_count,
        total_restaurants=len(RESTAURANTS),
        restaurant_data=valid_restaurants
    )

@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="restaurant-popular-times-api",
        timestamp=datetime.utcnow().isoformat(),
        database_connected=validate_supabase_connection(),
        restaurants_count=len(RESTAURANTS)
    )

@app.get("/health")
async def simple_health():
    """Simple health check"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/restaurants")
async def get_restaurants():
    """Get list of all configured restaurants"""
    return {
        "restaurants": RESTAURANTS,
        "count": len(RESTAURANTS)
    }

@app.get("/pizza-index/live")
async def get_pizza_index_live():
    """Get live Pentagon Pizza Index data"""
    try:
        # Get latest data for all restaurants
        all_latest = await get_all_latest_data()
        
        # Calculate the pizza index
        pizza_index = calculate_pizza_index(all_latest)
        
        return {
            "index": {
                "id": "pizza",
                "name": "Pentagon Pizza Index",
                "symbol": "PZZA",
                "value": pizza_index.value,
                "change": pizza_index.change,
                "changePercent": pizza_index.changePercent,
                "description": "Real-time pizza demand index around the Pentagon",
                "methodology": "Aggregates current popularity data from major pizza establishments around the Pentagon area. Higher values indicate increased demand and potential economic activity.",
                "dataSources": ["Google Maps Popular Times", "Real-time Restaurant Data", "Pentagon Area Establishments"]
            },
            "metadata": {
                "timestamp": pizza_index.timestamp,
                "total_popularity": pizza_index.total_popularity,
                "avg_popularity": pizza_index.avg_popularity,
                "active_restaurants": pizza_index.active_restaurants,
                "total_restaurants": pizza_index.total_restaurants
            },
            "restaurants": pizza_index.restaurant_data
        }
        
    except Exception as e:
        logger.error(f"Error calculating pizza index: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/pizza-index/chart-data")
async def get_pizza_index_chart_data(
    days: int = Query(7, description="Number of days of historical data"),
    interval: str = Query("hour", description="Data interval: hour, day")
):
    """Get historical chart data for the Pizza Index"""
    try:
        headers = get_supabase_headers(use_service_role=True)
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all data for the time period
        url = f"{SUPABASE_URL}/rest/v1/restaurant_popular_times"
        params = {
            'created_at': f'gte.{cutoff_date.isoformat()}',
            'order': 'created_at.asc'
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        url += f"?{query_string}"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Group data by timestamp intervals
            chart_data = []
            
            if interval == "hour":
                # Group by hour
                hourly_data = {}
                for item in data:
                    timestamp = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                    hour_key = timestamp.replace(minute=0, second=0, microsecond=0)
                    
                    if hour_key not in hourly_data:
                        hourly_data[hour_key] = []
                    hourly_data[hour_key].append(item)
                
                # Calculate index for each hour
                for hour, items in hourly_data.items():
                    total_popularity = 0
                    valid_count = 0
                    
                    for item in items:
                        if item.get('current_popularity') is not None:
                            total_popularity += item['current_popularity']
                            valid_count += 1
                    
                    if valid_count > 0:
                        avg_popularity = total_popularity / valid_count
                        index_value = 100 + (avg_popularity * 0.8)
                        
                        chart_data.append({
                            "timestamp": hour.isoformat(),
                            "value": round(index_value, 1),
                            "avg_popularity": round(avg_popularity, 1),
                            "data_points": len(items)
                        })
            
            elif interval == "day":
                # Group by day
                daily_data = {}
                for item in data:
                    timestamp = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                    day_key = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
                    
                    if day_key not in daily_data:
                        daily_data[day_key] = []
                    daily_data[day_key].append(item)
                
                # Calculate index for each day
                for day, items in daily_data.items():
                    total_popularity = 0
                    valid_count = 0
                    
                    for item in items:
                        if item.get('current_popularity') is not None:
                            total_popularity += item['current_popularity']
                            valid_count += 1
                    
                    if valid_count > 0:
                        avg_popularity = total_popularity / valid_count
                        index_value = 100 + (avg_popularity * 0.8)
                        
                        chart_data.append({
                            "timestamp": day.isoformat(),
                            "value": round(index_value, 1),
                            "avg_popularity": round(avg_popularity, 1),
                            "data_points": len(items)
                        })
            
            return {
                "chart_data": chart_data,
                "period_days": days,
                "interval": interval,
                "total_data_points": len(data)
            }
        else:
            logger.error(f"Supabase API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Database error")
            
    except Exception as e:
        logger.error(f"Error generating chart data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/restaurant/{restaurant_id}/data", response_model=List[RestaurantData])
async def get_restaurant_data(
    restaurant_id: str,
    limit: Optional[int] = Query(None, description="Limit number of records returned"),
    days: Optional[int] = Query(None, description="Get data from last N days"),
    hours: Optional[int] = Query(None, description="Get data from last N hours")
):
    """Get data for a specific restaurant"""
    if restaurant_id not in RESTAURANTS:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    try:
        headers = get_supabase_headers(use_service_role=True)
        
        # Build query parameters
        params = {
            'restaurant_id': f'eq.{restaurant_id}',
            'order': 'created_at.desc'
        }
        
        if limit:
            params['limit'] = str(limit)
        
        # Add time filter if specified
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            params['created_at'] = f'gte.{cutoff_date.isoformat()}'
        elif hours:
            cutoff_date = datetime.utcnow() - timedelta(hours=hours)
            params['created_at'] = f'gte.{cutoff_date.isoformat()}'
        
        # Build URL with query parameters
        url = f"{SUPABASE_URL}/rest/v1/restaurant_popular_times"
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        if query_string:
            url += f"?{query_string}"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            logger.error(f"Supabase API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Database error")
            
    except Exception as e:
        logger.error(f"Error fetching restaurant data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/restaurant/{restaurant_id}/latest", response_model=RestaurantData)
async def get_restaurant_latest(restaurant_id: str):
    """Get the most recent data for a specific restaurant"""
    if restaurant_id not in RESTAURANTS:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    try:
        headers = get_supabase_headers(use_service_role=True)
        
        url = f"{SUPABASE_URL}/rest/v1/restaurant_popular_times"
        params = {
            'restaurant_id': f'eq.{restaurant_id}',
            'order': 'created_at.desc',
            'limit': '1'
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        url += f"?{query_string}"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                return data[0]
            else:
                raise HTTPException(status_code=404, detail="No data available")
        else:
            logger.error(f"Supabase API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Database error")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest restaurant data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/restaurant/{restaurant_id}/stats")
async def get_restaurant_stats(restaurant_id: str, days: int = 7):
    """Get statistics for a restaurant over the last N days"""
    if restaurant_id not in RESTAURANTS:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    try:
        headers = get_supabase_headers(use_service_role=True)
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        url = f"{SUPABASE_URL}/rest/v1/restaurant_popular_times"
        params = {
            'restaurant_id': f'eq.{restaurant_id}',
            'created_at': f'gte.{cutoff_date.isoformat()}',
            'order': 'created_at.desc'
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        url += f"?{query_string}"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if not data:
                return {
                    "restaurant_id": restaurant_id,
                    "restaurant_name": RESTAURANTS[restaurant_id]["name"],
                    "period_days": days,
                    "data_points": 0,
                    "message": "No data available for the specified period"
                }
            
            # Calculate statistics
            current_popularities = [d.get('current_popularity') for d in data if d.get('current_popularity') is not None]
            ratings = [d.get('rating') for d in data if d.get('rating') is not None]
            
            stats = {
                "restaurant_id": restaurant_id,
                "restaurant_name": RESTAURANTS[restaurant_id]["name"],
                "period_days": days,
                "data_points": len(data),
                "latest_data": data[0] if data else None,
                "current_popularity": {
                    "latest": current_popularities[0] if current_popularities else None,
                    "average": sum(current_popularities) / len(current_popularities) if current_popularities else None,
                    "min": min(current_popularities) if current_popularities else None,
                    "max": max(current_popularities) if current_popularities else None
                },
                "rating": {
                    "latest": ratings[0] if ratings else None,
                    "average": sum(ratings) / len(ratings) if ratings else None
                }
            }
            
            return stats
        else:
            logger.error(f"Supabase API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Database error")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating restaurant stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/data/latest")
async def get_all_latest_data():
    """Get the most recent data for all restaurants"""
    try:
        headers = get_supabase_headers(use_service_role=True)
        
        # Get latest data for each restaurant
        all_latest = {}
        
        for restaurant_id in RESTAURANTS.keys():
            url = f"{SUPABASE_URL}/rest/v1/restaurant_popular_times"
            params = {
                'restaurant_id': f'eq.{restaurant_id}',
                'order': 'created_at.desc',
                'limit': '1'
            }
            
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            url += f"?{query_string}"
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    all_latest[restaurant_id] = {
                        "restaurant": RESTAURANTS[restaurant_id],
                        "latest_data": data[0]
                    }
                else:
                    all_latest[restaurant_id] = {
                        "restaurant": RESTAURANTS[restaurant_id],
                        "latest_data": None
                    }
            else:
                logger.error(f"Error fetching data for {restaurant_id}: {response.status_code}")
                all_latest[restaurant_id] = {
                    "restaurant": RESTAURANTS[restaurant_id],
                    "latest_data": None,
                    "error": "Failed to fetch data"
                }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "restaurants": all_latest
        }
        
    except Exception as e:
        logger.error(f"Error fetching all latest data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/data/summary")
async def get_data_summary(days: int = 7):
    """Get a summary of all restaurant data over the last N days"""
    try:
        headers = get_supabase_headers(use_service_role=True)
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        url = f"{SUPABASE_URL}/rest/v1/restaurant_popular_times"
        params = {
            'created_at': f'gte.{cutoff_date.isoformat()}',
            'order': 'created_at.desc'
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        url += f"?{query_string}"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Group data by restaurant
            restaurant_data = {}
            for item in data:
                restaurant_id = item['restaurant_id']
                if restaurant_id not in restaurant_data:
                    restaurant_data[restaurant_id] = []
                restaurant_data[restaurant_id].append(item)
            
            # Calculate summary for each restaurant
            summary = {
                "period_days": days,
                "total_data_points": len(data),
                "restaurants": {}
            }
            
            for restaurant_id, items in restaurant_data.items():
                current_popularities = [d.get('current_popularity') for d in items if d.get('current_popularity') is not None]
                ratings = [d.get('rating') for d in items if d.get('rating') is not None]
                
                summary["restaurants"][restaurant_id] = {
                    "restaurant": RESTAURANTS.get(restaurant_id, {"name": restaurant_id}),
                    "data_points": len(items),
                    "latest_data": items[0] if items else None,
                    "current_popularity": {
                        "latest": current_popularities[0] if current_popularities else None,
                        "average": sum(current_popularities) / len(current_popularities) if current_popularities else None,
                        "min": min(current_popularities) if current_popularities else None,
                        "max": max(current_popularities) if current_popularities else None
                    },
                    "rating": {
                        "latest": ratings[0] if ratings else None,
                        "average": sum(ratings) / len(ratings) if ratings else None
                    }
                }
            
            return summary
        else:
            logger.error(f"Supabase API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Database error")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating data summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Legacy endpoints for backward compatibility
@app.get("/extreme-pizza/live")
async def get_extreme_pizza_live():
    """Legacy endpoint for Extreme Pizza live data"""
    return await get_restaurant_latest("extreme_pizza")

@app.get("/extreme-pizza/history")
async def get_extreme_pizza_history():
    """Legacy endpoint for Extreme Pizza history"""
    return await get_restaurant_data("extreme_pizza")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
