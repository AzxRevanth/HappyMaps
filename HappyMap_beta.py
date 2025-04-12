import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import praw
import requests
import csv
import pandas as pd
import nltk
import spacy
from datetime import datetime, timedelta
from langdetect import detect
from geopy.geocoders import Nominatim
from nltk.sentiment.vader import SentimentIntensityAnalyzer

nltk.download('punkt')
nltk.download('vader_lexicon')
spacy_model = spacy.load("en_core_web_sm")

# Initialize VADER
sia = SentimentIntensityAnalyzer()

CLICKBAIT_WORDS = ["shocking", "you won't believe", "don't", "secret", "revealed", "this is why",
                   "click here", "goes viral", "only in", "just two days", "this site", "must see"]

# ----------------------------------------
# CONFIG
# ----------------------------------------
NEWS_API_KEY = "3503f6afcd6f435d996e561157a3134b"#List of API here
REDDIT_CLIENT_ID = "wW98Cz7x7Rvly3zaScWDvQ"
REDDIT_CLIENT_SECRET = "ChLWjBnbmNZHZCfb5bnU03LvvoCHog"
REDDIT_USER_AGENT = "happiness-mapper/0.2"
POST_LIMIT = 100
DAYS = 1
PAGES = 5
PAGE_SIZE = 20
MASTER_CSV = "city_happiness_master.csv"
# ----------------------------------------

# List of 100 major Indian cities
indian_cities = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Ahmedabad", 
    "Chennai", "Kolkata", "Surat", "Pune", "Jaipur",   
    "Mangalore", "Belgaum", "Ambattur", "Tirunelveli", "Malegaon", 
    "Gaya", "Jalgaon", "Udaipur", "Maheshtala", "Tirupur"
]

# List of 20 significant countries including India
countries = [
    "India", "United States", "China", "Japan", "Germany",
    "United Kingdom", "France", "Brazil", "Italy", "Canada",
    "Russia", "South Korea", "Australia", "Spain", "Mexico",
    "Indonesia", "Netherlands", "Saudi Arabia", "Turkey", "Switzerland"
]

# Combine cities and countries
locations = indian_cities + countries

# Get Coordinates
geolocator = Nominatim(user_agent="city_locator")

# Reddit Setup
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)
NEGATIVE_OVERRIDE = [
    "murder", "rape", "killed", "executed", "death", "dead", "suicide",
    "massacre", "assault", "beheaded", "explosion", "terrorist", "hanged"
]
# ----------------------------------------
# Functions
# ----------------------------------------
def fetch_reddit_posts(subreddit_name):#function to be modified to access list of apis
    time_cutoff = datetime.utcnow().timestamp() - (DAYS * 86400)
    subreddit = reddit.subreddit(subreddit_name)
    results = []
    try:
        for post in subreddit.hot(limit=POST_LIMIT):
            if post.created_utc < time_cutoff:
                continue
            post.comments.replace_more(limit=0)
            top_comments = [c.body for c in post.comments[:3] if len(c.body) > 0]
            results.append({
                "Title": post.title,
                "Description": post.selftext,
                "TopComment1": top_comments[0] if len(top_comments) > 0 else "",
                "TopComment2": top_comments[1] if len(top_comments) > 1 else "",
                "TopComment3": top_comments[2] if len(top_comments) > 2 else ""
            })
    except Exception as e:
        print(f"⚠️ Failed to fetch from r/{subreddit_name}: {e}")
    return results

def fetch_news_articles(location):
    to_date = datetime.now()
    from_date = to_date - timedelta(days=DAYS)
    seen_titles = set()
    articles_data = []
    for page in range(1, PAGES + 1):
        url = f"https://newsapi.org/v2/everything?q={location}&from={from_date.strftime('%Y-%m-%d')}&to={to_date.strftime('%Y-%m-%d')}&language=en&pageSize={PAGE_SIZE}&sortBy=publishedAt&page={page}&apiKey={NEWS_API_KEY}"
        r = requests.get(url).json()
        articles = r.get("articles", [])
        if not articles:
            break
        for article in articles:
            title = article.get("title", "")
            description = article.get("description", "")
            date = article.get("publishedAt", "")
            if title in seen_titles or not (title or description):
                continue
            seen_titles.add(title)
            articles_data.append([title, description, date])
    return articles_data

def is_english(text):
    try:
        return detect(text) == 'en'
    except:
        return False

