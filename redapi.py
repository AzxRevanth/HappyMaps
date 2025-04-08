import praw
import datetime
from textblob import TextBlob
import math

# Replace with your credentials
reddit = praw.Reddit(
    client_id="wW98Cz7x7Rvly3zaScWDvQ",
    client_secret="ChLWjBnbmNZHZCfb5bnU03LvvoCHog",
    user_agent="happiness-mapper/0.1"
)

# --- Parameters ---
subreddit_name = "bangalore"
post_limit = 100
time_cutoff = datetime.datetime.utcnow().timestamp() - (24 * 60 * 60)

# --- Relevance keywords with weights ---
relevance_keywords = {
    "high": (3, ["accident", "protest", "crime", "power cut", "flood", "fire", "hospital", "strike", "violence", "government", "robbery", "rape", "murder"]),
    "mid": (2, ["traffic", "pollution", "weather", "infrastructure", "civic", "electricity", "transport", "price hike", "water shortage", "road", "metro", "bus"]),
    "low": (1, ["restaurant", "event", "cats", "festival", "movie", "sale", "food", "recommendation", "photography", "adoption", "rehome", "pet"]),
}

# --- Function: Sentiment Score ---
def get_sentiment(text):
    blob = TextBlob(text)
    return blob.sentiment.polarity  # Between -1 and 1

# --- Function: Relevance Score ---
def get_relevance(text):
    score = 0
    text = text.lower()
    for level, (weight, keywords) in relevance_keywords.items():
        for kw in keywords:
            if kw in text:
                score += weight
    return score

# --- Analyze Posts ---
subreddit = reddit.subreddit(subreddit_name)
results = []

for post in subreddit.hot(limit=post_limit):
    if post.created_utc < time_cutoff:
        continue

    content = (post.title + " " + post.selftext).lower()
    post_sentiment = get_sentiment(content)
    relevance = get_relevance(content)

    post.comments.replace_more(limit=0)
    top_comments = post.comments[:3]
    comment_sentiments = [get_sentiment(c.body) for c in top_comments if len(c.body) > 0]
    avg_comment_sentiment = sum(comment_sentiments) / len(comment_sentiments) if comment_sentiments else 0

    # Relevance-based multiplier
    if relevance <= 1:
        multiplier = 1.0
    elif relevance == 2:
        multiplier = 1.2
    else:
        multiplier = 1.4

    # Upvote weight
    upvote_weight = math.log10(post.score + 10)

    # Happiness calculation
    raw_score = (post_sentiment + avg_comment_sentiment) * multiplier * upvote_weight
    happiness_score = round((raw_score + 1) * 5, 2)  # Normalize to 0-10

    results.append({
        "title": post.title,
        "score": post.score,
        "url": post.url,
        "post_sentiment": round(post_sentiment, 3),
        "comment_sentiments": [round(s, 3) for s in comment_sentiments],
        "relevance": relevance,
        "happiness_score": min(max(happiness_score, 0), 10)  # Clamp between 0-10
    })

# --- Sort by upvotes ---
results = sorted(results, key=lambda x: x["score"], reverse=True)

# --- Print Output ---
for post in results:
    print(f"\n🧵 Title: {post['title']}")
    print(f"🔥 Upvotes: {post['score']}")
    print(f"📎 URL: {post['url']}")
    print(f"😊 Post Sentiment: {post['post_sentiment']}")
    print(f"💬 Comment Sentiments: {post['comment_sentiments']}")
    print(f"🎯 Relevance Score: {post['relevance']}")
    print(f"🌈 Happiness Score (/10): {post['happiness_score']}")

# --- Overall Happiness Score ---
if results:
    overall_score = sum([p["happiness_score"] for p in results]) / len(results)
    overall_score = round(overall_score, 2)
    print(f"\n🌍 Overall Happiness Score (Bangalore) ➤ {overall_score} / 10")
else:
    print("\n⚠️ No posts found in the given time range.")

