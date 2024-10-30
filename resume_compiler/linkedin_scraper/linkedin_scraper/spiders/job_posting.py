import scrapy
from playwright.async_api import Page
from scrapy_playwright.page import PageMethod
from linkedin_scraper.linkedin_scraper.items import LinkedInPosting
from utils.helper_functions import get_job_id_from_url

class JobPostingSpider(scrapy.Spider):
    name = "job_posting"
    allowed_domains = ["www.linkedin.com"]

    def __init__(self, start_urls=[], *args, **kwargs):
        super(JobPostingSpider, self).__init__(*args, **kwargs)
        self.lot_ids = start_urls
        self.section_selectors = {
            'company': '.artdeco-entity-image',
            'role': '.top-card-layout__title',
            'description': '.description__text',
            'city': 'span.topcard__flavor:nth-child(2)'
        }
        
    async def init_page(self, page: Page, request):
        await page.route("**/*", lambda route, request: 
            route.abort() if request.resource_type in ["image", "media", "font"] else route.continue_())
        
        await page.context.add_init_script("""
            Object.defineProperty(Navigator.prototype, 'languages', { get: () => ['en-CA', 'en'] });
            Object.defineProperty(Navigator.prototype, 'language', { get: () => 'en-CA' });

            const timeZone = "America/Toronto";
            Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {
                value: new Proxy(Intl.DateTimeFormat.prototype.resolvedOptions, {
                    apply(target, thisArg, args) {
                        const options = Reflect.apply(target, thisArg, args);
                        options.timeZone = timeZone;
                        return options;
                    }
                })
            });

            Object.defineProperty(Navigator.prototype, "webdriver", {
                set: undefined,
                enumerable: true,
                configurable: true,
                get: () => false
            });
        """)

    def start_requests(self):
        for url in self.start_urls: 
            yield scrapy.Request(
                url=url,
                meta={
                    "playwright": True,
                    "playwright_page_init_callback": self.init_page,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", self.section_selectors['role']),
                    ],
                },
                callback=self.parse,
                errback=self.errback_close_page,
            )

    def parse(self, response,):
        self.logger.info(f"Parsing {response.url}")
        job_id = get_job_id_from_url(response.url)
        item = LinkedInPosting(job_id=job_id)

        for key, selector in self.section_selectors.items():
            element = response.css(selector)
            item[key] = self.extract_element(key, element)

        self.logger.debug(f"Parsed item: {item}")
        yield item
        
    async def errback_close_page(self, failure):
        page: Page = failure.request.meta["playwright_page"]
        self.logger.error(f"Request failed: {failure}", exc_info=True)
        await page.close()
