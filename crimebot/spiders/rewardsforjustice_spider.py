from datetime import datetime

from scrapy.loader import ItemLoader

from crimebot.items import CrimeItem
from crimebot.spiders.crime_spider import CrimeSpider


class RewardsforJusticeSpider(CrimeSpider):
    name = "rewardsforjustice"
    allowed_domains = ["rewardsforjustice.net"]
    start_urls = [
        "https://rewardsforjustice.net/wp-admin/admin-ajax.php",
    ]
    payload = {
        "action": "jet_smart_filters",
        "provider": "jet-engine/rewards-grid",
        "query[_tax_query_crime-category][]": ["1070", "1071", "1072", "1073", "1074"],
        "paged": "1",
        "settings[lisitng_id]": "22078",
        "settings[posts_num]": "50",
        "settings[max_posts_num]": "50",
    }
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
        self.meta.update({
            "payload": self.payload
        })
        return super().start_requests()

    def initial_parse(self, response):
        json_response = response.json()
        parsed_response = self.HtmlResponse(url="", body=json_response['content'], encoding='utf-8')
        criminal_list = parsed_response.xpath("//div[@data-elementor-type='jet-listing-items']/parent::div")
        if criminal_list:
            curr_page = int(response.meta['payload']['paged'])
            curr_page += 1
            meta = response.meta
            meta['payload']['paged'] = str(curr_page)
            yield self.FormRequest(
                url=response.url,
                formdata=meta['payload'],
                callback=self.initial_parse,
                errback=self.error_handler,
                meta=meta,
                dont_filter=True
            )

            criminal_link = [x.xpath("./a/@href").get() for x in criminal_list]
            category_list = [x.xpath(
                ".//h2[text()='Kidnapping' or text()='Terrorism Financing' or text()='Acts of Terrorism' or text()='Terrorism - Individuals' or text()='Organizations']/text()").get()
                             for x in criminal_list]
            item_list = list(zip(criminal_link, category_list))
            for link, category in item_list:
                item_meta = response.meta
                item_meta['category'] = category
                yield self.ScrapyRequest(
                    url=link,
                    callback=self.parse_item,
                    errback=self.error_handler,
                    meta=item_meta,
                    dont_filter=True
                )

    def parse_item(self, response):
        loader = ItemLoader(item=CrimeItem(), response=response)
        loader.add_value('page_url', response.url)
        loader.add_value('category', response.meta['category'])
        loader.add_xpath('title', "//h2[@class='elementor-heading-title elementor-size-default']")
        loader.add_xpath('about', "//div[@data-widget_type='theme-post-content.default']/div/p")
        loader.add_xpath('reward_amount',
                         "//h4[contains(text(),'Reward')]/parent::div/parent::div/following-sibling::div[1]/div/h2")
        loader.add_xpath('associated_organization', "//p[contains(text(),'Associated Organization')]/a")
        loader.add_xpath('associated_location',
                         "//h2[contains(text(),'Associated Location')]/parent::div/parent::div/following-sibling::div[1]//span[@class='jet-listing-dynamic-terms__link']")
        loader.add_xpath('image_url', "//div[contains(@class,'terrorist-gallery')]//img/@src")
        loader.add_xpath('date_of_birth',
                         "//h2[contains(text(),'Date of Birth')]/parent::div/parent::div/following-sibling::div[1]/div")
        parsed_data = loader.load_item()

        self.logger.debug(f"Item Loader: {parsed_data}")

        yield parsed_data