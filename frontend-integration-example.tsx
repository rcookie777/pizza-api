// Example of how to integrate the Pizza Index API with your Index.tsx frontend
// This shows how to replace the hardcoded data with real API calls

import React, { useState, useEffect } from 'react';
import { pizzaIndexService, PizzaIndexResponse, ChartDataResponse } from './pizza-index-service';

// Updated Index component that uses real API data
const IndexWithRealData = () => {
  const [pizzaIndexData, setPizzaIndexData] = useState<PizzaIndexResponse | null>(null);
  const [chartData, setChartData] = useState<ChartDataResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch live pizza index data
  const fetchPizzaIndexData = async () => {
    try {
      setLoading(true);
      const data = await pizzaIndexService.getPizzaIndexLive();
      setPizzaIndexData(data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch pizza index data');
      console.error('Error fetching pizza index:', err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch chart data
  const fetchChartData = async () => {
    try {
      const data = await pizzaIndexService.getPizzaIndexChartData(7, 'hour');
      setChartData(data);
    } catch (err) {
      console.error('Error fetching chart data:', err);
    }
  };

  // Load data on component mount
  useEffect(() => {
    fetchPizzaIndexData();
    fetchChartData();
  }, []);

  // Auto-refresh data every 5 minutes
  useEffect(() => {
    const interval = setInterval(() => {
      fetchPizzaIndexData();
    }, 5 * 60 * 1000); // 5 minutes

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading Pizza Index Data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error}</p>
          <button 
            onClick={fetchPizzaIndexData}
            className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!pizzaIndexData) {
    return null;
  }

  // Transform API data to match your frontend structure
  const weirdIndexes = [
    {
      id: pizzaIndexData.index.id,
      name: pizzaIndexData.index.name,
      symbol: pizzaIndexData.index.symbol,
      value: pizzaIndexData.index.value,
      change: pizzaIndexData.index.change,
      changePercent: pizzaIndexData.index.changePercent,
      description: pizzaIndexData.index.description,
      methodology: pizzaIndexData.index.methodology,
      dataSources: pizzaIndexData.index.dataSources,
      // Additional data from API
      metadata: pizzaIndexData.metadata,
      restaurants: pizzaIndexData.restaurants
    }
  ];

  return (
    <div className="min-h-screen bg-background text-foreground font-sans transition-colors">
      {/* Your existing MarketHeader component */}
      {/* <MarketHeader /> */}
      
      <div className="container mx-auto px-3 sm:px-4 lg:px-6 py-4 sm:py-6">
        <div className="mb-6 sm:mb-8 flex flex-col sm:flex-row justify-between items-start gap-4">
          <div className="flex-1">
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-2 text-foreground">
              Pentagon Pizza Index
            </h1>
            <p className="text-muted-foreground text-sm sm:text-base lg:text-lg">
              Real-time pizza demand around the Pentagon • Live Data • Professional Analytics
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              Last updated: {new Date(pizzaIndexData.metadata.timestamp).toLocaleString()}
            </p>
          </div>
          {/* <ThemeToggle /> */}
        </div>

        {/* Restaurant Status Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
          {Object.entries(pizzaIndexData.restaurants).map(([id, data]) => (
            <div key={id} className="bg-card border border-border rounded-lg p-4 text-center">
              <h3 className="font-semibold text-sm mb-2">{data.restaurant.name}</h3>
              <div className="text-2xl font-bold text-primary">
                {data.popularity}%
              </div>
              <div className="text-xs text-muted-foreground">
                {data.rating ? `⭐ ${data.rating}` : 'No rating'}
              </div>
            </div>
          ))}
        </div>

        {/* Main Index Card */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-8">
          {weirdIndexes.map((index) => (
            <div key={index.id} className="bg-card border-border hover:border-primary/30 hover:shadow-lg transition-all duration-200 rounded-lg p-6">
              <div className="flex flex-col sm:flex-row justify-between items-start gap-2 sm:gap-0 mb-4">
                <div className="flex-1 min-w-0">
                  <h2 className="text-lg sm:text-xl text-card-foreground font-semibold break-words">
                    {index.name}
                  </h2>
                  <p className="text-muted-foreground text-xs sm:text-sm mt-1">
                    {index.description}
                  </p>
                </div>
                <div className="bg-primary/10 text-primary border border-primary/20 px-2 py-1 rounded text-sm font-medium">
                  {index.symbol}
                </div>
              </div>
              
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-4 mb-4">
                <span className="text-2xl sm:text-3xl font-bold text-card-foreground">
                  {index.value}
                </span>
                <div className={`flex items-center gap-1 ${
                  index.change >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-500 dark:text-red-400'
                }`}>
                  <span className="text-lg">
                    {index.change >= 0 ? '↗' : '↘'}
                  </span>
                  <span className="font-semibold text-sm sm:text-base">
                    {index.change >= 0 ? '+' : ''}{index.change} ({index.changePercent >= 0 ? '+' : ''}{index.changePercent}%)
                  </span>
                </div>
              </div>

              {/* Additional Stats */}
              <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                <div>
                  <div className="text-muted-foreground">Active Restaurants</div>
                  <div className="font-semibold">{index.metadata.active_restaurants}/{index.metadata.total_restaurants}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Avg Popularity</div>
                  <div className="font-semibold">{index.metadata.avg_popularity}%</div>
                </div>
              </div>

              {/* Chart placeholder - you would integrate your IndexChart component here */}
              <div className="h-32 bg-muted rounded flex items-center justify-center text-muted-foreground">
                Chart Component Placeholder
                {/* <IndexChart 
                  indexId={index.id}
                  overlayEnabled={overlayEnabled}
                  overlayType={overlayType}
                  chartData={chartData}
                /> */}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default IndexWithRealData;

// Example of how to use the service in your existing Index.tsx
export const usePizzaIndexData = () => {
  const [data, setData] = useState<PizzaIndexResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await pizzaIndexService.getPizzaIndexLive();
        setData(result);
        setError(null);
      } catch (err) {
        setError('Failed to fetch data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
};

// Example of how to modify your existing weirdIndexes array
export const getRealPizzaIndexData = async (): Promise<any[]> => {
  try {
    const pizzaData = await pizzaIndexService.getPizzaIndexLive();
    
    return [
      {
        id: pizzaData.index.id,
        name: pizzaData.index.name,
        symbol: pizzaData.index.symbol,
        value: pizzaData.index.value,
        change: pizzaData.index.change,
        changePercent: pizzaData.index.changePercent,
        description: pizzaData.index.description,
        methodology: pizzaData.index.methodology,
        dataSources: pizzaData.index.dataSources
      }
    ];
  } catch (error) {
    console.error('Error fetching pizza index data:', error);
    // Return fallback data
    return [
      {
        id: 'pizza',
        name: 'Pentagon Pizza Index',
        symbol: 'PZZA',
        value: 127.4,
        change: +2.3,
        changePercent: +1.84,
        description: 'Real-time pizza demand index around the Pentagon',
        methodology: 'Aggregates current popularity data from major pizza establishments around the Pentagon area.',
        dataSources: ['Google Maps Popular Times', 'Real-time Restaurant Data']
      }
    ];
  }
}; 