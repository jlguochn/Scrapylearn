# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
import datetime
import redis
import re
from scrapy.loader.processors import MapCompose, TakeFirst, Join
from scrapy.loader import ItemLoader
from Spider.utils.common import extract_num
from Spider.settings import SQL_DATETIME_FORMAT, SQL_DATE_FORMAT
from w3lib.html import remove_tags
from Spider.models.es_types import ArticleType, ZhiHuQuestionType, ZhiHuAnswerType
from elasticsearch_dsl.connections import connections

es = connections.create_connection(ArticleType._doc_type.using)
es2 = connections.create_connection(ZhiHuQuestionType._doc_type.using)
es3 = connections.create_connection(ZhiHuAnswerType._doc_type.using)
redis_cli = redis.StrictRedis(host="localhost")

class SpiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


def date_convert(value):
    try:
        create_date = datetime.datetime.strptime(value, "%Y/%m/%d").date()
    except Exception as e:
        create_date = datetime.datetime.now().date()

    return create_date

def get_nums(value):
    a = value
    match_re = re.match('.*?(\d+)', value)
    if match_re:
        nums = int(match_re.group(0).strip())
    else:
        nums = 0

    return nums

def remove_comment_tags(value):
    #去掉tag中提取的评论
    if "评论" in value:
        return ""
    else:
        return value

def return_value(value):
    return value

class ArticleItemLoader(ItemLoader):
    #自定义itemloader
    default_output_processor = TakeFirst()


def gen_suggests(index,info_tuple):
    #根据字符串生成搜索建议数组
    used_words = set()
    suggests = []
    for text,weight in info_tuple:
        if text:
            #调用es的analyze接口分析字符串
            words = es.indices.analyze(index=index, analyzer="ik_max_word", params={'filter':["lowercase"]},body=text)
            analyzed_words = set([r["token"] for r in words["tokens"] if len(r["token"])>1])
            new_words = analyzed_words - used_words
        else:
            new_words = set()

        if new_words:
            suggests.append({"input":list(new_words),"weight":weight})

    return suggests

def gen_suggests2(index,info_tuple):
    #根据字符串生成搜索建议数组
    used_words = set()
    suggests = []
    for text,weight in info_tuple:
        if text:
            #调用es的analyze接口分析字符串
            words = es2.indices.analyze(index=index, analyzer="ik_max_word", params={'filter':["lowercase"]},body=text)
            analyzed_words = set([r["token"] for r in words["tokens"] if len(r["token"])>1])
            new_words = analyzed_words - used_words
        else:
            new_words = set()

        if new_words:
            suggests.append({"input":list(new_words),"weight":weight})

    return suggests

def gen_suggests3(index,info_tuple):
    #根据字符串生成搜索建议数组
    used_words = set()
    suggests = []
    for text,weight in info_tuple:
        if text:
            #调用es的analyze接口分析字符串
            words = es3.indices.analyze(index=index, analyzer="ik_max_word", params={'filter':["lowercase"]},body=text)
            analyzed_words = set([r["token"] for r in words["tokens"] if len(r["token"])>1])
            new_words = analyzed_words - used_words
        else:
            new_words = set()

        if new_words:
            suggests.append({"input":list(new_words),"weight":weight})

    return suggests

