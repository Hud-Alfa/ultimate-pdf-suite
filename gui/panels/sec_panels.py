"""Güvenlik ve optimizasyon panelleri."""

from __future__ import annotations

from PyQt6.QtWidgets import QComboBox

from modules import security_opt as sec
from gui.panels.base import TemelAracPaneli
from gui.sayfa_galerisi import SayfaGalerisiPaneli

Y_KAYNAK = (
    "İşlem yapılacak PDF dosyasını seçin. Sağdaki galeride sayfaları ön izleyebilirsiniz."
)
Y_CIKTI = "Sonucun kaydedileceği dosya yolunu belirleyin."


class KoruPaneli(TemelAracPaneli):
    def __init__(self, **kw):
        super().__init__(
            "Koru",
            "Güvenlik ve Optimizasyon",
            "PDF'i AES-256 şifre ile korur. Şifreyi güvenli bir yerde saklayın.",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._kaynak, _ = self._dosya_alani("Kaynak PDF", onizle=True, yardim=Y_KAYNAK)
        self._sifre = self._sifre_alani(
            "Belge şifresi",
            yardim="Açmak için gereken şifre. En az 4 karakter. Bu uygulama şifre kırmaz.",
        )
        self._tekrar = self._sifre_alani(
            "Şifre tekrar",
            yardim="Yazım hatasını önlemek için şifreyi tekrar girin.",
        )
        self._cikti = self._kaydet_alani("Korumalı PDF", yardim=Y_CIKTI)
        self._onizleme_ayarla(SayfaGalerisiPaneli.MOD_IZLEME)

    def islem_hazirla(self):
        s1 = self._metin_zorunlu(self._sifre, "Şifre")
        s2 = self._tekrar.text().strip()
        if s1 != s2:
            raise ValueError("Şifreler eşleşmiyor.")
        return (
            sec.koru,
            [
                self._metin_zorunlu(self._kaynak, "Kaynak"),
                self._metin_zorunlu(self._cikti, "Çıktı"),
                s1,
            ],
            {},
        )


class KilitAcPaneli(TemelAracPaneli):
    def __init__(self, **kw):
        super().__init__(
            "Kilit Aç",
            "Güvenlik ve Optimizasyon",
            "Şifresini bildiğiniz korumalı PDF'in kilidini kaldırır. Şifre kırma yapılmaz.",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._kaynak, _ = self._dosya_alani("Korumalı PDF", onizle=True, yardim=Y_KAYNAK)
        self._sifre = self._sifre_alani(
            "Mevcut şifre",
            yardim=(
                "Dosyayı açmak için kullandığınız şifre. Yanlışsa işlem başarısız olur. "
                "Bu uygulama şifre kırmaz veya tahmin etmez — yalnızca doğru şifreyle "
                "korumayı kaldırır."
            ),
        )
        self._cikti = self._kaydet_alani("Şifresiz PDF", yardim=Y_CIKTI)
        self._onizleme_ayarla(SayfaGalerisiPaneli.MOD_IZLEME)

    def islem_hazirla(self):
        return (
            sec.kilit_ac,
            [
                self._metin_zorunlu(self._kaynak, "Kaynak"),
                self._metin_zorunlu(self._cikti, "Çıktı"),
                self._metin_zorunlu(self._sifre, "Şifre"),
            ],
            {},
        )


class ImzalaPaneli(TemelAracPaneli):
    def __init__(self, **kw):
        super().__init__(
            "İmzala",
            "Güvenlik ve Optimizasyon",
            "PNG/JPG imza görselini PDF'e damga olarak ekler (yasal e-imza sertifikası değildir).",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._kaynak, _ = self._dosya_alani("Kaynak PDF", onizle=True, yardim=Y_KAYNAK)
        self._imza, _ = self._dosya_alani(
            "İmza görseli",
            filtre="Görsel (*.png *.jpg *.jpeg)",
            yardim="Şeffaf arka planlı PNG önerilir. Görsel sayfaya damga olarak basılır.",
        )
        self._konum = QComboBox()
        self._konum.addItem("Son sayfa", True)
        self._konum.addItem("Belirli sayfa", False)
        self._satir_ekle(
            "Konum",
            self._konum,
            yardim="İmzanın ekleneceği sayfa. «Belirli sayfa» için aşağıdaki numarayı girin.",
        )
        self._sayfa_no = self._adim_kutusu(
            "Sayfa no",
            minimum=1,
            maximum=9999,
            step=1,
            value=1,
            decimals=0,
            yardim="1 = ilk sayfa. Yalnızca «Belirli sayfa» seçiliyken kullanılır.",
        )
        self._x = self._adim_kutusu("X (pt)", maximum=2000, step=10, value=72, yardim="Soldan uzaklık (nokta).")
        self._y = self._adim_kutusu("Y (pt)", maximum=2000, step=10, value=650, yardim="Üstten uzaklık (nokta).")
        self._gen = self._adim_kutusu(
            "Genişlik (pt)", minimum=30, maximum=400, step=10, value=150,
            yardim="İmza görselinin genişliği.",
        )
        self._yuk = self._adim_kutusu(
            "Yükseklik (pt)", minimum=20, maximum=300, step=5, value=60,
            yardim="İmza görselinin yüksekliği.",
        )
        self._cikti = self._kaydet_alani("İmzalı PDF", yardim=Y_CIKTI)
        self._onizleme_ayarla(SayfaGalerisiPaneli.MOD_IZLEME)

    def islem_hazirla(self):
        return (
            sec.imzala,
            [self._metin_zorunlu(self._kaynak, "Kaynak"), self._metin_zorunlu(self._cikti, "Çıktı")],
            {
                "imza_yolu": self._metin_zorunlu(self._imza, "İmza görseli"),
                "son_sayfa": self._konum.currentData(),
                "sayfa_no": int(self._sayfa_no.value()),
                "x": self._x.value(),
                "y": self._y.value(),
                "genislik": self._gen.value(),
                "yukseklik": self._yuk.value(),
            },
        )


class KucultPaneli(TemelAracPaneli):
    def __init__(self, **kw):
        super().__init__(
            "Küçült",
            "Güvenlik ve Optimizasyon",
            "Dosya boyutunu düşürür: metadata temizliği ve görsel sıkıştırma.",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._kaynak, _ = self._dosya_alani("Kaynak PDF", onizle=True, yardim=Y_KAYNAK)
        self._dpi = self._adim_kutusu(
            "Hedef DPI",
            minimum=36,
            maximum=300,
            step=12,
            value=96,
            decimals=0,
            yardim="Düşük DPI = küçük dosya, daha düşük görüntü kalitesi. 72–120 arası önerilir.",
        )
        self._meta = self._onay_kutusu(
            "Gereksiz metadata'yı sil",
            varsayilan=True,
            yardim="Yazar, anahtar kelime gibi gizli bilgileri kaldırır.",
        )
        self._cikti = self._kaydet_alani("Küçültülmüş PDF", yardim=Y_CIKTI)
        self._onizleme_ayarla(SayfaGalerisiPaneli.MOD_IZLEME)

    def islem_hazirla(self):
        return (
            sec.kucult,
            [self._metin_zorunlu(self._kaynak, "Kaynak"), self._metin_zorunlu(self._cikti, "Çıktı")],
            {
                "dpi_hedef": int(self._dpi.value()),
                "metadata_temizle": self._meta.isChecked(),
            },
        )


class IyilestirPaneli(TemelAracPaneli):
    def __init__(self, **kw):
        super().__init__(
            "İyileştir",
            "Güvenlik ve Optimizasyon",
            "Soluk taranmış belgelerin kontrastını artırır ve netleştirir.",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._kaynak, _ = self._dosya_alani("Kaynak PDF", onizle=True, yardim=Y_KAYNAK)
        self._kontrast = self._adim_kutusu(
            "Kontrast",
            minimum=1.0,
            maximum=2.5,
            step=0.05,
            value=1.35,
            decimals=2,
            yardim="1 = değişiklik yok. 1.3–1.5 taranmış belgeler için iyi başlangıç.",
        )
        self._parlaklik = self._adim_kutusu(
            "Parlaklık",
            minimum=0.8,
            maximum=1.5,
            step=0.05,
            value=1.05,
            decimals=2,
            yardim="Çok yükseltmek beyaz lekeler oluşturabilir.",
        )
        self._cikti = self._kaydet_alani("İyileştirilmiş PDF", yardim=Y_CIKTI)
        self._onizleme_ayarla(SayfaGalerisiPaneli.MOD_IZLEME)

    def islem_hazirla(self):
        return (
            sec.iyilestir,
            [self._metin_zorunlu(self._kaynak, "Kaynak"), self._metin_zorunlu(self._cikti, "Çıktı")],
            {
                "kontrast": self._kontrast.value(),
                "parlaklik": self._parlaklik.value(),
            },
        )


class OnarPaneli(TemelAracPaneli):
    def __init__(self, **kw):
        super().__init__(
            "Onar",
            "Güvenlik ve Optimizasyon",
            "XREF hatası veya bozuk yapılı PDF'leri yeniden kaydederek onarmayı dener.",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._kaynak, _ = self._dosya_alani(
            "Bozuk PDF",
            onizle=True,
            yardim="Açılmayan veya «XREF» hatası veren dosya. Ağır hasarda onarım mümkün olmayabilir.",
        )
        self._cikti = self._kaydet_alani("Onarılmış PDF", yardim=Y_CIKTI)
        self._onizleme_ayarla(SayfaGalerisiPaneli.MOD_IZLEME)

    def islem_hazirla(self):
        return (
            sec.onar,
            [self._metin_zorunlu(self._kaynak, "Kaynak"), self._metin_zorunlu(self._cikti, "Çıktı")],
            {},
        )
