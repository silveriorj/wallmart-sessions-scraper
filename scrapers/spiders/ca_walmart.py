import json
import re
import scrapy
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

    def parse(self, response, **kwargs):
        # Get URL's from product list links
        for url in response.css('.product-link::attr(href)').getall():
            yield response.follow(url, callback=self.parse_html, cb_kwargs={'url': url})

        # Get net page item from page-select-list
        next_page = response.css('#loadmore::attr(href)').get()

        # Navigating through the pages
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)

    def parse_html(self, response, url):
        item = ProductItem()

        # Getting JS information from body
        general_info_dict = json.loads(re.findall(r'({.*})', response.xpath("/html/body/script[1]/text()").get())[0])
        product_dict = json.loads(response.css('.evlleax2 > script:nth-child(1)::text').get())

        sku = product_dict['sku']
        description = product_dict['description']
        name = product_dict['name']
        brand = product_dict['brand']['name']
        image_url = product_dict['image']

        upc = general_info_dict['entities']['skus'][sku]['upc']
        category = general_info_dict['entities']['skus'][sku]['facets'][0]['value']

        package = general_info_dict['entities']['skus'][sku]['description']

        item['store'] = response.xpath('/html/head/meta[10]/@content').get()
        item['sku'] = sku
        item['barcodes'] = ', '.join(upc)
        item['brand'] = brand
        item['name'] = name
        item['category'] = category
        item['package'] = package
        item['url'] = self.start_urls[0] + url
        item['image_url'] = ', '.join(image_url)
        item['description'] = description.replace('<br>', '')

        # Setting up the requested branches Coordinates
        branches = {'3106': ['43.656422', '-79.435567'], '3124': ['48.412997', '-89.239717']}

        # API to search products by stores coordinates
        store_url = 'https://www.walmart.ca/api/product-page/find-in-store?' \
                    'latitude={}&longitude={}&lang=en&upc={}'

        for k in branches:
            yield scrapy.http.Request(store_url.format(branches[k][0], branches[k][1], upc[0]),
                                      callback=self.parse_api, cb_kwargs={'item': item},
                                      meta={'handle_httpstatus_all': True},
                                      dont_filter=False, headers=self.header)

    @staticmethod
    def parse_api(response, item):
        store_dict = json.loads(response.body)

        branch = store_dict['info'][0]['id']
        stock = store_dict['info'][0]['availableToSellQty']

        if 'sellPrice' not in store_dict['info'][0]:
            price = 0
        else:
            price = store_dict['info'][0]['sellPrice']

        item['branch'] = branch
        item['stock'] = stock
        item['price'] = price

        yield item
