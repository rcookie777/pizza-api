# Restaurant Popular Times API

A FastAPI service that provides access to restaurant popular times data stored in Supabase. This API allows you to query historical data, get the latest information, and view statistics for restaurants around the Pentagon area.

## 🍕 Pentagon Pizza Index

The API now includes a **Pentagon Pizza Index** that aggregates real-time data from 5 major pizza establishments around the Pentagon:

- **Extreme Pizza** - 1419 S Fern St, Arlington, VA 22202
- **Colony Grill** - 2800 Clarendon Blvd, Arlington, VA 22201  
- **Wise Guy Pizza** - 1735 North Lynn St, Arlington, VA 22209
- **Night Hawk Brewery & Pizza** - 1201 S Joyce St, Ste C10, Arlington, VA 22202
- **District Pizza Palace** - 2325 S Eads St, Arlington, VA 22202

The index calculates a real-time value based on current popularity data from all restaurants, providing insights into pizza demand patterns around the Pentagon.

## Features

- **🍕 Pentagon Pizza Index**: Real-time aggregated index from 5 pizza establishments
- **📊 Live Data**: Current popularity, ratings, and wait times
- **📈 Historical Charts**: Hourly and daily historical data for trend analysis
- **🏪 Individual Restaurant Data**: Detailed data for each establishment
- **📱 Frontend Integration**: Ready-to-use TypeScript service for React apps
- **🔄 Auto-refresh**: Real-time data updates every 30 minutes
- **📋 Statistics**: Comprehensive analytics and trend analysis
- **🌐 CORS Support**: Ready for frontend integration
- **📚 Auto-generated Documentation**: Interactive API docs with Swagger UI

## API Endpoints

### 🍕 Pizza Index (New!)
- `GET /pizza-index/live` - Get live Pentagon Pizza Index data
- `GET /pizza-index/chart-data` - Get historical chart data for the index

### Health & Status
- `GET /` - Health check with database connectivity status
- `GET /health` - Simple health check
- `GET /restaurants` - List all configured restaurants

### Restaurant Data
- `GET /restaurant/{restaurant_id}/data` - Get historical data for a restaurant
- `GET /restaurant/{restaurant_id}/latest` - Get the most recent data for a restaurant
- `GET /restaurant/{restaurant_id}/stats` - Get statistics for a restaurant over time

### Aggregated Data
- `GET /data/latest` - Get latest data for all restaurants
- `GET /data/summary` - Get summary statistics for all restaurants

### Legacy Endpoints
- `GET /extreme-pizza/live` - Legacy endpoint for Extreme Pizza live data
- `GET /extreme-pizza/history` - Legacy endpoint for Extreme Pizza history

## Query Parameters

### Time Filtering
- `days` - Get data from the last N days
- `hours` - Get data from the last N hours
- `limit` - Limit the number of records returned

### Chart Data Parameters
- `interval` - Data interval: `hour` or `day`

### Examples
```
GET /pizza-index/live
GET /pizza-index/chart-data?days=7&interval=hour
GET /restaurant/extreme_pizza/data?days=7&limit=10
GET /restaurant/colony_grill/stats?days=30
GET /data/summary?days=14
```

## Restaurant IDs

Currently configured restaurants:
- `extreme_pizza` - Extreme Pizza
- `colony_grill` - Colony Grill
- `wise_guy` - Wise Guy Pizza
- `night_hawk` - Night Hawk Brewery & Pizza
- `district_pizza` - District Pizza Palace

## Frontend Integration

### TypeScript Service

The API includes a ready-to-use TypeScript service (`pizza-index-service.ts`) for frontend integration:

```typescript
import { pizzaIndexService } from './pizza-index-service';

// Get live pizza index data
const pizzaData = await pizzaIndexService.getPizzaIndexLive();

// Get historical chart data
const chartData = await pizzaIndexService.getPizzaIndexChartData(7, 'hour');

// Get restaurant data
const restaurantData = await pizzaIndexService.getRestaurantData('extreme_pizza', 10, 7);
```

