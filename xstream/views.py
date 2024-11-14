import csv
import os
import sys
import collections
import time
import math
from datetime import datetime

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPainter, QColor, QFont, QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QGroupBox, \
    QLabel, QLineEdit, QSizePolicy, QSpacerItem, QDialog, QMessageBox, QMenuBar, QFileDialog, QDialogButtonBox
import pyqtgraph as pg
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SplashScreen(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Splash Screen')
        self.setFixedSize(400, 300)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet('QDialog{background-color: #0000FF; color: white;}')
        self.rotation_angle = 0
        self.initUI()
        self.timer = QTimer()
        self.timer.timeout.connect(self.loading)

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        label_title = QLabel(
            '<span style="font-style:italic; font-size:36px; color: white;'
            ' text-shadow: -1px -1px 0px white, 1px -1px 0px white, -1px 1px 0px white, 1px 1px 0px white,'
            ' -2px -2px 0px blue, 2px -2px 0px blue, -2px 2px 0px blue, 2px 2px 0px blue;">X</span> STREAM'
        )
        label_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_title.setFont(QFont("Arial", 30, QFont.Weight.Bold))
        label_title.setStyleSheet("color: white; border: 3px solid blue; padding: 10px;")
        layout.addWidget(label_title)

        layout.addStretch(1)
        label_welcome = QLabel('Connecting to XSTREAM Data Visualization...')
        label_welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_welcome.setFont(QFont("Arial", 16))
        label_welcome.setStyleSheet("color: darkgrey")
        layout.addWidget(label_welcome)

        label_version = QLabel('Version 1.0')
        label_author = QLabel('by David Gansterer-Heider')
        label_date = QLabel('20.11.2023 IVET')
        for label in [label_version, label_author, label_date]:
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFont(QFont("Arial", 12))
            label.setStyleSheet("color: white")
            layout.addWidget(label)

    def show_screen(self):
        """Show the splash screen and start the loading animation."""
        self.show()
        self.start_loading_animation()

    def start_loading_animation(self):
        """Start the rotation animation."""
        self.timer.start(50)  # Speed of rotation

    def loading(self):
        self.rotation_angle += 5
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        radius = 5
        circle_count = 8
        center_x, center_y = 200, 130
        distance_from_center = 30
        for i in range(circle_count):
            angle_rad = math.radians(self.rotation_angle + i * (360 / circle_count))
            x = int(center_x + distance_from_center * math.cos(angle_rad) - radius)
            y = int(center_y + distance_from_center * math.sin(angle_rad) - radius)
            painter.setBrush(QColor(255, 255, 255))
            painter.drawEllipse(x, y, int(radius * 2), int(radius * 2))
        painter.end()

    def hide_screen(self):
        """Stop the animation and hide the splash screen."""
        self.timer.stop()
        self.hide()
class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connection Settings")
        self.setFixedSize(400, 200)

        # Eingabe für Login-URL
        self.login_label = QLabel("Login URL:", self)
        self.login_input = QLineEdit("http://192.168.1.88/login.htm", self)

        # Eingabe für WebDriver-Pfad
        self.path_label = QLabel("Webdriver Path:", self)
        self.path_input = QLineEdit("C:\\webdriver\\chromedriver-win64\\chromedriver.exe", self)

        # Buttons für Verbindung und Abbruch
        self.connect_button = QPushButton("Connect", self)
        self.connect_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)

        # Layout für das Verbindungsfenster
        layout = QVBoxLayout()
        layout.addWidget(self.login_label)
        layout.addWidget(self.login_input)
        layout.addWidget(self.path_label)
        layout.addWidget(self.path_input)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.connect_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def get_login_url(self):
        return self.login_input.text()

    def get_webdriver_path(self):
        return self.path_input.text()


class SavePathDialog(QDialog):
    def __init__(self, default_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Save Directory")
        self.setFixedSize(400, 150)

        self.save_path = default_path

        layout = QVBoxLayout()
        self.path_input = QLineEdit(self.save_path)
        layout.addWidget(QLabel("Save Path:"))
        layout.addWidget(self.path_input)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Discard)
        button_box.accepted.connect(self.save_and_accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)
        self.setLayout(layout)

    def save_and_accept(self):
        self.save_path = self.path_input.text()
        self.accept()

    def get_save_path(self):
        return self.save_path


