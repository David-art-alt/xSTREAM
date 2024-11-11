from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import os
from selenium.common.exceptions import WebDriverException

website = "http://192.168.1.88/index.htm"
path = "C:\\webdriver\\chromedriver-win64\\chromedriver.exe"

service = Service(executable_path=path)
driver = webdriver.Chrome(service=service)

driver.get(website)

CO2_values = []
CO_values = []
CH4_values = []
H2_values = []
O2_values = []

desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "Gas_Values.xlsx")

try:
    driver.switch_to.frame("unten")

    while True:
        try:
            if not driver.current_url:
                print("Browser closed or website unavailable. Exiting loop.")
                break

            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//td[@id="btmline"]'))
            )
            raw_text = element.text.strip()
            print(f"Retrieved Data: '{raw_text}'")

            try:
                CO2 = float(raw_text.split("Ch1/R4:")[1].split("Vol%")[0].strip().replace(',', '.'))
                CO = float(raw_text.split("Ch2/R4:")[1].split("Vol%")[0].strip().replace(',', '.'))
                CH4 = float(raw_text.split("Ch3/R4:")[1].split("Vol%")[0].strip().replace(',', '.'))
                H2 = float(raw_text.split("Ch4/R4:")[1].split("Vol%")[0].strip().replace(',', '.'))
                O2 = float(raw_text.split("Ch5/R4:")[1].split("Vol%")[0].strip().replace(',', '.'))

                CO2_values.append(CO2)
                CO_values.append(CO)
                CH4_values.append(CH4)
                H2_values.append(H2)
                O2_values.append(O2)
            except (IndexError, ValueError) as e:
                print(f"Error parsing data: {e}")
                CO2_values.append(None)
                CO_values.append(None)
                CH4_values.append(None)
                H2_values.append(None)
                O2_values.append(None)

            time.sleep(2)

        except WebDriverException:
            print("Browser closed or lost connection. Exiting loop.")
            break

finally:
    max_length = max(len(CO2_values), len(CO_values), len(CH4_values), len(H2_values), len(O2_values))
    CO2_values.extend([None] * (max_length - len(CO2_values)))
    CO_values.extend([None] * (max_length - len(CO_values)))
    CH4_values.extend([None] * (max_length - len(CH4_values)))
    H2_values.extend([None] * (max_length - len(H2_values)))
    O2_values.extend([None] * (max_length - len(O2_values)))

    my_dict = {
        'CO2 (Vol%)': CO2_values,
        'CO (Vol%)': CO_values,
        'CH4 (Vol%)': CH4_values,
        'H2 (Vol%)': H2_values,
        'O2 (Vol%)': O2_values
    }
    df_GasValues = pd.DataFrame(my_dict)

    df_GasValues.to_excel(desktop_path, index=False)
    print(f"Data saved to {desktop_path}")

    driver.quit()

