"""Ortak araç paneli tabanı."""

from __future__ import annotations

import os
from typing import Any, Callable, Dict, Tuple

from core.sayfa_model import plana_cevir

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from gui.sayfa_galerisi import SayfaGalerisiPaneli
from gui.widgets.adim_kutusu import AdimKutusu
from gui.widgets.surukle_birak import SurukleBirakAlani
from gui.widgets.yardim_ipucu import YardimButonu

IslemPaketi = Tuple[Callable[..., Any], tuple, dict]


class TemelAracPaneli(QFrame):
    """Dosya seçimi, form alanları, ön izleme ve Başlat düğmesi."""

    islem_istendi = pyqtSignal(object)  # IslemPaketi

    def __init__(
        self,
        arac_baslik: str,
        kategori_baslik: str,
        aciklama: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("workspace")
        self._arac_baslik = arac_baslik
        self._kategori_baslik = kategori_baslik
        self._onizleme_alanlari: list[QLineEdit] = []

        kok = QVBoxLayout(self)
        kok.setContentsMargins(32, 28, 32, 20)
        kok.setSpacing(12)

        baslik = QLabel(arac_baslik)
        baslik.setObjectName("workspaceTitle")
        kok.addWidget(baslik)

        alt = QLabel(kategori_baslik)
        alt.setObjectName("workspaceCategory")
        kok.addWidget(alt)

        if aciklama:
            bilgi = QLabel(aciklama)
            bilgi.setObjectName("workspaceDesc")
            bilgi.setWordWrap(True)
            kok.addWidget(bilgi)

        orta = QHBoxLayout()
        orta.setSpacing(20)

        kaydir = QScrollArea()
        kaydir.setWidgetResizable(True)
        kaydir.setFrameShape(QFrame.Shape.NoFrame)
        kaydir.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        kaydir.setMinimumWidth(340)

        govde = QWidget()
        self._form = QFormLayout(govde)
        self._form.setContentsMargins(0, 8, 8, 8)
        self._form.setSpacing(12)
        self._form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        kaydir.setWidget(govde)
        orta.addWidget(kaydir, stretch=3)

        self._onizleme = SayfaGalerisiPaneli()
        self._onizleme.setMinimumWidth(300)
        orta.addWidget(self._onizleme, stretch=2)

        kok.addLayout(orta, stretch=1)

        self._durum_etiketi = QLabel("")
        self._durum_etiketi.setObjectName("panelStatus")
        self._durum_etiketi.setWordWrap(True)
        kok.addWidget(self._durum_etiketi)

        dugme_satir = QHBoxLayout()
        dugme_satir.addStretch()
        self._baslat = QPushButton("Başlat")
        self._baslat.setObjectName("primaryButton")
        self._baslat.setCursor(Qt.CursorShape.PointingHandCursor)
        self._baslat.setMinimumWidth(140)
        self._baslat.setMinimumHeight(40)
        self._baslat.clicked.connect(self._baslat_tiklandi)
        dugme_satir.addWidget(self._baslat)
        kok.addLayout(dugme_satir)

        self._form_olustur()

    def _form_olustur(self) -> None:
        """Alt sınıflar form alanlarını ekler."""

    def islem_hazirla(self) -> IslemPaketi:
        raise NotImplementedError

    def _baslat_tiklandi(self) -> None:
        try:
            self._durum_etiketi.setText("")
            paket = self.islem_hazirla()
            self.islem_istendi.emit(paket)
        except (ValueError, FileNotFoundError) as exc:
            self._durum_goster(str(exc), hata=True)

    def _durum_goster(self, metin: str, *, hata: bool = False) -> None:
        self._durum_etiketi.setProperty("error", hata)
        self._durum_etiketi.style().unpolish(self._durum_etiketi)
        self._durum_etiketi.style().polish(self._durum_etiketi)
        self._durum_etiketi.setText(metin)

    def islem_bitti(self, sonuc: Any) -> None:
        self._durum_goster(f"İşlem tamamlandı: {sonuc}", hata=False)
        self._cikti_onizle(sonuc)

    def islem_hatasi(self, mesaj: str) -> None:
        self._durum_goster(mesaj, hata=True)

    def _cikti_onizle(self, sonuc: Any) -> None:
        if isinstance(sonuc, str) and sonuc.lower().endswith(".pdf") and os.path.isfile(sonuc):
            self._onizleme.yukle_tek(sonuc)
        elif isinstance(sonuc, list):
            pdfler = [p for p in sonuc if isinstance(p, str) and p.lower().endswith(".pdf")]
            if pdfler:
                self._onizleme.yukle(pdfler[:4])

    # --- yardımcılar ---

    def _satir_ekle(self, etiket: str, widget: QWidget, *, yardim: str = "") -> None:
        if yardim:
            self._form.addRow(self._form_etiket(etiket, yardim), widget)
        else:
            self._form.addRow(etiket, widget)

    def _form_etiket(self, metin: str, yardim: str) -> QWidget:
        kutu = QWidget()
        satir = QHBoxLayout(kutu)
        satir.setContentsMargins(0, 0, 0, 0)
        satir.setSpacing(6)
        lb = QLabel(metin)
        satir.addWidget(lb)
        satir.addWidget(YardimButonu(yardim))
        satir.addStretch()
        return kutu

    def _sifre_alani(self, etiket: str, *, yardim: str = "") -> QLineEdit:
        alan = QLineEdit()
        alan.setEchoMode(QLineEdit.EchoMode.Password)
        alan.setPlaceholderText("Şifre…")
        self._satir_ekle(etiket, alan, yardim=yardim)
        return alan

    def _surukle_birak(
        self,
        etiket: str = "",
        *,
        coklu: bool = False,
        uzantilar: list[str] | None = None,
        baslik: str = "Dosyaları buraya sürükleyin",
        yardim: str = "",
    ) -> SurukleBirakAlani:
        alan = SurukleBirakAlani(coklu=coklu, uzantilar=uzantilar, baslik=baslik)
        self._satir_ekle(etiket or "Dosya", alan, yardim=yardim)
        return alan

    def _onizleme_gizle(self) -> None:
        self._onizleme.hide()

    def _onay_kutusu(self, etiket: str, *, varsayilan: bool = True, yardim: str = "") -> QCheckBox:
        kutu = QCheckBox(etiket)
        kutu.setChecked(varsayilan)
        self._satir_ekle("", kutu, yardim=yardim)
        return kutu

    def _pdf_onizle_guncelle(self, ham: str, *, coklu: bool = False) -> None:
        if coklu:
            yollar = [p.strip() for p in ham.split(";") if p.strip()]
        else:
            yol = ham.strip()
            yollar = [yol] if yol else []
        pdfler = [p for p in yollar if p.lower().endswith(".pdf") and os.path.isfile(p)]
        if pdfler:
            self._onizleme.yukle(pdfler)
        elif not ham.strip():
            self._onizleme.temizle()

    def _dosya_alani(
        self,
        etiket: str,
        *,
        coklu: bool = False,
        filtre: str = "PDF (*.pdf)",
        klasor: bool = False,
        onizle: bool = False,
        yardim: str = "",
    ) -> Tuple[QLineEdit, QPushButton]:
        satir = QHBoxLayout()
        alan = QLineEdit()
        alan.setReadOnly(True)
        alan.setPlaceholderText("Klasör seçin…" if klasor else "Dosya seçin…")
        btn = QPushButton("Gözat…")
        btn.setObjectName("secondaryButton")

        def sec() -> None:
            if klasor:
                yol = QFileDialog.getExistingDirectory(self, etiket)
                if yol:
                    alan.setText(yol)
            elif coklu:
                yollar, _ = QFileDialog.getOpenFileNames(self, etiket, "", filtre)
                if yollar:
                    alan.setText(";".join(yollar))
                    if onizle:
                        self._pdf_onizle_guncelle(alan.text(), coklu=True)
            else:
                yol, _ = QFileDialog.getOpenFileName(self, etiket, "", filtre)
                if yol:
                    alan.setText(yol)
                    if onizle:
                        self._pdf_onizle_guncelle(yol)

        btn.clicked.connect(sec)
        satir.addWidget(alan, stretch=1)
        satir.addWidget(btn)
        kutu = QWidget()
        kutu.setLayout(satir)
        self._satir_ekle(etiket, kutu, yardim=yardim)

        if onizle and not klasor:
            self._onizleme_alanlari.append(alan)

        return alan, btn

    def _kaydet_alani(
        self,
        etiket: str = "Çıktı dosyası",
        filtre: str = "PDF (*.pdf)",
        *,
        yardim: str = "",
    ) -> QLineEdit:
        satir = QHBoxLayout()
        alan = QLineEdit()
        alan.setPlaceholderText("Kayıt konumu…")
        btn = QPushButton("Kaydet…")
        btn.setObjectName("secondaryButton")

        def sec() -> None:
            yol, _ = QFileDialog.getSaveFileName(self, etiket, "", filtre)
            if yol:
                if filtre.startswith("PDF") and not yol.lower().endswith(".pdf"):
                    yol += ".pdf"
                alan.setText(yol)

        btn.clicked.connect(sec)
        satir.addWidget(alan, stretch=1)
        satir.addWidget(btn)
        kutu = QWidget()
        kutu.setLayout(satir)
        self._satir_ekle(etiket, kutu, yardim=yardim)
        return alan

    def _adim_kutusu(
        self,
        etiket: str,
        *,
        minimum: float = 0,
        maximum: float = 100,
        step: float = 1,
        value: float = 0,
        decimals: int = 0,
        suffix: str = "",
        yardim: str = "",
    ) -> AdimKutusu:
        kutu = AdimKutusu(
            minimum=minimum,
            maximum=maximum,
            step=step,
            value=value,
            decimals=decimals,
            suffix=suffix,
        )
        self._satir_ekle(etiket, kutu, yardim=yardim)
        return kutu

    def _onizleme_ayarla(self, mod: str) -> None:
        self._onizleme.set_mod(mod)

    def _onizleme_bagla_secim(self, alan: QLineEdit) -> None:
        """Ön izleme tıklaması ↔ sayfa metin kutusu senkronu."""
        self._onizleme_ayarla(SayfaGalerisiPaneli.MOD_SECIM)
        self._onizleme.secim_degisti.connect(alan.setText)
        alan.textChanged.connect(self._onizleme.secim_uygula)

    def _birlestirme_plani_kwargs(self) -> Dict[str, Any]:
        plan = self._onizleme.sayfa_plani()
        if plan:
            return {"sayfa_plani": plan}
        return {}

    def _sayfa_metni_veya_secim(
        self,
        alan: QLineEdit,
        *,
        zorunlu_mesaj: str,
    ) -> str:
        secim = self._onizleme.secim_metni().strip()
        metin = alan.text().strip()
        if secim:
            return secim
        if metin:
            return metin
        raise ValueError(zorunlu_mesaj)

    def _secim_plani_kwargs(self, kaynak: str) -> Dict[str, Any]:
        secili = self._onizleme.secili_refs()
        if secili:
            return {"sayfa_plani": plana_cevir(secili)}
        return {}

    @staticmethod
    def _metin_zorunlu(alan: QLineEdit, ad: str) -> str:
        deger = alan.text().strip()
        if not deger:
            raise ValueError(f"{ad} gerekli.")
        return deger

    @staticmethod
    def _coklu_dosya(alan: QLineEdit) -> list[str]:
        ham = alan.text().strip()
        if not ham:
            raise ValueError("En az bir dosya seçin.")
        return [p.strip() for p in ham.split(";") if p.strip()]
