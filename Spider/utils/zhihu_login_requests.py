import requests
try:
    import cookielib
except:
    import http.cookiejar as cookielib

try:
    from PIL import Image
except:
    pass

import re
import time
import os

session = requests.session()
session.cookies = cookielib.LWPCookieJar(filename="cookies.txt")
try:
    session.cookies.load(ignore_discard=True)
except:
    print("cookie未能加载")

agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36"
header = {
    "HOST" : "www.zhihu.com",
    "Referer" : "https://www.zhihu.com",
    "User-Agent" : agent
}

def get_xsrf():
    response = session.get("https://www.zhihu.com", headers = header)
    match_obj = re.match('.*name="_xsrf" value="(.*?)"',response.text)
    if match_obj:
        return (match_obj.group(1))
    else:
        return ""

def get_index():
    response = session.get("https://www.zhihu.com", headers = header)
    with open("index_page.html", "wb") as f:
        f.write(response.text.encode("utf-8"))
    print("OK")

# 获取验证码
def get_captcha():
    t = str(int(time.time() * 1000))
    captcha_url = 'https://www.zhihu.com/captcha.gif?r=' + t + "&type=login"
    r = session.get(captcha_url, headers=header)
    with open('captcha.jpg', 'wb') as f:
        f.write(r.content)
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
    return captcha


def zhihu_login(account, password):
    #知乎登录
    if re.match("^1\d{10}",account):
        print("手机号码登录")
        post_url = "https://www.zhihu.com/login/phone_num"
        post_data = {
            # "_xsrf" : get_xsrf(),
            "phone_num" : account,
            "password" : password
        }
    else:
        if "@" in account:
            #判断用户名是否为邮箱
            print("邮箱登录\n")
            post_url = "https://www.zhihu.com/login/email"
            post_data = {
                # "_xsrf" : get_xsrf(),
                "email": account,
                "password": password
            }
        else:
            print("输入账号格式有误，请检查")


    response_text = session.post(post_url,data=post_data,headers=header)
    login_code = response_text.json()
    if login_code['r'] == 1:
        # 不输入验证码登录失败
        # 使用需要输入验证码的方式登录
        post_data["captcha"] = get_captcha()
        response_text = session.post(post_url, data=post_data, headers=header)
        login_code = response_text.json()
        print(login_code['msg'])
    session.cookies.save()


def isLogin():
    # 通过查看用户个人信息来判断是否已经登录
    url = "https://www.zhihu.com/settings/profile"
    login_code = session.get(url, headers=header, allow_redirects=False).status_code
    if login_code == 200:
        return True
    else:
        return False


zhihu_login("用户名", "密码")

print(isLogin())

