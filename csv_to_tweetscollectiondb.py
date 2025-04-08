import csv
import pymongo
import os

client=pymongo.MongoClient("your connection string here from mongoDB")
db = client["HappyMaps"]
collection = db["tweets"]  # You can change this to whatever you want

# Read CSV and insert into MongoDB
csv_path = os.path.join(os.path.dirname(__file__), "data.csv") #filename as per convinience
with open(csv_path, newline='', encoding='utf-8') as csvfile:
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
