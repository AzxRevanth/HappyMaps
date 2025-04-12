import tweepy
import pandas as pd
import time
import os
import json
import random
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from tweepy.errors import TooManyRequests

# Your Bearer Token
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAGad0QEAAAAA0a1TyXSeyxpUbG14hYoqmEAxI3Q%3DpAs5LwE1tlOWsWGTaQXnFcdjmebQV09ogVkiqeEWgIVcXEwBK9"  # Replace with yours

# Initialize Tweepy client
client = tweepy.Client(bearer_token=BEARER_TOKEN)

# Setup Geolocator
geolocator = Nominatim(user_agent="tweet_locator")

# Output files
output_file = 'data.csv'
cache_file = 'location_cache.json'
shuffled_file = 'shuffled_localities.json'
progress_file = 'progress_state.json'

# Daily tweet cap (Free tier limit)
DAILY_TWEET_LIMIT = 100
TWEETS_PER_LOCALITY = 10  # Must be between 10 and 100 per API limits

# Expanded Localities List
localities = [
    # Central
    "MG Road", "Brigade Road", "Commercial Street", "Shivajinagar", "Cubbon Park", "Vidhana Soudha",

    # South
    "Jayanagar", "JP Nagar", "Banashankari", "Basavanagudi", "BTM Layout", "Electronic City", "Bannerghatta Road",

    # North
    "Hebbal", "Yelahanka", "RT Nagar", "Sanjay Nagar", "Manyata Tech Park",

    # East
    "Indiranagar", "Domlur", "HAL Layout", "CV Raman Nagar", "Whitefield", "KR Puram", "Marathahalli", "Mahadevpura",

    # West
    "Rajajinagar", "Malleswaram", "Vijayanagar", "Magadi Road", "Nayandahalli",

    # South-East
    "Koramangala", "HSR Layout", "Sarjapur Road", "Bellandur", "Harlur", "Kasavanahalli", "Agara",

    # Tech Parks
    "EcoSpace", "Bagmane Tech Park", "ITPL", "Global Village Tech Park"
]

# Geocode once and cache

def build_location_cache(localities):
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            cache = json.load(f)
        print("✅ Loaded location cache from file")
    else:
        cache = {}

    updated = False
    for loc in localities:
        if loc not in cache or cache[loc] == [None, None]:
            try:
                time.sleep(1)
                place = geolocator.geocode(loc + ", Bangalore, India")
                if place:
                    cache[loc] = [place.latitude, place.longitude]
                    print(f"📍 {loc}: {place.latitude}, {place.longitude}")
                else:
                    cache[loc] = [None, None]
                    print(f"⚠️ Could not geocode {loc}")
                updated = True
            except Exception as e:
                print(f"🚫 Error geocoding {loc}: {e}")
                cache[loc] = [None, None]
                updated = True

    if updated:
        with open(cache_file, 'w') as f:
            json.dump(cache, f)
        print("💾 Saved updated location cache")

    return cache

# Wait until the next 15-minute mark
def wait_until_next_15_minute():
    now = datetime.now()
    minutes = now.minute
    next_quarter = (minutes // 15 + 1) * 15
    if next_quarter == 60:
        next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    else:
        next_time = now.replace(minute=next_quarter, second=0, microsecond=0)
    wait_time = (next_time - now).total_seconds()
    print(f"🕒 Waiting {int(wait_time)} seconds until next 15-minute mark ({next_time.strftime('%H:%M')})...")
    time.sleep(wait_time)

# Fetch tweets and save

def fetch_and_store_tweets(locality, lat, lon, tweets_collected):
    if tweets_collected >= DAILY_TWEET_LIMIT:
        return tweets_collected

    query = f'{locality} -is:retweet lang:en'
    try:
        response = client.search_recent_tweets(
            query=query,
            tweet_fields=['created_at'],
            max_results=TWEETS_PER_LOCALITY
        )

        data = []
        if response.data:
            for tweet in response.data:
                if tweets_collected >= DAILY_TWEET_LIMIT:
                    break
                data.append({
                    'tweet_text': tweet.text,
                    'created_at': tweet.created_at,
                    'location': locality,
                    'latitude': lat,
                    'longitude': lon
                })
                tweets_collected += 1

            new_df = pd.DataFrame(data)

            if os.path.exists(output_file):
                existing_df = pd.read_csv(output_file)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df.drop_duplicates(subset=['tweet_text', 'created_at'], inplace=True)
            else:
                combined_df = new_df

            combined_df.to_csv(output_file, index=False)
            print(f"✅ {len(data)} tweets from '{locality}' saved to {output_file}")
        else:
            print(f"⚠️ No tweets found for {locality}")

    except TooManyRequests:
        print("🚨 Rate limit hit! Skipping to next 15-minute mark...")

    return tweets_collected

# Main Run
if __name__ == "__main__":
    location_cache = build_location_cache(localities)

    if os.path.exists(shuffled_file):
        with open(shuffled_file, 'r') as f:
            localities = json.load(f)
        print("✅ Loaded shuffled locality list from file")
    else:
        random.shuffle(localities)
        with open(shuffled_file, 'w') as f:
            json.dump(localities, f)
        print("🔀 Shuffled and saved new locality list")

    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            state = json.load(f)
        start_index = state.get('last_index', 0)
    else:
        start_index = 0

    tweet_count = 0

    for idx in range(start_index, len(localities)):
        if tweet_count >= DAILY_TWEET_LIMIT:
            print("🎯 Daily tweet limit reached.")
            break

        wait_until_next_15_minute()

        loc = localities[idx]
        lat, lon = location_cache[loc]
        tweet_count = fetch_and_store_tweets(loc, lat, lon, tweet_count)

        with open(progress_file, 'w') as f:
            json.dump({'last_index': idx + 1}, f)

    print(f"📊 Total tweets collected today: {tweet_count}")
