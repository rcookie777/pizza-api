#!/usr/bin/env python3
"""
Restaurant Popular Times API
FastAPI service to interact with restaurant data stored in Supabase
"""

import os
import logging
from datetime import datetime, timedelta, timezone
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
    },
    "we_the_pizza": {
        "name": "We, The Pizza",
        "address": "2100 Crystal Dr, Arlington, VA 22202"
    },
    "dominos_1": {
        "name": "Dominos Pizza",
        "address": "2602 Columbia Pike, Arlington, VA 22204"
    },
    "dominos_2": {
        "name": "Dominos Pizza",
        "address": "3535 S Ball St, Arlington, VA 22202"
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
    created_at: Optional[str] = None

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

def parse_timestamp_robust(timestamp_str: str) -> datetime:
    """Parse timestamp string robustly, handling various formats including 5-digit microseconds"""
    try:
        # Handle Z suffix
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str.replace('Z', '+00:00')
        elif not timestamp_str.endswith('+00:00'):
            timestamp_str = timestamp_str + '+00:00'
        
        # Try direct parsing first
        return datetime.fromisoformat(timestamp_str)
    except ValueError as e:
        # Handle case where microseconds have 5 digits instead of 6
        if 'Invalid isoformat string' in str(e) and '.' in timestamp_str:
            try:
                # Split on the decimal point
                base_part, micro_part = timestamp_str.split('.', 1)
                
                # Extract microseconds and timezone
                if '+' in micro_part:
                    micro_seconds, tz_part = micro_part.split('+', 1)
                    tz_part = '+' + tz_part
                else:
                    micro_seconds = micro_part
                    tz_part = '+00:00'
                
                # Pad microseconds to 6 digits if needed
                if len(micro_seconds) == 5:
                    micro_seconds = micro_seconds + '0'
                elif len(micro_seconds) > 6:
                    micro_seconds = micro_seconds[:6]
                
                # Reconstruct timestamp
                fixed_timestamp = f"{base_part}.{micro_seconds}{tz_part}"
                return datetime.fromisoformat(fixed_timestamp)
            except Exception:
                pass
        
        # If all else fails, try parsing without microseconds
        try:
            # Remove microseconds and timezone, then add UTC
            if '.' in timestamp_str:
                base_part = timestamp_str.split('.')[0]
            else:
                base_part = timestamp_str.split('+')[0].split('Z')[0]
            
            # Add UTC timezone
            base_part += '+00:00'
            return datetime.fromisoformat(base_part)
        except Exception:
            # Last resort: return current time
            logger.warning(f"Could not parse timestamp: {timestamp_str}, using current time")
            return datetime.utcnow().replace(tzinfo=timezone.utc)

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

def calculate_pizza_index(latest_data: Dict[str, Any], interval: str = 'hour') -> PizzaIndexData:
    """Calculate the Pizza Index from latest restaurant data"""
    current_time = datetime.utcnow().replace(tzinfo=timezone.utc)
    
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
    
    # Calculate change based on interval
    change = 0.0
    change_percent = 0.0
    
    try:
        headers = get_supabase_headers(use_service_role=True)
        
        # Determine the time period to look back based on interval
        if interval == "minute":
            lookback_time = current_time - timedelta(minutes=1)
        elif interval == "hour":
            lookback_time = current_time - timedelta(hours=1)
        elif interval == "day":
            lookback_time = current_time - timedelta(days=1)
        else:
            lookback_time = current_time - timedelta(hours=1)  # default to hour
        
        # Get historical data for comparison
        url = f"{SUPABASE_URL}/rest/v1/restaurant_popular_times"
        params = {
            'timestamp': f'gte.{lookback_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")}',
            'order': 'timestamp.desc'
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        url += f"?{query_string}"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            historical_data = response.json()
            
            if historical_data:
                # Group historical data by interval to get the previous period's value
                if interval == "minute":
                    # Get data from exactly 1 minute ago (previous minute)
                    minute_ago = current_time - timedelta(minutes=1)
                    period_data = []
                    for d in historical_data:
                        # Parse timestamp using robust parser
                        item_time = parse_timestamp_robust(d['timestamp'])
                        # Get data from the previous minute
                        if minute_ago.replace(second=0, microsecond=0) <= item_time < current_time.replace(second=0, microsecond=0):
                            period_data.append(d)
                elif interval == "hour":
                    # Get data from exactly 1 hour ago (previous hour)
                    hour_ago = current_time - timedelta(hours=1)
                    period_data = []
                    for d in historical_data:
                        # Parse timestamp using robust parser
                        item_time = parse_timestamp_robust(d['timestamp'])
                        # Get data from the previous hour
                        if hour_ago.replace(minute=0, second=0, microsecond=0) <= item_time < current_time.replace(minute=0, second=0, microsecond=0):
                            period_data.append(d)
                elif interval == "day":
                    # Get data from exactly 1 day ago (previous day)
                    day_ago = current_time - timedelta(days=1)
                    period_data = []
                    for d in historical_data:
                        # Parse timestamp using robust parser
                        item_time = parse_timestamp_robust(d['timestamp'])
                        # Get data from the previous day
                        if day_ago.replace(hour=0, minute=0, second=0, microsecond=0) <= item_time < current_time.replace(hour=0, minute=0, second=0, microsecond=0):
                            period_data.append(d)
                
                if period_data:
                    # Calculate previous period's average index value
                    prev_total_popularity = 0
                    prev_valid_count = 0
                    
                    for item in period_data:
                        if item.get('current_popularity') is not None:
                            prev_total_popularity += item['current_popularity']
                            prev_valid_count += 1
                    
                    if prev_valid_count > 0:
                        prev_avg_popularity = prev_total_popularity / prev_valid_count
                        prev_index_value = 100 + (prev_avg_popularity * 0.8)
                        
                        # Calculate change
                        change = round(index_value - prev_index_value, 1)
                        change_percent = round((change / prev_index_value) * 100, 2) if prev_index_value > 0 else 0.0
                        
    except Exception as e:
        logger.error(f"Error calculating change for interval {interval}: {e}")
        # Keep default values if calculation fails
    
    return PizzaIndexData(
        timestamp=current_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),  # Proper ISO format
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
async def get_pizza_index_live(interval: str = Query("hour", description="Time interval for change calculation: minute, hour, day")):
    """Get live Pizza Index data"""
    try:
        # Get latest data for all restaurants
        all_latest = await get_all_latest_data()
        
        # Calculate the pizza index with the specified interval
        pizza_index = calculate_pizza_index(all_latest, interval)
        
        return {
            "index": {
                "id": "pizza",
                "name": "Pizza Index",
                "symbol": "PZZA",
                "value": pizza_index.value,
                "change": pizza_index.change,
                "changePercent": pizza_index.changePercent,
                "description": "Real-time pizza demand",
                "methodology": "Aggregates current popularity data from major pizza establishments around the arlington area. Higher values indicate increased demand and potential economic activity.",
                "dataSources": ["Google Maps Popular Times", "Real-time Restaurant Data"]
            },
            "metadata": {
                "timestamp": pizza_index.timestamp,
                "total_popularity": pizza_index.total_popularity,
                "avg_popularity": pizza_index.avg_popularity,
                "active_restaurants": pizza_index.active_restaurants,
                "total_restaurants": pizza_index.total_restaurants,
                "interval": interval
            },
            "restaurants": pizza_index.restaurant_data
        }
        
    except Exception as e:
        logger.error(f"Error calculating pizza index: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/pizza-index/chart-data")
async def get_pizza_index_chart_data(
    days: int = Query(30, description="Number of days of historical data"),
    interval: str = Query("hour", description="Data interval: minute, hour, day")
):
    """Get historical chart data for the Pizza Index"""
    try:
        headers = get_supabase_headers(use_service_role=True)
        
        cutoff_date = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=days)
        
        # Add debug logging
        logger.info(f"Chart data request: days={days}, interval={interval}")
        logger.info(f"Cutoff date: {cutoff_date}")
        logger.info(f"Current time: {datetime.utcnow().replace(tzinfo=timezone.utc)}")
        
        # Get all data for the time period with pagination to handle large datasets
        all_data = []
        page_size = 1000
        offset = 0
        
        while True:
            url = f"{SUPABASE_URL}/rest/v1/restaurant_popular_times"
            params = {
                'timestamp': f'gte.{cutoff_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")}',
                'order': 'timestamp.asc',
                'limit': str(page_size),
                'offset': str(offset)
            }
            
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            url += f"?{query_string}"
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                page_data = response.json()
                if not page_data:  # No more data
                    break
                    
                all_data.extend(page_data)
                offset += page_size
                
                # If we got less than page_size, we've reached the end
                if len(page_data) < page_size:
                    break
            else:
                logger.error(f"Supabase API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=500, detail="Database error")
        
        data = all_data
        logger.info(f"Retrieved {len(data)} total records from database")
            
        # Group data by timestamp intervals
        chart_data = []
        
        if interval == "minute":
            # Group by minute
            minute_data = {}
            for item in data:
                # Parse timestamp using robust parser
                timestamp = parse_timestamp_robust(item['timestamp'])
                minute_key = timestamp.replace(second=0, microsecond=0)
                if minute_key not in minute_data:
                    minute_data[minute_key] = []
                minute_data[minute_key].append(item)
            
            # Calculate index for each minute
            for minute, items in sorted(minute_data.items()):
                total_popularity = 0
                valid_count = 0
                restaurant_count = 0
                
                for item in items:
                    restaurant_count += 1
                    if item.get('current_popularity') is not None:
                        total_popularity += item['current_popularity']
                        valid_count += 1
                
                # Only include data points if we have at least some valid data
                if valid_count > 0:
                    avg_popularity = total_popularity / valid_count
                    index_value = 100 + (avg_popularity * 0.8)
                    chart_data.append({
                        "timestamp": minute.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                        "value": round(index_value, 1),
                        "avg_popularity": round(avg_popularity, 1),
                        "data_points": valid_count,
                        "total_restaurants": restaurant_count
                    })
        elif interval == "hour":
            # Group by hour
            hourly_data = {}
            for item in data:
                # Parse timestamp using robust parser
                timestamp = parse_timestamp_robust(item['timestamp'])
                hour_key = timestamp.replace(minute=0, second=0, microsecond=0)
                if hour_key not in hourly_data:
                    hourly_data[hour_key] = []
                hourly_data[hour_key].append(item)
            
            # Calculate index for each hour
            for hour, items in sorted(hourly_data.items()):
                total_popularity = 0
                valid_count = 0
                restaurant_count = 0
                
                for item in items:
                    restaurant_count += 1
                    if item.get('current_popularity') is not None:
                        total_popularity += item['current_popularity']
                        valid_count += 1
                
                # Only include data points if we have at least some valid data
                if valid_count > 0:
                    avg_popularity = total_popularity / valid_count
                    index_value = 100 + (avg_popularity * 0.8)
                    chart_data.append({
                        "timestamp": hour.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                        "value": round(index_value, 1),
                        "avg_popularity": round(avg_popularity, 1),
                        "data_points": valid_count,
                        "total_restaurants": restaurant_count
                    })
        elif interval == "day":
            # Group by day
            daily_data = {}
            for item in data:
                # Parse timestamp using robust parser
                timestamp = parse_timestamp_robust(item['timestamp'])
                day_key = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
                if day_key not in daily_data:
                    daily_data[day_key] = []
                daily_data[day_key].append(item)
            
            # Calculate index for each day
            for day, items in sorted(daily_data.items()):
                total_popularity = 0
                valid_count = 0
                restaurant_count = 0
                
                for item in items:
                    restaurant_count += 1
                    if item.get('current_popularity') is not None:
                        total_popularity += item['current_popularity']
                        valid_count += 1
                
                # Only include data points if we have at least some valid data
                if valid_count > 0:
                    avg_popularity = total_popularity / valid_count
                    index_value = 100 + (avg_popularity * 0.8)
                    chart_data.append({
                        "timestamp": day.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                        "value": round(index_value, 1),
                        "avg_popularity": round(avg_popularity, 1),
                        "data_points": valid_count,
                        "total_restaurants": restaurant_count
                    })
        
        return {
            "chart_data": chart_data,
            "period_days": days,
            "interval": interval,
            "total_data_points": len(data)
        }
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
            'order': 'timestamp.desc'
        }
        
        if limit:
            params['limit'] = str(limit)
        
        # Add time filter if specified
        if days:
            cutoff_date = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=days)
            params['timestamp'] = f'gte.{cutoff_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")}'
        elif hours:
            cutoff_date = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(hours=hours)
            params['timestamp'] = f'gte.{cutoff_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")}'
        
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
            'order': 'timestamp.desc',
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

