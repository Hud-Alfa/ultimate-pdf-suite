"""PDF'e dönüştür — Office, görsel, HTML, tarama, genel."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, List, Optional

import fitz

from core.pdf_core import ilerleme
from modules.convert_to_office import office_pdf

ProgressCallback = Callable[[int], None]
MessageCallback = Callable[[str], None]

GORSEL_UZANTILAR = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff", ".gif"}
OFFICE_WORD = {".doc", ".docx", ".rtf", ".odt"}
OFFICE_EXCEL = {".xls", ".xlsx", ".csv", ".ods"}
OFFICE_PPT = {".ppt", ".pptx", ".odp"}
HTML_UZ = {".html", ".htm"}


def _cikti_kontrol(cikti: str) -> str:
    yol = Path(cikti)
    if yol.suffix.lower() != ".pdf":
        yol = yol.with_suffix(".pdf")
    yol.parent.mkdir(parents=True, exist_ok=True)
    return str(yol)


def word_to_pdf(
    kaynak: str,
    cikti: str,
    *,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    cikti = _cikti_kontrol(cikti)
    ilerleme(progress_callback, 20, message_callback, "Word → PDF…")
    office_pdf(kaynak, cikti, "word")
    ilerleme(progress_callback, 100, message_callback, "Tamamlandı.")
    return cikti


def excel_to_pdf(
    kaynak: str,
    cikti: str,
    *,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    cikti = _cikti_kontrol(cikti)
    ilerleme(progress_callback, 20, message_callback, "Excel → PDF…")
    office_pdf(kaynak, cikti, "excel")
    ilerleme(progress_callback, 100, message_callback, "Tamamlandı.")
    return cikti


def ppt_to_pdf(
    kaynak: str,
    cikti: str,
    *,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    cikti = _cikti_kontrol(cikti)
    ilerleme(progress_callback, 20, message_callback, "PowerPoint → PDF…")
    office_pdf(kaynak, cikti, "ppt")
    ilerleme(progress_callback, 100, message_callback, "Tamamlandı.")
    return cikti


def jpg_to_pdf(
    kaynaklar: List[str],
    cikti: str,
    *,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    if not kaynaklar:
        raise ValueError("En az bir görsel seçin.")
    cikti = _cikti_kontrol(cikti)
    ilerleme(progress_callback, 15, message_callback, "Görseller birleştiriliyor…")

    try:
        import img2pdf  # type: ignore[import-untyped]

        gecerli = [k for k in kaynaklar if os.path.isfile(k)]
        with open(cikti, "wb") as f:
            f.write(img2pdf.convert(gecerli))
    except ImportError:
        _jpg_to_pdf_fitz(kaynaklar, cikti, progress_callback, message_callback)
    except Exception:
        _jpg_to_pdf_fitz(kaynaklar, cikti, progress_callback, message_callback)

    ilerleme(progress_callback, 100, message_callback, "Tamamlandı.")
    return cikti


def _jpg_to_pdf_fitz(
    kaynaklar: List[str],
    cikti: str,
    progress_callback: Optional[ProgressCallback],
    message_callback: Optional[MessageCallback],
) -> None:
    from PIL import Image

    belge = fitz.open()
    toplam = len(kaynaklar)
    try:
        for i, yol in enumerate(kaynaklar):
            ilerleme(
                progress_callback,
                int(20 + (i / max(toplam, 1)) * 70),
                message_callback,
                f"Sayfa {i + 1}…",
            )
            img = Image.open(yol)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            buf = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            try:
                img.save(buf.name, "JPEG", quality=95, optimize=True)
                buf.close()
                sayfa = belge.new_page(
                    width=float(img.width),
                    height=float(img.height),
                )
                sayfa.insert_image(sayfa.rect, filename=buf.name)
            finally:
                os.unlink(buf.name)
        belge.save(cikti, garbage=4, deflate=True)
    finally:
        belge.close()


def html_to_pdf(
    kaynak: str,
    cikti: str,
    *,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    cikti = _cikti_kontrol(cikti)
    ilerleme(progress_callback, 20, message_callback, "HTML → PDF…")

    try:
        import pdfkit  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError("HTML dönüşümü için: pip install pdfkit ve wkhtmltopdf kurun.") from exc

    yol = Path(kaynak)
    secenek = {}
    wk = os.environ.get("WKHTMLTOPDF_PATH") or shutil.which("wkhtmltopdf")
    if wk:
        secenek["wkhtmltopdf"] = wk

    cfg = pdfkit.configuration(**secenek) if secenek else None
    if yol.is_file():
        pdfkit.from_file(str(yol.resolve()), cikti, configuration=cfg)
    else:
        pdfkit.from_string(kaynak, cikti, configuration=cfg)

    ilerleme(progress_callback, 100, message_callback, "Tamamlandı.")
    return cikti


def tara_pdf(
    cikti: str,
    *,
    coklu_sayfa: bool = True,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    """Windows WIA ile fiziksel tarayıcıdan PDF (yalnızca Windows)."""
    if sys.platform != "win32":
        raise OSError("Tarama yalnızca Windows'ta desteklenir.")

    cikti = _cikti_kontrol(cikti)
    ilerleme(progress_callback, 10, message_callback, "Tarayıcı açılıyor…")

    try:
        import comtypes.client  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError("Tarama için: pip install comtypes") from exc

    wia = comtypes.client.CreateObject("WIA.CommonDialog")
    belge = fitz.open()
    sayac = 0

    try:
        while True:
            ilerleme(
                progress_callback,
                min(85, 15 + sayac * 25),
                message_callback,
                "Belgeyi tarayıcıya yerleştirin ve Tarama'ya basın…",
            )
            try:
                img = wia.ShowAcquireImage()
            except Exception as exc:  # noqa: BLE001
                if sayac == 0:
                    raise ValueError(f"Tarama iptal edildi veya başarısız: {exc}") from exc
                break

            if img is None:
                break

            gecici = tempfile.mktemp(suffix=".bmp")
            try:
                img.SaveFile(gecici)
                pix = fitz.open(gecici)
                sayfa = pix[0]
                r = sayfa.rect
                yeni = belge.new_page(width=r.width, height=r.height)
                yeni.show_pdf_page(yeni.rect, pix, 0)
                pix.close()
            finally:
                if os.path.isfile(gecici):
                    os.unlink(gecici)

            sayac += 1
            if not coklu_sayfa:
                break

        if sayac == 0:
            raise ValueError("Taranan sayfa yok.")

        ilerleme(progress_callback, 95, message_callback, "PDF kaydediliyor…")
        belge.save(cikti, garbage=4, deflate=True)
    finally:
        belge.close()

    ilerleme(progress_callback, 100, message_callback, f"{sayac} sayfa tarandı.")
    return cikti


def genel_to_pdf(
    kaynak: str,
    cikti: str,
    *,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    """Uzantıya göre uygun dönüştürücüyü seçer."""
    yol = Path(kaynak)
    if not yol.is_file():
        raise FileNotFoundError(f"Dosya bulunamadı: {kaynak}")

    ext = yol.suffix.lower()
    ilerleme(progress_callback, 5, message_callback, f"Algılanan format: {ext or 'bilinmiyor'}")

    if ext == ".pdf":
        shutil.copy2(kaynak, _cikti_kontrol(cikti))
        ilerleme(progress_callback, 100, message_callback, "PDF kopyalandı.")
        return _cikti_kontrol(cikti)
    if ext in OFFICE_WORD:
        return word_to_pdf(kaynak, cikti, progress_callback=progress_callback, message_callback=message_callback)
    if ext in OFFICE_EXCEL:
        return excel_to_pdf(kaynak, cikti, progress_callback=progress_callback, message_callback=message_callback)
    if ext in OFFICE_PPT:
        return ppt_to_pdf(kaynak, cikti, progress_callback=progress_callback, message_callback=message_callback)
    if ext in GORSEL_UZANTILAR:
        return jpg_to_pdf([kaynak], cikti, progress_callback=progress_callback, message_callback=message_callback)
    if ext in HTML_UZ:
        return html_to_pdf(kaynak, cikti, progress_callback=progress_callback, message_callback=message_callback)

    raise ValueError(
        f"Desteklenmeyen format: {ext}\n"
        "Desteklenen: Word, Excel, PPT, görsel, HTML veya mevcut PDF."
    )


# Geriye uyumluluk (eski isim)
tarayicidan_pdf = tara_pdf
