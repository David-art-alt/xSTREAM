# -*- coding: utf-8 -*-
"""
This module provides interfaces for managing the visualization and storage of gas volume percentages measured by the
gas analyzer X-STREAM by Emerson. The data is fetched directly from the built-in user interface of the analyzer.
"""
import csv
import os
import sys
import collections
import time
from datetime import datetime
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QAction
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QGroupBox, \
    QLabel, QLineEdit, QDialog, QMessageBox, QMenuBar, QFileDialog, QDialogButtonBox
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
        self.setFixedSize(500, 270)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet('QDialog{background-color: #0000FF; color: white;}')

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Titel mit großem "X"
        label_title = QLabel(
            '<span style="font-style:italic; font-size:120px; color: white;'
            ' text-shadow: -1px -1px 0px white, 1px -1px 0px white, -1px 1px 0px white, 1px 1px 0px white,'
            ' -2px -2px 0px blue, 2px -2px 0px blue, -2px 2px 0px blue, 2px 2px 0px blue;">X</span> STREAM'
        )
        label_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_title.setFont(QFont("Arial", 50, QFont.Weight.Bold))
        label_title.setStyleSheet("color: white; border: 3px solid blue; padding: 10px;")
        layout.addWidget(label_title)

        layout.addStretch(1)

        # Status-Label für Updates
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 16px; color: lightgrey;")
        layout.addWidget(self.status_label)

        layout.addWidget(self.status_label)

        label_version = QLabel('Version 1.0')
        label_author = QLabel('by David Gansterer-Heider')
        label_date = QLabel('20.11.2024 IVET')
        for label in [label_version, label_author, label_date]:
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFont(QFont("Arial", 12))
            label.setStyleSheet("color: white")
            layout.addWidget(label)

    def update_status(self, message):
        """Aktualisiert die Statusnachricht."""
        self.status_label.setText(message)

class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connection Settings")
        self.setFixedSize(400, 170)

        self.login_label = QLabel("Login URL:", self)
        self.login_input = QLineEdit("http://192.168.1.88/login.htm", self)

        self.path_label = QLabel("Webdriver Path:", self)
        self.path_input = QLineEdit("C:\\webdriver\\chromedriver-win64\\chromedriver.exe", self)

        self.connect_button = QPushButton("Connect", self)
        self.connect_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.login_label)
        layout.addWidget(self.login_input)
        layout.addWidget(self.path_label)
        layout.addWidget(self.path_input)
        layout.addStretch(1)

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

        # Layout und Widgets
        layout = QVBoxLayout()

        # Aktueller Pfad
        self.path_input = QLineEdit(self.save_path)
        layout.addWidget(QLabel("Save Path:"))
        layout.addWidget(self.path_input)

        # Button zum Öffnen des Dateisystems für die Auswahl eines neuen Speicherverzeichnisses
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.open_file_system)
        layout.addWidget(browse_button)

        layout.addStretch(1)

        # Speicher- und Schließen-Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Close)
        button_box.accepted.connect(self.save_and_accept)
        button_box.rejected.connect(self.discard_and_accept)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def open_file_system(self):
        """Öffnet den Dateidialog zur Auswahl eines neuen Verzeichnisses."""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", self.save_path)
        if directory:
            self.path_input.setText(directory)
            self.save_path = directory

    def save_and_accept(self):
        self.save_path = self.path_input.text()
        self.accept()

    def discard_and_accept(self):
        self.save_path = None
        self.accept()

    def get_save_path(self):
        return self.save_path

class StartAcquisitionDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle("Start Acquisition")
                self.setFixedSize(300, 150)

                # Layout und Widgets
                layout = QVBoxLayout()
                self.path_label = QLabel("Current Save Path:")
                self.path_display = QLineEdit()
                self.path_display.setReadOnly(True)
                layout.addWidget(self.path_label)
                layout.addWidget(self.path_display)

                # Speicherpfad ändern
                change_path_button = QPushButton("Change Save Path")
                change_path_button.clicked.connect(self.change_save_path)
                layout.addWidget(change_path_button)

                # Start-Button für die Datenerfassung
                start_button = QPushButton("Start Acquisition")
                start_button.clicked.connect(self.accept)
                layout.addWidget(start_button)

                self.setLayout(layout)

            def set_save_path(self, path):
                self.path_display.setText(path)

            def change_save_path(self):
                directory = QFileDialog.getExistingDirectory(self, "Select Directory")
                if directory:
                    self.path_display.setText(directory)
                    self.save_path = directory

            def get_save_path(self):
                return self.save_path if hasattr(self, 'save_path') else None

