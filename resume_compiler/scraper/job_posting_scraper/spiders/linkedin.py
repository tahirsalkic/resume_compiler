import json
import random
import scrapy
from scrapy import signals
from scrapy.downloadermiddlewares.retry import get_retry_request
from scraper.job_posting_scraper.items import LinkedInPosting
from utils.helper_functions import get_job_id_from_url


class LinkedinSpider(scrapy.Spider):
    name = "linkedin"
    max_retries = 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = kwargs.get('start_urls', [])

        self.user_agents = self.load_user_agents()

        self.section_selectors = {
            'company': '.artdeco-entity-image',
            'role': '.top-card-layout__title',
            'description': '.description__text'
        }

    @staticmethod
    def load_user_agents():
        with open('resume_compiler/utils/user_agents.json', 'r') as f:
            return json.load(f)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def start_requests(self):
        for url in self.start_urls:
            headers = {'User-Agent': random.choice(self.user_agents)['user_agent']}
            yield scrapy.Request(url=url, callback=self.parse_content, errback=self.handle_error,
                                 headers=headers)

    def parse_content(self, response):
        if self.is_authwall(response):
            yield from self.retry_request(response)
        else:
            self.logger.info(f"Parsing {response.url}")
            job_id = get_job_id_from_url(response.url)
            item = LinkedInPosting(job_id=job_id)

            for key, selector in self.section_selectors.items():
                element = response.css(selector)
                item[key] = self.extract_element(key, element)

            self.logger.debug(f"Parsed item: {item}")
            yield item

    def is_authwall(self, response):
        return any(substring in response.url for substring in ["authwall", "login"]) or \
               response.url == 'https://www.linkedin.com/'

    def retry_request(self, response):
        current_retry = response.meta['retry_times']
        if current_retry < self.max_retries:
            self.logger.warning(f"AuthWall encountered at {response.url}. Retrying {current_retry + 1}/{self.max_retries}...")
            retryreq = response.request.copy()
            retryreq.meta['retry_times'] += 1
            retryreq.dont_filter = True
            yield retryreq
        else:
            self.logger.error(f"Exceeded retries for {response.url}. Skipping.")

    @staticmethod
    def extract_element(key, element):
        if key == 'company':
            return element.css('*::attr(alt)').get(default='').strip()
        elif key == 'role':
            return element.css('*::text').get(default='').strip()
        elif key == 'description':
            description_elements = element.css('*::text').getall()
            return ' '.join([desc.strip() for desc in description_elements if desc.strip()])

    def handle_error(self, failure):
        request = failure.request
        if failure.value.response.status == 429:
            self.logger.warning(f"429 Too Many Requests at {request.url}. Retrying...")
            retryreq = get_retry_request(request, spider=self)
            if retryreq:
                yield retryreq
            else:
                self.logger.error(f"Giving up on {request.url} after retries due to 429 status.")

    def spider_closed(self):
        self.logger.info("Closing spider.")
