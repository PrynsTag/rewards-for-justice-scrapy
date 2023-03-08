from datetime import datetime

from scrapy import FormRequest, Request, Spider
from scrapy.http import HtmlResponse
from scrapy.loader import ItemLoader
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TCPTimedOutError

from crimebot.items import CrimeItem


class RewardsforJusticeSpider(Spider):
    name = "rewardsforjustice"
    allowed_domains = ["rewardsforjustice.net"]
    start_urls = [
        "https://rewardsforjustice.net/index/" +
        "?jsf=jet-engine:rewards-grid&tax=crime-category:1070%2C1071%2C1073%2C1072%2C1074",
    ]
    output_filename = f"{name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    custom_settings = {"FEEDS": {
        f"{output_filename}.json": {
            "format": "json"
        },
        f"{output_filename}.xlsx": {
            "format": "xlsx"
        },
    }}

    def start_requests(self):
        meta = {
            "payload": {
                "action": "jet_engine_ajax",
                "handler": "get_listing",
                "page_settings[post_id]": "22076",
                "page_settings[queried_id]": "22076|WP_Post",
                "page_settings[element_id]": "ddd7ae9",
                "page_settings[page]": "1",
                "listing_type": "elementor",
                "isEditMode": "false",
                "addedPostCSS[]": "22078"
            },
            "spider_name": self.name,
        }

        for url in self.start_urls:
            yield FormRequest(
                url=url,
                formdata=meta["payload"],
                callback=self.parse,
                errback=self.error_handler,
                meta=meta,
            )

    def parse(self, response, **kwargs):
        json_response = response.json()
        html_response = HtmlResponse(url="", body=json_response["data"]["html"], encoding="utf-8")
        criminal_list = html_response.xpath("//div[@data-elementor-type='jet-listing-items']/parent::div")
        if criminal_list:
            curr_page = int(response.meta["payload"]["page_settings[page]"])
            curr_page += 1
            meta = response.meta
            meta["payload"]["page_settings[page]"] = str(curr_page)
            yield FormRequest(
                url=response.url,
                formdata=meta["payload"],
                callback=self.parse,
                errback=self.error_handler,
                meta=meta,
                dont_filter=True
            )

            criminal_list_link = [x.xpath("./a/@href").get() for x in criminal_list]
            category_list = [x.xpath(
                ".//h2[text()='Kidnapping' or text()='Terrorism Financing' or text()='Acts of Terrorism' or " +
                "text()='Terrorism - Individuals' or text()='Organizations']/text()").get() for x in criminal_list]
            item_list = list(zip(criminal_list_link, category_list))
            for link, category in item_list:
                item_meta = response.meta
                item_meta["category"] = category
                yield Request(
                    url=link,
                    callback=self.parse_item,
                    errback=self.error_handler,
                    meta=item_meta,
                    dont_filter=True
                )

    def parse_item(self, response):
        loader = ItemLoader(item=CrimeItem(), response=response)
        loader.add_value("page_url", response.url)
        loader.add_value("category", response.meta["category"])
        loader.add_xpath("title", "//h2[@class='elementor-heading-title elementor-size-default']")
        loader.add_xpath("about", "//div[@data-widget_type='theme-post-content.default']/div/p")
        loader.add_xpath("reward_amount",
                         "//h4[contains(text(),'Reward')]/parent::div/parent::div/following-sibling::div[1]/div/h2")
        loader.add_xpath("associated_organization", "//p[contains(text(),'Associated Organization')]/a")
        loader.add_xpath("associated_location",
                         "//h2[contains(text(),'Associated Location')]/parent::div/parent::div/" +
                         "following-sibling::div[1]//span[@class='jet-listing-dynamic-terms__link']")
        loader.add_xpath("image_url", "//div[contains(@class,'terrorist-gallery')]//img/@src")
        loader.add_xpath("date_of_birth",
                         "//h2[contains(text(),'Date of Birth')]/parent::div/parent::div/following-sibling::div[1]/div")
        parsed_data = loader.load_item()

        self.logger.debug(f"Item Loader: {parsed_data}")

        yield parsed_data

    def error_handler(self, failure):
        self.logger.error(repr(failure))
        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error("HttpError on %s", response.url)

        elif failure.check(DNSLookupError):
            request = failure.request
            self.logger.error("DNSLookupError on %s", request.url)

        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error("TimeoutError on %s", request.url)
