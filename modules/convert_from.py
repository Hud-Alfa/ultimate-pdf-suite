"""PDF'den dönüştür ve OCR — Word, Excel, PPT, görsel, PDF/A, OCR."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple

import fitz

from core.pdf_core import dosya_ac, ilerleme

ProgressCallback = Callable[[int], None]
MessageCallback = Callable[[str], None]

# OCR çok süreçli iş için üst düzey fonksiyon (Windows pickle)
def _ocr_sayfa_parca(
    pdf_yolu: str,
    sayfa_no: int,
    dpi: int,
    dil: str,
) -> Tuple[int, bytes, List[Tuple[float, float, float, float, str]]]:
    """Tek sayfa: görsel baytı + görünmez metin kutuları."""
    import pytesseract
    from PIL import Image

    belge = fitz.open(pdf_yolu)
    try:
        sayfa = belge[sayfa_no]
        olcek = dpi / 72.0
        mat = fitz.Matrix(olcek, olcek)
        pix = sayfa.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    finally:
        belge.close()

    buf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    try:
        img.save(buf.name, "PNG")
        buf.close()
        data = pytesseract.image_to_data(
            buf.name,
            lang=dil,
            output_type=pytesseract.Output.DICT,
        )
    finally:
        os.unlink(buf.name)

    kutular: List[Tuple[float, float, float, float, str]] = []
    n = len(data["text"])
    for i in range(n):
        metin = (data["text"][i] or "").strip()
        if not metin:
            continue
        x, y, w, h = (
            float(data["left"][i]),
            float(data["top"][i]),
            float(data["width"][i]),
            float(data["height"][i]),
        )
        kutular.append((x, y, x + w, y + h, metin))

    png_buf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    try:
        img.save(png_buf.name, "PNG")
        png_buf.close()
        with open(png_buf.name, "rb") as f:
            png_bytes = f.read()
    finally:
        os.unlink(png_buf.name)

    return sayfa_no, png_bytes, kutular


def pdf_to_jpg(
    kaynak: str,
    cikti_klasoru: str,
    *,
    format: str = "png",
    dpi: int = 200,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> List[str]:
    """Her sayfayı yüksek çözünürlükte PNG veya JPG olarak kaydeder."""
    fmt = format.lower().lstrip(".")
    if fmt not in ("png", "jpg", "jpeg"):
        raise ValueError("Format png veya jpg olmalı.")
    if fmt == "jpeg":
        fmt = "jpg"

    klasor = Path(cikti_klasoru)
    klasor.mkdir(parents=True, exist_ok=True)
    ad = Path(kaynak).stem
    belge = dosya_ac(kaynak)
    cikti_dosyalari: List[str] = []

    try:
        toplam = belge.page_count
        olcek = dpi / 72.0
        mat = fitz.Matrix(olcek, olcek)

        for i in range(toplam):
            ilerleme(
                progress_callback,
                int((i / max(toplam, 1)) * 95),
                message_callback,
                f"Sayfa {i + 1}/{toplam} dışa aktarılıyor…",
            )
            pix = belge[i].get_pixmap(matrix=mat, alpha=False)
            hedef = klasor / f"{ad}_sayfa_{i + 1:04d}.{fmt}"
            if fmt == "png":
                pix.save(str(hedef))
            else:
                from PIL import Image

                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img.save(str(hedef), "JPEG", quality=95, optimize=True)
            cikti_dosyalari.append(str(hedef))
    finally:
        belge.close()

    ilerleme(progress_callback, 100, message_callback, f"{len(cikti_dosyalari)} dosya oluşturuldu.")
    return cikti_dosyalari


def pdf_to_word(
    kaynak: str,
    cikti: str,
    *,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    try:
        from pdf2docx import Converter
    except ImportError as exc:
        raise ImportError("Word dönüşümü için: pip install pdf2docx") from exc

    cikti_yolu = Path(cikti)
    if cikti_yolu.suffix.lower() != ".docx":
        cikti_yolu = cikti_yolu.with_suffix(".docx")

    ilerleme(progress_callback, 20, message_callback, "PDF → Word (pdf2docx)…")
    cv = Converter(kaynak)
    try:
        cv.convert(str(cikti_yolu))
    finally:
        cv.close()

    ilerleme(progress_callback, 100, message_callback, "Word dosyası hazır.")
    return str(cikti_yolu)


def pdf_to_excel(
    kaynak: str,
    cikti: str,
    *,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    try:
        import pdfplumber
        from openpyxl import Workbook
    except ImportError as exc:
        raise ImportError("Excel için: pip install pdfplumber openpyxl") from exc

    cikti_yolu = Path(cikti)
    if cikti_yolu.suffix.lower() not in (".xlsx", ".xls"):
        cikti_yolu = cikti_yolu.with_suffix(".xlsx")

    ilerleme(progress_callback, 15, message_callback, "Tablolar taranıyor…")
    wb = Workbook()
    wb.remove(wb.active)
    tablo_say = 0

    with pdfplumber.open(kaynak) as pdf:
        toplam = len(pdf.pages)
        for p_idx, page in enumerate(pdf.pages):
            ilerleme(
                progress_callback,
                int(15 + (p_idx / max(toplam, 1)) * 75),
                message_callback,
                f"Sayfa {p_idx + 1} tabloları…",
            )
            tablolar = page.extract_tables() or []
            for t_idx, tablo in enumerate(tablolar):
                if not tablo:
                    continue
                tablo_say += 1
                ws = wb.create_sheet(title=f"S{p_idx + 1}_T{t_idx + 1}"[:31])
                for r, satir in enumerate(tablo, start=1):
                    for c, hucre in enumerate(satir, start=1):
                        ws.cell(row=r, column=c, value=hucre)

    if tablo_say == 0:
        ws = wb.create_sheet("Veri")
        ws.cell(row=1, column=1, value="Otomatik tablo bulunamadı.")
        ws.cell(
            row=2,
            column=1,
            value="Karmaşık düzenlerde Word veya manuel dışa aktarım deneyin.",
        )

    wb.save(str(cikti_yolu))
    ilerleme(progress_callback, 100, message_callback, f"{tablo_say} tablo aktarıldı.")
    return str(cikti_yolu)


def pdf_to_ppt(
    kaynak: str,
    cikti: str,
    *,
    dpi: int = 150,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    try:
        from pptx import Presentation
        from pptx.util import Inches
    except ImportError as exc:
        raise ImportError("PowerPoint için: pip install python-pptx") from exc

    cikti_yolu = Path(cikti)
    if cikti_yolu.suffix.lower() not in (".pptx", ".ppt"):
        cikti_yolu = cikti_yolu.with_suffix(".pptx")

    belge = dosya_ac(kaynak)
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    bos = prs.slide_layouts[6]
    olcek = dpi / 72.0
    mat = fitz.Matrix(olcek, olcek)

    try:
        toplam = belge.page_count
        for i in range(toplam):
            ilerleme(
                progress_callback,
                int((i / max(toplam, 1)) * 90),
                message_callback,
                f"Slayt {i + 1}…",
            )
            pix = belge[i].get_pixmap(matrix=mat, alpha=False)
            gecici = tempfile.mktemp(suffix=".png")
            try:
                pix.save(gecici)
                slayt = prs.slides.add_slide(bos)
                slayt.shapes.add_picture(
                    gecici,
                    0,
                    0,
                    width=prs.slide_width,
                    height=prs.slide_height,
                )
            finally:
                if os.path.isfile(gecici):
                    os.unlink(gecici)
        prs.save(str(cikti_yolu))
    finally:
        belge.close()

    ilerleme(progress_callback, 100, message_callback, "Sunum hazır.")
    return str(cikti_yolu)


def pdf_to_pdfa(
    kaynak: str,
    cikti: str,
    *,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    """PDF/A arşiv standardı — önce OCRmyPDF, yedek Ghostscript."""
    cikti = str(Path(cikti).with_suffix(".pdf"))
    ilerleme(progress_callback, 15, message_callback, "PDF/A dönüşümü…")

    try:
        import ocrmypdf

        ocrmypdf.convert(
            kaynak,
            cikti,
            output_type="pdfa",
            skip_text=True,
            progress_bar=False,
        )
        ilerleme(progress_callback, 100, message_callback, "PDF/A (OCRmyPDF) tamamlandı.")
        return cikti
    except ImportError:
        pass
    except Exception:
        pass

    gs = shutil.which("gswin64c") or shutil.which("gswin32c") or shutil.which("gs")
    if gs:
        ilerleme(progress_callback, 40, message_callback, "Ghostscript PDF/A…")
        subprocess.run(
            [
                gs,
                "-dPDFA=2",
                "-dBATCH",
                "-dNOPAUSE",
                "-sProcessColorModel=DeviceRGB",
                "-sDEVICE=pdfwrite",
                f"-sOutputFile={cikti}",
                kaynak,
            ],
            check=True,
            capture_output=True,
            timeout=600,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        ilerleme(progress_callback, 100, message_callback, "PDF/A (Ghostscript) tamamlandı.")
        return cikti

    ilerleme(progress_callback, 60, message_callback, "Basit PDF/A kaydı (yedek)…")
    belge = dosya_ac(kaynak)
    try:
        belge.save(cikti, garbage=4, deflate=True, clean=True)
    finally:
        belge.close()
    ilerleme(
        progress_callback,
        100,
        message_callback,
        "Kaydedildi. Tam PDF/A için OCRmyPDF veya Ghostscript kurun.",
    )
    return cikti


def ocr_pdf(
    kaynak: str,
    cikti: str,
    dil: str = "tur",
    *,
    dpi: int = 200,
    isci_sayisi: Optional[int] = None,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    """Görsel PDF → aranabilir metin katmanlı PDF (pytesseract, çok çekirdekli)."""
    try:
        import pytesseract
    except ImportError as exc:
        raise ImportError("OCR için: pip install pytesseract") from exc

    if not shutil.which("tesseract"):
        raise EnvironmentError(
            "Tesseract OCR sistemde kurulu değil.\n"
            "Windows: https://github.com/UB-Mannheim/tesseract/wiki\n"
            "Kurulumdan sonra PATH'e ekleyin."
        )

    _ = pytesseract.get_tesseract_version()

    belge = dosya_ac(kaynak)
    sayfa_say = belge.page_count
    belge.close()

    workers = isci_sayisi or max(1, min((os.cpu_count() or 2), 8))
    ilerleme(progress_callback, 5, message_callback, f"OCR başlıyor ({workers} iş parçacığı)…")

    sonuclar: dict[int, Tuple[bytes, List]] = {}
    with ProcessPoolExecutor(max_workers=workers) as havuz:
        gelecek = {
            havuz.submit(_ocr_sayfa_parca, kaynak, i, dpi, dil): i
            for i in range(sayfa_say)
        }
        tamamlanan = 0
        for g in as_completed(gelecek):
            sayfa_no, png_bytes, kutular = g.result()
            sonuclar[sayfa_no] = (png_bytes, kutular)
            tamamlanan += 1
            ilerleme(
                progress_callback,
                int(10 + (tamamlanan / max(sayfa_say, 1)) * 75),
                message_callback,
                f"OCR {tamamlanan}/{sayfa_say}",
            )

    kaynak_belge = dosya_ac(kaynak)
    yeni = fitz.open()
    try:
        for i in range(sayfa_say):
            png_bytes, kutular = sonuclar[i]
            orijinal = kaynak_belge[i]
            sayfa = yeni.new_page(width=orijinal.rect.width, height=orijinal.rect.height)
            sayfa.insert_image(sayfa.rect, stream=png_bytes)

            pix_gec = fitz.open(stream=png_bytes, filetype="png")
            pw = pix_gec[0].rect.width
            ph = pix_gec[0].rect.height
            pix_gec.close()
            olcek_x = sayfa.rect.width / max(pw, 1)
            olcek_y = sayfa.rect.height / max(ph, 1)

            for x0, y0, x1, y1, metin in kutular:
                r = fitz.Rect(
                    x0 * olcek_x,
                    y0 * olcek_y,
                    x1 * olcek_x,
                    y1 * olcek_y,
                )
                sayfa.insert_textbox(
                    r,
                    metin,
                    fontsize=max(6, min(11, r.height * 0.8)),
                    color=(1, 1, 1),
                    render_mode=3,
                )

        ilerleme(progress_callback, 95, message_callback, "PDF kaydediliyor…")
        yeni.save(cikti, garbage=4, deflate=True)
    finally:
        kaynak_belge.close()
        yeni.close()

    ilerleme(progress_callback, 100, message_callback, "Aranabilir PDF hazır.")
    return cikti


# Eski isim
ocr = ocr_pdf


def genel_from_pdf(
    kaynak: str,
    cikti: str,
    *,
    hedef_format: str = "word",
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> Any:
    """hedef_format: jpg | word | excel | ppt | pdfa | ocr"""
    fmt = hedef_format.lower().strip()
    yonlendir = {
        "jpg": lambda: pdf_to_jpg(kaynak, cikti, progress_callback=progress_callback, message_callback=message_callback),
        "png": lambda: pdf_to_jpg(kaynak, cikti, format="png", progress_callback=progress_callback, message_callback=message_callback),
        "word": lambda: pdf_to_word(kaynak, cikti, progress_callback=progress_callback, message_callback=message_callback),
        "docx": lambda: pdf_to_word(kaynak, cikti, progress_callback=progress_callback, message_callback=message_callback),
        "excel": lambda: pdf_to_excel(kaynak, cikti, progress_callback=progress_callback, message_callback=message_callback),
        "xlsx": lambda: pdf_to_excel(kaynak, cikti, progress_callback=progress_callback, message_callback=message_callback),
        "ppt": lambda: pdf_to_ppt(kaynak, cikti, progress_callback=progress_callback, message_callback=message_callback),
        "pptx": lambda: pdf_to_ppt(kaynak, cikti, progress_callback=progress_callback, message_callback=message_callback),
        "pdfa": lambda: pdf_to_pdfa(kaynak, cikti, progress_callback=progress_callback, message_callback=message_callback),
        "ocr": lambda: ocr_pdf(kaynak, cikti, progress_callback=progress_callback, message_callback=message_callback),
    }
    if fmt not in yonlendir:
        raise ValueError(f"Desteklenmeyen hedef: {hedef_format}")
    return yonlendir[fmt]()
