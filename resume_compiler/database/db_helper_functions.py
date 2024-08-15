import logging
from pymongo import MongoClient, errors
from config.settings import load_config

logger = logging.getLogger(__name__)

def load_mongodb_config() -> dict:
    """Load MongoDB configuration from settings."""
    try:
        logger.info("Loading configuration...")
        config = load_config()
        return {key: config['MONGODB'][key] for key in ('username', 'password', 'database', 'backup_dir')}
    except KeyError as e:
        logger.error(f"Missing configuration key: {e}")
        raise

def get_client() -> MongoClient:
    """Establish a connection to the MongoDB database."""
    try:
        config = load_mongodb_config()
        logger.info("Connecting to MongoDB...")
        client = MongoClient(
            host="db",
            port=27017,
            username=config['username'],
            password=config['password'],
            authSource="admin"
        )
        client.admin.command('ping')  # Verify the connection by pinging the server
        logger.info("MongoDB connection established.")
        return client
    except (errors.ConnectionFailure, errors.PyMongoError) as e:
        logger.error(f"MongoDB connection error: {e}")
        raise
