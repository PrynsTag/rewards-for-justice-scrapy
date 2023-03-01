# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
import re
from datetime import datetime
from statistics import median

import scrapy
from scrapy.loader.processors import MapCompose, TakeFirst, Join
from w3lib.html import remove_tags


def get_date(date):
    regex = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{1,2},\s\d{4}|$"
    clean_date = re.compile(regex).findall(date)[0]
    if not clean_date:
        regex = r"\d{4}"
        clean_date = re.compile(regex).findall(date)
        if len(clean_date) > 1:
            clean_date = int(median(list(map(int, clean_date))))
        else:
            clean_date = clean_date[0]

        # use July 02 as a default date for dates that only have a year
        clean_date = "July 02, {}".format(clean_date)

    return datetime.strptime(clean_date, "%B %d, %Y").isoformat()


class CrimeItem(scrapy.Item):
    page_url = scrapy.Field()
    category = scrapy.Field()
    title = scrapy.Field(input_processor=MapCompose(remove_tags), output_processor=TakeFirst())
    reward_amount = scrapy.Field(input_processor=MapCompose(remove_tags), output_processor=TakeFirst())
    associated_organization = scrapy.Field(input_processor=MapCompose(remove_tags))
    associated_location = scrapy.Field(input_processor=MapCompose(remove_tags, str.strip))
    about = scrapy.Field(input_processor=MapCompose(remove_tags), output_processor=Join("\n"))
    image_url = scrapy.Field()
    date_of_birth = scrapy.Field(input_processor=MapCompose(remove_tags, get_date), output_processor=TakeFirst())
