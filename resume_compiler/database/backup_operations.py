import json
import logging
import os
from datetime import datetime
from pymongo import MongoClient
from database.db_helper_functions import get_client, load_mongodb_config

# Set up logging
logger = logging.getLogger(__name__)

def generate_collections_map(backup_dir: str) -> dict:
    """Generate map of required collections."""
    try:
        backup_path = get_most_recent_backup(backup_dir)
        return {
            "bullet_points": os.path.join(backup_path, 'bullet_points.json'),
            "job_postings": os.path.join(backup_path, 'job_postings.json')
        }
    except FileNotFoundError as e:
        logger.error(e)
        return {}

def db_exists(client: MongoClient, db_name: str) -> bool:
    """Check if a database exists in the MongoDB instance."""
    return db_name in client.list_database_names()

def collection_is_empty(db, collection_name: str) -> bool:
    """Check if a collection is empty or doesn't exist."""
    return not (collection_name in db.list_collection_names() and db[collection_name].count_documents({}) > 0)

def get_most_recent_backup(backup_dir: str) -> str:
    """Return the most recent backup based on the timestamp encoded in the directory name."""
    dirs = [d for d in os.listdir(backup_dir) if os.path.isdir(os.path.join(backup_dir, d))]
    if not dirs:
        raise FileNotFoundError(f"No backup directories found in {backup_dir}")

    sorted_dirs = sorted(dirs, key=lambda x: datetime.strptime('_'.join(x.split('_')[-5:]), '%Y_%m_%d_%H_%M'))
    return os.path.join(backup_dir, sorted_dirs[-1])

def import_collection_from_file(db, collection_name: str, file_path: str):
    """Helper function to import data from a JSON file into a specified collection."""
    try:
        with open(file_path, 'r') as file:
            for line in file:
                data = json.loads(line)
                data.pop('_id', None)
                if isinstance(data, list):
                    db[collection_name].insert_many(data)
                else:
                    db[collection_name].insert_one(data)
        logger.info(f"Imported {collection_name} data from {file_path}")
    except Exception as e:
        logger.error(f"Failed to import collection '{collection_name}' from file '{file_path}': {e}")
        raise

def import_backup(client: MongoClient, db_name: str, collections_map):
    """Import collections into the specified MongoDB database."""
    db = client[db_name]
    try:
        for collection_name, file_path in collections_map.items():
            if collection_is_empty(db, collection_name):
                import_collection_from_file(db, collection_name, file_path)
    except Exception as e:
        logger.error(f"Error importing backup: {e}")
        raise

def check_and_import():
    """Check if a database exists and is non-empty. If it doesn't exist or is empty, import a backup."""
    mongodb_config = load_mongodb_config()
    backup_dir = mongodb_config['backup_dir']
    db_name = mongodb_config['database']
    
    client = get_client()
    collections_map = generate_collections_map(backup_dir)
    
    try:
        if not db_exists(client, db_name):
            logger.info(f"Database '{db_name}' does not exist. Creating and importing backup.")
            import_backup(client, db_name, collections_map)
        else:
            db = client[db_name]
            required_collections = set(collections_map.keys())
            existing_collections = set(db.list_collection_names())

            missing_or_empty_collections = required_collections - existing_collections | {
                col for col in required_collections & existing_collections if collection_is_empty(db, col)}

            if missing_or_empty_collections:
                logger.info("Some collections are missing or empty. Importing backup.")
                import_backup(client, db_name, collections_map)
            else:
                logger.info("All required collections are present and non-empty. No action needed.")
    finally:
        client.close()
        logger.info("MongoDB connection closed.")
