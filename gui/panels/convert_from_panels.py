"""PDF'den dönüştür ve OCR panelleri."""

from __future__ import annotations

from PyQt6.QtWidgets import QComboBox

from modules import convert_from as cfr
from gui.panels.base import TemelAracPaneli
from gui.sayfa_galerisi import SayfaGalerisiPaneli

Y_PDF = "Kaynak PDF dosyası."
Y_SURUKLE = "PDF'i buraya sürükleyip bırakın."
Y_KLASOR = "Sayfa görsellerinin kaydedileceği klasör."
Y_CIKTI = "Oluşturulacak dosyanın kayıt yolu."
TESSERACT_NOTU = (
    "OCR için Tesseract'ın sistemde kurulu ve PATH'te tanımlı olması gerekir. "
    "Windows: https://github.com/UB-Mannheim/tesseract/wiki — Türkçe için «tur» dil paketi."
)


class _PdfdenTemel(TemelAracPaneli):
    def _pdf_alanlari(self) -> str:
        self._drop = self._surukle_birak(
            "PDF",
            uzantilar=[".pdf"],
            baslik="PDF sürükleyin",
            yardim=Y_SURUKLE,
        )
        self._kaynak, _ = self._dosya_alani("veya PDF seç", onizle=True, yardim=Y_PDF)
        self._drop.dosyalar_degisti.connect(lambda p: self._kaynak.setText(p[0] if p else ""))
        return ""

    def _kaynak_yolu(self) -> str:
        yol = self._kaynak.text().strip()
        if not yol and self._drop.yollar():
            yol = self._drop.yollar()[0]
        if not yol:
            raise ValueError("PDF dosyası seçin.")
        return yol

    def _kur_pdfden(self, *, ocr_uyari: bool = False) -> None:
        self._onizleme_ayarla(SayfaGalerisiPaneli.MOD_IZLEME)
        if ocr_uyari:
            from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout

            cerceve = QFrame()
            cerceve.setObjectName("tesseractNotice")
            layout = QVBoxLayout(cerceve)
            lb = QLabel(TESSERACT_NOTU)
            lb.setWordWrap(True)
            lb.setObjectName("tesseractNoticeText")
            layout.addWidget(lb)
            self._form.insertRow(0, "", cerceve)


