import scrapy

class LinkedInPosting(scrapy.Item):
    job_id = scrapy.Field()
    company = scrapy.Field()
    role = scrapy.Field()
    description = scrapy.Field()
    city = scrapy.Field()