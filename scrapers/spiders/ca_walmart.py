import json
import scrapy
import re
from scrapers.items import ProductItem
import logging


class CaWalmartSpider(scrapy.Spider):
    name = 'ca_walmart'
    allowed_domains = ['walmart.ca']
    start_urls = ['https://www.walmart.ca/en/grocery/fruits-vegetables/fruits/N-3852']
    header = {
        'Host': 'www.walmart.ca',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/json',
        'Connection': 'keep-alive'
    }

    def parse(self, response):

        for url in response.css('.product-link::attr(href)').getall():
            yield response.follow(url, callback=self.parse_html, cb_kwargs={'url': url})

        next_page = response.css('#loadmore::attr(href)').get()

        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)

    def parse_html(self, response, url):
        pass