class PdfJpgPaneli(_PdfdenTemel):
    def __init__(self, **kw):
        super().__init__(
            "JPG / PNG",
            "PDF'den Dönüştür & OCR",
            "Her sayfayı ayrı yüksek kaliteli görsel olarak dışa aktarır.",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._pdf_alanlari()
        self._format = QComboBox()
        self._format.addItem("PNG (en iyi kalite)", "png")
        self._format.addItem("JPG", "jpg")
        self._satir_ekle("Görsel formatı", self._format, yardim="PNG kayıpsıza yakın.")
        self._dpi = self._adim_kutusu(
            "DPI",
            minimum=72,
            maximum=600,
            step=24,
            value=200,
            decimals=0,
            yardim="200–300 taranmış belgeler için uygundur.",
        )
        self._klasor, _ = self._dosya_alani("Çıktı klasörü", klasor=True, yardim=Y_KLASOR)
        self._kur_pdfden()

    def islem_hazirla(self):
        return (
            cfr.pdf_to_jpg,
            [self._kaynak_yolu(), self._metin_zorunlu(self._klasor, "Çıktı klasörü")],
            {"format": self._format.currentData(), "dpi": int(self._dpi.value())},
        )


class PdfWordPaneli(_PdfdenTemel):
    def __init__(self, **kw):
        super().__init__(
            "Word",
            "PDF'den Dönüştür & OCR",
            "PDF'i düzenlenebilir DOCX'e çevirir (pdf2docx).",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._pdf_alanlari()
        self._cikti = self._kaydet_alani("DOCX dosyası", filtre="Word (*.docx)", yardim=Y_CIKTI)
        self._kur_pdfden()

    def islem_hazirla(self):
        cikti = self._metin_zorunlu(self._cikti, "Çıktı")
        if not cikti.lower().endswith(".docx"):
            cikti += ".docx"
        return (cfr.pdf_to_word, [self._kaynak_yolu(), cikti], {})


class PdfExcelPaneli(_PdfdenTemel):
    def __init__(self, **kw):
        super().__init__(
            "Excel",
            "PDF'den Dönüştür & OCR",
            "PDF içindeki tabloları algılayıp Excel'e aktarır (pdfplumber).",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._pdf_alanlari()
        self._cikti = self._kaydet_alani("Excel dosyası", filtre="Excel (*.xlsx)", yardim=Y_CIKTI)
        self._kur_pdfden()

    def islem_hazirla(self):
        cikti = self._metin_zorunlu(self._cikti, "Çıktı")
        if not cikti.lower().endswith(".xlsx"):
            cikti += ".xlsx"
        return (cfr.pdf_to_excel, [self._kaynak_yolu(), cikti], {})


class PdfPptPaneli(_PdfdenTemel):
    def __init__(self, **kw):
        super().__init__(
            "PPT",
            "PDF'den Dönüştür & OCR",
            "Her PDF sayfası bir PowerPoint slaytı olur.",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._pdf_alanlari()
        self._dpi = self._adim_kutusu("Slayt DPI", minimum=96, maximum=300, step=12, value=150, decimals=0)
        self._cikti = self._kaydet_alani("PPTX dosyası", filtre="PowerPoint (*.pptx)", yardim=Y_CIKTI)
        self._kur_pdfden()

    def islem_hazirla(self):
        cikti = self._metin_zorunlu(self._cikti, "Çıktı")
        if not cikti.lower().endswith(".pptx"):
            cikti += ".pptx"
        return (
            cfr.pdf_to_ppt,
            [self._kaynak_yolu(), cikti],
            {"dpi": int(self._dpi.value())},
        )


class PdfPdfaPaneli(_PdfdenTemel):
    def __init__(self, **kw):
        super().__init__(
            "PDF/A",
            "PDF'den Dönüştür & OCR",
            "Uzun süreli arşiv için PDF/A standardına dönüştürür.",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._pdf_alanlari()
        self._cikti = self._kaydet_alani(yardim="PDF/A çıktı dosyası.")
        self._kur_pdfden()

    def islem_hazirla(self):
        return (cfr.pdf_to_pdfa, [self._kaynak_yolu(), self._metin_zorunlu(self._cikti, "Çıktı")], {})


class PdfGenelPaneli(_PdfdenTemel):
    def __init__(self, **kw):
        super().__init__(
            "Genel",
            "PDF'den Dönüştür & OCR",
            "Tek PDF'den istediğiniz hedef formatı seçin.",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._pdf_alanlari()
        self._hedef = QComboBox()
        self._hedef.addItem("Word (DOCX)", "word")
        self._hedef.addItem("Excel (XLSX)", "excel")
        self._hedef.addItem("PowerPoint (PPTX)", "ppt")
        self._hedef.addItem("Görseller (PNG klasörü)", "png")
        self._hedef.addItem("PDF/A", "pdfa")
        self._hedef.addItem("OCR (aranabilir PDF)", "ocr")
        self._satir_ekle("Hedef format", self._hedef, yardim="Çıktı türünü buradan seçin.")
        self._cikti = self._kaydet_alani("Çıktı", filtre="Tüm dosyalar (*.*)", yardim=Y_CIKTI)
        self._klasor, _ = self._dosya_alani(
            "veya klasör (JPG/PNG)",
            klasor=True,
            yardim="Görsel dışa aktarımda klasör seçin.",
        )
        self._kur_pdfden(ocr_uyari=True)

    def islem_hazirla(self):
        hedef = self._hedef.currentData()
        if hedef in ("png", "jpg"):
            klasor = self._klasor.text().strip() or self._cikti.text().strip()
            return (
                cfr.pdf_to_jpg,
                [self._kaynak_yolu(), klasor],
                {"format": "png" if hedef == "png" else "jpg"},
            )
        return (
            cfr.genel_from_pdf,
            [self._kaynak_yolu(), self._metin_zorunlu(self._cikti, "Çıktı")],
            {"hedef_format": hedef},
        )


class OcrPaneli(_PdfdenTemel):
    def __init__(self, **kw):
        super().__init__(
            "OCR",
            "PDF'den Dönüştür & OCR",
            "Görsel PDF'e aranabilir metin katmanı ekler (çok çekirdekli).",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._pdf_alanlari()
        self._dil = QComboBox()
        self._dil.addItem("Türkçe (tur)", "tur")
        self._dil.addItem("İngilizce (eng)", "eng")
        self._dil.addItem("Türkçe + İngilizce", "tur+eng")
        self._satir_ekle("OCR dili", self._dil, yardim="Tesseract dil paketleri kurulu olmalı.")
        self._dpi = self._adim_kutusu("DPI", minimum=100, maximum=400, step=25, value=200, decimals=0)
        self._isci = self._adim_kutusu(
            "İş parçacığı",
            minimum=1,
            maximum=16,
            step=1,
            value=4,
            decimals=0,
            yardim="Çok sayfalı belgelerde CPU çekirdek sayısı kadar artırın.",
        )
        self._cikti = self._kaydet_alani(yardim="Aranabilir PDF çıktısı.")
        self._kur_pdfden(ocr_uyari=True)

    def islem_hazirla(self):
        return (
            cfr.ocr_pdf,
            [self._kaynak_yolu(), self._metin_zorunlu(self._cikti, "Çıktı")],
            {
                "dil": self._dil.currentData(),
                "dpi": int(self._dpi.value()),
                "isci_sayisi": int(self._isci.value()),
            },
        )
