"""Sayfa yönetimi — birleştir, ayır, sil, ayıkla (PyMuPDF)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, List, Optional, Sequence, Tuple

import fitz

from core.pdf_core import (
    aralik_segmentleri_coz,
    dosya_ac,
    dosya_kaydet,
    ilerleme,
    sayfa_listesi_coz,
)

ProgressCallback = Callable[[int], None]
MessageCallback = Callable[[str], None]


def birlestir(
    dosyalar: List[str],
    cikti: str,
    *,
    sayfa_plani: Optional[Sequence[Tuple[str, int]]] = None,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    if not dosyalar:
        raise ValueError("En az bir PDF dosyası seçin.")

    hedef = fitz.open()
    acik: dict[str, fitz.Document] = {}
    try:
        if sayfa_plani:
            plan = list(sayfa_plani)
            if len(plan) < 1:
                raise ValueError("Birleştirilecek en az bir sayfa gerekir.")
            toplam = len(plan)
            for i, (yol, sayfa_no) in enumerate(plan):
                ilerleme(
                    progress_callback,
                    int((i / toplam) * 85),
                    message_callback,
                    f"Sayfa ekleniyor: {os.path.basename(yol)} — {sayfa_no + 1}",
                )
                if yol not in acik:
                    acik[yol] = fitz.open(yol)
                hedef.insert_pdf(acik[yol], from_page=sayfa_no, to_page=sayfa_no)
        else:
            if len(dosyalar) < 2:
                raise ValueError("Birleştirmek için en az iki PDF gerekir.")
            toplam = len(dosyalar)
            for i, yol in enumerate(dosyalar):
                ilerleme(
                    progress_callback,
                    int((i / toplam) * 85),
                    message_callback,
                    f"Birleştiriliyor: {os.path.basename(yol)}",
                )
                kaynak = fitz.open(yol)
                hedef.insert_pdf(kaynak)
                kaynak.close()

        ilerleme(progress_callback, 95, message_callback, "Kaydediliyor…")
        dosya_kaydet(hedef, cikti, garbage=4, deflate=True)
    finally:
        for belge in acik.values():
            belge.close()
        hedef.close()

    ilerleme(progress_callback, 100, message_callback, "Tamamlandı.")
    return cikti


def ayir(
    kaynak: str,
    aralik_metni: str,
    cikti_klasoru: str,
    *,
    dosya_on_ek: str = "bolum_",
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> List[str]:
    belge = dosya_ac(kaynak)
    try:
        segmentler = aralik_segmentleri_coz(aralik_metni, belge.page_count)
        klasor = Path(cikti_klasoru)
        klasor.mkdir(parents=True, exist_ok=True)
        kaynak_adi = Path(kaynak).stem
        cikti_dosyalari: List[str] = []
        toplam = len(segmentler)

        for idx, sayfalar in enumerate(segmentler, start=1):
            ilerleme(
                progress_callback,
                int(((idx - 1) / toplam) * 90),
                message_callback,
                f"Bölüm {idx}/{toplam} oluşturuluyor…",
            )
            yeni = fitz.open()
            for s in sayfalar:
                yeni.insert_pdf(belge, from_page=s, to_page=s)

            hedef = klasor / f"{kaynak_adi}_{dosya_on_ek}{idx}.pdf"
            dosya_kaydet(yeni, str(hedef), garbage=4, deflate=True)
            yeni.close()
            cikti_dosyalari.append(str(hedef))
    finally:
        belge.close()

    ilerleme(progress_callback, 100, message_callback, f"{len(cikti_dosyalari)} dosya oluşturuldu.")
    return cikti_dosyalari


def sayfa_sil(
    kaynak: str,
    sayfa_metni: str,
    cikti: str,
    *,
    sayfa_plani: Optional[Sequence[Tuple[str, int]]] = None,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    belge = dosya_ac(kaynak)
    try:
        if sayfa_plani:
            silinecek = sorted({s for y, s in sayfa_plani if y == kaynak})
        else:
            silinecek = sayfa_listesi_coz(sayfa_metni, belge.page_count)
        if len(silinecek) >= belge.page_count:
            raise ValueError("Tüm sayfalar silinemez; en az bir sayfa kalmalı.")

        ilerleme(progress_callback, 30, message_callback, f"{len(silinecek)} sayfa siliniyor…")
        belge.delete_pages(silinecek)
        ilerleme(progress_callback, 80, message_callback, "Kaydediliyor…")
        dosya_kaydet(belge, cikti, garbage=4, deflate=True)
    finally:
        belge.close()

    ilerleme(progress_callback, 100, message_callback, "Tamamlandı.")
    return cikti


def ayikla(
    kaynak: str,
    sayfa_metni: str,
    cikti: str,
    *,
    sayfa_plani: Optional[Sequence[Tuple[str, int]]] = None,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    belge = dosya_ac(kaynak)
    try:
        if sayfa_plani:
            tutulacak = [s for y, s in sayfa_plani if y == kaynak]
            if not tutulacak:
                raise ValueError("Ön izlemeden en az bir sayfa seçin.")
        else:
            tutulacak = sayfa_listesi_coz(sayfa_metni, belge.page_count)
        yeni = fitz.open()
        toplam = len(tutulacak)

        for i, s in enumerate(tutulacak):
            ilerleme(
                progress_callback,
                int((i / max(toplam, 1)) * 85),
                message_callback,
                f"Sayfa {s + 1} ekleniyor…",
            )
            yeni.insert_pdf(belge, from_page=s, to_page=s)

        ilerleme(progress_callback, 95, message_callback, "Kaydediliyor…")
        dosya_kaydet(yeni, cikti, garbage=4, deflate=True)
        yeni.close()
    finally:
        belge.close()

    ilerleme(progress_callback, 100, message_callback, "Tamamlandı.")
    return cikti
