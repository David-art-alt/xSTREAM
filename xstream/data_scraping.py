from PyQt6.QtCore import QObject, pyqtSignal
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import datetime
from collections import deque
import time


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
        # Startet den Webdriver mit Selenium
        service = Service(executable_path=self.path)
        self.driver = webdriver.Chrome(service=service)
        self.driver.get(self.website)

        # Wechsel zum Frame, falls erforderlich
        try:
            self.driver.switch_to.frame("unten")
        except Exception as e:
            print(f"Fehler beim Wechsel zum Frame: {e}")

    def fetch_data(self):
        if self.driver is None:
            print("Webdriver nicht initialisiert.")
            return

        try:
            # Daten extrahieren
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//td[@id="btmline"]'))
            )
            raw_text = element.text.strip()
            data = self.parse_data(raw_text)

            # Zeitstempel hinzufügen und in den Log speichern
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.data_log.append((timestamp, data))
            self.update_graph_data(data)

            # Signal für Anzeige im GUI
            self.data_received.emit(data)

            # Speichern der Daten
            self.save_data()

        except Exception as e:
            print(f"Fehler beim Abrufen der Daten: {e}")

    def parse_data(self, text):
        # Beispielhafte Datenextraktion
        data = {}
        for gas in ["CO2", "CO", "CH4", "H2", "O2"]:
            try:
                # Extrahiert die Werte für jeden Gasparameter aus dem Text
                data[gas] = int(text.split(f'{gas}">')[1].split("</")[0])
            except (IndexError, ValueError):
                data[gas] = 0  # Fallback-Wert, falls die Extraktion fehlschlägt
        return data

    def update_graph_data(self, data):
        for gas, value in data.items():
            self.graph_data[gas].append(value)

    def save_data(self):
        # Speichert die Daten in einer CSV-Datei
        file_path = f"xtreamdata_{datetime.datetime.now().strftime('%Y-%m-%d')}.csv"
        df = pd.DataFrame(self.data_log, columns=["Timestamp", "CO2", "CO", "CH4", "H2", "O2"])
        df.to_csv(file_path, index=False)

    def stop_webdriver(self):
        # Beendet den Webdriver
        if self.driver:
            self.driver.quit()