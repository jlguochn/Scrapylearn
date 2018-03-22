import hashlib
import re

def get_md5(url):
    if isinstance(url,str):
        url = url.encode("utf-8")
    m = hashlib.md5()
    m.update(url)
    return m.hexdigest()

def extract_num(text):
    #提取字符串中的数字
    match_re = re.match('.*?(\d+)', text)
    if match_re:
        nums = int(match_re.group(0).strip())
    else:
        nums = 0

    return nums
