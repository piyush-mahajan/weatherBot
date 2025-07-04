from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
client = None

def init_db():
    global client
    if client is None:
        client = MongoClient(MONGO_URI)
        # Test connection
        client.admin.command('ping')
        print("MongoDB connection established")

def get_db():
    if client is None:
        init_db()
    return client.get_database("weather_bot")