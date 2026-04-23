import sys
import os
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils.logger import logger

def main():
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        # Load stylesheet
        app_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        if getattr(sys, 'frozen', False):
            # PyInstaller logic
            qss_path = os.path.join(app_dir, 'ui', 'styles.qss')
        else:
            qss_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ui', 'styles.qss')
            
        if os.path.exists(qss_path):
            with open(qss_path, 'r', encoding='utf-8') as f:
                app.setStyleSheet(f.read())
                
        # Set app icon
        from PySide6.QtGui import QIcon
        icon_path = os.path.join(app_dir, "app_icon.png")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            
        window = MainWindow()
        window.show()
        
        logger.info("Application started.")
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Application crashed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