### React Integration Example

```typescript
import React, { useState, useEffect } from 'react';
import { pizzaIndexService } from './pizza-index-service';

const PizzaIndexComponent = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const pizzaData = await pizzaIndexService.getPizzaIndexLive();
        setData(pizzaData);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (!data) return <div>No data available</div>;

  return (
    <div>
      <h1>{data.index.name}</h1>
      <div>Value: {data.index.value}</div>
      <div>Change: {data.index.change}%</div>
    </div>
  );
};
```

## Setup

### Prerequisites
- Python 3.8+
- Supabase account and project
- Environment variables configured

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your Supabase credentials
```

4. Run the API:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Environment Variables

Create a `.env` file with the following variables:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Logging
LOG_LEVEL=INFO
```

## Deployment

### Render (Recommended)

1. Connect your repository to Render
2. Create a new Web Service
3. Configure the following:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables in Render dashboard
5. Deploy!

### Other Platforms

The API can be deployed to any platform that supports Python web applications:
- Heroku
- Railway
- DigitalOcean App Platform
- AWS Elastic Beanstalk
- Google Cloud Run

## API Documentation

Once the API is running, you can access:
- **Interactive Docs**: `http://localhost:8000/docs` (Swagger UI)
- **ReDoc**: `http://localhost:8000/redoc` (Alternative documentation)

## Response Format

### Pizza Index Response
```json
{
  "index": {
    "id": "pizza",
    "name": "Pentagon Pizza Index",
    "symbol": "PZZA",
    "value": 156.8,
    "change": 2.3,
    "changePercent": 1.49,
    "description": "Real-time pizza demand index around the Pentagon",
    "methodology": "Aggregates current popularity data from major pizza establishments...",
    "dataSources": ["Google Maps Popular Times", "Real-time Restaurant Data"]
  },
  "metadata": {
    "timestamp": "2024-01-15T14:30:00Z",
    "total_popularity": 425,
    "avg_popularity": 85.0,
    "active_restaurants": 5,
    "total_restaurants": 5
  },
  "restaurants": {
    "extreme_pizza": {
      "restaurant": {
        "name": "Extreme Pizza",
        "address": "1419 S Fern St, Arlington, VA 22202"
      },
      "popularity": 75,
      "rating": 4.2,
      "timestamp": "2024-01-15T14:30:00Z"
    }
  }
}
```

### Chart Data Response
```json
{
  "chart_data": [
    {
      "timestamp": "2024-01-15T14:00:00Z",
      "value": 156.8,
      "avg_popularity": 85.0,
      "data_points": 5
    }
  ],
  "period_days": 7,
  "interval": "hour",
  "total_data_points": 840
}
```

### Restaurant Data
```json
{
  "id": 1,
  "restaurant_id": "extreme_pizza",
  "restaurant_name": "Extreme Pizza",
  "restaurant_address": "1419 S Fern St, Arlington, VA 22202",
  "timestamp": "2024-01-15T14:30:00Z",
  "rating": 4.2,
  "rating_count": 150,
  "current_popularity": 75,
  "time_spent_min": 15,
  "time_spent_max": 45,
  "popular_times": {...},
  "created_at": "2024-01-15T14:30:00Z"
}
```

## Error Handling

The API returns appropriate HTTP status codes:
- `200` - Success
- `404` - Restaurant not found or no data available
- `500` - Internal server error or database connection issues

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest httpx

# Run tests
python test_api.py
```

### Adding New Restaurants

To add a new restaurant, update the `RESTAURANTS` dictionary in `main.py`:

```python
RESTAURANTS = {
    "extreme_pizza": {
        "name": "Extreme Pizza",
        "address": "1419 S Fern St, Arlington, VA 22202"
    },
    "new_restaurant": {
        "name": "New Restaurant",
        "address": "123 Main St, City, State 12345"
    }
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.


