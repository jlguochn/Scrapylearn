import requests
from scrapy.selector import Selector
import MySQLdb

conn = MySQLdb.connect(host="127.0.0.1", user="root", passwd="Clown0018", db="article_spider", charset="utf8")
cursor = conn.cursor()

def crawl_ips():
    #爬取西刺的免费ip代理
    headers = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36"
    }

    for i in range(1000):
        re = requests.get(url = "http://www.xicidaili.com/nn/{0}".format(i),headers=headers)

        selector = Selector(text=re.text)
        all_trs = selector.css("#ip_list tr")


        ip_list = []
        for tr in all_trs[1:]:
            speed_str = tr.css(".bar::attr(title)").extract_first("")
            if speed_str:
                speed = float(speed_str.split("秒")[0])

            all_text = tr.css("td::text").extract()
            ip = all_text[0]
            port = all_text[1]
            proxy_type = all_text[5]
            ip_list.append((ip,port,proxy_type,speed))

        for ip_info in ip_list:
            cursor.execute(
                "insert proxy_ip(ip,port,speed,proxy_type) VALUES('{0}','{1}','{2}','{3}') ON DUPLICATE KEY UPDATE port=VALUES(port), speed=VALUES(speed), proxy_type=VALUES(proxy_type)".format(
                    ip_info[0], ip_info[1], ip_info[3], ip_info[2]
                )
            )
            conn.commit()

class GetIp(object):

    def delete_ip(self,ip):
        delete_sql = """
            delete from proxy_ip WHERE ip='{0}'
        """.format(ip)
        cursor.execute(delete_sql)
        conn.commit()
        return True

    def judge_ip(self,ip,port):
        #判断ip是否可用
        http_url = "http://www.jobbole.com/"
        proxy_url = "http://{0}:{1}".format(ip,port)
        try:
            proxy_dict = {
                "http":proxy_url
            }
            response = requests.get(http_url,proxies=proxy_dict)
        except Exception as e:
            print("invalid ip and port")
            self.delete_ip(ip)
            return False
        else:
            code = response.status_code
            if code>=200 and code<300:
                print("effective ip")
                return True
            else:
                print("invalid ip and port")
                self.delete_ip(ip)
                return False


    def get_random_ip(self):
        #从数据库中随机获取一个可用的url

        random_sql = """
        SELECT ip,port FROM proxy_ip
        ORDER BY RAND() LIMIT 1
        """
        result = cursor.execute(random_sql)
        for ip_info in cursor.fetchall():
            ip = ip_info[0]
            port = ip_info[1]

            judge_re = self.judge_ip(ip,port)
            if judge_re:
                return "http://{0}:{1}".format(ip,port)
            else:
                return self.get_random_ip()



if __name__ == '__main__':
    get_ip = GetIp()
    # # print(get_ip.get_random_ip())
    # print(get_ip.judge_ip("182.244.156.92","5616"))

    print(get_ip.get_random_ip())

