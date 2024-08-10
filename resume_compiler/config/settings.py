from configparser import ConfigParser


def load_config():
    """Load configuration from config.ini."""
    config = ConfigParser()
    config.read('config.ini')
    return config