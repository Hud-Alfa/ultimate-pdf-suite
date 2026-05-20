"""Ultimate PDF Suite — uygulama giriş noktası."""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from gui.main_window import MainWindow


def _yukle_stil(app: QApplication) -> None:
    stil_yolu = Path(__file__).resolve().parent / "gui" / "styles.qss"
    if stil_yolu.is_file():
        app.setStyleSheet(stil_yolu.read_text(encoding="utf-8"))


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Ultimate PDF Suite")
    app.setOrganizationName("Ultimate PDF Suite")

    _yukle_stil(app)

    pencere = MainWindow()
    pencere.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
