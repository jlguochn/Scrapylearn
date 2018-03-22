from datetime import datetime
from elasticsearch_dsl import DocType, Date, Nested, Boolean, \
    analyzer, Completion, Keyword, Text, Integer
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer

connections.create_connection(hosts=["127.0.0.1"])

class CustomAnalyer(_CustomAnalyzer):
    def get_analysis_definition(self):
        return {}

ik_analyzer = CustomAnalyer("ik_max_word",filter=["lowercase"])

class ArticleType(DocType):
    #伯乐在线文章类型
    suggest = Completion()
    title = Text(analyzer=ik_analyzer)
    create_date = Date()
    url = Keyword()
    url_object_id = Keyword()
    front_image_url = Keyword()
    front_image_path = Keyword()
    praise_nums = Integer()
    comment_nums = Integer()
    fav_nums = Integer()
    tags = Text(analyzer="ik_max_word")
    content = Text(analyzer="ik_max_word")

    class Meta:
        index = "jobbole"
        doc_type = "article"

class ZhiHuQuestionType(DocType):
    #知乎问题类型
    suggest = Completion()
    zhihu_id = Keyword()
    topics = Text(analyzer=ik_analyzer)
    url = Keyword()
    title = Text(analyzer=ik_analyzer)
    content = Text(analyzer=ik_analyzer)
    answer_num = Integer()
    comments_num = Integer()
    watch_user_num = Integer()
    click_num = Integer()
    crawl_time = Date()

    class Meta:
        index = "zhihu"
        doc_type = "question"

class ZhiHuAnswerType(DocType):
    #知乎答案类型
    suggest = Completion()
    zhihu_id = Keyword()
    url = Keyword()
    question_id = Integer()
    question_title = Text(analyzer=ik_analyzer)
    author_id = Keyword()
    content = Text(analyzer=ik_analyzer)
    praise_num = Integer()
    comments_num = Integer()
    create_time = Date()
    update_time = Date()
    crawl_time = Date()

    class Meta:
        index = "zhihu"
        doc_type = "answer"

if __name__ == '__main__':
    # ArticleType.init()
    ZhiHuQuestionType.init()
    ZhiHuAnswerType.init()