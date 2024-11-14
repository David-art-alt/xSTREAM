import datetime
import pandas as pd
from collections import deque
from PyQt6.QtCore import QObject, pyqtSignal
from selenium import webdriver
from selenium.common import WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re

class DataFetcher(QObject):
    data_received = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.website = "http://192.168.1.88/index.htm"
        self.path = "C:\\webdriver\\chromedriver-win64\\chromedriver.exe"
        self.graph_data = {gas: deque(maxlen=100) for gas in ["CO2", "CO", "CH4", "H2", "O2"]}
        self.data_log = []
        self.driver = None

    def start_webdriver(self):
        service = Service(executable_path=self.path)
        self.driver = webdriver.Chrome(service=service)
        self.driver.get(self.website)
        try:
            self.driver.switch_to.frame("unten")
        except Exception as e:
            print(f"Fehler beim Wechsel zum Frame: {e}")

    def fetch_data(self):
        if self.driver is None:
            print("Webdriver nicht initialisiert.")
            return

        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//td[@id="btmline"]'))
            )
            raw_text = element.text.strip()
            print(f"Retrieved Data: '{raw_text}'")

            try:
                CO2 = float(raw_text.split("Ch1/R4:")[1].split("Vol%")[0].strip())
                CO = float(raw_text.split("Ch2/R4:")[1].split("Vol%")[0].strip())
                CH4 = float(raw_text.split("Ch3/R4:")[1].split("Vol%")[0].strip())
                H2 = float(raw_text.split("Ch4/R4:")[1].split("Vol%")[0].strip())
                O2 = float(raw_text.split("Ch5/R4:")[1].split("Vol%")[0].strip())
                data = {"CO2": CO2, "CO": CO, "CH4": CH4, "H2": H2, "O2": O2}
                print(data)

                self.data_log.append([datetime.now().strftime('%Y-%m-%d %H:%M:%S')] + list(data.values()))
                self.update_graph_data(data)
                self.data_received.emit(data)

            except (IndexError, ValueError) as e:
                print(f"Error parsing data: {e}")
                data = {"CO2": None, "CO": None, "CH4": None, "H2": None, "O2": None}
                self.data_log.append([datetime.now().strftime('%Y-%m-%d %H:%M:%S')] + list(data.values()))

        except WebDriverException:
            print("Browser closed or lost connection. Exiting fetch_data.")
            self.stop_webdriver()

    def update_graph_data(self, data):
        for gas, value in data.items():
            self.graph_data[gas].append(value if value is not None else 0)

    def save_data(self):
        file_path = f"xtreamdata_{datetime.now().strftime('%Y-%m-%d')}.csv"
        df = pd.DataFrame(self.data_log, columns=["Timestamp", "CO2", "CO", "CH4", "H2", "O2"])
        df.to_csv(file_path, index=False)

    def stop_webdriver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None