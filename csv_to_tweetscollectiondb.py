import csv
import pymongo

# Replace this with your actual connection string
client = pymongo.MongoClient("mongodb+srv://piyushrathi105:19QXv6uNNlARGBiy@cluster0.grxmynq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# Connect to the database and collection
db = client["HappyMaps"]
collection = db["tweets"]  # You can change this to whatever you want

# Read CSV and insert into MongoDB
with open("data.csv", newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    data = list(reader)
    
    '''for i, row in enumerate(reader, start=1):
        row["index"] = i  # Add custom index starting from 1
        data.append(row)'''

    if data:
        collection.delete_many({})  # This clears all existing data in the collection
        collection.insert_many(data)
        print("CSV data inserted successfully!")
    else:
        print("No data found in CSV.")
