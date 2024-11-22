# -*- coding :utf-8 -*-
# xstream/main.py
'''This module provides XSTREAM application.'''

import sys
from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox
from xstream.views import SplashScreen, ConnectionDialog, MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Splashscreen erstellen und sofort anzeigen
    splash = SplashScreen()
    splash.show()
    splash.update_status("Waiting for connection settings...")
    app.processEvents()  # Sicherstellen, dass der SplashScreen vollständig gerendert wird

    while True:
        # Zeige das Verbindungsdialogfenster
        connection_dialog = ConnectionDialog()
        if connection_dialog.exec() == QDialog.DialogCode.Accepted:
            login_url = connection_dialog.get_login_url()
            path = connection_dialog.get_webdriver_path()

            splash.update_status("Initializing WebDriver...")  # Statusmeldung
            app.processEvents()  # Aktualisiere GUI, damit SplashScreen sichtbar bleibt

            try:
                # Initiale Gasdaten abrufen
                initial_data, driver = MainWindow.fetch_initial_data(path, login_url)
                if initial_data:
                    splash.update_status("Initializing Main Window...")  # Status aktualisieren
                    app.processEvents()

                    # Hauptfenster erstellen und anzeigen
                    window = MainWindow(path, login_url, driver, initial_data=initial_data)
                    splash.close()  # SplashScreen schließen
                    window.show()
                    sys.exit(app.exec())
                else:
                    splash.update_status("Failed to fetch initial data. Retrying...")
                    QMessageBox.warning(None, "Data Error", "Failed to fetch initial gas data. Please try again.")
            except Exception as e:
                splash.update_status("Connection failed. Retrying...")
                QMessageBox.warning(None, "Connection Error", f"Failed to connect: {str(e)}")
        else:
            splash.close()  # SplashScreen schließen, wenn der Benutzer abbricht
            break  # Schleife verlassen, wenn der Benutzer abbricht

