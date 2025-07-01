// Pizza Index API Service
// This service connects the frontend to the pizza index API

export interface PizzaIndexData {
  id: string;
  name: string;
  symbol: string;
  value: number;
  change: number;
  changePercent: number;
  description: string;
  methodology: string;
  dataSources: string[];
}

export interface PizzaIndexResponse {
  index: PizzaIndexData;
  metadata: {
    timestamp: string;
    total_popularity: number;
    avg_popularity: number;
    active_restaurants: number;
    total_restaurants: number;
  };
  restaurants: Record<string, {
    restaurant: {
      name: string;
      address: string;
    };
    popularity: number;
    rating?: number;
    timestamp: string;
  }>;
}

export interface ChartDataPoint {
  timestamp: string;
  value: number;
  avg_popularity: number;
  data_points: number;
}

export interface ChartDataResponse {
  chart_data: ChartDataPoint[];
  period_days: number;
  interval: string;
  total_data_points: number;
}

export interface RestaurantData {
  id: number;
  restaurant_id: string;
  restaurant_name: string;
  restaurant_address: string;
  timestamp: string;
  rating?: number;
  rating_count?: number;
  current_popularity?: number;
  time_spent_min?: number;
  time_spent_max?: number;
  popular_times?: any;
  created_at: string;
}

class PizzaIndexService {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  // Get live pizza index data
  async getPizzaIndexLive(): Promise<PizzaIndexResponse> {
    const response = await fetch(`${this.baseUrl}/pizza-index/live`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  // Get historical chart data
  async getPizzaIndexChartData(days: number = 7, interval: 'hour' | 'day' = 'hour'): Promise<ChartDataResponse> {
    const params = new URLSearchParams({
      days: days.toString(),
      interval: interval
    });
    
    const response = await fetch(`${this.baseUrl}/pizza-index/chart-data?${params}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  // Get data for a specific restaurant
  async getRestaurantData(
    restaurantId: string, 
    limit?: number, 
    days?: number, 
    hours?: number
  ): Promise<RestaurantData[]> {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (days) params.append('days', days.toString());
    if (hours) params.append('hours', hours.toString());
    
    const response = await fetch(`${this.baseUrl}/restaurant/${restaurantId}/data?${params}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  // Get latest data for a specific restaurant
  async getRestaurantLatest(restaurantId: string): Promise<RestaurantData> {
    const response = await fetch(`${this.baseUrl}/restaurant/${restaurantId}/latest`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  // Get statistics for a restaurant
  async getRestaurantStats(restaurantId: string, days: number = 7): Promise<any> {
    const params = new URLSearchParams({ days: days.toString() });
    const response = await fetch(`${this.baseUrl}/restaurant/${restaurantId}/stats?${params}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  // Get all restaurants list
  async getRestaurants(): Promise<{ restaurants: Record<string, any>; count: number }> {
    const response = await fetch(`${this.baseUrl}/restaurants`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  // Get latest data for all restaurants
  async getAllLatestData(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/data/latest`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  // Get data summary
  async getDataSummary(days: number = 7): Promise<any> {
    const params = new URLSearchParams({ days: days.toString() });
    const response = await fetch(`${this.baseUrl}/data/summary?${params}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  // Health check
  async healthCheck(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }
}

// Export a default instance
export const pizzaIndexService = new PizzaIndexService();

// Export the class for custom instances
export default PizzaIndexService; 