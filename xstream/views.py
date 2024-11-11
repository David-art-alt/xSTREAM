import os
import sys
import math
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QPainter, QColor
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QMainWindow, QHBoxLayout, QLineEdit, \
    QPushButton, QWidget
from pyqtgraph import PlotWidget

from xstream.data_scraping import DataFetcher

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
        self.setStyleSheet('QDialog{background-color: #0000FF; color: white;}')  # Blauer Hintergrund und weißer Text

        self.counter = 0
        self.n = 100  # Anzahl der Ladeintervalle für Timer-Loop
        self.rotation_angle = 0  # Initialer Rotationswinkel für Kreisbewegung

        self.initUI()

        self.timer = QTimer()
        self.timer.timeout.connect(self.loading)
        self.timer.start(50)

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Haupttitel "X STREAM" mit mehrschichtigem Rand für "X"
        label_title = QLabel(
            '<span style="font-style:italic; font-size:36px; color: white;'
            ' text-shadow: -1px -1px 0px white, 1px -1px 0px white, -1px 1px 0px white, 1px 1px 0px white,'
            ' -2px -2px 0px blue, 2px -2px 0px blue, -2px 2px 0px blue, 2px 2px 0px blue;">X</span> STREAM'
        )
        label_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_title.setFont(QFont("Arial", 30, QFont.Weight.Bold))
        label_title.setStyleSheet("color: white; border: 3px solid blue; padding: 10px;")
        layout.addWidget(label_title)

        # Begrüßungstext
        layout.addStretch(1)
        label_welcome = QLabel('Welcome to XSTREAM Data Visualization')
        label_welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_welcome.setFont(QFont("Arial", 16))
        layout.addWidget(label_welcome)

        # Versionsnummer und Autor
        label_version = QLabel('Version 1.0')
        label_author = QLabel('by David Gansterer-Heider')
        label_date = QLabel('20.11.2023 IVET')

        for label in [label_version, label_author, label_date]:
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFont(QFont("Arial", 12))
            layout.addWidget(label)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Kleinere Kreiseinstellungen
        radius = 5  # Reduziere den Radius des Kreises
        circle_count = 8
        center_x, center_y = 200, 130  # Zentrum für das Ladesymbol
        distance_from_center = 30  # Abstand zum Mittelpunkt verringern

        # Zeichne die Kreise im rotierenden Winkel
        for i in range(circle_count):
            angle_rad = math.radians(self.rotation_angle + i * (360 / circle_count))
            x = int(center_x + distance_from_center * math.cos(angle_rad) - radius)
            y = int(center_y + distance_from_center * math.sin(angle_rad) - radius)
            painter.setBrush(QColor(255, 255, 255))  # Weißer Kreis
            painter.drawEllipse(x, y, int(radius * 2), int(radius * 2))

        painter.end()  # Wichtig: Beende den QPainter korrekt

    def loading(self):
        if self.counter >= self.n:
            self.timer.stop()
            self.close()
        else:
            # Erhöhe den Rotationswinkel für die Animation
            self.rotation_angle += 5  # Erhöht den Winkel für jede Drehung
            self.update()  # Bildschirm neu zeichnen

        self.counter += 1


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initiale Einstellungen
        self.data_fetcher = DataFetcher()
        self.data_fetcher.data_received.connect(self.update_display_and_plot)
        self.timer = QTimer()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("XSTREAM Data Visualization")
        self.setGeometry(100, 100, 800, 600)

        # Layouts und Widgets
        main_layout = QVBoxLayout()

        # Eingabefelder für URL und Pfad
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit(self.data_fetcher.website)
        self.path_input = QLineEdit(self.data_fetcher.path)
        url_layout.addWidget(QLabel("Website URL:"))
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(QLabel("Webdriver Path:"))
        url_layout.addWidget(self.path_input)
        main_layout.addLayout(url_layout)

        # Datenlabels
        self.data_labels = {gas: QLabel(f"{gas}: ---") for gas in ["CO2", "CO", "CH4", "H2", "O2"]}
        for label in self.data_labels.values():
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(label)

        # Plot für Echtzeitdaten
        self.graph_widget = PlotWidget()
        main_layout.addWidget(self.graph_widget)
        self.curves = {gas: self.graph_widget.plot(pen=color) for gas, color in
                       zip(self.data_labels.keys(), ['r', 'g', 'b', 'y', 'm'])}

        # Start-Button
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_acquisition)
        main_layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        # Setzt das Layout im Hauptfenster
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def start_acquisition(self):
        # Aktualisiere URL und Pfad
        self.data_fetcher.website = self.url_input.text()
        self.data_fetcher.path = self.path_input.text()

        # Starte den Webdriver über Selenium
        self.data_fetcher.start_webdriver()

        # Startet den Timer für Datenabfragen
        self.timer.timeout.connect(self.data_fetcher.fetch_data)
        self.timer.start(1000)

    def update_display_and_plot(self, data):
        # Aktualisiert digitale Anzeige und Plot-Daten
        for gas, value in data.items():
            self.data_labels[gas].setText(f"{gas}: {value}")
            self.curves[gas].setData(self.data_fetcher.graph_data[gas])

