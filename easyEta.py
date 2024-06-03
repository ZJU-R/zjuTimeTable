from typing import Dict, Any
import requests
import re
import logging
import threading
from urllib.parse import quote
from utils.encrypt import eta_AES_encrypt, tc_rsa_encrypt
from time import time as tt

# 设置日志
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class etaOperator:
    username: str
    password: str
    name: str
    sess: requests.Session
    cookies: Dict[str, str]
    session_update_time: int

    def __init__(self, username: str = None, password: str = None, validate=True):
        password = password.strip()
        self.name = username
        self.username = username
        self.password = password
        self.session_update_time = 0
        self.lock = threading.Lock()
        if validate:
            self.get_session(username=username, password=password)


    def get(self, url: str, **kwargs) -> requests.Response:
        logging.debug(f"{self.name}({self.username}) GET url: {url}")
        last_update_time = self.session_update_time
        response = self.sess.get(url, **kwargs)
 
        if "href=/assets/css/chunk-03736c7b.3c916d04.css" in response.text or "浙大通行证" in response.text:
            logging.warning("session 失效, 重新获取")
            with self.lock:
                if self.session_update_time == last_update_time:
                    self.get_session(self.username, self.password)
                response = self.sess.get(url, **kwargs)
        return response

    def get_session(self, username: str = None, password: str = None):
        username = username or self.username
        password = password or self.password
        sess = requests.session()
        logging.info(f"username: {username} 正在获取 session")
        r = sess.get("http://zjuam.zju.edu.cn/cas/oauth2.0/authorize?response_type=code&client_id=RKC5F6GbNhA00enbNx&redirect_uri=http://course.zju.edu.cn/callback/")
        post_url = 'https://zjuam.zju.edu.cn/cas/login?service=http%3A%2F%2Fzjuam.zju.edu.cn%2Fcas%2Foauth2.0%2FcallbackAuthorize'
        execution = re.search('name="execution" value="(.*?)"', r.text).group(1)
        r = sess.get('https://zjuam.zju.edu.cn/cas/v2/getPubKey')
        modulus = r.json()['modulus']
        exponent = r.json()['exponent']
        encrypted_password = tc_rsa_encrypt(exponent, modulus, password)
        data = {
            'username': username,
            'password': encrypted_password,
            'authcode': '',
            'execution': execution,
            '_eventId': 'submit'
        }
        r = sess.post(post_url, data=data)
        if "密码错误" in r.text:
            logging.warning(f"username: {username} 密码错误")
            return None
        else:
            logging.info(f"username: {username} 登录成功")

        r = sess.get('http://eta.zju.edu.cn/')
        for i in range(3):
            sess.get("http://eta.zju.edu.cn/zftal-xgxt-web/teacher/xshx/getXnpjjd.zf?xh=cfU83Pe5nokCzxyA25LIQw%3D%3D")
        self.sess = sess
        self.session_update_time = int(tt())

    def get_course_arrangement(self, school_number: str, year_and_term: str = None):
        encoded_school_number = quote(eta_AES_encrypt(school_number))
        url = f"http://eta.zju.edu.cn/zftal-xgxt-web/student/xtgl/index/getTableKcb.zf?xnxq={year_and_term}&xh={encoded_school_number}"
        logging.info(f"username: {school_number} 获取课程表, url: {url}")
        return self.get(url).json()
    
    def get_name(self):
        url = f"http://eta.zju.edu.cn/zftal-xgxt-web/teacher/xtgl/index/getUserRoleInfo.zf"
        return self.get(url).json().get("data", {}).get("xm", None)

if __name__ == "__main__":
    pass
