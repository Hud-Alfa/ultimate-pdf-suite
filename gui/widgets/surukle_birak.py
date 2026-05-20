"""Sürükle-bırak dosya alanı."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Set

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout


class SurukleBirakAlani(QFrame):
    """Dosyaları sürükleyip bırakma veya tıklayarak seçme."""

    dosyalar_degisti = pyqtSignal(list)

    def __init__(
        self,
        *,
        coklu: bool = False,
        uzantilar: Iterable[str] | None = None,
        baslik: str = "Dosyaları buraya sürükleyin",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self._coklu = coklu
        self._uzantilar: Set[str] | None = (
            {u.lower() if u.startswith(".") else f".{u.lower()}" for u in uzantilar}
            if uzantilar
            else None
        )
        self._yollar: list[str] = []

        kok = QVBoxLayout(self)
        kok.setContentsMargins(16, 20, 16, 20)
        self._baslik = QLabel(baslik)
        self._baslik.setObjectName("dropZoneTitle")
        self._baslik.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._alt = QLabel("veya Gözat ile seçin")
        self._alt.setObjectName("dropZoneHint")
        self._alt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._liste = QLabel("")
        self._liste.setObjectName("dropZoneFiles")
        self._liste.setWordWrap(True)
        self._liste.setAlignment(Qt.AlignmentFlag.AlignCenter)
        kok.addWidget(self._baslik)
        kok.addWidget(self._alt)
        kok.addWidget(self._liste)

    def yollar(self) -> list[str]:
        return list(self._yollar)

    def ayarla(self, yollar: list[str]) -> None:
        self._yollar = [y for y in yollar if y]
        self._guncelle_etiket()

    def temizle(self) -> None:
        self.ayarla([])

    def _guncelle_etiket(self) -> None:
        if not self._yollar:
            self._liste.setText("")
            return
        if len(self._yollar) == 1:
            self._liste.setText(Path(self._yollar[0]).name)
        else:
            self._liste.setText(f"{len(self._yollar)} dosya seçildi")

    def _kabul_mu(self, yol: str) -> bool:
        if not Path(yol).is_file():
            return False
        if self._uzantilar is None:
            return True
        return Path(yol).suffix.lower() in self._uzantilar

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("dragOver", True)
            self.style().unpolish(self)
            self.style().polish(self)

    def dragLeaveEvent(self, event) -> None:  # type: ignore[override]
        self.setProperty("dragOver", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        self.setProperty("dragOver", False)
        self.style().unpolish(self)
        self.style().polish(self)
        eklenen: list[str] = []
        for url in event.mimeData().urls():
            yol = url.toLocalFile()
            if self._kabul_mu(yol):
                eklenen.append(yol)
        if not eklenen:
            return
        if self._coklu:
            self._yollar = list(dict.fromkeys(self._yollar + eklenen))
        else:
            self._yollar = [eklenen[0]]
        self._guncelle_etiket()
        self.dosyalar_degisti.emit(self.yollar())
        event.acceptProposedAction()
