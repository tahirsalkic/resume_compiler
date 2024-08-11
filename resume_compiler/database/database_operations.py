import logging
from pymongo import MongoClient
from pymongo.collection import Collection

from utils.mongodb_utils import get_client, load_mongodb_config
from utils.helper_functions import clean_bookmarks

logger = logging.getLogger(__name__)

def get_existing_bookmarks(collection: Collection, bookmarks_list: list[str]) -> set[str]:
    """Fetch existing bookmarks from the collection"""
    return set(
        doc['url'] for doc in collection.find({'url': {'$in': bookmarks_list}}, {'url': 1})
    )

def get_new_bookmarks(client: MongoClient, db_name: str, bookmarks_list: list) -> list:
    """Get bookmarks new to job_postings collection"""
    bookmarks_list = clean_bookmarks(bookmarks_list)
    collection = client[db_name]['job_postings']

    try:
        existing_bookmarks = get_existing_bookmarks(collection, bookmarks_list)
        new_bookmarks = [bookmark for bookmark in bookmarks_list if bookmark not in existing_bookmarks]

        logger.info(f"Found {len(new_bookmarks)} missing bookmarks.") if new_bookmarks else logger.info("All bookmarks are present in the collection.")
        return new_bookmarks
    except Exception as e:
        logger.error(f"An error occurred while checking bookmarks: {e}")
        return []

def insert_new_bookmarks(bookmarks_list: list) -> None:
    """Insert new bookmarks into job_postings collection"""
    client = get_client()
    config = load_mongodb_config()
    db_name = config['database']
    
    try:
        new_bookmarks = get_new_bookmarks(client, db_name, bookmarks_list)
        if new_bookmarks:
            bookmark_documents = [{'url': url} for url in new_bookmarks]
            result = client[db_name]['job_postings'].insert_many(bookmark_documents)
            logger.info(f"Inserted {len(result.inserted_ids)} bookmarks into the collection.")
        else:
            logger.info("No new bookmarks to insert.")
    except Exception as e:
        logger.error(f"An error occurred while inserting bookmarks: {e}")
    finally:
        client.close()
