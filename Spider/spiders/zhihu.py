# -*- coding: utf-8 -*-
import scrapy
import json
import time
import os
import re
import datetime
from urllib import parse
from scrapy.loader import ItemLoader
from Spider.items import ZhihuQuestionItem, ZhihuAnswerItem

try:
    from PIL import Image
except:
    pass

class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['https://www.zhihu.com/']

    #question的第一页answer的请求url
    start_answer_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?sort_by=default&include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit={1}&offset={2}"

    agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36"
    headers = {
    "HOST" : "www.zhihu.com",
    "Referer" : "https://www.zhihu.com",
    "User-Agent" : agent
    }

    custom_settings = {
        "COOKIES_ENABLED" : True
    }

    # 获取验证码url
    def get_captcha_url(self):
        t = str(int(time.time() * 1000))
        captcha_url = 'https://www.zhihu.com/captcha.gif?r=' + t + "&type=login"
        return captcha_url


    def parse(self, response):
        #提取出html页面中所有url 并跟踪这些URL进行进一步爬取
        #如果提取的URL中格式为/question/xxx 就下载之后直接进入解析函数

        all_urls = response.css("a::attr(href)").extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        # all_urls = filter(lambda x:True if x.startswith("https") else False, all_urls)
        for url in all_urls:
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|).*", url)
            if match_obj:
                #如果提取到question 相关的页面则下载后交由提取函数进行提取
                request_url = match_obj.group(1)
                # question_id = match_obj.group(2)

                yield scrapy.Request(request_url, headers=self.headers, callback=self.parse_question)
                break
            else:
                #如果不是question页面则直接进一步跟踪
                yield scrapy.Request(url, headers=self.headers, callback=self.parse)
                pass

    def parse_question(self, response):
        #处理question页面，从页面中提取出具体的question item
        match_obj = re.match("(.*zhihu.com/question/(\d+))", response.url)
        question_id = match_obj.group(2)

        item_loader = ItemLoader(item=ZhihuQuestionItem(),response=response)
        item_loader.add_css("title","h1.QuestionHeader-title::text")
        item_loader.add_css("content",".QuestionHeader-detail")
        item_loader.add_value("url",response.url)
        item_loader.add_value("zhihu_id",question_id)
        item_loader.add_css("answer_num",".List-headerText span::text")
        item_loader.add_css("comments_num",".QuestionHeader-Comment button::text")
        item_loader.add_css("watch_user_num",".NumberBoard-itemValue::text")
        item_loader.add_css("topics",".QuestionHeader-topics .Popover div::text")

        question_item = item_loader.load_item()

        yield scrapy.Request(self.start_answer_url.format(question_id, 20, 0), headers=self.headers, callback=self.parse_answer)
        yield question_item

    def parse_answer(self, reponse):
        #处理question的answer
        ans_json = json.loads(reponse.text)
        is_end = ans_json["paging"]["is_end"]
        # totals_answer = ans_json["paging"]["totals"]
        next_url = ans_json["paging"]["next"].replace("http:","https:")

        #提取answer的具体字段
        for answer in ans_json["data"]:
            answer_item = ZhihuAnswerItem()
            answer_item["zhihu_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["question_title"] = answer["question"]["title"]
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else None
            answer_item["praise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["crawl_time"] = datetime.datetime.now()

            yield answer_item


        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answer)

    def start_requests(self):
        return [scrapy.Request(self.get_captcha_url(),headers=self.headers,callback=self.login)]

    def login(self,response):
        with open('captcha.jpg', 'wb') as f:
            f.write(response.body)
            f.close()
        # 用pillow 的 Image 显示验证码
        # 如果没有安装 pillow 到源代码所在的目录去找到验证码然后手动输入
        try:
            im = Image.open('captcha.jpg')
            im.show()
            im.close()
        except:
            print(u'请到 %s 目录找到captcha.jpg 手动输入' % os.path.abspath('captcha.jpg'))
        captcha = input("please input the captcha\n>")

        post_url = "https://www.zhihu.com/login/phone_num"
        post_data = {
            "phone_num" : "用户名",
            "password" : "密码",
            "captcha"  :  captcha,
        }

        return [scrapy.FormRequest(
            url = post_url,
            formdata = post_data,
            headers = self.headers,
            callback = self.check_login
        )]

    def check_login(self, response):
        #验证服务器返回诗句判断是否成功
        text_json = json.loads(response.text)
        if "msg" in text_json and text_json["msg"] == "登录成功":
            print(text_json["msg"])
            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter=True, headers=self.headers)

