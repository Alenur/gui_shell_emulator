import sys
from PySide6.QtWidgets import QApplication
from emulator import Console

if __name__ == "__main__":
    app = QApplication(sys.argv)
    console = Console()
    console.show()
    sys.exit(app.exec())
