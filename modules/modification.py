"""Düzenleme — kırp, döndür, filigran, numara, formlar, düzelt, düzenle (PyMuPDF)."""

from __future__ import annotations

import os
from typing import Any, Callable, Dict, List, Optional, Tuple

import fitz

from core.pdf_core import (
    dosya_ac,
    dosya_kaydet,
    ilerleme,
    mm_to_pt,
    sayfa_listesi_coz,
)

ProgressCallback = Callable[[int], None]
MessageCallback = Callable[[str], None]


def _hedef_sayfalar(belge: fitz.Document, sayfa_metni: str) -> List[int]:
    return sayfa_listesi_coz(sayfa_metni, belge.page_count, bos_ise_tumu=True)


def kirp(
    kaynak: str,
    cikti: str,
    *,
    ust_mm: float = 0,
    alt_mm: float = 0,
    sol_mm: float = 0,
    sag_mm: float = 0,
    sayfa_metni: str = "",
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    belge = dosya_ac(kaynak)
    try:
        ust, alt, sol, sag = mm_to_pt(ust_mm), mm_to_pt(alt_mm), mm_to_pt(sol_mm), mm_to_pt(sag_mm)
        sayfalar = _hedef_sayfalar(belge, sayfa_metni)
        toplam = len(sayfalar)

        for i, s in enumerate(sayfalar):
            ilerleme(
                progress_callback,
                int((i / max(toplam, 1)) * 85),
                message_callback,
                f"Sayfa {s + 1} kırpılıyor…",
            )
            sayfa = belge[s]
            r = sayfa.rect
            yeni = fitz.Rect(r.x0 + sol, r.y0 + ust, r.x1 - sag, r.y1 - alt)
            if yeni.width < 20 or yeni.height < 20:
                raise ValueError(f"Sayfa {s + 1}: kenar boşlukları çok büyük.")
            sayfa.set_cropbox(yeni)

        dosya_kaydet(belge, cikti, garbage=4, deflate=True)
    finally:
        belge.close()

    ilerleme(progress_callback, 100, message_callback, "Tamamlandı.")
    return cikti


def dondur(
    kaynak: str,
    cikti: str,
    aci: int = 90,
    *,
    sayfa_metni: str = "",
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    if aci not in (90, 180, 270):
        raise ValueError("Açı yalnızca 90, 180 veya 270 olabilir.")

    belge = dosya_ac(kaynak)
    try:
        sayfalar = _hedef_sayfalar(belge, sayfa_metni)
        toplam = len(sayfalar)

        for i, s in enumerate(sayfalar):
            ilerleme(
                progress_callback,
                int((i / max(toplam, 1)) * 85),
                message_callback,
                f"Sayfa {s + 1} döndürülüyor…",
            )
            sayfa = belge[s]
            mevcut = int(sayfa.rotation) % 360
            sayfa.set_rotation((mevcut + aci) % 360)

        dosya_kaydet(belge, cikti, garbage=4, deflate=True)
    finally:
        belge.close()

    ilerleme(progress_callback, 100, message_callback, "Tamamlandı.")
    return cikti


def filigran_ekle(
    kaynak: str,
    cikti: str,
    *,
    metin: str = "",
    logo_yolu: str = "",
    saydam: float = 0.25,
    sayfa_metni: str = "",
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    if not metin.strip() and not logo_yolu.strip():
        raise ValueError("Metin veya PNG logo yolu girin.")

    belge = dosya_ac(kaynak)
    try:
        sayfalar = _hedef_sayfalar(belge, sayfa_metni)
        opak = max(0.05, min(1.0, saydam))
        toplam = len(sayfalar)

        for i, s in enumerate(sayfalar):
            ilerleme(
                progress_callback,
                int((i / max(toplam, 1)) * 85),
                message_callback,
                f"Sayfa {s + 1} filigran…",
            )
            sayfa = belge[s]
            r = sayfa.rect

            if logo_yolu.strip():
                if not os.path.isfile(logo_yolu):
                    raise FileNotFoundError(f"Logo bulunamadı: {logo_yolu}")
                genislik = r.width * 0.45
                yukseklik = genislik * 0.6
                x0 = (r.width - genislik) / 2
                y0 = (r.height - yukseklik) / 2
                img_rect = fitz.Rect(x0, y0, x0 + genislik, y0 + yukseklik)
                sayfa.insert_image(img_rect, filename=logo_yolu, overlay=True)
            else:
                metin_rect = fitz.Rect(r.x0, r.y0, r.x1, r.y1)
                sayfa.insert_textbox(
                    metin_rect,
                    metin,
                    fontsize=48,
                    fontname="helv",
                    color=(0.55, 0.55, 0.55),
                    align=fitz.TEXT_ALIGN_CENTER,
                    rotate=45,
                    overlay=True,
                    opacity=opak,
                )

        dosya_kaydet(belge, cikti, garbage=4, deflate=True)
    finally:
        belge.close()

    ilerleme(progress_callback, 100, message_callback, "Tamamlandı.")
    return cikti


def sayfa_numarasi(
    kaynak: str,
    cikti: str,
    *,
    konum: str = "alt_orta",
    sayfa_metni: str = "",
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    belge = dosya_ac(kaynak)
    try:
        sayfalar = _hedef_sayfalar(belge, sayfa_metni)
        toplam_sayfa = belge.page_count
        toplam = len(sayfalar)

        for i, s in enumerate(sayfalar):
            ilerleme(
                progress_callback,
                int((i / max(toplam, 1)) * 85),
                message_callback,
                f"Sayfa {s + 1} numaralanıyor…",
            )
            sayfa = belge[s]
            r = sayfa.rect
            metin = f"{s + 1} / {toplam_sayfa}"
            fs = max(9, min(14, r.width / 50))

            if konum == "alt_sol":
                nokta = fitz.Point(r.x0 + 36, r.y1 - 28)
            elif konum == "alt_sag":
                nokta = fitz.Point(r.x1 - 80, r.y1 - 28)
            else:
                nokta = fitz.Point(r.width / 2 - 25, r.y1 - 28)

            sayfa.insert_text(
                nokta,
                metin,
                fontsize=fs,
                fontname="helv",
                color=(0.2, 0.2, 0.2),
                overlay=True,
            )

        dosya_kaydet(belge, cikti, garbage=4, deflate=True)
    finally:
        belge.close()

    ilerleme(progress_callback, 100, message_callback, "Tamamlandı.")
    return cikti


def _alan_degerleri_coz(metin: str) -> Dict[str, str]:
    sonuc: Dict[str, str] = {}
    for satir in (metin or "").splitlines():
        satir = satir.strip()
        if not satir or "=" not in satir:
            continue
        anahtar, deger = satir.split("=", 1)
        sonuc[anahtar.strip()] = deger.strip()
    return sonuc


def formlar_isle(
    kaynak: str,
    cikti: str,
    *,
    alan_metni: str = "",
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    degerler = _alan_degerleri_coz(alan_metni)
    belge = dosya_ac(kaynak)
    try:
        guncellenen = 0
        sayfa_say = belge.page_count

        for s in range(sayfa_say):
            ilerleme(
                progress_callback,
                int((s / max(sayfa_say, 1)) * 80),
                message_callback,
                f"Formlar taranıyor (sayfa {s + 1})…",
            )
            for w in belge[s].widgets() or []:
                ad = w.field_name
                if ad and ad in degerler:
                    w.field_value = degerler[ad]
                    w.update()
                    guncellenen += 1

        if degerler and guncellenen == 0:
            raise ValueError("Eşleşen form alanı bulunamadı. Alan adlarını kontrol edin.")

        dosya_kaydet(belge, cikti, garbage=4, deflate=True)
    finally:
        belge.close()

    ilerleme(
        progress_callback,
        100,
        message_callback,
        f"Tamamlandı ({guncellenen} alan güncellendi).",
    )
    return cikti


def duzelt(
    kaynak: str,
    cikti: str,
    *,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    """Formları ve ek açıklamaları düzleştirir (flatten)."""
    belge = dosya_ac(kaynak)
    try:
        for s in range(belge.page_count):
            ilerleme(
                progress_callback,
                int((s / max(belge.page_count, 1)) * 70),
                message_callback,
                f"Sayfa {s + 1} düzleştiriliyor…",
            )
            sayfa = belge[s]
            sayfa.clean_contents()

            for w in sayfa.widgets() or []:
                w.update()
                w.field_flags = fitz.PDF_FIELD_IS_READ_ONLY

            for annot in sayfa.annots() or []:
                if annot.type[0] != fitz.PDF_ANNOT_WIDGET:
                    annot.set_flags(annot.flags | fitz.PDF_ANNOT_IS_PRINT)
                    annot.update()

        dosya_kaydet(belge, cikti, garbage=4, deflate=True, clean=True)
    finally:
        belge.close()

    ilerleme(progress_callback, 100, message_callback, "Düzleştirme tamamlandı.")
    return cikti


def duzenle(
    kaynak: str,
    cikti: str,
    *,
    tur: str = "metin",
    metin: str = "Örnek metin",
    x: float = 72,
    y: float = 72,
    genislik: float = 200,
    yukseklik: float = 40,
    sayfa_metni: str = "",
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    belge = dosya_ac(kaynak)
    try:
        sayfalar = _hedef_sayfalar(belge, sayfa_metni)
        if not sayfalar:
            sayfalar = [0]
        hedef = sayfalar[0]
        ilerleme(progress_callback, 40, message_callback, "İçerik ekleniyor…")

        sayfa = belge[hedef]
        rect = fitz.Rect(x, y, x + genislik, y + yukseklik)

        if tur == "metin":
            sayfa.insert_textbox(
                rect,
                metin,
                fontsize=12,
                fontname="helv",
                color=(0, 0, 0),
                align=fitz.TEXT_ALIGN_LEFT,
            )
        elif tur == "dikdortgen":
            sayfa.draw_rect(rect, color=(0.2, 0.4, 0.9), width=1.5)
        elif tur == "daire":
            sayfa.draw_oval(rect, color=(0.9, 0.3, 0.2), width=1.5)
        else:
            raise ValueError("Geçersiz tür: metin, dikdortgen veya daire.")

        dosya_kaydet(belge, cikti, garbage=4, deflate=True)
    finally:
        belge.close()

    ilerleme(progress_callback, 100, message_callback, "Tamamlandı.")
    return cikti
