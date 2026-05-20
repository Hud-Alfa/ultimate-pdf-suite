"""Sol yan menü — katlanabilir kategoriler ve alt araçlar."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class AracTanimi:
    """Tek bir araç satırı."""

    kimlik: str
    baslik: str
    aciklama: str = ""


@dataclass(frozen=True)
class KategoriTanimi:
    """Yan menüde bir kategori ve alt araçları."""

    kimlik: str
    baslik: str
    ikon: str
    araclar: List[AracTanimi]
    api_gerekebilir: bool = False


KATEGORILER: List[KategoriTanimi] = [
    KategoriTanimi(
        kimlik="sayfa_yonetimi",
        baslik="Sayfa Yönetimi",
        ikon="📄",
        araclar=[
            AracTanimi("birlestir", "Birleştir", "Birden fazla PDF'i tek dosyada birleştir"),
            AracTanimi("ayir", "Ayır", "PDF'i ayrı dosyalara böl"),
            AracTanimi("sil", "Sil", "Seçilen sayfaları kaldır"),
            AracTanimi("ayikla", "Ayıkla", "Belirli sayfaları çıkar"),
        ],
    ),
    KategoriTanimi(
        kimlik="duzenleme",
        baslik="Düzenleme",
        ikon="✏️",
        araclar=[
            AracTanimi("kirp", "Kırp"),
            AracTanimi("dondur", "Döndür"),
            AracTanimi("filigran", "Filigran"),
            AracTanimi("numara", "Numara"),
            AracTanimi("formlar", "Formlar"),
            AracTanimi("duzelt", "Düzelt"),
            AracTanimi("duzenle", "Düzenle"),
        ],
    ),
    KategoriTanimi(
        kimlik="guvenlik_opt",
        baslik="Güvenlik ve Optimizasyon",
        ikon="🔒",
        araclar=[
            AracTanimi("koru", "Koru"),
            AracTanimi("kilit_ac", "Kilit Aç"),
            AracTanimi("imzala", "İmzala"),
            AracTanimi("kucult", "Küçült"),
            AracTanimi("iyilestir", "İyileştir"),
            AracTanimi("onar", "Onar"),
        ],
    ),
    KategoriTanimi(
        kimlik="pdf_e_donustur",
        baslik="PDF'e Dönüştür",
        ikon="➡️",
        araclar=[
            AracTanimi("word_to_pdf", "Word", "DOC/DOCX → PDF"),
            AracTanimi("excel_to_pdf", "Excel", "XLS/XLSX → PDF"),
            AracTanimi("ppt_to_pdf", "PPT", "PPT/PPTX → PDF"),
            AracTanimi("jpg_to_pdf", "JPG", "Görseller → tek PDF"),
            AracTanimi("html_to_pdf", "HTML", "HTML → PDF (wkhtmltopdf)"),
            AracTanimi("tara", "Tara", "Tarayıcıdan doğrudan PDF"),
            AracTanimi("genel", "Genel", "Desteklenen herhangi bir format"),
        ],
    ),
    KategoriTanimi(
        kimlik="pdf_den_donustur",
        baslik="PDF'den Dönüştür & OCR",
        ikon="⬅️",
        araclar=[
            AracTanimi("pdf_to_jpg", "JPG / PNG", "Sayfa sayfa görsel"),
            AracTanimi("pdf_to_word", "Word", "PDF → DOCX"),
            AracTanimi("pdf_to_excel", "Excel", "Tablolar → XLSX"),
            AracTanimi("pdf_to_ppt", "PPT", "Sayfa → slayt"),
            AracTanimi("pdf_a", "PDF/A", "Arşiv standardı"),
            AracTanimi("genel_from", "Genel", "Hedef format seç"),
            AracTanimi("ocr", "OCR", "Aranabilir PDF"),
        ],
    ),
    KategoriTanimi(
        kimlik="akilli_araclar",
        baslik="Akıllı Araçlar",
        ikon="🤖",
        api_gerekebilir=True,
        araclar=[
            AracTanimi("ai_ozet", "Yapay Zeka Özet"),
            AracTanimi("ceviri", "Çeviri"),
            AracTanimi("intelligence", "Intelligence"),
            AracTanimi("karsilastirma", "Karşılaştırma"),
        ],
    ),
]


class KategoriBolumu(QFrame):
    """Tek kategori: tıklanabilir başlık + gizlenebilir araç listesi."""

    baslik_tiklandi = pyqtSignal(int)  # kategori_indeks
    arac_tiklandi = pyqtSignal(int, int)  # kategori_indeks, arac_indeks

    def __init__(
        self,
        kategori: KategoriTanimi,
        kategori_indeks: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._kategori_indeks = kategori_indeks
        self._kategori = kategori
        self._acik = False

        self.setObjectName("categorySection")
        kok = QVBoxLayout(self)
        kok.setContentsMargins(0, 0, 0, 0)
        kok.setSpacing(0)

        ok_sayisi = len(kategori.araclar)
        self._baslik_dugme = QPushButton()
        self._baslik_dugme.setObjectName("categoryToggle")
        self._baslik_dugme.setCursor(Qt.CursorShape.PointingHandCursor)
        self._baslik_dugme.setCheckable(False)
        self._baslik_dugme.setToolTip(
            f"{kategori.baslik} — tıklayarak araç listesini aç/kapat"
        )
        self._baslik_metnini_guncelle(ok_sayisi)
        self._baslik_dugme.clicked.connect(self._baslik_tiklandi)
        kok.addWidget(self._baslik_dugme)

        self._arac_kapsayici = QFrame()
        self._arac_kapsayici.setObjectName("categoryTools")
        arac_layout = QVBoxLayout(self._arac_kapsayici)
        arac_layout.setContentsMargins(4, 2, 4, 6)
        arac_layout.setSpacing(2)

        self._arac_dugmeleri: List[QPushButton] = []
        for a_idx, arac in enumerate(kategori.araclar):
            dugme = QPushButton(arac.baslik)
            dugme.setObjectName("toolButton")
            dugme.setCheckable(True)
            dugme.setCursor(Qt.CursorShape.PointingHandCursor)
            dugme.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            dugme.setToolTip(arac.aciklama or arac.baslik)
            dugme.clicked.connect(
                lambda _c=False, k=kategori_indeks, a=a_idx: self.arac_tiklandi.emit(k, a)
            )
            self._arac_dugmeleri.append(dugme)
            arac_layout.addWidget(dugme)

        if kategori.api_gerekebilir:
            uyari = QLabel("API gerektirebilir")
            uyari.setObjectName("apiBadge")
            arac_layout.addWidget(uyari)

        kok.addWidget(self._arac_kapsayici)
        self._gorunurluk_ayarla(False)

    @property
    def kategori_indeks(self) -> int:
        return self._kategori_indeks

    @property
    def acik_mi(self) -> bool:
        return self._acik

    def _baslik_metnini_guncelle(self, arac_sayisi: int) -> None:
        ok = "▼" if self._acik else "▶"
        self._baslik_dugme.setText(
            f"  {ok}  {self._kategori.ikon}  {self._kategori.baslik}  ({arac_sayisi})"
        )

    def _baslik_tiklandi(self) -> None:
        self.toggle()
        self.baslik_tiklandi.emit(self._kategori_indeks)

    def toggle(self) -> None:
        self._gorunurluk_ayarla(not self._acik)

    def ac(self) -> None:
        if not self._acik:
            self._gorunurluk_ayarla(True)

    def kapat(self) -> None:
        if self._acik:
            self._gorunurluk_ayarla(False)

    def _gorunurluk_ayarla(self, acik: bool) -> None:
        self._acik = acik
        self._arac_kapsayici.setVisible(acik)
        self._baslik_dugme.setProperty("expanded", acik)
        self._baslik_dugme.style().unpolish(self._baslik_dugme)
        self._baslik_dugme.style().polish(self._baslik_dugme)
        self._baslik_metnini_guncelle(len(self._kategori.araclar))

    def arac_sec(self, arac_indeks: int) -> None:
        for a_idx, dugme in enumerate(self._arac_dugmeleri):
            dugme.setChecked(arac_indeks >= 0 and a_idx == arac_indeks)


class Sidebar(QFrame):
    """Modern yan menü; katlanabilir kategoriler ve araç seçimi."""

    arac_secildi = pyqtSignal(int, int)  # kategori_indeks, arac_indeks

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(280)

        self._bolumler: List[KategoriBolumu] = []
        self._aktif_kategori = 0
        self._aktif_arac = 0
        self._tek_acik_mod = True  # bir kategori açılınca diğerleri kapanır

        self._kur()

    def _kur(self) -> None:
        ana = QVBoxLayout(self)
        ana.setContentsMargins(0, 0, 0, 0)
        ana.setSpacing(0)

        baslik_alani = QFrame()
        baslik_alani.setObjectName("sidebarHeader")
        baslik_layout = QVBoxLayout(baslik_alani)
        baslik_layout.setContentsMargins(20, 24, 20, 12)

        logo = QLabel("Ultimate PDF Suite")
        logo.setObjectName("appTitle")
        alt = QLabel("Sınırsız · Ücretsiz · Hızlı")
        alt.setObjectName("appSubtitle")
        baslik_layout.addWidget(logo)
        baslik_layout.addWidget(alt)

        ipucu = QLabel("Kategorilere tıklayarak listeyi açıp kapatabilirsiniz")
        ipucu.setObjectName("sidebarHint")
        ipucu.setWordWrap(True)
        baslik_layout.addWidget(ipucu)
        ana.addWidget(baslik_alani)

        kaydir = QScrollArea()
        kaydir.setWidgetResizable(True)
        kaydir.setFrameShape(QFrame.Shape.NoFrame)
        kaydir.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        icerik = QWidget()
        icerik.setObjectName("sidebarScrollContent")
        self._menu_layout = QVBoxLayout(icerik)
        self._menu_layout.setContentsMargins(8, 4, 8, 24)
        self._menu_layout.setSpacing(6)

        for k_idx, kategori in enumerate(KATEGORILER):
            bolum = KategoriBolumu(kategori, k_idx)
            bolum.arac_tiklandi.connect(self._arac_tiklandi)
            bolum.baslik_tiklandi.connect(self._kategori_baslik_islendi)
            self._bolumler.append(bolum)
            self._menu_layout.addWidget(bolum)

        self._menu_layout.addStretch()
        kaydir.setWidget(icerik)
        ana.addWidget(kaydir, stretch=1)

        self._bolum_ac(0)
        self._guncelle_secim(0, 0)

    def _bolum_ac(self, kategori_indeks: int) -> None:
        if self._tek_acik_mod:
            for k_idx, bolum in enumerate(self._bolumler):
                if k_idx == kategori_indeks:
                    bolum.ac()
                else:
                    bolum.kapat()
        else:
            self._bolumler[kategori_indeks].ac()

    def _kategori_baslik_islendi(self, kategori_indeks: int) -> None:
        """Başlığa tıklanınca açılan bölüm tek kalır; kapanınca diğerleri etkilenmez."""
        if not self._tek_acik_mod:
            return
        if self._bolumler[kategori_indeks].acik_mi:
            for k_idx, bolum in enumerate(self._bolumler):
                if k_idx != kategori_indeks:
                    bolum.kapat()

    def _arac_tiklandi(self, kategori_indeks: int, arac_indeks: int) -> None:
        self._bolum_ac(kategori_indeks)
        self._guncelle_secim(kategori_indeks, arac_indeks)
        self.arac_secildi.emit(kategori_indeks, arac_indeks)

    def _guncelle_secim(self, kategori_indeks: int, arac_indeks: int) -> None:
        self._aktif_kategori = kategori_indeks
        self._aktif_arac = arac_indeks
        for k_idx, bolum in enumerate(self._bolumler):
            bolum.arac_sec(arac_indeks if k_idx == kategori_indeks else -1)

    @staticmethod
    def global_arac_indeksi(kategori_indeks: int, arac_indeks: int) -> int:
        """Tüm araçlar için düz QStackedWidget indeksi."""
        indeks = 0
        for k_idx, kategori in enumerate(KATEGORILER):
            if k_idx == kategori_indeks:
                return indeks + arac_indeks
            indeks += len(kategori.araclar)
        return 0

    @staticmethod
    def toplam_arac_sayisi() -> int:
        return sum(len(k.araclar) for k in KATEGORILER)
