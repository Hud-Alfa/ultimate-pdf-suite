"""Büyük − / + düğmeli sayı seçici (spinbox yerine)."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class AdimKutusu(QWidget):
    """Metin kutusu içindeki küçük oklar yerine geniş − ve + düğmeleri."""

    valueChanged = pyqtSignal(float)

    def __init__(
        self,
        minimum: float = 0,
        maximum: float = 100,
        step: float = 1,
        value: float = 0,
        *,
        decimals: int = 0,
        suffix: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._min = float(minimum)
        self._max = float(maximum)
        self._step = float(step)
        self._decimals = max(0, decimals)
        self._suffix = suffix
        self._deger = self._sinirla(float(value))

        kok = QHBoxLayout(self)
        kok.setContentsMargins(0, 0, 0, 0)
        kok.setSpacing(8)

        self._eksi = QPushButton("−")
        self._eksi.setObjectName("stepperButton")
        self._eksi.setFixedSize(48, 48)
        self._eksi.setCursor(Qt.CursorShape.PointingHandCursor)
        self._eksi.setToolTip(f"Azalt (−{self._step:g})")
        self._eksi.clicked.connect(self._azalt)

        self._goster = QLabel()
        self._goster.setObjectName("stepperValue")
        self._goster.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._goster.setMinimumWidth(88)
        self._goster.setMinimumHeight(48)

        self._arti = QPushButton("+")
        self._arti.setObjectName("stepperButton")
        self._arti.setFixedSize(48, 48)
        self._arti.setCursor(Qt.CursorShape.PointingHandCursor)
        self._arti.setToolTip(f"Artır (+{self._step:g})")
        self._arti.clicked.connect(self._artir)

        kok.addWidget(self._eksi)
        kok.addWidget(self._goster, stretch=1)
        kok.addWidget(self._arti)

        self._etiket_guncelle()

    def _sinirla(self, v: float) -> float:
        return max(self._min, min(self._max, v))

    def _etiket_guncelle(self) -> None:
        if self._decimals == 0:
            metin = f"{int(round(self._deger))}"
        else:
            metin = f"{self._deger:.{self._decimals}f}"
        self._goster.setText(metin + self._suffix)

    def _deger_ata(self, v: float, *, bildir: bool = True) -> None:
        yeni = self._sinirla(v)
        if yeni == self._deger:
            return
        self._deger = yeni
        self._etiket_guncelle()
        if bildir:
            self.valueChanged.emit(self._deger)

    def _azalt(self) -> None:
        self._deger_ata(self._deger - self._step)

    def _artir(self) -> None:
        self._deger_ata(self._deger + self._step)

    def value(self) -> float:
        return self._deger

    def setValue(self, v: float) -> None:
        self._deger_ata(float(v))