class MainWindow(QMainWindow):
    def __init__(self, path, login_url, driver, initial_data=None):
        super().__init__()
        self.path = path
        self.login_url = login_url
        self.driver = driver
        self.initial_data = initial_data  # Speichere initial_data
        self.save_directory = "C:\\Users\\IVET74\\Desktop\\X_Stream_Data"
        self.csv_file = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.fetch_data)
        self.resize(1000, 700)

        # UI-Komponenten initialisieren
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
        self.setWindowTitle("X-Stream Gas Monitoring")
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)
        # Aktion zum Beenden der Anwendung hinzufügen
        file_menu = menubar.addMenu("Exit")
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Cmd+Q")

        exit_action.triggered.connect(self.close)  # Verknüpft die Aktion mit der Schließfunktion
        file_menu.addAction(exit_action)


        main_layout = QVBoxLayout()
        main_layout.addWidget(self.create_gas_volume_perc_groupbox())
        main_layout.addWidget(self.plot_widget)

        # Statusanzeige (Info-Text)
        self.status_label = QLabel("Status: Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333333; padding: 10px;")
        main_layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_or_stop_acquisition)
        button_layout.addStretch(1)
        button_layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignRight)
        main_layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def update_status_message(self, message):
        self.status_label.setText(message)

    def change_save_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.save_directory = directory
            QMessageBox.information(self, "Directory Changed", f"Save path set to: {self.save_directory}")

    def create_gas_volume_perc_groupbox(self):
        """Erstellt die GroupBox für die Anzeige der Gasvolumenprozentsätze."""
        groupbox = QGroupBox("Gas Volume Percentage")
        groupbox.setStyleSheet("font-size: 16px; font-weight: bold;")

        layout = QHBoxLayout()
        layout.setSpacing(10)

        self.data_labels = {}
        colors = {
            "CO2": '#808080', "CO": '#000000', "CH4": '#008000', "H2": '#FF0000', "O2": '#0000FF'
        }
        gases = [("CO₂:", "CO2"), ("CO:", "CO"), ("CH₄:", "CH4"), ("H₂:", "H2"), ("O₂:", "O2")]

        for gas_name, gas_key in gases:
            label = QLabel(gas_name)
            label.setStyleSheet(f"color: {colors[gas_key]}; font-size: 18px; font-weight: bold;")
            line_edit = QLineEdit("---")
            line_edit.setReadOnly(True)
            line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            line_edit.setFixedWidth(80)
            line_edit.setStyleSheet(f"color: {colors[gas_key]}; font-size: 16px; padding: 5px;")
            self.data_labels[gas_key] = line_edit

            layout.addWidget(label)
            layout.addWidget(line_edit)

        layout.addStretch(1)
        groupbox.setLayout(layout)
        return groupbox

    @staticmethod
    def fetch_initial_data(path, login_url):
        """
        Fetches the initial gas data for scaling the Y-axis of the plot.
        Initializes the WebDriver, navigates to the login page, and extracts data.

        Args:
            path: Path to the WebDriver executable.
            login_url: URL of the login page.

        Returns:
            Tuple: A dictionary containing gas data and the WebDriver instance.
                   Example: ({"CO2": 0.02, "CO": 0.0, "CH4": 0.01, "H2": 0.11, "O2": 20.95}, driver)
            (None, None): If an error occurred.
        """
        try:
            # Starte den WebDriver
            service = Service(executable_path=path)
            driver = webdriver.Chrome(service=service)

            # Öffne die Login-Seite
            driver.get(login_url)
            QMessageBox.information(None, "Login", "Please log in on the webpage. Then press OK.")

            # Wechsel in den richtigen Frame (falls notwendig)
            driver.switch_to.frame("unten")

            # Warte auf das Element und extrahiere die Daten
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//td[@id="btmline"]'))
            )
            raw_text = element.text.strip()

            # Parse die Gasvolumendaten
            gas_values = {
                "CO2": float(raw_text.split("Ch1/R4:")[1].split("Vol%")[0].strip()),
                "CO": float(raw_text.split("Ch2/R4:")[1].split("Vol%")[0].strip()),
                "CH4": float(raw_text.split("Ch3/R4:")[1].split("Vol%")[0].strip()),
                "H2": float(raw_text.split("Ch4/R4:")[1].split("Vol%")[0].strip()),
                "O2": float(raw_text.split("Ch5/R4:")[1].split("Vol%")[0].strip()),
            }

            #print(f"Initial gas values successfully parsed: {gas_values}")
            return gas_values, driver
        except Exception as e:
            #print(f"Error initializing WebDriver or fetching data: {e}")
            return None, None


    def initialize_plot(self):
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', 'Gas Vol%')
        self.plot_widget.setAxisItems({'bottom': pg.DateAxisItem()})
        self.plot_widget.getViewBox().setMouseEnabled(x=False)
        self.plot_widget.setLimits(yMin=0, yMax=100)
        self.plot_widget.setTitle("Gas Concentrations Over Time")

        self.time_data = collections.deque(maxlen=1000)
        self.gas_data = {gas: collections.deque(maxlen=1000) for gas in ["CO2", "CO", "CH4", "H2", "O2"]}

        # Farben für die Gase
        colors = {
            "CO2": '#808080', "CO": '#000000', "CH4": '#008000', "H2": '#FF0000', "O2": '#0000FF'
        }

        # Mapping für chemische Symbole mit tiefgestellten Zahlen
        gas_labels = {
            "CO2": "CO₂",
            "CO": "CO",
            "CH4": "CH₄",
            "H2": "H₂",
            "O2": "O₂",
        }

        # Erstelle Kurven und Labels
        self.curves = {}
        self.labels = {}
        # Schleife zur Erstellung von Kurven und Labels
        for gas, color in colors.items():
            self.curves[gas] = self.plot_widget.plot(pen=color, name=gas)
            # Füge das Label mit dem tiefgestellten Text hinzu
            self.labels[gas] = pg.TextItem(text=gas_labels[gas], color=color, anchor=(0, 1))
            #self.plot_widget.addItem(self.labels[gas])


        self.plot_widget.addLegend()

        if hasattr(self, 'initial_data') and self.initial_data:
            self.apply_initial_data()

    def apply_initial_data(self):
        """Plottet Initialdaten, falls vorhanden."""
        time_data = [time.time()]  # Initiale Zeit
        for gas, value in self.initial_data.items():
            self.gas_data[gas].append(value)
            self.curves[gas].setData(x=time_data, y=[value])
            #self.labels[gas].setPos(time_data[-1], value)

    def update_plot(self):
        """Aktualisiert den Plot bei neuen Daten."""
        if len(self.time_data) == 0:
            return  # Keine Daten vorhanden

        # Zeitdaten in hh:mm:ss umwandeln
        time_labels = [datetime.fromtimestamp(t).strftime("%H:%M:%S") for t in self.time_data]

        # X-Daten basieren auf den Indizes (beginnend bei 0)
        x_data = list(range(len(self.time_data)))

        for gas, data in self.gas_data.items():
            if len(data) > 0:
                y_data = list(data)

                # Synchronisiere die Längen von x_data und y_data
                min_length = min(len(x_data), len(y_data))
                x_data_synced = x_data[-min_length:]
                y_data_synced = y_data[-min_length:]

                # Aktualisiere den Plot
                self.curves[gas].setData(x=x_data_synced, y=y_data_synced)

                # Labels hinzufügen, falls nicht vorhanden, und ihre Position aktualisieren
                if not self.labels[gas].parentItem():
                    self.plot_widget.addItem(self.labels[gas])


                self.labels[gas].setPos(x_data_synced[-1], y_data_synced[-1])


        # Dynamische Skalierung der x-Achse basierend auf der Anzahl der Datenpunkte
        max_x = max(len(self.time_data), 1)
        self.plot_widget.setLimits(xMin=0, xMax=max_x + 10)  # Pufferbereich für xMax

        # Setze die Ticks der x-Achse mit den Zeitlabels
        tick_positions = [(i, time_labels[i]) for i in range(len(time_labels)) if
                          i % max(1, len(time_labels) // 10) == 0]
        self.plot_widget.getAxis('bottom').setTicks([tick_positions])

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

    def save_data_to_csv(self, timestamp, gas_values):
        if not os.path.isfile(self.csv_file):
            with open(self.csv_file, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Timestamp", "CO2", "CO", "CH4", "H2", "O2"])

        with open(self.csv_file, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([timestamp] + list(gas_values.values()))

    def start_or_stop_acquisition(self):
        if not self.timer.isActive():
            path_dialog = SavePathDialog(self.save_directory)
            if path_dialog.exec() == QDialog.DialogCode.Accepted:
                self.save_directory = path_dialog.get_save_path()
                if self.save_directory:
                    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
                    self.csv_file = os.path.join(self.save_directory, f"xtream_data_{now}.csv")
                    with open(self.csv_file, mode="w", newline="") as file:
                        writer = csv.writer(file)
                        writer.writerow(["Timestamp", "CO2", "CO", "CH4", "H2", "O2"])
                    self.update_status_message(f"Save selected - Data will be saved to: {self.csv_file}")
                else:
                    self.csv_file = None
                    self.update_status_message("Discard selected - No data will be saved.")

                self.timer.start(1000)
                self.start_button.setText("Stop")
            else:
                self.update_status_message("Acquisition cancelled.")
        else:
            self.timer.stop()
            self.update_status_message("Saving and Plotting stopped.")
            self.start_button.setText("Start")

    def closeEvent(self, event):
        """Blockiert das Schließen, wenn der Prozess aktiv ist."""
        if self.timer.isActive():  # Prüft, ob der Prozess läuft
            reply = QMessageBox.warning(
                self,
                "Process Running",
                "The process is still running. Please stop the process before exiting.",
                QMessageBox.StandardButton.Ok
            )
            event.ignore()  # Schließen verhindern
        else:
            event.accept()  # Schließen erlauben

