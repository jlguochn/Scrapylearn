# -*- coding: utf-8 -*-
import scrapy
import re
import datetime
from scrapy import Request
from urllib import parse
from Spider.items import JobBoleArticleItem, ArticleItemLoader
from Spider.utils.common import get_md5

class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    def parse(self, response):
        #获取文章列表中的文章url并交给scrapy下载后并进行解析
        #获取下一页的url并交给scrapy进行下载，下载完成后交给parse

        #解析列表文章中的所有url
        post_nodes = response.css("#archive .floated-thumb .post-thumb a")
        for post_node in post_nodes:
            image_url = post_node.css("img::attr(src)").extract_first("")
            post_url = post_node.css("::attr(href)").extract_first("")
            yield Request(url=parse.urljoin(response.url,post_url),meta={"front_image_url":image_url},callback=self.detail)
        #提取下一页并交给scrapy进行下载
        next_url = response.css(".next.page-numbers::attr(href)").extract_first();
        if next_url:
            yield Request(url=parse.urljoin(response.url,next_url),callback=self.parse)

    def detail(self,response):
        # article_item = JobBoleArticleItem()

        front_image_url = response.meta.get("front_image_url","")#文章封面图
        # title = response.xpath('//*[@class="entry-header"]/h1/text()').extract_first()
        # create_date = response.xpath('//p[@class="entry-meta-hide-on-mobile"]/text()').extract_first().replace('·','').strip()
        # praise_nums = int(response.xpath('//span[contains(@class,"vote-post-up")]/h10/text()').extract_first())
        # fav_nums = response.xpath('//span[contains(@class,"bookmark-btn")]/text()').extract_first()
        # match_re = re.match('.*?(\d+)',fav_nums)
        # if match_re:
        #     fav_nums = int(match_re.group(0).strip())
        # else:
        #     fav_nums = 0
        # comment_num = response.xpath('//a[@href="#article-comment"]/span/text()').extract_first()
        # match_re = re.match('.*?(\d+)',comment_num)
        # if match_re:
        #     comment_nums = int(match_re.group(0).strip())
        # else:
        #     comment_nums = 0
        # content = response.xpath('//div[@class="entry"]').extract_first()
        #
        # tag_list = response.xpath('//p[@class="entry-meta-hide-on-mobile"]/a/text()').extract()
        # tag_list = [element for element in tag_list if not element.strip().endswith("评论")]
        # tags = ",".join(tag_list)
        #
        # article_item["title"] = title
        # article_item["url"] = response.url
        # article_item["url_object_id"] = get_md5(response.url)
        # try:
        #     create_date = datetime.datetime.strptime(create_date, "%Y/%m/%d").date()
        # except Exception as e:
        #     create_date = datetime.datetime.now().date()
        # article_item["create_date"] = create_date
        # article_item["front_image_url"] = [front_image_url]
        # article_item["praise_nums"] = praise_nums
        # article_item["comment_nums"] = comment_nums
        # article_item["fav_nums"] = fav_nums
        # article_item["tags"] = tags
        # article_item["content"] = content

        #通过item_loader加载item
        item_loader = ArticleItemLoader(item=JobBoleArticleItem(),response=response)
        item_loader.add_xpath("title",'//*[@class="entry-header"]/h1/text()')
        item_loader.add_value("url",response.url)
        item_loader.add_value("url_object_id",get_md5(response.url))
        item_loader.add_xpath("create_date", '//p[@class="entry-meta-hide-on-mobile"]/text()')
        item_loader.add_value("front_image_url",[front_image_url])
        item_loader.add_xpath("praise_nums", '//span[contains(@class,"vote-post-up")]/h10/text()')
        item_loader.add_xpath("comment_nums",'//a[@href="#article-comment"]/span/text()')
        item_loader.add_xpath("fav_nums", '//span[contains(@class,"bookmark-btn")]/text()')
        item_loader.add_xpath("tags",'//p[@class="entry-meta-hide-on-mobile"]/a/text()')
        item_loader.add_xpath("content",'//div[@class="entry"]')

        article_item = item_loader.load_item()

        try:
            article_item["praise_nums"]
        except:
            article_item["praise_nums"] = 0

        try:
            article_item["comment_nums"]
        except:
            article_item["comment_nums"] = 0

        try:
            article_item["fav_nums"]
        except:
            article_item["fav_nums"] = 0

        yield article_item

        pass
