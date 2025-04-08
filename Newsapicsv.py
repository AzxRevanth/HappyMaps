import requests
import csv
from datetime import datetime, timedelta

API_KEY = "db95476cd3cb4943b989aa069f3c886f"
CITY = input("City name: ").strip()

# Date range
to_date = datetime.now()
from_date = to_date - timedelta(days=3)

PAGES = 5
PAGE_SIZE = 20

# Collect data
articles_data = []
seen_titles = set()

for page in range(1, PAGES + 1):
    print(f"📦 Fetching Page {page}")
    url = f"https://newsapi.org/v2/everything?q={CITY}&from={from_date.strftime('%Y-%m-%d')}&to={to_date.strftime('%Y-%m-%d')}&language=en&pageSize={PAGE_SIZE}&sortBy=publishedAt&page={page}&apiKey={API_KEY}"
    r = requests.get(url).json()

    articles = r.get("articles", [])
    if not articles:
        print("❌ No articles found.")
        break

    for article in articles:
        title = article.get("title", "")
        description = article.get("description", "")
        date = article.get("publishedAt", "")

        if title in seen_titles or (not title and not description):
            continue
        seen_titles.add(title)

        articles_data.append([title, description, date])

# Save to CSV
newsdat = f"{CITY}_news.csv"
with open(newsdat, "w", newline='', encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Title", "Description", "Published At"])
    writer.writerows(articles_data)

print(f"\n✅ Saved {len(articles_data)} articles to {newsdat}")
