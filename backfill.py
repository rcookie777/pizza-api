import os
import requests
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def fetch_all_popular_times():
    headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json'
    }
    all_data = []
    page_size = 1000
    offset = 0
    while True:
        url = f"{SUPABASE_URL}/rest/v1/restaurant_popular_times"
        params = {
            'order': 'timestamp.asc',
            'limit': str(page_size),
            'offset': str(offset)
        }
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        resp = requests.get(f"{url}?{query_string}", headers=headers)
        if resp.status_code != 200:
            print(f"Error fetching: {resp.status_code} {resp.text}")
            break
        page = resp.json()
        if not page:
            break
        all_data.extend(page)
        offset += page_size
        if len(page) < page_size:
            break
    print(f"Fetched {len(all_data)} records")
    return all_data

def aggregate_and_upsert(data, interval='hour'):
    # Group by interval bucket
    buckets = defaultdict(list)
    for item in data:
        ts = item['timestamp']
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        if interval == 'minute':
            bucket = dt.replace(second=0, microsecond=0)
        elif interval == 'hour':
            bucket = dt.replace(minute=0, second=0, microsecond=0)
        elif interval == 'day':
            bucket = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            continue
        buckets[bucket].append(item)
    print(f"Aggregating {len(buckets)} {interval} buckets")
    # Aggregate and upsert
    headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates'
    }
    agg_url = f"{SUPABASE_URL}/rest/v1/pizza_index_aggregates"
    for bucket, items in buckets.items():
        total_popularity = 0
        valid_count = 0
        for item in items:
            if item.get('current_popularity') is not None:
                total_popularity += item['current_popularity']
                valid_count += 1
        avg_popularity = (total_popularity / valid_count) if valid_count else 0
        index_value = 100 + (avg_popularity * 0.8) if valid_count else 100
        agg_data = {
            "interval": interval,
            "timestamp": bucket.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "value": round(index_value, 1),
            "avg_popularity": round(avg_popularity, 1),
            "data_points": valid_count
        }
        resp = requests.post(agg_url, headers=headers, json=agg_data)
        if resp.status_code not in [200, 201]:
            print(f"Failed to upsert {agg_data}: {resp.status_code} {resp.text}")
        else:
            print(f"Upserted: {agg_data}")

if __name__ == "__main__":
    all_data = fetch_all_popular_times()
    aggregate_and_upsert(all_data, interval='minute')
    aggregate_and_upsert(all_data, interval='hour')
    aggregate_and_upsert(all_data, interval='day')