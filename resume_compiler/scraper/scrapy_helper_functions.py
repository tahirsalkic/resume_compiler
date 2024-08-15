import logging
from scrapy.crawler import CrawlerRunner
from scrapy.settings import Settings
from twisted.internet import reactor, defer
from scraper.job_posting_scraper import settings as my_settings
from scraper.job_posting_scraper.spiders.linkedin import LinkedinSpider
from scraper.job_posting_scraper.spiders.user_agents import UserAgentsSpider
from utils.helper_functions import ids_to_urls


logger = logging.getLogger(__name__)

def run_job_scraper(ids: list):
    logger.info("Starting the user agent spider and then the LinkedIn scraper.")
    
    try:
        urls = ids_to_urls(ids)
        
        crawler_settings = Settings()
        crawler_settings.setmodule(my_settings)
        crawler_dict = dict(crawler_settings)
        runner = CrawlerRunner(settings=crawler_dict)

        @defer.inlineCallbacks
        def crawl():
            yield runner.crawl(UserAgentsSpider)
            yield runner.crawl(LinkedinSpider, start_urls=urls)
            reactor.stop()
            
        crawl()
        reactor.run()
        logger.info("User Agent Spider and LinkedIn scraper finished successfully.")
    except Exception as e:
        logger.error("An error occurred while running the spiders: %s", str(e))