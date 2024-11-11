import os
import sys
from datetime import datetime, time
import pyqtgraph as pg
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class SplashScreen(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Splash Screen')
        self.setFixedSize(400, 200)  # Größe des Fortschrittsbalkens ändern
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet('QDialog{border: 1px solid #888888}')  # Add thin black border

        self.counter = 0
        self.n = 100  # Gesamtanzahl von Instanzen

        self.initUI()

        self.timer = QTimer()
        self.timer.timeout.connect(self.loading)
        self.timer.start(20)

    def initUI(self):

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Überschrift
        label_welcome = QLabel('Welcome to XSTREAM Datavisualisation')
        label_welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_welcome.setFont(QFont("Arial", 16))  # Textgröße ändern
        layout.addWidget(label_welcome)

        # Versionsnummer
        label_version = QLabel('Version 1.0')
        label_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_version.setFont(QFont("Arial", 14))  # Textgröße ändern
        layout.addWidget(label_version)

        # Zusätzlicher Text
        label_author = QLabel('by David Gansterer-Heider')
        label_date = QLabel('20.11.2023 IVET')
        label_author.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label_author)
        layout.addWidget(label_date)

        # Fortschrittsbalken
        self.progressBar = QProgressBar()
        self.progressBar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progressBar.setFixedHeight(10)  # Höhe des Fortschrittsbalkens
        self.progressBar.setTextVisible(False)  # Text im Fortschrittsbalken ausblenden
        self.progressBar.setRange(0, self.n)
        self.progressBar.setValue(20)
        self.progressBar.setStyleSheet(
            "QProgressBar {"
            "    background-color: lightgray;"
            "    border: 1px solid gray;"
            "    border-radius: 5px;"
            "}"
            "QProgressBar::chunk {"
            "    background-color:darkgray;"
            "    width: 10px;"  # Breite des blauen Balkens
            "}"
        )
        layout.addWidget(self.progressBar)

    def loading(self):
        self.progressBar.setValue(self.counter)

        if self.counter >= self.n:
            self.timer.stop()
            self.close()

            time.sleep(1)

        self.counter += 1