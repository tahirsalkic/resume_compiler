import logging
from shutil import copyfile, SameFileError, SpecialFileError
from config.logging_config import setup_logging

# Set up logging
logger = logging.getLogger(__name__)

def copy_file(src: str, dst: str, description: str) -> bool:
    """
    Copy a file from a source to a destination and log the outcome.

    Args:
        src (str): Source file path.
        dst (str): Destination file path.
        description (str): Description of the file being copied.

    Returns:
        bool: True if the file was copied successfully, False otherwise.
    """
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