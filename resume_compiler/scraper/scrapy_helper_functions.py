import logging
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from scraper.job_posting_scraper import settings as my_settings
from scraper.job_posting_scraper.spiders.linkedin import LinkedinSpider
from utils.helper_functions import ids_to_urls
from scrapy.utils.log import configure_logging

logger = logging.getLogger(__name__)

def run_job_scraper(ids: list):
    logger.info("Starting the LinkedIn scraper.")
    
    try:
        urls = ids_to_urls(ids)
        
        configure_logging({"LOG_FORMAT": "%(levelname)s: %(message)s"})
        crawler_settings = Settings()
        crawler_settings.setmodule(my_settings)
        process = CrawlerProcess(settings=crawler_settings)

        process.crawl(LinkedinSpider, start_urls = urls)
        process.start()
        logger.info("LinkedIn scraper finished successfully.")
    except Exception as e:
        logger.error("An error occurred while running the scraper: %s", str(e))
