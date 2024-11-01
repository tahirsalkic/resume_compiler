import logging
from re import sub
from datetime import datetime
from urllib.parse import urlparse
from shutil import copyfile, SameFileError, SpecialFileError
from PIL import ImageFont, ImageDraw, Image

logger = logging.getLogger(__name__)

def copy_file(src: str, dst: str, description: str) -> bool:
    """Copy a file from a source to a destination and log the outcome."""
    try:
        copyfile(src, dst)
        logger.info(f"{description} copied successfully from '{src}' to '{dst}'.")
        return True
    except SameFileError:
        logger.error(f"Source '{src}' and destination '{dst}' files are the same.")
    except FileNotFoundError:
        logger.error(f"Source file '{src}' not found.")
    except PermissionError:
        logger.error(f"Permission denied while copying '{description}' from '{src}' to '{dst}'.")
    except SpecialFileError:
        logger.error(f"Failed to copy special file '{src}'.")
    except IOError as e:
        logger.error(f"IO error occurred while copying '{description}' from '{src}' to '{dst}': {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while copying '{description}' from '{src}' to '{dst}': {e}")
    return False

def get_job_id_from_url(url: str) -> str:
    """Extracts the job ID from a given LinkedIn job URL."""
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.split('/')

    try:
        if 'jobs-guest' in path_parts:
            job_id = path_parts[path_parts.index('jobPosting') + 1]
        elif 'view' in path_parts:
            job_id = path_parts[path_parts.index('view') + 1]
        else:
            return None
        return job_id
    except (ValueError, IndexError):
        return None
    
def ids_to_urls(ids):
    """Returns a list of LinkedIn job URLs give a list of ids."""
    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/"
    return [f"{base_url}{id}" for id in ids]

def line_fit(text, line, font_name='arial', font_size=10):
    try:
        font = ImageFont.truetype(f"{font_name}.ttf", font_size)
    except IOError:
        logger.error(f"Font '{font_name}' not found.")
        return None

    dummy_image = Image.new('RGB', (1000, 1000), color='white')
    draw = ImageDraw.Draw(dummy_image)

    bbox = draw.textbbox((0, 0), text, font=font)
    bbox_meter = draw.textbbox((0, 0), line, font=font)
    width = bbox[2] - bbox[0]
    meter = bbox_meter[2] - bbox_meter[0]

    if width <= meter:
        return True
    
    return False

def get_user_confirmation(question: str):
    user_input = input(f"{question} (yes/no): ").strip().lower()
    while user_input not in ['yes', 'no']:
        user_input = input("Please answer with 'yes' or 'no': ").strip().lower()
    return user_input == 'yes'

def sanitize_filename(filename):
    return sub(r'[^a-zA-Z0-9 \-_\.]', '', filename)

def get_current_date():
    return datetime.now().strftime("%b-%Y")

def config_exists(config, *keys):
    current = config
    try:
        for key in keys:
            current = current[key]
        return True
    except KeyError:
        return False