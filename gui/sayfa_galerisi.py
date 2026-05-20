"""Etkileşimli sayfa galerisi — sıralama, seçim, kaldırma."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional

import fitz
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QIcon, QImage, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.sayfa_model import SayfaRef, metne_cevir, metinden_sec, plana_cevir


@dataclass
class SayfaOgesiVeri:
    ref: SayfaRef
    image: QImage  # iş parçacığından güvenle aktarılır; QPixmap yalnızca GUI'de
    baslik: str


class GaleriWorker(QThread):
    hazir = pyqtSignal(list)
    hata = pyqtSignal(str)

    def __init__(
        self,
        yollar: List[str],
        *,
        max_genislik: int = 130,
        dosya_basina_max: int = 300,
    ) -> None:
        super().__init__()
        self._yollar = yollar
        self._max_genislik = max_genislik
        self._dosya_basina_max = dosya_basina_max

    def run(self) -> None:
        try:
            ogeler: List[SayfaOgesiVeri] = []
            for yol in self._yollar:
                if not os.path.isfile(yol) or not yol.lower().endswith(".pdf"):
                    continue
                belge = fitz.open(yol)
                ad = os.path.basename(yol)
                n = min(belge.page_count, self._dosya_basina_max)

                for i in range(n):
                    if self.isInterruptionRequested():
                        belge.close()
                        return
                    sayfa = belge[i]
                    olcek = self._max_genislik / max(sayfa.rect.width, 1)
                    mat = fitz.Matrix(olcek, olcek)
                    pix = sayfa.get_pixmap(matrix=mat, alpha=False)
                    img = QImage(
                        pix.samples,
                        pix.width,
                        pix.height,
                        pix.stride,
                        QImage.Format.Format_RGB888,
                    )
                    ref = SayfaRef(dosya=yol, sayfa=i)
                    ogeler.append(
                        SayfaOgesiVeri(
                            ref=ref,
                            image=img.copy(),
                            baslik=f"{ad}\ns.{i + 1}",
                        )
                    )
                belge.close()

            self.hazir.emit(ogeler)
        except Exception as exc:  # noqa: BLE001
            self.hata.emit(str(exc))


ROL_REF = Qt.ItemDataRole.UserRole
ROL_SECILI = Qt.ItemDataRole.UserRole + 1


class SayfaGalerisiPaneli(QFrame):
    """
    Etkileşimli ön izleme.

    modlar:
      - izleme: salt okunur
      - sira: sürükle-bırak ile sıralama (birleştirme)
      - secim: tıkla = seç / kaldır (sil, ayıkla, döndür, kırp)
    """

    MOD_IZLEME = "izleme"
    MOD_SIRA = "sira"
    MOD_SECIM = "secim"

    secim_degisti = pyqtSignal(str)
    sira_degisti = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("pdfPreview")
        self._mod = self.MOD_IZLEME
        self._worker: Optional[GaleriWorker] = None
        self._tek_dosya: str = ""
        self._orijinal_ogeler: List[SayfaOgesiVeri] = []

        kok = QVBoxLayout(self)
        kok.setContentsMargins(0, 0, 0, 0)
        kok.setSpacing(8)

        baslik = QLabel("Sayfa galerisi")
        baslik.setObjectName("previewTitle")
        kok.addWidget(baslik)

        self._bilgi = QLabel("PDF seçin; sayfalarla etkileşime geçebilirsiniz.")
        self._bilgi.setObjectName("previewHint")
        self._bilgi.setWordWrap(True)
        kok.addWidget(self._bilgi)

        self._arac = QHBoxLayout()
        self._sifirla = QPushButton("Sırayı sıfırla")
        self._sifirla.setObjectName("secondaryButton")
        self._sifirla.setVisible(False)
        self._sifirla.clicked.connect(self._sirayi_sifirla)
        self._secim_temizle = QPushButton("Seçimi temizle")
        self._secim_temizle.setObjectName("secondaryButton")
        self._secim_temizle.setVisible(False)
        self._secim_temizle.clicked.connect(self._tum_secimi_kaldir)
        self._kaldir = QPushButton("Seçili sayfayı çıkar")
        self._kaldir.setObjectName("secondaryButton")
        self._kaldir.setVisible(False)
        self._kaldir.clicked.connect(self._secili_ogeyi_kaldir)
        self._arac.addWidget(self._sifirla)
        self._arac.addWidget(self._secim_temizle)
        self._arac.addWidget(self._kaldir)
        self._arac.addStretch()
        kok.addLayout(self._arac)

        self._liste = QListWidget()
        self._liste.setObjectName("sayfaListesi")
        self._liste.setViewMode(QListWidget.ViewMode.IconMode)
        self._liste.setIconSize(QSize(120, 155))
        self._liste.setResizeMode(QListWidget.ResizeMode.Adjust)
        self._liste.setMovement(QListWidget.Movement.Snap)
        self._liste.setSpacing(12)
        self._liste.setWrapping(True)
        self._liste.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._liste.itemClicked.connect(self._oge_tiklandi)
        self._liste.model().rowsMoved.connect(lambda *a: self._sira_guncelle())

        kaydir = QScrollArea()
        kaydir.setWidgetResizable(True)
        kaydir.setFrameShape(QFrame.Shape.NoFrame)
        kaydir.setWidget(self._liste)
        kok.addWidget(kaydir, stretch=1)

        self.set_mod(self.MOD_IZLEME)

    def set_mod(self, mod: str) -> None:
        self._mod = mod
        self._sifirla.setVisible(mod == self.MOD_SIRA)
        self._secim_temizle.setVisible(mod == self.MOD_SECIM)
        self._kaldir.setVisible(mod in (self.MOD_SIRA, self.MOD_SECIM))

        if mod == self.MOD_SIRA:
            self._liste.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
            self._liste.setDefaultDropAction(Qt.DropAction.MoveAction)
            self._bilgi.setText("Sayfaları sürükleyerek sıralayın. Çıkarmak için seçip «Çıkar».")
        elif mod == self.MOD_SECIM:
            self._liste.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
            self._bilgi.setText("Sayfaya tıklayarak seçin/kaldırın. Seçim metin kutusuyla senkron.")
        else:
            self._liste.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
            self._bilgi.setText("Sayfa ön izlemesi.")

    def yukle(self, yollar: List[str]) -> None:
        pdfler = [y for y in yollar if y.lower().endswith(".pdf") and os.path.isfile(y)]
        if not pdfler:
            self.temizle()
            return

        self._tek_dosya = pdfler[0] if len(pdfler) == 1 else ""
        self._bilgi.setText("Sayfalar yükleniyor…")
        self._liste.clear()
        self._worker_durdur()

        self._worker = GaleriWorker(pdfler)
        self._worker.hazir.connect(self._ogeleri_doldur)
        self._worker.hata.connect(self._hata)
        self._worker.start()

    def yukle_tek(self, yol: str) -> None:
        if yol.strip():
            self.yukle([yol.strip()])
        else:
            self.temizle()

    def temizle(self, mesaj: str = "PDF seçin; sayfalarla etkileşime geçebilirsiniz.") -> None:
        self._worker_durdur()
        self._liste.clear()
        self._orijinal_ogeler = []
        self._tek_dosya = ""
        self._bilgi.setText(mesaj)

    def sayfa_plani(self) -> List[tuple[str, int]]:
        return plana_cevir(self.sayfa_refs())

    def secili_refs(self) -> List[SayfaRef]:
        """Seçim modunda işaretli sayfalar."""
        if self._mod != self.MOD_SECIM:
            return []
        secili: List[SayfaRef] = []
        for i in range(self._liste.count()):
            item = self._liste.item(i)
            if item and self._oge_secili_mi(item):
                ref = item.data(ROL_REF)
                if ref:
                    secili.append(ref)
        return secili

    def sayfa_refs(self) -> List[SayfaRef]:
        refs: List[SayfaRef] = []
        for i in range(self._liste.count()):
            item = self._liste.item(i)
            ref = item.data(ROL_REF)
            if ref:
                refs.append(ref)
        return refs

    def secim_metni(self) -> str:
        if not self._tek_dosya:
            return ""
        secili: List[SayfaRef] = []
        for i in range(self._liste.count()):
            item = self._liste.item(i)
            if item and self._oge_secili_mi(item):
                ref = item.data(ROL_REF)
                if ref:
                    secili.append(ref)
        return metne_cevir(secili, tek_dosya=self._tek_dosya)

    def secim_uygula(self, metin: str) -> None:
        if not self._tek_dosya or self._mod != self.MOD_SECIM:
            return
        secilen = metinden_sec(metin, self._tum_refs(), tek_dosya=self._tek_dosya)
        sec_set = {(r.dosya, r.sayfa) for r in secilen}
        for i in range(self._liste.count()):
            item = self._liste.item(i)
            ref: SayfaRef = item.data(ROL_REF)
            item.setData(ROL_SECILI, (ref.dosya, ref.sayfa) in sec_set)
            self._oge_stil_guncelle(item)
        self._bilgi_guncelle()

    def _tum_refs(self) -> List[SayfaRef]:
        return [self._liste.item(i).data(ROL_REF) for i in range(self._liste.count())]

    def _worker_durdur(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.requestInterruption()
            self._worker.wait(2500)
        self._worker = None

    def _ogeleri_doldur(self, ogeler: list) -> None:
        self._orijinal_ogeler = list(ogeler)
        self._liste.clear()
        for veri in ogeler:
            self._oge_ekle(veri, secili=False)
        self._bilgi_guncelle()

    def _oge_ekle(self, veri: SayfaOgesiVeri, *, secili: bool) -> None:
        item = QListWidgetItem()
        item.setData(ROL_REF, veri.ref)
        item.setData(ROL_SECILI, secili)
        pm = QPixmap.fromImage(veri.image)
        item.setIcon(QIcon(pm))
        item.setText(veri.baslik)
        item.setSizeHint(QSize(130, 185))
        item.setToolTip(veri.ref.etiket())
        self._liste.addItem(item)
        self._oge_stil_guncelle(item)

    @staticmethod
    def _oge_secili_mi(item: QListWidgetItem) -> bool:
        return bool(item.data(ROL_SECILI))

    def _oge_stil_guncelle(self, item: QListWidgetItem) -> None:
        if self._mod == self.MOD_SECIM and self._oge_secili_mi(item):
            item.setBackground(QColor("#1e4d38"))
        else:
            item.setBackground(QColor("#1a2030"))

    def _oge_tiklandi(self, item: QListWidgetItem) -> None:
        if self._mod != self.MOD_SECIM:
            return
        sec = not self._oge_secili_mi(item)
        item.setData(ROL_SECILI, sec)
        self._oge_stil_guncelle(item)
        if self._tek_dosya:
            self.secim_degisti.emit(self.secim_metni())
        self._bilgi_guncelle()

    def _sirayi_sifirla(self) -> None:
        if self._orijinal_ogeler:
            self._ogeleri_doldur(self._orijinal_ogeler)
            self.sira_degisti.emit()

    def _tum_secimi_kaldir(self) -> None:
        for i in range(self._liste.count()):
            item = self._liste.item(i)
            item.setData(ROL_SECILI, False)
            self._oge_stil_guncelle(item)
        if self._tek_dosya:
            self.secim_degisti.emit("")
        self._bilgi_guncelle()

    def _secili_ogeyi_kaldir(self) -> None:
        row = self._liste.currentRow()
        if row < 0:
            return
        self._liste.takeItem(row)
        self._bilgi_guncelle()
        if self._mod == self.MOD_SIRA:
            self.sira_degisti.emit()
        elif self._mod == self.MOD_SECIM and self._tek_dosya:
            self.secim_degisti.emit(self.secim_metni())

    def _sira_guncelle(self) -> None:
        if self._mod == self.MOD_SIRA:
            self._bilgi_guncelle()
            self.sira_degisti.emit()

    def _bilgi_guncelle(self) -> None:
        n = self._liste.count()
        if self._mod == self.MOD_SIRA:
            self._bilgi.setText(f"{n} sayfa — sürükleyerek sıralayın")
        elif self._mod == self.MOD_SECIM:
            sec = sum(1 for i in range(n) if self._oge_secili_mi(self._liste.item(i)))
            self._bilgi.setText(f"{n} sayfa — {sec} seçili")
        else:
            self._bilgi.setText(f"{n} sayfa ön izlemesi")

    def _hata(self, mesaj: str) -> None:
        self.temizle(f"Hata: {mesaj}")


# Geriye uyumluluk
PdfOnizlemePaneli = SayfaGalerisiPaneli
