"""Düzenleme panelleri."""

from __future__ import annotations

from PyQt6.QtWidgets import QComboBox, QLineEdit

from modules import modification as mod
from gui.panels.base import TemelAracPaneli
from gui.sayfa_galerisi import SayfaGalerisiPaneli


def _sayfa_alani(panel: TemelAracPaneli, etiket: str = "Sayfalar (boş=tümü)") -> QLineEdit:
    alan = QLineEdit()
    alan.setPlaceholderText("ör. 1,3,5-7 veya boş bırakın")
    panel._satir_ekle(etiket, alan)
    return alan


class KirpPaneli(TemelAracPaneli):
    def __init__(self, **kw):
        super().__init__(
            "Kırp",
            "Düzenleme",
            "Kenar boşluklarını milimetre cinsinden kırpar. Hedef sayfaları ön izlemeden seçebilirsiniz.",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._kaynak, _ = self._dosya_alani("Kaynak PDF", onizle=True)
        self._ust = self._adim_kutusu("Üst (mm)", maximum=200, step=1, value=0, decimals=1, suffix=" mm")
        self._alt = self._adim_kutusu("Alt (mm)", maximum=200, step=1, value=0, decimals=1, suffix=" mm")
        self._sol = self._adim_kutusu("Sol (mm)", maximum=200, step=1, value=0, decimals=1, suffix=" mm")
        self._sag = self._adim_kutusu("Sağ (mm)", maximum=200, step=1, value=0, decimals=1, suffix=" mm")
        self._sayfalar = _sayfa_alani(self)
        self._cikti = self._kaydet_alani("Çıktı PDF")
        self._onizleme_bagla_secim(self._sayfalar)

    def islem_hazirla(self):
        sayfa = self._sayfalar.text().strip()
        sec = self._onizleme.secim_metni().strip()
        return (
            mod.kirp,
            [self._metin_zorunlu(self._kaynak, "Kaynak"), self._metin_zorunlu(self._cikti, "Çıktı")],
            {
                "ust_mm": self._ust.value(),
                "alt_mm": self._alt.value(),
                "sol_mm": self._sol.value(),
                "sag_mm": self._sag.value(),
                "sayfa_metni": sec or sayfa,
            },
        )


class DondurPaneli(TemelAracPaneli):
    def __init__(self, **kw):
        super().__init__(
            "Döndür",
            "Düzenleme",
            "Seçili veya tüm sayfaları 90°, 180° veya 270° döndürür.",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._kaynak, _ = self._dosya_alani("Kaynak PDF", onizle=True)
        self._aci = QComboBox()
        self._aci.addItems(["90", "180", "270"])
        self._satir_ekle("Döndürme açısı", self._aci)
        self._sayfalar = _sayfa_alani(self)
        self._cikti = self._kaydet_alani("Çıktı PDF")
        self._onizleme_bagla_secim(self._sayfalar)

    def islem_hazirla(self):
        sayfa = self._sayfalar.text().strip()
        sec = self._onizleme.secim_metni().strip()
        return (
            mod.dondur,
            [
                self._metin_zorunlu(self._kaynak, "Kaynak"),
                self._metin_zorunlu(self._cikti, "Çıktı"),
                int(self._aci.currentText()),
            ],
            {"sayfa_metni": sec or sayfa},
        )


class FiligranPaneli(TemelAracPaneli):
    def __init__(self, **kw):
        super().__init__(
            "Filigran",
            "Düzenleme",
            "Metin veya saydam PNG logosu ekler.",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._kaynak, _ = self._dosya_alani("Kaynak PDF", onizle=True)
        self._metin = QLineEdit()
        self._metin.setPlaceholderText("ör. GİZLİ — boş bırakılabilir")
        self._satir_ekle("Filigran metni", self._metin)
        self._logo, _ = self._dosya_alani("PNG logo (isteğe bağlı)", filtre="PNG (*.png)")
        self._saydam = self._adim_kutusu(
            "Saydamlık",
            minimum=0.05,
            maximum=1.0,
            step=0.05,
            value=0.25,
            decimals=2,
        )
        self._sayfalar = _sayfa_alani(self)
        self._cikti = self._kaydet_alani("Çıktı PDF")
        self._onizleme_bagla_secim(self._sayfalar)

    def islem_hazirla(self):
        sayfa = self._sayfalar.text().strip()
        sec = self._onizleme.secim_metni().strip()
        return (
            mod.filigran_ekle,
            [self._metin_zorunlu(self._kaynak, "Kaynak"), self._metin_zorunlu(self._cikti, "Çıktı")],
            {
                "metin": self._metin.text().strip(),
                "logo_yolu": self._logo.text().strip(),
                "saydam": self._saydam.value(),
                "sayfa_metni": sec or sayfa,
            },
        )


class NumaraPaneli(TemelAracPaneli):
    def __init__(self, **kw):
        super().__init__(
            "Numara",
            "Düzenleme",
            "Alt köşeye sayfa numarası basar.",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._kaynak, _ = self._dosya_alani("Kaynak PDF", onizle=True)
        self._konum = QComboBox()
        self._konum.addItem("Alt orta", "alt_orta")
        self._konum.addItem("Alt sol", "alt_sol")
        self._konum.addItem("Alt sağ", "alt_sag")
        self._satir_ekle("Konum", self._konum)
        self._sayfalar = _sayfa_alani(self)
        self._cikti = self._kaydet_alani("Çıktı PDF")
        self._onizleme_bagla_secim(self._sayfalar)

    def islem_hazirla(self):
        sayfa = self._sayfalar.text().strip()
        sec = self._onizleme.secim_metni().strip()
        return (
            mod.sayfa_numarasi,
            [self._metin_zorunlu(self._kaynak, "Kaynak"), self._metin_zorunlu(self._cikti, "Çıktı")],
            {
                "konum": self._konum.currentData(),
                "sayfa_metni": sec or sayfa,
            },
        )


class FormlarPaneli(TemelAracPaneli):
    def __init__(self, **kw):
        super().__init__(
            "Formlar",
            "Düzenleme",
            "Her satırda AlanAdi=Değer yazarak interaktif form alanlarını doldurur.",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._kaynak, _ = self._dosya_alani("Kaynak PDF", onizle=True)
        from PyQt6.QtWidgets import QTextEdit

        self._alanlar = QTextEdit()
        self._alanlar.setPlaceholderText("Ad=Soyad\nEposta=ornek@mail.com")
        self._alanlar.setMaximumHeight(120)
        self._satir_ekle("Alan değerleri", self._alanlar)
        self._cikti = self._kaydet_alani("Çıktı PDF")

    def islem_hazirla(self):
        return (
            mod.formlar_isle,
            [self._metin_zorunlu(self._kaynak, "Kaynak"), self._metin_zorunlu(self._cikti, "Çıktı")],
            {"alan_metni": self._alanlar.toPlainText()},
        )


class DuzeltPaneli(TemelAracPaneli):
    def __init__(self, **kw):
        super().__init__(
            "Düzelt",
            "Düzenleme",
            "Formları ve ek açıklamaları düzleştirir (flatten).",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._kaynak, _ = self._dosya_alani("Kaynak PDF", onizle=True)
        self._cikti = self._kaydet_alani("Çıktı PDF")

    def islem_hazirla(self):
        return (
            mod.duzelt,
            [self._metin_zorunlu(self._kaynak, "Kaynak"), self._metin_zorunlu(self._cikti, "Çıktı")],
            {},
        )


class DuzenlePaneli(TemelAracPaneli):
    def __init__(self, **kw):
        super().__init__(
            "Düzenle",
            "Düzenleme",
            "İlk hedef sayfaya metin veya şekil ekler.",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._kaynak, _ = self._dosya_alani("Kaynak PDF", onizle=True)
        self._tur = QComboBox()
        self._tur.addItem("Metin", "metin")
        self._tur.addItem("Dikdörtgen", "dikdortgen")
        self._tur.addItem("Daire", "daire")
        self._satir_ekle("Tür", self._tur)
        self._metin = QLineEdit("Örnek metin")
        self._satir_ekle("Metin", self._metin)
        self._x = self._adim_kutusu("X (pt)", maximum=5000, step=5, value=72, decimals=0)
        self._y = self._adim_kutusu("Y (pt)", maximum=5000, step=5, value=72, decimals=0)
        self._gen = self._adim_kutusu("Genişlik (pt)", minimum=10, maximum=5000, step=10, value=200, decimals=0)
        self._yuk = self._adim_kutusu("Yükseklik (pt)", minimum=10, maximum=5000, step=5, value=40, decimals=0)
        self._sayfalar = _sayfa_alani(self, "Hedef sayfa (boş=1)")
        self._cikti = self._kaydet_alani("Çıktı PDF")

    def islem_hazirla(self):
        return (
            mod.duzenle,
            [self._metin_zorunlu(self._kaynak, "Kaynak"), self._metin_zorunlu(self._cikti, "Çıktı")],
            {
                "tur": self._tur.currentData(),
                "metin": self._metin.text(),
                "x": self._x.value(),
                "y": self._y.value(),
                "genislik": self._gen.value(),
                "yukseklik": self._yuk.value(),
                "sayfa_metni": self._sayfalar.text().strip() or "1",
            },
        )
