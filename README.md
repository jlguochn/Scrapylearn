# Scrapy Learn
###### 学习使用Scrapy框架，爬取知乎网问答信息，伯乐在线文章信息，拉勾网职位信息。  
实现了:  
1. 知乎网的模拟登陆，以及验证码提交。
2. 将爬取到的数据写入文件/mysql/elasticsearch中。
3. 添加DOWNLOADER_MIDDLEWARES每次Request请求自动更换User-Agent以及ip代理。