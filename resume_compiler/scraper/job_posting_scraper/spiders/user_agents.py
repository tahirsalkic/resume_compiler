import scrapy
import re

class UserAgentsSpider(scrapy.Spider):
    name = "useragents"
    start_urls = [
        'https://www.useragents.me/#most-common-desktop-useragents',
    ]

    custom_settings = {
        'FEEDS': {
            'resume_compiler/utils/user_agents.json': {
                'format': 'json', 
                'overwrite': True,
            },
        },
        'ITEM_PIPELINES': {}  # Disable the item pipelines
    }

    def parse(self, response):
        user_agents = response.css('textarea.form-control::text').getall()
        ua_pattern = re.compile(r"Mozilla/\d+\.\d+ \([^)]*\) AppleWebKit/\d+\.\d+ \(KHTML, like Gecko\) \S+")

        for user_agent in user_agents:
            user_agent = user_agent.strip()
            if ua_pattern.match(user_agent):
                yield {
                    'user_agent': user_agent,
                }
