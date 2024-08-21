from datetime import datetime
import logging
from pymongo import MongoClient
from pymongo.collection import Collection

from database.db_helper_functions import get_client, load_mongodb_config
from utils.helper_functions import get_job_id_from_url

logger = logging.getLogger(__name__)

def get_existing_job_ids(collection: Collection, job_ids: list[str]) -> set[str]:
    """Fetch existing job IDs from the collection"""
    return set(
        doc['job_id'] for doc in collection.find({'job_id': {'$in': job_ids}}, {'job_id': 1})
    )

def fetch_new_job_ids(client: MongoClient, db_name: str, bookmark_urls: list) -> list:
    """Get new job IDs not present in the job_postings collection"""
    job_ids = [get_job_id_from_url(url) for url in bookmark_urls]
    job_postings_collection = client[db_name]['job_postings']

    try:
        existing_job_ids = get_existing_job_ids(job_postings_collection, job_ids)
        new_job_ids = [id for id in job_ids if id not in existing_job_ids]

        if new_job_ids:
            logger.info(f"Found {len(new_job_ids)} new job postings.")
        else:
            logger.info("All job postings are already present in the collection.")
        
        return new_job_ids
    except Exception as e:
        logger.error(f"An error occurred while checking job postings: {e}")
        return []

def collect_new_job_postings(bookmark_urls: list) -> list:
    """Insert new job postings into the job_postings collection"""
    client = get_client()
    config = load_mongodb_config()
    db_name = config['database']
    
    try:
        new_job_ids = fetch_new_job_ids(client, db_name, bookmark_urls)
        if new_job_ids:
            new_job_documents = [{'job_id': job_id} for job_id in new_job_ids]
            insertion_result = client[db_name]['job_postings'].insert_many(new_job_documents)
            logger.info(f"Inserted {len(insertion_result.inserted_ids)} job postings into the collection.")
        else:
            logger.info("No new job postings to insert.")
    except Exception as e:
        logger.error(f"An error occurred while inserting job postings: {e}")
    finally:
        client.close()

    return new_job_ids

def find_documents_missing_field(collection_name: str, key_name: str, field_name: str) -> list:
    """Find documents in the specified collection that lack a specified field."""
    client = get_client()
    config = load_mongodb_config()
    db_name = config['database']
    collection = client[db_name][collection_name]
    try:
        query_results = collection.find({field_name: {"$exists": False}}, {"_id": 0, key_name: 1})
        documents_missing_field = [doc[key_name] for doc in query_results]
        
        logger.info(f"Found {len(documents_missing_field)} documents without the {field_name} field.")
        return documents_missing_field
    except Exception as e:
        logger.error(f"An error occurred while finding documents without the {field_name} field: {e}")
        return []
    finally:
        client.close()
    
def propagate_skills_field_across_docs():
    """Propagate the skills field across documents with matching company and role, and return IDs of updated documents."""
    client = get_client()
    config = load_mongodb_config()
    db_name = config['database']
    collection = client[db_name]["job_postings"]
    
    try:
        aggregation_pipeline = [
            {
                "$group": {
                    "_id": {"company": "$company", "role": "$role"},
                    "documents": {"$push": "$$ROOT"},
                    "skills_count": {"$sum": {"$cond": [{"$ifNull": ["$skills", False]}, 1, 0]}}
                }
            },
            {"$match": {"skills_count": {"$gte": 1}}}
        ]
        
        aggregated_groups = list(collection.aggregate(aggregation_pipeline))
        
        for group in aggregated_groups:
            skills_to_propagate = None
            
            for document in group['documents']:
                if 'skills' in document:
                    skills_to_propagate = document['skills']
                    break
            
            if skills_to_propagate:
                for document in group['documents']:
                    if 'skills' not in document:
                        collection.update_one(
                            {"_id": document['_id']},
                            {"$set": {"skills": skills_to_propagate}}
                        )
        
        logger.info("Skills field successfully propagated across matching documents.")
    except Exception as e:
        logger.error(f"An error occurred while propagating the skills field: {e}")
    finally:
        client.close()

def get_documents(collection_name: str, criteria: dict, fields: list) -> list:
    """Query job_postings collection based on specific criteria."""
    client = get_client()
    config = load_mongodb_config()
    db_name = config['database']
    collection = client[db_name][collection_name]
    
    projection = {field: 1 for field in fields}
    results_cursor = collection.find(criteria, projection)
    
    job_listings = []
    for document in results_cursor:
        job_listings.append(document)
    
    client.close()
    
    return job_listings

def update_field(collection_name, search_field, search_value, update_field, new_value):
    """Update a field in a MongoDB document where a specified field matches a value."""
    client = get_client()
    try:
        config = load_mongodb_config()
        db_name = config['database']
        collection = client[db_name][collection_name]

        query = {search_field: search_value}
        update = {"$set": {update_field: new_value}}

        collection.update_one(query, update)

    finally:
        client.close()

def update_many_fields(collection_name, filter_field, filter, update_field, new_value, array_filters={}):
    """Update many fields in MongoDB where a specified field matches a value."""
    client = get_client()
    try:
        config = load_mongodb_config()
        db_name = config['database']
        collection = client[db_name][collection_name]

        query = {filter_field: filter}
        update = {"$set": {update_field: new_value}}

        collection.update_many(query, update, array_filters=array_filters)

    finally:
        client.close()

def insert_document(collection_name, document):
    """Inserts a document into a specific MongoDB collection."""
    client = get_client()
    config = load_mongodb_config()
    db_name = config['database']
    collection = client[db_name][collection_name]

    try:
        collection.insert_one(document)
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        client.close()

def insert_skill(skill: str):
    """Inserts a skill document into bullet_points collection if it doesn't exist."""
    client = get_client()
    config = load_mongodb_config()
    db_name = config['database']
    collection = client[db_name]['bullet_points']

    try:
        s = skill.lower()
        if collection.count_documents({'skill': s}) == 0:
            collection.insert_one({'skill': s})
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        client.close()

def update_skill_bullets(skill, verified_achievements):
    client = get_client()
    config = load_mongodb_config()
    db_name = config['database']
    collection = client[db_name]['bullet_points']

    document = collection.find_one({'skill': skill})
    if not document:
        raise ValueError('Document not found')

    bullets = document.get('bullets', [])
    current_time = datetime.now()

    new_bullets = [
        {
            'verb': verb,
            'bullet': bullet,
            'created_date': current_time,
            'resume_reference': current_time
        }
        for verb, bullet in verified_achievements.items()
    ]

    bullets.extend(new_bullets)
    collection.update_one({'skill': skill}, {'$set': {'bullets': bullets}})

def get_aggregated_data(collection_name, pipeline):
    client = get_client()
    config = load_mongodb_config()
    db_name = config['database']
    bullets_collection = client[db_name][collection_name]
    return bullets_collection.aggregate(pipeline)