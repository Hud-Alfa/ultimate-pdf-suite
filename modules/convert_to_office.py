"""Windows Office / LibreOffice ile Office → PDF."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def _soffice_yolu() -> str | None:
    adaylar = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    for yol in adaylar:
        if os.path.isfile(yol):
            return yol
    return shutil.which("soffice")


def libreoffice_pdf(kaynak: str, cikti: str) -> None:
    soffice = _soffice_yolu()
    if not soffice:
        raise RuntimeError(
            "LibreOffice bulunamadı. Kurun veya Microsoft Office yükleyin."
        )
    out_dir = str(Path(cikti).parent)
    subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir", out_dir, kaynak],
        check=True,
        capture_output=True,
        timeout=300,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    uretilen = Path(out_dir) / (Path(kaynak).stem + ".pdf")
    if not uretilen.is_file():
        raise RuntimeError("LibreOffice PDF üretemedi.")
    if uretilen.resolve() != Path(cikti).resolve():
        shutil.move(str(uretilen), cikti)


def _comtypes_word_pdf(kaynak: str, cikti: str) -> None:
    import comtypes.client  # type: ignore[import-untyped]

    wd_format_pdf = 17
    word = comtypes.client.CreateObject("Word.Application")
    word.Visible = False
    doc = None
    try:
        doc = word.Documents.Open(os.path.abspath(kaynak), ReadOnly=True)
        doc.SaveAs(os.path.abspath(cikti), FileFormat=wd_format_pdf)
    finally:
        if doc is not None:
            doc.Close(False)
        word.Quit()


def _comtypes_excel_pdf(kaynak: str, cikti: str) -> None:
    import comtypes.client  # type: ignore[import-untyped]

    xl_type_pdf = 0
    excel = comtypes.client.CreateObject("Excel.Application")
    excel.Visible = False
    wb = None
    try:
        wb = excel.Workbooks.Open(os.path.abspath(kaynak), ReadOnly=True)
        wb.ExportAsFixedFormat(xl_type_pdf, os.path.abspath(cikti))
    finally:
        if wb is not None:
            wb.Close(False)
        excel.Quit()


def _comtypes_ppt_pdf(kaynak: str, cikti: str) -> None:
    import comtypes.client  # type: ignore[import-untyped]

    pp_save_as_pdf = 32
    ppt = comtypes.client.CreateObject("PowerPoint.Application")
    ppt.Visible = 1
    pres = None
    try:
        pres = ppt.Presentations.Open(os.path.abspath(kaynak), WithWindow=False)
        pres.SaveAs(os.path.abspath(cikti), pp_save_as_pdf)
    finally:
        if pres is not None:
            pres.Close()
        ppt.Quit()


def office_pdf(kaynak: str, cikti: str, tur: str) -> None:
    """tur: word | excel | ppt"""
    hatalar: list[str] = []
    if sys.platform == "win32":
        try:
            import comtypes  # noqa: F401

            if tur == "word":
                _comtypes_word_pdf(kaynak, cikti)
            elif tur == "excel":
                _comtypes_excel_pdf(kaynak, cikti)
            else:
                _comtypes_ppt_pdf(kaynak, cikti)
            return
        except Exception as exc:  # noqa: BLE001
            hatalar.append(f"Microsoft Office: {exc}")

    try:
        libreoffice_pdf(kaynak, cikti)
    except Exception as exc:  # noqa: BLE001
        hatalar.append(f"LibreOffice: {exc}")

    raise RuntimeError(
        "Office dönüşümü başarısız.\n"
        + "\n".join(hatalar)
        + "\n\nWindows: Word/Excel/PowerPoint veya LibreOffice kurulu olmalı."
    )
