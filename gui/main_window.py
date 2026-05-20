"""Ana pencere — yan menü ve çalışma alanları."""

from __future__ import annotations

from typing import Any, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from gui.panels.base import TemelAracPaneli
from gui.panels.registry import panel_olustur
from gui.sidebar import KATEGORILER, Sidebar
from gui.workers import PdfWorker, WorkerController


class AracCalismaAlani(QFrame):
    """Henüz paneli olmayan araçlar için yer tutucu."""

    def __init__(
        self,
        kategori_baslik: str,
        arac_baslik: str,
        api_uyarisi: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("workspace")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        baslik = QLabel(arac_baslik)
        baslik.setObjectName("workspaceTitle")
        layout.addWidget(baslik)

        alt = QLabel(kategori_baslik)
        alt.setObjectName("workspaceCategory")
        layout.addWidget(alt)

        if api_uyarisi:
            uyari = QLabel("Bu araç harici bir API anahtarı gerektirebilir.")
            uyari.setObjectName("apiWarning")
            layout.addWidget(uyari)

        yer_tutucu = QFrame()
        yer_tutucu.setObjectName("workspacePlaceholder")
        yer_layout = QVBoxLayout(yer_tutucu)
        bilgi = QLabel("Bu araç yakında eklenecek.")
        bilgi.setObjectName("placeholderText")
        bilgi.setAlignment(Qt.AlignmentFlag.AlignCenter)
        yer_layout.addStretch()
        yer_layout.addWidget(bilgi)
        yer_layout.addStretch()
        layout.addWidget(yer_tutucu, stretch=1)


class MainWindow(QMainWindow):
    """Ultimate PDF Suite ana penceresi."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Ultimate PDF Suite")
        self.setMinimumSize(1200, 760)
        self.resize(1360, 860)

        self._worker_yonetici = WorkerController()
        self._aktif_panel: Optional[TemelAracPaneli] = None
        self._kur_arayuz()
        self._durum_hazir()

    def _kur_arayuz(self) -> None:
        merkez = QWidget()
        self.setCentralWidget(merkez)

        kok = QHBoxLayout(merkez)
        kok.setContentsMargins(0, 0, 0, 0)
        kok.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.arac_secildi.connect(self._arac_degisti)
        kok.addWidget(self._sidebar)

        sag = QFrame()
        sag.setObjectName("mainContent")
        sag_layout = QVBoxLayout(sag)
        sag_layout.setContentsMargins(0, 0, 0, 0)
        sag_layout.setSpacing(0)

        self._yigin = QStackedWidget()
        self._yigin.setObjectName("workspaceStack")
        self._calisma_alanlarini_doldur()
        sag_layout.addWidget(self._yigin, stretch=1)

        alt_cubuk = QFrame()
        alt_cubuk.setObjectName("bottomBar")
        alt_layout = QHBoxLayout(alt_cubuk)
        alt_layout.setContentsMargins(24, 12, 24, 12)

        self._ilerleme = QProgressBar()
        self._ilerleme.setObjectName("mainProgress")
        self._ilerleme.setRange(0, 100)
        self._ilerleme.setValue(0)
        self._ilerleme.setTextVisible(True)
        self._ilerleme.setFormat("%p%")
        self._ilerleme.setFixedHeight(8)
        alt_layout.addWidget(self._ilerleme)

        sag_layout.addWidget(alt_cubuk)
        kok.addWidget(sag, stretch=1)

        self._durum = QStatusBar()
        self.setStatusBar(self._durum)

    def _calisma_alanlarini_doldur(self) -> None:
        for kategori in KATEGORILER:
            for arac in kategori.araclar:
                panel = panel_olustur(
                    arac.kimlik,
                    arac.baslik,
                    kategori.baslik,
                    arac.aciklama,
                )
                if panel is not None:
                    panel.islem_istendi.connect(self._islem_baslat)
                    alan: QWidget = panel
                else:
                    alan = AracCalismaAlani(
                        kategori_baslik=kategori.baslik,
                        arac_baslik=arac.baslik,
                        api_uyarisi=kategori.api_gerekebilir,
                    )
                self._yigin.addWidget(alan)

    def _mevcut_panel(self) -> Optional[TemelAracPaneli]:
        w = self._yigin.currentWidget()
        return w if isinstance(w, TemelAracPaneli) else None

    def _arac_degisti(self, kategori_indeks: int, arac_indeks: int) -> None:
        global_indeks = Sidebar.global_arac_indeksi(kategori_indeks, arac_indeks)
        self._yigin.setCurrentIndex(global_indeks)
        kategori = KATEGORILER[kategori_indeks]
        arac = kategori.araclar[arac_indeks]
        self._aktif_panel = self._mevcut_panel()
        self._durum.showMessage(f"{kategori.baslik} → {arac.baslik}")

    def _islem_baslat(self, paket: object) -> None:
        if self._worker_yonetici.calisiyor:
            QMessageBox.warning(self, "İşlem devam ediyor", "Mevcut işlem bitene kadar bekleyin.")
            return

        func, args, kwargs = paket  # type: ignore[misc]
        self._aktif_panel = self._mevcut_panel()
        self._baslat_dugmeleri(False)
        self._ilerleme.setValue(0)
        self._durum.showMessage("İşleniyor…")

        worker = PdfWorker(func, *args, **kwargs)
        worker.progress.connect(self.ilerleme_guncelle)
        worker.message.connect(self._durum.showMessage)
        worker.finished.connect(self._islem_bitti)
        worker.error.connect(self._islem_hata)
        self._worker_yonetici.baslat(worker)

    def _islem_bitti(self, sonuc: Any) -> None:
        self._ilerleme.setValue(100)
        self._durum.showMessage("İşlem tamamlandı.")
        self._baslat_dugmeleri(True)
        if self._aktif_panel:
            self._aktif_panel.islem_bitti(sonuc)
        if isinstance(sonuc, dict) or (isinstance(sonuc, str) and sonuc.endswith(".pkl")):
            return
        if isinstance(sonuc, str) and len(sonuc) > 500:
            QMessageBox.information(self, "Başarılı", "İşlem tamamlandı. Sonuç panelde gösteriliyor.")
        else:
            QMessageBox.information(self, "Başarılı", f"İşlem tamamlandı.\n\n{sonuc}")

    def _islem_hata(self, mesaj: str) -> None:
        self._ilerleme.setValue(0)
        self._durum.showMessage("Hata oluştu.")
        self._baslat_dugmeleri(True)
        if self._aktif_panel:
            self._aktif_panel.islem_hatasi(mesaj)
        QMessageBox.critical(self, "Hata", mesaj)

    def _baslat_dugmeleri(self, aktif: bool) -> None:
        panel = self._aktif_panel or self._mevcut_panel()
        if panel:
            panel._baslat.setEnabled(aktif)

    def _durum_hazir(self) -> None:
        self._ilerleme.setValue(0)
        self._durum.showMessage("Hazır")

    def ilerleme_guncelle(self, yuzde: int) -> None:
        self._ilerleme.setValue(yuzde)

    @property
    def worker_yonetici(self) -> WorkerController:
        return self._worker_yonetici
