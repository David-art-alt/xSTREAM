import os
import sys
import math
from datetime import datetime

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QPainter, QColor
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QMainWindow, QHBoxLayout, QLineEdit, \
    QPushButton, QWidget, QGroupBox, QSpacerItem, QSizePolicy
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
        label_welcome.setStyleSheet("color: darkgrey")
        layout.addWidget(label_welcome)

        # Versionsnummer und Autor
        label_version = QLabel('Version 1.0')
        label_author = QLabel('by David Gansterer-Heider')
        label_date = QLabel('20.11.2023 IVET')

        for label in [label_version, label_author, label_date]:
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFont(QFont("Arial", 12))
            label.setStyleSheet("color: white")
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

        # GroupBox für Gasvolumenprozente
        main_layout.addWidget(self.createGasVolumePercGroupbox())

        # Plot für Echtzeitdaten
        main_layout.addWidget(self.createPlot())

        # Start-Button
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_acquisition)
        main_layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        # Setzt das Layout im Hauptfenster
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def createGasVolumePercGroupbox(self):
        # Erstellen der GroupBox für die Gasvolumenprozente
        groupbox = QGroupBox("Gasvolumenprozente")

        # Horizontales Layout für die Gasanzeigen in einer Zeile
        data_layout = QHBoxLayout()
        data_layout.setSpacing(5)  # Abstand zwischen den Feldern

        # Datenfelder für die Gasanzeige
        self.data_labels = {}
        fields = [
            ("CO₂:", "CO2", "Vol%", 60),
            ("CO:", "CO", "Vol%", 60),
            ("CH₄:", "CH4", "Vol%", 60),
            ("H₂:", "H2", "Vol%", 60),
            ("O₂:", "O2", "Vol%", 60)
        ]

        # Erstellen der Labels und QLineEdits aus den Feldern
        for label_text, gas, unit, width in fields:
            # Label für die chemische Formel
            label = QLabel(label_text)
            #label.setAlignment(Qt.AlignmentFlag.AlignRight)
            label.setStyleSheet("font-weight: bold; color: #333;")

            # QLineEdit für den Wert des Gases
            line_edit = QLineEdit("---")
            line_edit.setReadOnly(True)
            line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            line_edit.setFixedWidth(width)
            line_edit.setStyleSheet("background-color: #f0f0f0; color: #333; border: 1px solid #ccc;")

            # Speichern des QLineEdit im Dictionary für spätere Updates
            self.data_labels[gas] = line_edit

            # Label für die Einheit (z. B. "Vol%")
            unit_label = QLabel(unit)
            #unit_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            # Fügen Sie Abstand (Leerzeichen) zwischen den Widgets hinzu
            spacer_item = QSpacerItem(40, 30, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            # Füge das Label, das QLineEdit und das Einheits-Label zum Layout hinzu
            data_layout.addWidget(label)
            data_layout.addWidget(line_edit)
            data_layout.addWidget(unit_label)
            data_layout.addItem(spacer_item)

        # Setze das Layout für die GroupBox
        data_layout.addStretch(1)
        #groupbox.setFixedHeight(120)
        groupbox.setLayout(data_layout)
        return groupbox

    def createPlot(self):
        # Initialisiert das PlotWidget für Echtzeitdaten
        self.graph_widget = PlotWidget()
        self.graph_widget.setBackground('w')
        self.graph_widget.showGrid(x=False, y=False, alpha=0.3)
        self.graph_widget.setLabel('left', 'Gas Vol%')
        self.graph_widget.setLabel('bottom', 'time')

        # Deaktivieren der horizontalen Verschiebung für die x-Achse
        self.graph_widget.getViewBox().setMouseEnabled(x=False)

        # Setzt die y-Achse auf einen Bereich von 0 bis 100 als Limit
        self.graph_widget.setLimits(yMin=0, yMax=100)

        # Setze den Anzeigebereich der y-Achse auf 0 bis 110, um zusätzlichen Raum oberhalb von 100 zu schaffen
        self.graph_widget.getViewBox().setRange(yRange=(0, 110), padding=0)

        self.graph_widget.setTitle(
            '<span style="color: darkgrey; font-size: 20pt">Gas Vol% vs Time</span>'
        )
        # Erstellt die Kurven für jedes Gas mit unterschiedlichen Farben
        colors = ['r', 'g', 'b', 'y', 'm']
        self.curves = {gas: self.graph_widget.plot(pen=color) for gas, color in zip(self.data_labels.keys(), colors)}

        return self.graph_widget

    def start_acquisition(self):
        # Aktualisiere URL und Pfad
        self.data_fetcher.website = self.url_input.text()
        self.data_fetcher.path = self.path_input.text()

        # Starte den Webdriver über Selenium
        self.data_fetcher.start_webdriver()

        # Startet den Timer für Datenabfragen
        self.timer.timeout.connect(self.data_fetcher.fetch_data)
        self.timer.start(1000)

    import datetime

    def update_display_and_plot(self, data):
        # Erfasse den aktuellen Zeitstempel für die x-Achse
        current_time = datetime.datetime.now()

        # Füge den Zeitstempel zu den gespeicherten Daten hinzu
        if "time" not in self.data_fetcher.graph_data:
            self.data_fetcher.graph_data["time"] = []  # Initialisiere Zeitstempelliste, falls nicht vorhanden
        self.data_fetcher.graph_data["time"].append(current_time.timestamp())

        # Aktualisiert die digitalen Anzeigen und den Plot
        for gas, value in data.items():
            # Setzt den neuen Wert ins QLineEdit
            if gas in self.data_labels:
                self.data_labels[gas].setText(str(value))

            # Speichere den neuen Wert in der entsprechenden Datenliste
            self.data_fetcher.graph_data[gas].append(value)

            # Aktualisiert die Kurve im Plot für das entsprechende Gas
            if gas in self.curves:
                # Verwende Zeitstempel als x-Werte und Gaswerte als y-Werte im Plot
                self.curves[gas].setData(
                    x=self.data_fetcher.graph_data["time"],
                    y=self.data_fetcher.graph_data[gas]
                )