class MainWindow(QMainWindow):
    def __init__(self, path, login_url):
        super().__init__()
        self.path = path
        self.login_url = login_url
        self.driver = None
        self.save_directory = "C:\\Users\\IVET74\\Desktop\\X_Stream_Data"
        self.csv_file = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.fetch_data)

        self.initialize_plot()
        self.initUI()

    def start_webdriver(self):
        try:
            service = Service(executable_path=self.path)
            self.driver = webdriver.Chrome(service=service)

            self.driver.get(self.login_url)
            QMessageBox.information(self, "Login", "Please log in on the webpage. Then press OK.")

            main_url = self.driver.current_url
            self.driver.get(main_url)
            self.driver.switch_to.frame("unten")
            return True
        except WebDriverException:
            self.show_error_message("Connection failed. Please check WebDriver path.")
            return False

    def show_error_message(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Connection Error")
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def initUI(self):
        self.setWindowTitle("Gas Monitoring")
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        file_menu = menubar.addMenu("File")
        change_save_path_action = QAction("Change Save Path", self)
        change_save_path_action.triggered.connect(self.change_save_path)
        file_menu.addAction(change_save_path_action)

        start_stop_action = QAction("Start/Stop Acquisition", self)
        start_stop_action.triggered.connect(self.start_acquisition)
        file_menu.addAction(start_stop_action)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.create_gas_volume_perc_groupbox())
        main_layout.addWidget(self.plot_widget)

        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_acquisition)
        button_layout.addStretch(1)
        button_layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignRight)
        main_layout.addLayout(button_layout)
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def change_save_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.save_directory = directory
            QMessageBox.information(self, "Directory Changed", f"Save path set to: {self.save_directory}")

    def create_gas_volume_perc_groupbox(self):
        groupbox = QGroupBox("Gas Volume Percentage")
        data_layout = QHBoxLayout()
        data_layout.setSpacing(5)
        self.data_labels = {}

        colors = {
            "CO2": '#808080',  # Grau für CO₂
            "CO": '#000000',  # Schwarz für CO
            "CH4": '#00FF00',  # Hellgrün für CH₄
            "H2": '#FF0000',  # Rot für H₂
            "O2": '#0000FF',  # Blau für O₂
        }

        fields = [("CO₂:", "CO2"), ("CO:", "CO"), ("CH₄:", "CH4"), ("H₂:", "H2"), ("O₂:", "O2")]
        for label_text, gas in fields:
            label = QLabel(label_text)
            label.setStyleSheet(f"color: {colors[gas]}; font-weight: bold;")

            line_edit = QLineEdit("---")
            line_edit.setReadOnly(True)
            line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            line_edit.setFixedWidth(60)
            line_edit.setStyleSheet(f"color: {colors[gas]};")

            self.data_labels[gas] = line_edit
            data_layout.addWidget(label)
            data_layout.addWidget(line_edit)
            spacer_item = QSpacerItem(40, 30, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            data_layout.addItem(spacer_item)
        data_layout.addStretch(1)
        groupbox.setLayout(data_layout)
        return groupbox

    def initialize_plot(self):
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', 'Gas Vol%')
        self.plot_widget.setLabel('bottom', 'Time')
        self.plot_widget.getViewBox().setMouseEnabled(x=False)
        self.plot_widget.setLimits(yMin=0, yMax=100)

        self.time_data = collections.deque(maxlen=1000)
        self.gas_data = {gas: collections.deque(maxlen=1000) for gas in ["CO2", "CO", "CH4", "H2", "O2"]}
        colors = {
            "CO2": '#808080', "CO": '#000000', "CH4": '#00FF00', "H2": '#FF0000', "O2": '#0000FF'
        }
        self.curves = {gas: self.plot_widget.plot(pen=color) for gas, color in colors.items()}
        self.plot_widget.addLegend()
        self.plot_widget.setAxisItems({'bottom': pg.DateAxisItem()})

    def fetch_data(self):
        current_time = time.time()
        self.time_data.append(current_time)

        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//td[@id="btmline"]')))
            raw_text = element.text.strip()

            gas_values = {
                "CO2": float(raw_text.split("Ch1/R4:")[1].split("Vol%")[0].strip()),
                "CO": float(raw_text.split("Ch2/R4:")[1].split("Vol%")[0].strip()),
                "CH4": float(raw_text.split("Ch3/R4:")[1].split("Vol%")[0].strip()),
                "H2": float(raw_text.split("Ch4/R4:")[1].split("Vol%")[0].strip()),
                "O2": float(raw_text.split("Ch5/R4:")[1].split("Vol%")[0].strip()),
            }
            for gas, value in gas_values.items():
                self.gas_data[gas].append(value)
                self.data_labels[gas].setText(f"{value:.2f}")

            if self.csv_file:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.save_data_to_csv(timestamp, gas_values)

            self.update_plot()
        except WebDriverException:
            self.timer.stop()
            self.show_error_message("Connection lost. Webdriver is closing.")
            self.driver.quit()

    def update_plot(self):
        time_data = list(self.time_data)
        for gas, data in self.gas_data.items():
            self.curves[gas].setData(x=time_data, y=list(data))

    def save_data_to_csv(self, timestamp, gas_values):
        if not os.path.isfile(self.csv_file):
            with open(self.csv_file, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Timestamp", "CO2", "CO", "CH4", "H2", "O2"])

        with open(self.csv_file, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([timestamp] + list(gas_values.values()))

    def start_acquisition(self):
        if not self.timer.isActive():
            path_dialog = SavePathDialog(self.save_directory)
            if path_dialog.exec() == QDialog.DialogCode.Accepted:
                self.save_directory = path_dialog.get_save_path()
                now = datetime.now().strftime("%Y-%m-%d_%H-%M")
                self.csv_file = os.path.join(self.save_directory, f"xtream_data_{now}.csv")

                with open(self.csv_file, mode="w", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow(["Timestamp", "CO2", "CO", "CH4", "H2", "O2"])

                self.timer.start(1000)
                self.start_button.setText("Stop")
            else:
                self.csv_file = None
                self.timer.start(1000)
                self.start_button.setText("Stop")
        else:
            self.timer.stop()
            self.start_button.setText("Start")
            QMessageBox.information(self, "Acquisition Stopped", "Data fetching and saving have been stopped.")