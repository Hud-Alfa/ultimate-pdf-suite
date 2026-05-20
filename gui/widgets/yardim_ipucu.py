"""Küçük ? düğmesi — üzerine gelince kullanım ipucu."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton, QToolTip, QWidget


class YardimButonu(QPushButton):
    """Form alanlarının yanında kısa kullanım açıklaması."""

    def __init__(self, aciklama: str, parent: QWidget | None = None) -> None:
        super().__init__("?", parent)
        self.setObjectName("helpButton")
        self.setFixedSize(24, 24)
        self.setCursor(Qt.CursorShape.WhatsThisCursor)
        self.setToolTip(aciklama)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._aciklama = aciklama

    def enterEvent(self, event) -> None:  # type: ignore[override]
        QToolTip.showText(self.mapToGlobal(self.rect().center()), self._aciklama, self)
        super().enterEvent(event)
