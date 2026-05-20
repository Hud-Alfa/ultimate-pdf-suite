"""PDF'e dönüştür panelleri."""

from __future__ import annotations

from PyQt6.QtWidgets import QLineEdit

from modules import convert_to as cnv
from gui.panels.base import TemelAracPaneli
from gui.sayfa_galerisi import SayfaGalerisiPaneli

Y_CIKTI = "Oluşacak PDF dosyasının kayıt yolu."
Y_SURUKLE = "Dosyayı buraya sürükleyip bırakabilir veya Gözat ile seçebilirsiniz."


class _DonusturTemel(TemelAracPaneli):
    """Dönüştürme panelleri — ön izleme çıktıda dolar."""

    def _kur_donustur(self) -> None:
        self._onizleme_ayarla(SayfaGalerisiPaneli.MOD_IZLEME)


class WordPaneli(_DonusturTemel):
    def __init__(self, **kw):
        super().__init__(
            "Word",
            "PDF'e Dönüştür",
            "Word belgelerini PDF'e çevirir (Office veya LibreOffice gerekir).",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._drop = self._surukle_birak(
            "Kaynak",
            uzantilar=[".doc", ".docx", ".rtf", ".odt"],
            baslik="Word dosyasını sürükleyin",
            yardim=Y_SURUKLE + " En iyi sonuç için yüklü Microsoft Word.",
        )
        self._kaynak, _ = self._dosya_alani(
            "veya dosya seç",
            filtre="Word (*.doc *.docx *.rtf *.odt)",
            yardim="Klasik dosya seçici.",
        )
        self._drop.dosyalar_degisti.connect(lambda p: self._kaynak.setText(p[0] if p else ""))
        self._cikti = self._kaydet_alani(yardim=Y_CIKTI)
        self._kur_donustur()

    def islem_hazirla(self):
        kaynak = self._kaynak.text().strip() or (self._drop.yollar()[0] if self._drop.yollar() else "")
        if not kaynak:
            raise ValueError("Word dosyası seçin.")
        return (cnv.word_to_pdf, [kaynak, self._metin_zorunlu(self._cikti, "Çıktı")], {})


class ExcelPaneli(_DonusturTemel):
    def __init__(self, **kw):
        super().__init__(
            "Excel",
            "PDF'e Dönüştür",
            "Excel tablolarını PDF'e çevirir.",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._drop = self._surukle_birak(
            "Kaynak",
            uzantilar=[".xls", ".xlsx", ".csv", ".ods"],
            baslik="Excel dosyasını sürükleyin",
            yardim=Y_SURUKLE,
        )
        self._kaynak, _ = self._dosya_alani(
            "veya dosya seç",
            filtre="Excel (*.xls *.xlsx *.csv *.ods)",
        )
        self._drop.dosyalar_degisti.connect(lambda p: self._kaynak.setText(p[0] if p else ""))
        self._cikti = self._kaydet_alani(yardim=Y_CIKTI)
        self._kur_donustur()

    def islem_hazirla(self):
        kaynak = self._kaynak.text().strip() or (self._drop.yollar()[0] if self._drop.yollar() else "")
        if not kaynak:
            raise ValueError("Excel dosyası seçin.")
        return (cnv.excel_to_pdf, [kaynak, self._metin_zorunlu(self._cikti, "Çıktı")], {})


class PptPaneli(_DonusturTemel):
    def __init__(self, **kw):
        super().__init__(
            "PPT",
            "PDF'e Dönüştür",
            "PowerPoint sunumlarını PDF'e çevirir.",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._drop = self._surukle_birak(
            "Kaynak",
            uzantilar=[".ppt", ".pptx", ".odp"],
            baslik="PowerPoint dosyasını sürükleyin",
            yardim=Y_SURUKLE,
        )
        self._kaynak, _ = self._dosya_alani(
            "veya dosya seç",
            filtre="PowerPoint (*.ppt *.pptx *.odp)",
        )
        self._drop.dosyalar_degisti.connect(lambda p: self._kaynak.setText(p[0] if p else ""))
        self._cikti = self._kaydet_alani(yardim=Y_CIKTI)
        self._kur_donustur()

    def islem_hazirla(self):
        kaynak = self._kaynak.text().strip() or (self._drop.yollar()[0] if self._drop.yollar() else "")
        if not kaynak:
            raise ValueError("PowerPoint dosyası seçin.")
        return (cnv.ppt_to_pdf, [kaynak, self._metin_zorunlu(self._cikti, "Çıktı")], {})


class JpgPaneli(_DonusturTemel):
    def __init__(self, **kw):
        super().__init__(
            "JPG",
            "PDF'e Dönüştür",
            "Görselleri tek PDF'te birleştirir (img2pdf, yüksek kalite).",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._drop = self._surukle_birak(
            "Görseller",
            coklu=True,
            uzantilar=[".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"],
            baslik="Görselleri sürükleyin (birden fazla)",
            yardim="Sıra, PDF sayfa sırası olur.",
        )
        self._dosyalar, _ = self._dosya_alani(
            "veya dosya seç",
            coklu=True,
            filtre="Görseller (*.jpg *.jpeg *.png *.bmp *.webp *.tif *.tiff)",
        )
        self._drop.dosyalar_degisti.connect(
            lambda p: self._dosyalar.setText(";".join(p))
        )
        self._cikti = self._kaydet_alani(yardim=Y_CIKTI)
        self._kur_donustur()

    def islem_hazirla(self):
        dosyalar = self._coklu_dosya(self._dosyalar) if self._dosyalar.text().strip() else self._drop.yollar()
        if not dosyalar:
            raise ValueError("En az bir görsel seçin.")
        return (cnv.jpg_to_pdf, [dosyalar, self._metin_zorunlu(self._cikti, "Çıktı")], {})


class HtmlPaneli(_DonusturTemel):
    def __init__(self, **kw):
        super().__init__(
            "HTML",
            "PDF'e Dönüştür",
            "HTML dosyasını PDF'e çevirir (wkhtmltopdf kurulu olmalı).",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._drop = self._surukle_birak(
            "HTML",
            uzantilar=[".html", ".htm"],
            baslik="HTML dosyasını sürükleyin",
            yardim="wkhtmltopdf: https://wkhtmltopdf.org — PATH'e ekleyin.",
        )
        self._kaynak, _ = self._dosya_alani(
            "veya dosya seç",
            filtre="HTML (*.html *.htm)",
        )
        self._drop.dosyalar_degisti.connect(lambda p: self._kaynak.setText(p[0] if p else ""))
        self._cikti = self._kaydet_alani(yardim=Y_CIKTI)
        self._kur_donustur()

    def islem_hazirla(self):
        kaynak = self._kaynak.text().strip() or (self._drop.yollar()[0] if self._drop.yollar() else "")
        if not kaynak:
            raise ValueError("HTML dosyası seçin.")
        return (cnv.html_to_pdf, [kaynak, self._metin_zorunlu(self._cikti, "Çıktı")], {})


class TaraPaneli(_DonusturTemel):
    def __init__(self, **kw):
        super().__init__(
            "Tara",
            "PDF'e Dönüştür",
            "Fiziksel tarayıcıdan doğrudan PDF oluşturur (Windows WIA).",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._coklu = self._onay_kutusu(
            "Birden fazla sayfa tara",
            varsayilan=True,
            yardim="Her sayfa için tarama penceresi açılır; bitirmek için iptal edin.",
        )
        self._cikti = self._kaydet_alani(yardim=Y_CIKTI)
        self._kur_donustur()

    def islem_hazirla(self):
        return (
            cnv.tara_pdf,
            [self._metin_zorunlu(self._cikti, "Çıktı")],
            {"coklu_sayfa": self._coklu.isChecked()},
        )


class GenelPaneli(_DonusturTemel):
    def __init__(self, **kw):
        super().__init__(
            "Genel",
            "PDF'e Dönüştür",
            "Word, Excel, PPT, görsel veya HTML — format otomatik algılanır.",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._drop = self._surukle_birak(
            "Dosya",
            coklu=False,
            uzantilar=[
                ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
                ".jpg", ".jpeg", ".png", ".html", ".htm", ".pdf",
                ".rtf", ".odt", ".ods", ".odp", ".csv", ".bmp", ".webp", ".tif",
            ],
            baslik="Herhangi bir desteklenen dosyayı sürükleyin",
            yardim="Uzantıya göre uygun dönüştürücü seçilir.",
        )
        self._kaynak, _ = self._dosya_alani("veya dosya seç", filtre="Desteklenen dosyalar (*.*)")
        self._drop.dosyalar_degisti.connect(lambda p: self._kaynak.setText(p[0] if p else ""))
        self._cikti = self._kaydet_alani(yardim=Y_CIKTI)
        self._kur_donustur()

    def islem_hazirla(self):
        kaynak = self._kaynak.text().strip() or (self._drop.yollar()[0] if self._drop.yollar() else "")
        if not kaynak:
            raise ValueError("Dosya seçin veya sürükleyin.")
        return (cnv.genel_to_pdf, [kaynak, self._metin_zorunlu(self._cikti, "Çıktı")], {})
