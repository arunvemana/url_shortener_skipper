import os

from selenium import webdriver

import time
import re
import random
from datetime import datetime
import json





class Parser:
    def __init__(self):
        # self.basic_url_reg = re.compile('(?<=\swindow.location.href = )[^\"]+',re.IGNORECASE)
        self.basic_url_reg = re.compile('"([^"]+)"',re.IGNORECASE)
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

class PublicEarn(Parser):
    def __init__(self,url:str):
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
        self.driver.execute_script(script)

    def get_verify(self):
        self.general_wait()
        self.driver.execute_script('ajaxCallMaker("tp98");')
        self.general_wait()
        self.driver.execute_script('ajaxCallMaker("tp98");')
        self.general_wait()

    @staticmethod
    def process_browser_logs_for_network_events(logs):
        for entry in logs:
            log = json.loads(entry["message"])["message"]
            if "Network.request" in log["method"]:
                yield log

    def store_logs(self) -> str:
        rand_int = random.randint(0,99999)
        current_date = datetime.now().strftime("%Y%m%d")
        filename = f"network_{rand_int}{current_date}.json"
        raw_logs = self.driver.get_log("performance")
        events = self.process_browser_logs_for_network_events(raw_logs)
        path = os.path.join(os.getcwd(),'url_shortener_skipper','network_traffic',filename)
        with open(path,"w") as f:
            json.dump(list(events), f, indent=4)
        return path

    def process(self):
        if "publicearn" in self.url.lower() and self.url.startswith('https'):
            self.initial()
            self.get_verify()
            filename = self.store_logs()
            with open(filename, "r") as f:
                events = json.load(f)
            for event in events:
                if event['method'] == 'Network.requestWillBeSent':
                    if event['params']['request']['method'] == 'POST' and event['params']['request']['url'] == 'https://publicearn.com/link/verify.php':
                        data = event['params']['request']['postData']
                        pattern = r"id=(\d+)"
                        try:
                            id_value = re.findall(pattern, data)[0]
                        except IndexError as _:
                            continue
                        print(id_value)  # Output: 872001
                        generate_output_url = f"{self.url}/?sid={id_value}"
                        print(generate_output_url)
                        self.quit()
                        return generate_output_url
        else:
            return "we wont support this website"
