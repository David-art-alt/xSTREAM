import sys
from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox
from xstream.views import SplashScreen, ConnectionDialog, MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    while True:
        connection_dialog = ConnectionDialog()
        if connection_dialog.exec() == QDialog.DialogCode.Accepted:
            login_url = connection_dialog.get_login_url()
            path = connection_dialog.get_webdriver_path()

            splash = SplashScreen()
            splash.show_screen()  # Display the splash screen

            window = MainWindow(path, login_url)
            if window.start_webdriver():
                splash.hide_screen()  # Hide after successful connection
                window.show()
                sys.exit(app.exec())
            else:
                splash.hide_screen()
                QMessageBox.warning(None, "Connection Error", "Failed to establish connection. Please try again.")
        else:
            break  # Exit if the user cancels

def close_splash_and_show_main(splash_screen):
    """Schließt den Splash Screen und zeigt das Hauptfenster an."""
    splash_screen.close()  # Schließt den Splash Screen
    splash_screen.main_window.show()  # Zeige das Hauptfenster an, das als Attribut gespeichert wurdefenster an, das als Attribut gespeichert wurde