class JobBoleArticleItem(scrapy.Item):
    title = scrapy.Field()
    create_date = scrapy.Field(
        input_processor = MapCompose(date_convert),
    )
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    front_image_url = scrapy.Field(
        output_processor = MapCompose(return_value)
    )
    front_image_path = scrapy.Field()
    praise_nums = scrapy.Field(
        input_processor = MapCompose(get_nums)
    )
    comment_nums = scrapy.Field(
        input_processor = MapCompose(get_nums)
    )
    fav_nums = scrapy.Field(
        input_processor = MapCompose(get_nums)
    )
    tags = scrapy.Field(
        input_processor = MapCompose(remove_comment_tags),
        output_processor = Join(",")

    )
    content = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
                   insert into jobbole_article(title, url, create_date, url_object_id, praise_nums, comment_nums, fav_nums,tags, content)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE praise_nums=VALUES(praise_nums), comment_nums=VALUES(comment_nums), fav_nums=VALUES(fav_nums)
               """

        params = (self["title"],self["url"],self["create_date"],self["url_object_id"],self["praise_nums"],self["comment_nums"],self["fav_nums"],self["tags"],self["content"])

        return insert_sql, params

    def save_to_es(self):
        article = ArticleType()
        article.title = self['title']
        article.create_date = self["create_date"]
        article.content = remove_tags(self["content"]).replace("\r","").replace("\n","").replace("\t","")
        article.front_image_url = self["front_image_url"][0]
        article.praise_nums = self["praise_nums"]
        article.fav_nums = self["fav_nums"]
        article.comment_nums = self["comment_nums"]
        article.url = self["url"]
        article.tags = self["tags"]
        article.meta.id = self["url_object_id"]

        article.suggest = gen_suggests(ArticleType._doc_type.index,((article.title,10),(article.tags,7)))

        article.save()
        redis_cli.incr("jobbole_count")

        return


class ZhihuQuestionItem(scrapy.Item):
    #知乎的问题 item
    zhihu_id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    answer_num = scrapy.Field()
    comments_num = scrapy.Field()
    watch_user_num = scrapy.Field()
    click_num = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        #插入知乎question表的sql语句
        insert_sql = """
            insert into zhihu_question(zhihu_id, topics, url, title, content, answer_num, comments_num, watch_user_num, click_num, crawl_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE content=VALUES(content), answer_num=VALUES(answer_num), comments_num=VALUES(comments_num), watch_user_num=VALUES(watch_user_num), 
            click_num=VALUES(click_num), crawl_time=VALUES(crawl_time)
        """

        zhihu_id = int(self["zhihu_id"][0])
        topics = ",".join(self["topics"])
        url = self["url"][0]
        title = "".join(self["title"])
        content = "".join(self["content"])
        try:
            answer_num = extract_num("".join(self["answer_num"]))
        except:
            answer_num = 0
        comments_num = extract_num("".join(self["comments_num"]))
        watch_user_num = extract_num(self["watch_user_num"][0].replace(",",""))
        click_num = extract_num(self["watch_user_num"][1].replace(",",""))
        crawl_time = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)

        params =(zhihu_id, topics, url, title, content, answer_num, comments_num,
            watch_user_num, click_num, crawl_time)

        return insert_sql, params

    def save_to_es(self):
        question = ZhiHuQuestionType()
        question.zhihu_id = int(self["zhihu_id"][0])
        question.topics = ",".join(self["topics"])
        question.url = self["url"][0]
        question.title = "".join(self["title"])
        question.content = "".join(self["content"])
        try:
            question.answer_num = extract_num("".join(self["answer_num"]))
        except:
            question.answer_num = 0
        question.comments_num = extract_num("".join(self["comments_num"]))
        question.watch_user_num = extract_num(self["watch_user_num"][0].replace(",",""))
        question.click_num = extract_num(self["watch_user_num"][1].replace(",",""))
        question.crawl_time = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)

        question.suggest = gen_suggests2(ZhiHuQuestionType._doc_type.index,((question.title,10),(question.content,7)))

        question.save()
        redis_cli.incr("zhihu_count")

        return

class ZhihuAnswerItem(scrapy.Item):
    #知乎的答案item
    zhihu_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    question_title = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    praise_num = scrapy.Field()
    comments_num = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        #插入知乎question表的sql语句
        insert_sql = """
            insert into zhihu_answer(zhihu_id, url, question_id, author_id, content, praise_num, comments_num, create_time, update_time, crawl_time
            )VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE content=VALUES(content), comments_num=VALUES(comments_num), 
            praise_num=VALUES(praise_num), update_time=VALUES(update_time), crawl_time=VALUES (crawl_time)
        """

        zhihu_id = self["zhihu_id"]
        url = self["url"]
        question_id = self["question_id"]
        author_id = self["author_id"]
        content = self["content"]
        praise_num = self["praise_num"]
        comments_num = self["comments_num"]
        create_time = datetime.datetime.fromtimestamp(self["create_time"]).strftime(SQL_DATETIME_FORMAT)
        update_time = datetime.datetime.fromtimestamp(self["update_time"]).strftime(SQL_DATETIME_FORMAT)
        crawl_time = self["crawl_time"].strftime(SQL_DATETIME_FORMAT)

        params = (
            zhihu_id, url, question_id, author_id, content, praise_num, comments_num, create_time, update_time, crawl_time
        )

        return insert_sql, params

    def save_to_es(self):
        answer = ZhiHuAnswerType()
        answer.zhihu_id = self["zhihu_id"]
        answer.url = self["url"].replace("http://www.zhihu.com/api/v4/answers","https://www.zhihu.com/question/{0}/answer".format(self["question_id"]))
        answer.question_id = self["question_id"]
        answer.question_title = self["question_title"]
        answer.author_id = self["author_id"]
        answer.content = self["content"]
        answer.praise_num = self["praise_num"]
        answer.comments_num = self["comments_num"]
        answer.create_time = datetime.datetime.fromtimestamp(self["create_time"]).strftime(SQL_DATETIME_FORMAT)
        answer.update_time = datetime.datetime.fromtimestamp(self["update_time"]).strftime(SQL_DATETIME_FORMAT)
        answer.crawl_time = self["crawl_time"].strftime(SQL_DATETIME_FORMAT)

        answer.suggest = gen_suggests3(ZhiHuQuestionType._doc_type.index,((answer.question_title,7),(answer.content,answer.praise_num)))

        answer.save()
        redis_cli.incr("zhihu_count")

        return



def remove_splash(value):
    return value.replace("/","")

def handle_jobaddr(value):
    addr_list = value.splist("\n")
    addr_list = [item.strip() for item in addr_list if item.strip()!="查看地图"]
    return "".join(addr_list)


class LagouJobItemLoader(ItemLoader):
    #自定义itemloader
    default_output_processor = TakeFirst()


class LagouJobItem(scrapy.Item):
    #拉勾网职位信息
    title = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    salary = scrapy.Field()
    job_city = scrapy.Field(
        input_processor = MapCompose(remove_splash),
    )
    work_years = scrapy.Field(
        input_processor = MapCompose(remove_splash),
    )
    degree_need = scrapy.Field(
        input_processor = MapCompose(remove_splash),
    )
    job_type = scrapy.Field()
    publish_time = scrapy.Field()
    job_advantage = scrapy.Field()
    job_desc = scrapy.Field()
    job_addr = scrapy.Field(
        input_processor=MapCompose(remove_tags, handle_jobaddr),
    )
    company_name = scrapy.Field()
    company_url = scrapy.Field()
    tags = scrapy.Field(
        input_processor = Join(",")
    )
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        inser_sql = """
            insert into lagou_job(title,url,url_object_id,salary,job_city,work_years,degree_need,
            job_type,publish_time,job_advantage,job_desc,job_addr,company_name,company_url
            tags,crawl_time) VALUES(%s，%s, %s, %s, %s，%s, %s, %s, %s，%s, %s, %s, %s，%s, %s, %s)
            ON DUPLICATE KEY UPDATE content=VALUES(salary), comments_num=VALUES(job_desc)
        """
        params = (
            self["title"],self["url"], self["url_object_id"],self["salary"],self["job_city"],self["work_years"],self["degree_need"],self["job_type"],self["publish_time"],
            self["job_advantage"], self["job_desc"], self["job_addr"], self["company_name"], self["company_url"], self["tags"], self["crawl_time"].strftime(SQL_DATETIME_FORMAT)
        )

        return inser_sql,params