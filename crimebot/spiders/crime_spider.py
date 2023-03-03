import json

import scrapy
from scrapy.http import HtmlResponse
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError


class CrimeSpider(scrapy.Spider):
    name = "DefaultSpiderName"
    allowed_domains = []
    start_urls = []
    meta = {}
    payload = {}

    json = json
    ScrapyRequest = scrapy.Request
    FormRequest = scrapy.FormRequest
    HtmlResponse = HtmlResponse

    def start_requests(self):
        self.meta.update({
            "spider_name": self.name,
        })
        for url in self.start_urls:
            yield self.FormRequest(
                url=url,
                formdata=self.payload,
                callback=self.initial_parse,
                errback=self.error_handler,
                meta=self.meta,
            )

    def error_handler(self, failure):
        self.logger.error(repr(failure))
        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)

        elif failure.check(DNSLookupError):
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)

        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)

    def initial_parse(self, response):
        pass
