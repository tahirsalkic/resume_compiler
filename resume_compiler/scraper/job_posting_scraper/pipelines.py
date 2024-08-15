import logging
from scrapy.exceptions import DropItem
from database.db_helper_functions import get_client, load_mongodb_config

class MongoDBPipeline(object):

    def __init__(self):
        self.mongo_config = load_mongodb_config()
    
    def open_spider(self, spider):
        logging.info("Opening spider and setting up MongoDB client.")
        self.client = get_client()
        self.db = self.client[self.mongo_config['database']]
        self.collection = self.db['job_postings']
    
    def close_spider(self, spider):
        logging.info("Closing spider and shutting down MongoDB client.")
        self.client.close()

    def validate_item(self, item):
        mandatory_fields = ['job_id', 'company', 'role', 'description']

        for field in mandatory_fields:
            if not item.get(field):
                raise ValueError(f"Missing mandatory field: {field}")

        if len(item['description']) < 50:
            raise ValueError("Description is too short; must be at least 50 characters.")

        if len(item['role']) < 2:
            raise ValueError("Role name seems invalid; must be at least 2 characters.")

        return True
    
    def process_item(self, item, spider):
        try:
            self.validate_item(item)
            
            filter_criteria = {'job_id': item.get('job_id')}
            update_data = dict(item)
            update_data['general'] = False
            update_data['tailored'] = False
            update_operation = {'$set': update_data}
            
            logging.info(f"Upserting item into MongoDB for id: {item.get('job_id')}")
            self.collection.update_one(filter_criteria, update_operation, upsert=True)
        
        except Exception as e:
            logging.error(f"Error processing item: {e}")
            raise DropItem(f"Item failed validation: {e}")
        
        return item
