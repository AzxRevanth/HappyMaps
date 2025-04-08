import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # Suppress TensorFlow warnings

import transformers
transformers.logging.set_verbosity_error()  # Suppress Hugging Face warnings

print("🧠 Loading sentiment model...")
from transformers import pipeline
sentiment_model = pipeline(
    "sentiment-analysis",
    model="distilbert-base-uncased-finetuned-sst-2-english"
)
print("✅ Model loaded.\n")

import pandas as pd
import nltk
import spacy
from langdetect import detect

nltk.download('punkt')
ner_model = spacy.load("en_core_web_sm")

CITY = "Bengaluru"
CSV_FILE = f"{CITY}_news.csv"

CLICKBAIT_WORDS = [
    "shocking", "you won't believe", "don't", "secret", "revealed", "this is why",
    "click here", "goes viral", "only in", "just two days", "this site", "must see"
]

def is_english(text):
    try:
        return detect(text) == 'en'
    except:
        return False

def is_clickbait(text):
    return any(word in text.lower() for word in CLICKBAIT_WORDS)

def get_sentiment(text):
    try:
        chunk = text[:256]
        result = sentiment_model(chunk)[0]
        score = result['score']
        return score if result['label'] == 'POSITIVE' else -score
    except:
        return 0.0
def has_city_as_location(text, city):
    aliases = [
        city.lower(),
        "bangalore",
        "namma bangalore",
        "silicon valley of india",
        "garden city",
        "blr",
        "bengaluru",
        "namma bengaluru",
        "b'lore",
        "it capital of india",
        "startup hub",
        "india’s tech city",
        "garden city",
        "air conditioned city",
        "pub capital of india",
        "lake city",
        "south india's metro",
        "karnataka's capital",
        "india's tech capital"
    ]
    
    text_lower = text.lower()
    for alias in aliases:
        if alias in text_lower:
            return True

    # fallback to spaCy NER
    doc = ner_model(text)
    for ent in doc.ents:
        if ent.label_ == "GPE" and any(alias in ent.text.lower() for alias in aliases):
            return True

    return False

# Load and clean CSV
df = pd.read_csv(CSV_FILE)
df.drop_duplicates(subset=["Title", "Description"], inplace=True)
df.dropna(subset=["Title", "Description"], inplace=True)

seen_titles = set()
all_scores = []

# Loop through news entries
for _, row in df.iterrows():
    title = row.get("Title", "")
    description = row.get("Description", "")
    text = f"{title}. {description}".strip()

    if title in seen_titles or not isinstance(text, str) or not text.strip():
        continue
    seen_titles.add(title)

    if not is_english(text):
        continue
    if not has_city_as_location(title + " " + description, CITY):
        continue
    weight = 0.5 if is_clickbait(title) else 1.0
    score = get_sentiment(text)
    final_score = score * weight
    all_scores.append(final_score)

    print("=" * 80)
    print(f"📰 Title: {title}")
    print(f"💬 Description: {description}")
    print(f"📊 Final weighted sentiment score: {final_score:.3f}")
    print("=" * 80)

# Final happiness score
PAGES = 5
PAGE_SIZE = 20

if all_scores:
    avg = sum(all_scores) / len(all_scores)
    norm = avg * (len(all_scores) / (PAGES * PAGE_SIZE))
    happiness = round((norm + 1) * 5, 2)
else:
    happiness = 0.0

print(f"\n🎯 Final happiness score for {CITY}: {happiness} / 10")
