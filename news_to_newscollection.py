import csv
import pymongo
import os
# Replace this with your actual connection string
client = pymongo.MongoClient("mongodb+srv://piyushrathi105:19QXv6uNNlARGBiy@cluster0.grxmynq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# Connect to the database and collection
db = client["HappyMaps"]
collection = db["news"]  # You can change this to whatever you want

# Read CSV and insert into MongoDB
csv_path = os.path.join(os.path.dirname(__file__), "Bengaluru_news.csv")
with open(csv_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    data = list(reader)
    
    if data:
        collection.delete_many({})  # This clears all existing data in the collection
        collection.insert_many(data)
        print("CSV data inserted successfully!")
    else:
        print("No data found in CSV.")
