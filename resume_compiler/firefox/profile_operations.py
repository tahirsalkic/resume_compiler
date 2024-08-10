import logging
import os
from pathlib import Path
from sqlite3 import connect, Error

from config.logging_config import setup_logging
from config.settings import load_config
from utils.helper_functions import copy_file

# Setup logging
logger = logging.getLogger(__name__)

# Load and parse configuration
config = load_config()
folder_title = config.get('FIREFOX', 'folder_title')
firefox_profile_path = config.get('FIREFOX', 'firefox_profile_path')
local_firefox_path = config.get('FIREFOX', 'local_firefox_path')

def find_firefox_profile():
    """Find the Firefox profile directory."""
    logger.debug(f"Starting search in: {firefox_profile_path}")

    if not os.path.exists(firefox_profile_path):
        logger.error(f"The specified path does not exist: {firefox_profile_path}")
        return None

    try:
        for root, dirs, _ in os.walk(firefox_profile_path):
            logger.debug(f"Walking through: {root}")
            for dir_name in dirs:
                logger.debug(f"Checking directory: {dir_name}")
                if dir_name.endswith('.root'):
                    profile_path = Path(root) / dir_name
                    logger.info(f"Found Firefox profile: {profile_path}")
                    return profile_path
    except Exception as e:
        logger.exception("Error finding Firefox profile")
        return None

    logger.warning("Firefox profile not found.")
    return None

def setup_firefox():
    """Setup Firefox profile to have cookies and bookmarks from local Firefox."""
    firefox_profile = find_firefox_profile()
    if not firefox_profile:
        logger.error("Firefox profile not found.")
        return None

    # Define paths
    places_src = Path(local_firefox_path) / 'places.sqlite'
    cookies_src = Path(local_firefox_path) / 'cookies.sqlite'
    places_dest = firefox_profile / 'places.sqlite'
    cookies_dest = firefox_profile / 'cookies.sqlite'

    # Copy files, fail fast on any errors
    if not copy_file(places_src, places_dest, "Places file"):
        logger.error("Setup aborted due to failure in copying Places file.")
        return None

    if not copy_file(cookies_src, cookies_dest, "Cookies file"):
        logger.error("Setup aborted due to failure in copying Cookies file.")
        return None

    logger.info("Firefox profile setup completed successfully.")
    return firefox_profile

def get_folder_id(cursor):
    """Retrieve the ID of a folder given its title."""
    try:
        cursor.execute("SELECT id FROM moz_bookmarks WHERE title=? AND type=2", (folder_title,))
        result = cursor.fetchone()
        if result:
            logger.debug(f"Folder '{folder_title}' found with ID: {result[0]}")
            return result[0]
        else:
            logger.warning(f"Folder '{folder_title}' not found.")
    except Error as e:
        logger.error(f"An error occurred while getting folder ID: {e}")
    return None

def get_bookmarks():
    """Fetch all bookmark URLs from a specified folder."""
    profile_places = setup_firefox()
    if not profile_places:
        logger.error("No valid Firefox profile. Aborting bookmark retrieval.")
        return []

    try:
        with connect(profile_places / 'places.sqlite') as conn:
            cursor = conn.cursor()
            folder_id = get_folder_id(cursor)
            if not folder_id:
                return []

            query = """
            WITH RECURSIVE
            under_folder(id) AS (
              SELECT id FROM moz_bookmarks WHERE parent=?
              UNION ALL
              SELECT moz_bookmarks.id FROM moz_bookmarks JOIN under_folder ON moz_bookmarks.parent=under_folder.id
            )
            SELECT moz_places.url
            FROM moz_bookmarks
            JOIN moz_places ON moz_bookmarks.fk=moz_places.id
            WHERE moz_bookmarks.id IN under_folder;
            """
            cursor.execute(query, (folder_id,))
            bookmarks = [url[0] for url in cursor.fetchall()]
            
            if bookmarks:
                logger.info(f"Total bookmarks retrieved: {len(bookmarks)}")
            else:
                logger.warning("No bookmarks found.")
                
            return bookmarks if bookmarks else []
    except Error as e:
        logger.error(f"An error occurred while fetching bookmarks: {e}")
        return []

if __name__ == "__main__":
    bookmarks = get_bookmarks()
    if bookmarks:
        for bookmark in bookmarks:
            print(bookmark)
    else:
        print("No bookmarks found.")
