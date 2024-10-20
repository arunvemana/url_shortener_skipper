import os

import requests
import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By

import time
import re
import random
from datetime import datetime
import json


class Parser:
    def __init__(self):
        # self.basic_url_reg = re.compile('(?<=\swindow.location.href = )[^\"]+',re.IGNORECASE)
        self.basic_url_reg = re.compile('"([^"]+)"', re.IGNORECASE)
        self.driver = self.set_property()

    @staticmethod
    def set_property():
        options = webdriver.ChromeOptions()
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('headless')
        options.add_argument('disable-infobars')
        options.add_argument('--disable-gpu')
        options.add_argument('--remote-debuggin-pipes')
        driver = webdriver.Chrome(options=options)
        return driver

    @staticmethod
    def general_wait():
        time.sleep(5)

    def quit(self):
        self.driver.quit()


class GpLinks(Parser):
    def __init__(self, url: str):
        super(GpLinks, self).__init__()
        self.url: str = url
        self.set_visit_url = 'https://gplinks.com/track/data.php'

    def set_visitor(self, status: str, impressions: str, visitor_id: str):
        _payload = {
            'request': "setVisitor",
            'status': status,
            'imps': impressions,
            'vid': visitor_id
        }
        headers = {
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'}
        response = requests.post(self.set_visit_url, data=_payload,headers=headers)
        print(response.status_code)

    def get_original_link(self,vid :str ,status:str) -> str:
        _payload = {
            'request':'setVisitor',
            'vid':vid,
            'status':status
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36' }
        requests.post(self.set_visit_url, data=_payload, headers=headers)


    def get_details(self):
        vid, pub_id, link_id = None, None, None
        try:
            vid = self.driver.get_cookie('vid')['value']
            pub_id = self.driver.get_cookie('pid')['value']
            link_id = self.driver.get_cookie('lid')['value']
        except selenium.common.exceptions.NoSuchCookieException as e:
            print("no cookie found :", e)
        except Exception as e:
            print("Cookie type changed")
        return vid, pub_id, link_id

    def process(self):
        self.driver.get(url=self.url)
        try:
            vid, pub_id, link_id = self.get_details()
            print(pub_id)
            if vid and pub_id and link_id:
                self.set_visitor(1, 2, visitor_id=vid)
                self.set_visitor(2, 4, visitor_id=vid)
                self.set_visitor(3, 6, visitor_id=vid)
                print(vid)
                self.get_original_link(vid,4)
                return  f"https://gplinks.co/{link_id}/?pid={pub_id}&vid={vid}"
        except Exception as e:
            print("glink issue", e)
        return "Faced issue! Please try again"


class PublicEarn(Parser):
    def __init__(self, url: str):
        super().__init__()
        self.url: str = url

    def initial(self):
        self.driver.get(self.url)
        html_source = self.driver.page_source
        # Find the script tag in the HTML source
        script_tag = '<script>'
        # Find the script tag in the HTML source
        script_start_index = html_source.find(script_tag)
        script_end_index = html_source.find('</script>', script_start_index)
        script = html_source[script_start_index + len(script_tag):script_end_index]
        try:
            self.driver.execute_script(script)
        except selenium.common.exceptions.JavascriptException as e:
            print(f"Scripted Failed ! retry once again for {self.url}:{e}")

    def get_verify(self) -> bool:
        try:
            self.general_wait()
            self.driver.execute_script('ajaxCallMaker("tp98");')
            self.general_wait()
            self.driver.execute_script('ajaxCallMaker("tp98");')
            self.general_wait()
            return True
        except selenium.common.exceptions.JavascriptException as e:
            print("Scripted Failed ! server was busy")
            return False

    @staticmethod
    def process_browser_logs_for_network_events(logs):
        for entry in logs:
            log = json.loads(entry["message"])["message"]
            if "Network.request" in log["method"]:
                yield log

    def store_logs(self) -> str:
        rand_int = random.randint(0, 99999)
        current_date = datetime.now().strftime("%Y%m%d")
        filename = f"network_{rand_int}{current_date}.json"
        raw_logs = self.driver.get_log("performance")
        events = self.process_browser_logs_for_network_events(raw_logs)
        path = os.path.join(os.getcwd(), 'url_shortener_skipper', 'network_traffic', filename)
        with open(path, "w") as f:
            json.dump(list(events), f, indent=4)
        return path

    def process(self):
        if "publicearn" in self.url.lower() and self.url.startswith('https'):
            self.initial()
            if self.get_verify():
                filename = self.store_logs()
                with open(filename, "r") as f:
                    events = json.load(f)
                for event in events:
                    if event['method'] == 'Network.requestWillBeSent':
                        if event['params']['request']['method'] == 'POST' and event['params']['request'][
                            'url'] == 'https://publicearn.com/link/verify.php':
                            data = event['params']['request']['postData']
                            pattern = r"id=(\d+)"
                            try:
                                id_value = re.findall(pattern, data)[0]
                            except IndexError as _:
                                continue
                            generate_output_url = f"{self.url}/?sid={id_value}"
                            self.quit()
                            return generate_output_url
            else:
                return "Please! try again,Server was busy"

        else:
            return "we wont support this website"