@app.get("/restaurant/{restaurant_id}/chart-data")
async def get_restaurant_chart_data(
    restaurant_id: str,
    days: int = Query(7, description="Number of days of historical data"),
    interval: str = Query("hour", description="Data interval: hour, day")
):
    """Get historical chart data for a specific restaurant"""
    if restaurant_id not in RESTAURANTS:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    try:
        headers = get_supabase_headers(use_service_role=True)
        
        cutoff_date = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=days)
        
        # Get data for the specific restaurant
        url = f"{SUPABASE_URL}/rest/v1/restaurant_popular_times"
        params = {
            'restaurant_id': f'eq.{restaurant_id}',
            'timestamp': f'gte.{cutoff_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")}',
            'order': 'timestamp.asc'
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
                    timestamp = parse_timestamp_robust(item['timestamp'])
                    hour_key = timestamp.replace(minute=0, second=0, microsecond=0)
                    
                    if hour_key not in hourly_data:
                        hourly_data[hour_key] = []
                    hourly_data[hour_key].append(item)
                
                # Calculate metrics for each hour
                for hour, items in hourly_data.items():
                    if items:
                        # Find the most recent item with valid popularity data
                        valid_items = [item for item in items if item.get('current_popularity') is not None]
                        
                        if valid_items:
                            latest_item = valid_items[-1]  # Most recent valid item
                            chart_data.append({
                                "timestamp": hour.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                                "popularity": latest_item.get('current_popularity', 0),
                                "rating": latest_item.get('rating'),
                                "data_points": len(valid_items),
                                "total_attempts": len(items),
                                "data_quality": len(valid_items) / len(items) if items else 0
                            })
                        else:
                            # No valid data for this hour, but we know we tried
                            chart_data.append({
                                "timestamp": hour.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                                "popularity": None,
                                "rating": None,
                                "data_points": 0,
                                "total_attempts": len(items),
                                "data_quality": 0,
                                "status": "no_data"
                            })
            
            elif interval == "day":
                # Group by day
                daily_data = {}
                for item in data:
                    timestamp = parse_timestamp_robust(item['timestamp'])
                    day_key = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
                    
                    if day_key not in daily_data:
                        daily_data[day_key] = []
                    daily_data[day_key].append(item)
                
                # Calculate metrics for each day
                for day, items in daily_data.items():
                    if items:
                        # Find the most recent item with valid popularity data
                        valid_items = [item for item in items if item.get('current_popularity') is not None]
                        
                        if valid_items:
                            latest_item = valid_items[-1]  # Most recent valid item
                            chart_data.append({
                                "timestamp": day.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                                "popularity": latest_item.get('current_popularity', 0),
                                "rating": latest_item.get('rating'),
                                "data_points": len(valid_items),
                                "total_attempts": len(items),
                                "data_quality": len(valid_items) / len(items) if items else 0
                            })
                        else:
                            # No valid data for this day, but we know we tried
                            chart_data.append({
                                "timestamp": day.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                                "popularity": None,
                                "rating": None,
                                "data_points": 0,
                                "total_attempts": len(items),
                                "data_quality": 0,
                                "status": "no_data"
                            })
            
            return {
                "restaurant_id": restaurant_id,
                "restaurant_name": RESTAURANTS[restaurant_id]["name"],
                "chart_data": chart_data,
                "period_days": days,
                "interval": interval,
                "total_data_points": len(data)
            }
        else:
            logger.error(f"Supabase API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Database error")
            
    except Exception as e:
        logger.error(f"Error generating restaurant chart data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/restaurant/{restaurant_id}/stats")
async def get_restaurant_stats(restaurant_id: str, days: int = 7):
    """Get statistics for a restaurant over the last N days"""
    if restaurant_id not in RESTAURANTS:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    try:
        headers = get_supabase_headers(use_service_role=True)
        
        cutoff_date = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=days)
        
        url = f"{SUPABASE_URL}/rest/v1/restaurant_popular_times"
        params = {
            'restaurant_id': f'eq.{restaurant_id}',
            'timestamp': f'gte.{cutoff_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")}',
            'order': 'timestamp.desc'
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
                'order': 'timestamp.desc',
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
        
        cutoff_date = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=days)
        
        url = f"{SUPABASE_URL}/rest/v1/restaurant_popular_times"
        params = {
            'timestamp': f'gte.{cutoff_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")}',
            'order': 'timestamp.desc'
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
