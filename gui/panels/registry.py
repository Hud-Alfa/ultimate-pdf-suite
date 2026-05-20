"""Araç kimliği → panel sınıfı eşlemesi."""

from __future__ import annotations

from typing import Dict, Optional, Type

from gui.panels.base import TemelAracPaneli
from gui.panels.org_panels import AyiklaPaneli, AyirPaneli, BirlestirPaneli, SayfaSilPaneli
from gui.panels.mod_panels import (
    DondurPaneli,
    DuzenlePaneli,
    DuzeltPaneli,
    FiligranPaneli,
    FormlarPaneli,
    KirpPaneli,
    NumaraPaneli,
)
from gui.panels.sec_panels import (
    ImzalaPaneli,
    IyilestirPaneli,
    KilitAcPaneli,
    KoruPaneli,
    KucultPaneli,
    OnarPaneli,
)
from gui.panels.convert_to_panels import (
    ExcelPaneli as ToExcelPaneli,
    GenelPaneli as ToGenelPaneli,
    HtmlPaneli,
    JpgPaneli as ToJpgPaneli,
    PptPaneli as ToPptPaneli,
    TaraPaneli,
    WordPaneli as ToWordPaneli,
)
from gui.panels.convert_from_panels import (
    OcrPaneli,
    PdfExcelPaneli,
    PdfGenelPaneli,
    PdfJpgPaneli,
    PdfPdfaPaneli,
    PdfPptPaneli,
    PdfWordPaneli,
)
from gui.panels.ai_panels import (
    CeviriPaneli,
    IntelligencePaneli,
    KarsilastirmaPaneli,
    OzetPaneli,
)

PANEL_SINIFLARI: Dict[str, Type[TemelAracPaneli]] = {
    "birlestir": BirlestirPaneli,
    "ayir": AyirPaneli,
    "sil": SayfaSilPaneli,
    "ayikla": AyiklaPaneli,
    "kirp": KirpPaneli,
    "dondur": DondurPaneli,
    "filigran": FiligranPaneli,
    "numara": NumaraPaneli,
    "formlar": FormlarPaneli,
    "duzelt": DuzeltPaneli,
    "duzenle": DuzenlePaneli,
    "koru": KoruPaneli,
    "kilit_ac": KilitAcPaneli,
    "imzala": ImzalaPaneli,
    "kucult": KucultPaneli,
    "iyilestir": IyilestirPaneli,
    "onar": OnarPaneli,
    "word_to_pdf": ToWordPaneli,
    "excel_to_pdf": ToExcelPaneli,
    "ppt_to_pdf": ToPptPaneli,
    "jpg_to_pdf": ToJpgPaneli,
    "html_to_pdf": HtmlPaneli,
    "tara": TaraPaneli,
    "genel": ToGenelPaneli,
    "pdf_to_jpg": PdfJpgPaneli,
    "pdf_to_word": PdfWordPaneli,
    "pdf_to_excel": PdfExcelPaneli,
    "pdf_to_ppt": PdfPptPaneli,
    "pdf_a": PdfPdfaPaneli,
    "genel_from": PdfGenelPaneli,
    "ocr": OcrPaneli,
    "intelligence": IntelligencePaneli,
    "ai_ozet": OzetPaneli,
    "ceviri": CeviriPaneli,
    "karsilastirma": KarsilastirmaPaneli,
}


def panel_olustur(
    kimlik: str,
    arac_baslik: str,
    kategori_baslik: str,
    aciklama: str = "",
) -> Optional[TemelAracPaneli]:
    sinif = PANEL_SINIFLARI.get(kimlik)
    if sinif is None:
        return None
    return sinif()
