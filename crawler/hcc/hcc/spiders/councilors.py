# -*- coding: utf-8 -*-
import re
import urllib
from urlparse import urljoin
import scrapy
from scrapy.http import Request, FormRequest
from scrapy.selector import Selector
from hcc.items import Councilor
from crawler_lib import parse
from crawler_lib import misc
import logging

_key_map = {
    u'黨籍': 'party',
    u'經歷': 'experience',
    u'政見': 'platform',
    u'選舉區別': 'district',
    u'個人網站': 'link',
    u'E-mail': 'email',
    u'電話': 'voice',
    u'住址': 'address',
}


class Spider(scrapy.Spider):
    name = "councilors"
    base_url = "http://www.hcc.gov.tw/03councilor/councilor.asp"
    allowed_domains = ["www.hcc.gov.tw"]
    start_urls = ["http://www.hcc.gov.tw/03councilor/councilor.asp"]
    download_delay = 0.5

    def parse(self, response):
        response = parse.get_decoded_response(response, 'Big5')
        sel = Selector(response)
        areas = sel.xpath(u'//div[@class="testdiv"]')
        base_url = self.base_url

        for area in areas:
            urls = area.xpath('.//a/@href').extract()
            urls = area.xpath('.//a')
            for url in urls:
                href = url.xpath('@href').extract()[0]
                if not re.search('^view.asp\?id=', href):
                    continue
                item = Councilor()
                item['constituency'] = url.xpath('preceding::strong[1]/text()').re(u'第(\d+)選區')[0]
                logging.warning('url: %s', href)
                the_url = urljoin(base_url, href)
                yield Request(the_url, callback=self.parse_profile, meta={'item': item})

    def parse_profile(self, response):
        response = parse.get_decoded_response(response, 'Big5')
        sel = Selector(response)
        name_node = sel.xpath('//td[@class="w06"]')
        logging.warning('name_node: %s', name_node)
        name_str = parse.get_inner_text(name_node)

        logging.warning('name_str: %s', name_str)

        item = response.request.meta['item']
        item['county'] = u'新竹縣'
        item['election_year'] = '2009'
        item['term_start'] = '%s-12-25' % item['election_year']
        item['term_end'] = {'date': '2014-12-25'}
        item['in_office'] = True
        item['name'] = name_str.split('-')[-1]
        item['title'] = re.search(u'(副?議長|議員)', name_str).group()

        w02_nodes = sel.xpath('//th[@class="w02"]')
        for each_node in w02_nodes:
            key = parse.get_inner_text(each_node).strip()
            logging.warning('w02_node: key: %s', key)
            if key != u'學歷':
                continue
            education_node = each_node.xpath('../td')
            education_str = parse.get_inner_text(education_node)
            logging.warning('key: %s education_str: %s', key, education_str)
            item['education'] = education_str.split('\n')

            image_node = each_node.xpath('../../../../td[2]/img/@src')
            image_str = parse.get_extracted(image_node)

            logging.warning('key: %s education_str: %s image_str: %s', key, education_str, image_str)
            item['image'] = urljoin(response.url, urllib.quote(image_str.encode('utf8')))

        main_nodes = sel.xpath('//tr[@class="line_02"]')

        contact_details = []
        links = [{'url': response.url, 'note': u'議會個人官網'}]
        for each_node in main_nodes:
            key = parse.get_inner_text(each_node.xpath('./th'))
            item_key = _key_map.get(key, '')

            if item_key == 'experience':
                val_nodes = each_node.xpath('./td/ol/li')
                if val_nodes:
                    val = [re.sub(ur' ', '', re.sub(ur'。', '', parse.get_inner_text(each_each_node))) for each_each_node in val_nodes]
                else:
                    val = parse.get_inner_text(each_node.xpath('./td')).split("\n")
                    val = [re.sub(ur' ', '', each_val) for each_val in val]
            elif item_key == 'platform':
                val_nodes = each_node.xpath('./td/ol/li')
                val = [re.sub(ur' ', '', parse.get_inner_text(each_each_node)) for each_each_node in val_nodes]
            else:
                val = parse.get_inner_text(each_node.xpath('./td'))

            if key not in _key_map:
                logging.error('key not in _key_map!: key: %s', key)
                continue

            if item_key in ['email', 'address', 'voice']:
                contact_details.append({"type": item_key, "value": val, "label": key})
            elif item_key in ['link']:
                val = re.sub(ur'^\.\.', 'http://www.hcc.gov.tw', val)
                links.append({"url": val, "note": key})
            else:
                item[item_key] = val

            logging.warning('key: %s val: %s item_key: %s', key, val, item_key)

            # item[item_key] = val
        item['contact_details'] = contact_details
        item['links'] = links

        return item
