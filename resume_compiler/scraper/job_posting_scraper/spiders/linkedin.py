import json
import random
import scrapy
import time
from scraper.job_posting_scraper.items import LinkedInPosting
from utils.helper_functions import get_job_id_from_url
from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy import signals
from scrapy.utils.project import get_project_settings

class LinkedinSpider(scrapy.Spider):
    name = "linkedin"
    max_retries = 3
    custom_settings = {
        'HTTPERROR_ALLOWED_CODES': [400, 403, 404, 429],
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = kwargs.get('start_urls', [])
        self.user_agents = self.load_user_agents()
        self.section_selectors = {
            'company': '.artdeco-entity-image',
            'role': '.top-card-layout__title',
            'description': '.description__text'
        }

    def load_user_agents(self):
        settings = get_project_settings()
        user_agents_file = settings.get('USER_AGENTS_FILE', 'resume_compiler/utils/user_agents.json')
        with open(user_agents_file, 'r') as f:
            return json.load(f)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def start_requests(self):
        for url in self.start_urls:
            headers = self.generate_headers()
            yield scrapy.Request(url=url, callback=self.parse_content, errback=self.handle_error,
                                 headers=headers, meta={'retry_times': 0}, dont_filter=True)

    def generate_headers(self):
        user_agent = random.choice(self.user_agents)['user_agent']
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Host': 'www.linkedin.com',
            'Priority': 'u=0, i',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Sec-GPC': '1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': user_agent
        }
        return headers

    def parse_content(self, response):
        if response.status != 200:
            self.logger.warning(f"Non-200 response received: {response.status} from {response.url}")
            yield from self.retry_request(response)
            return
        
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
        current_retry = response.meta.get('retry_times', 0)
        if current_retry < self.max_retries:
            wait_time = random.uniform(1, 5)
            self.logger.warning(f"AuthWall encountered at {response.url}. Retrying {current_retry + 1}/{self.max_retries} after {wait_time:.2f} seconds...")
            time.sleep(wait_time)
            
            retryreq = response.request.copy()
            retryreq.meta['retry_times'] += 1
            retryreq.dont_filter = True
            
            new_headers = self.generate_headers()
            retryreq.headers.update(new_headers)
            
            yield retryreq
        else:
            self.logger.error(f"Exceeded retries for {response.url}. Skipping.")

    @staticmethod
    def extract_element(key, element):
        if key == 'company':
            return element.xpath('@alt').get('').strip()
        elif key == 'role':
            return element.xpath('text()').get('').strip()
        elif key == 'description':
            description_elements = element.xpath('.//text()[normalize-space()]').getall()
            return ' '.join([desc.strip() for desc in description_elements if desc.strip()])

    def handle_error(self, failure):
        request = failure.request
        if failure.check(HttpError) and failure.value.response.status == 429:
            self.logger.warning(f"429 Too Many Requests at {request.url}. Retrying...")
            wait_time = random.uniform(1, 5)
            time.sleep(wait_time)
            
            retryreq = get_retry_request(request, spider=self)
            if retryreq:
                retryreq.meta['retry_times'] += 1
                
                new_headers = self.generate_headers()
                retryreq.headers.update(new_headers)
                
                yield retryreq
            else:
                self.logger.error(f"Giving up on {request.url} after retries due to 429 status.")
        else:
            self.logger.error(f"Request failed with exception: {failure}")

    def spider_closed(self):
        self.logger.info("Closing spider.")