def is_clickbait(text):
    return any(word in text.lower() for word in CLICKBAIT_WORDS)

def get_sentiment(text):
    text_lower = text.lower()
    
    # Check for any hard negative word from the override list
    if any(neg_word in text_lower for neg_word in NEGATIVE_OVERRIDE):
        return 0.01  # Return default negative value and skip VADER
    
    # Calculate VADER sentiment score if no negative override
    scores = sia.polarity_scores(text)
    compound = scores['compound']
    
    # Scale compound score to 0–10 (VADER returns -1 to 1 range, so this scales it to 0 to 10)
    return 5 * (compound + 1)  # Scale from -1 to 1 to 0 to 10

def compute_happiness_score(scores, max_len):
    # Step 1: Filter out 0.0 scores (neutral/off-topic)
    filtered_scores = [s for s in scores if s != 0.0]
    
    if not filtered_scores:
        return 0.0  # Default neutral if no valid data
    
    # Step 2: Calculate average of non-neutral scores
    avg_score = sum(filtered_scores) / len(filtered_scores)
    
    # Step 3: Confidence weighting (more data → trust the score more)
    confidence = min(1.0, len(filtered_scores) / 10)  # 10+ articles = full confidence
    weighted_score = avg_score * confidence + 5.0 * (1 - confidence)
    
    return round(weighted_score, 2)

def analyze_entries(entries):
    all_scores = []
    seen = set()
    for entry in entries:
        title = entry["Title"]
        text = f"{entry['Title']}. {entry['Description']}"
        if title in seen or not text or not is_english(text):
            continue
        seen.add(title)
        score = get_sentiment(text)
        # Skip neutral (4-6) to amplify signal
        if 4 <= score <= 6:
            continue
        # Apply clickbait penalty *before* appending
        if is_clickbait(title):
            score *= 0.5  # Halve score, but don't invert
        all_scores.append(score)
    return all_scores

def process_location(location):
    print(f"\nProcessing: {location}")
    location_lower = location.lower()
    subreddit_name = location_lower.replace(" ", "")
    
    # Get Coordinates
    try:
        location_data = geolocator.geocode(location)
        if not location_data:
            print(f"❌ Couldn't find location data for {location}")
            return None
        
        latitude, longitude = location_data.latitude, location_data.longitude
    except Exception as e:
        print(f"❌ Geocoding failed for {location}: {e}")
        return None
    
    # 1. Fetch Reddit posts
    print(f"📥 Fetching Reddit posts for r/{subreddit_name}")
    reddit_data = fetch_reddit_posts(subreddit_name)
    
    # 2. Fetch News articles
    print(f"📰 Fetching News articles for {location}")
    news_data = fetch_news_articles(location)
    
    # 3. Analyze Reddit
    reddit_scores = analyze_entries([
        {"Title": row["Title"], "Description": row["Description"]}
        for row in reddit_data
    ])
    
    # 4. Analyze News
    news_scores = analyze_entries([
        {"Title": row[0], "Description": row[1]} for row in news_data
    ])
    
    reddit_score = compute_happiness_score(reddit_scores, POST_LIMIT)
    news_score = compute_happiness_score(news_scores, PAGES * PAGE_SIZE)
    total_score = news_score*0.78 + 0.22*reddit_score
    
    print(f"🎯 Scores for {location}:")
    print(f"Reddit Score: {reddit_score} / 10")
    print(f"News Score:   {news_score} / 10")
    print(f"Total Score:  {total_score} / 10")
    
    return {
        "Location": location,
        "Latitude": latitude,
        "Longitude": longitude,
        "Reddit_Score": reddit_score,
        "News_Score": news_score,
        "Total_Score": total_score
    }

# ----------------------------------------
# Main Execution
# ----------------------------------------

# Initialize master CSV
if not os.path.exists(MASTER_CSV):
    with open(MASTER_CSV, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Location", "Latitude", "Longitude", "Total_Score"])

# Process all locations
for i, location in enumerate(locations, 1):
    print(f"\n🔹 Processing location {i} of {len(locations)}: {location}")
    try:
        result = process_location(location)
        if result:
            with open(MASTER_CSV, "a", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    result["Location"],
                    result["Latitude"],
                    result["Longitude"],
                    result["Total_Score"]
                ])
    except Exception as e:
        print(f"❌ Error processing {location}: {e}")
        continue

print("\n✅ All locations processed and saved to", MASTER_CSV)
