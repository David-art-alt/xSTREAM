import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import xstream.views

def main():
    """Project main function"""
    # Erstelle die Anwendung
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Erstelle und zeige den Splash Screen
    splash_screen = xstream.views.SplashScreen()

    # Setze das Hauptfenster als Attribut des Splash Screens
    splash_screen.main_window = xstream.views.MainWindow()

    # Timer, um den Splash Screen nach 3 Sekunden zu schließen und das Hauptfenster zu zeigen
    QTimer.singleShot(3000, lambda: close_splash_and_show_main(splash_screen))

    # Splash Screen anzeigen
    splash_screen.show()

    # Start der Event-Schleife
    sys.exit(app.exec())

def close_splash_and_show_main(splash_screen):
    """Schließt den Splash Screen und zeigt das Hauptfenster an."""
    splash_screen.close()  # Schließt den Splash Screen
    splash_screen.main_window.show()  # Zeige das Hauptfenster an, das als Attribut gespeichert wurde