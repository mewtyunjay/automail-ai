import os
import logging
from dotenv import load_dotenv
import psycopg2
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv(override=True)

# PostgreSQL Connection
def get_postgres_connection():
    """Create and return a PostgreSQL connection using the Supabase session pooler."""
    try:
        conn_str = os.getenv("SUPABASE_POOLER_URI")
        connection = psycopg2.connect(conn_str)
        logger.info("Supabase session pooler PostgreSQL connection successful!")
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL (pooler): {e}")
        return None

# MongoDB Connection
def get_mongodb_client():
    """Create and return a MongoDB client."""
    try:
        # MongoDB connection URI
        uri = "mongodb+srv://mabhijeet11:hN13RpAGFtkmpQXV@automail.kdwlo53.mongodb.net/?retryWrites=true&w=majority&appName=automail"
        
        # Create a new client and connect to the server
        client = MongoClient(uri, server_api=ServerApi('1'))
        
        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        logger.info("MongoDB connection successful! Connected to MongoDB Atlas.")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return None

# Example function to get a MongoDB collection
def get_mongodb_collection(collection_name, database_name="automail"):
    """Get a MongoDB collection from the specified database."""
    client = get_mongodb_client()
    if client:
        db = client[database_name]
        return db[collection_name]
    return None

# Example function to execute a PostgreSQL query
def execute_postgres_query(query, params=None, fetch=True):
    """Execute a PostgreSQL query and return results if fetch is True."""
    connection = get_postgres_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        cursor.execute(query, params or ())
        
        result = None
        if fetch:
            result = cursor.fetchall()
        else:
            connection.commit()
        
        cursor.close()
        connection.close()
        logger.info("PostgreSQL query executed successfully.")
        return result
    except Exception as e:
        logger.error(f"Error executing PostgreSQL query: {e}")
        if connection:
            connection.close()
        return None
