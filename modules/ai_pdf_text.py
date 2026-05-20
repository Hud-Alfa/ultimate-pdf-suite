"""PDF metin çıkarma ve parçalama."""

from __future__ import annotations

from typing import Any, Callable, List, Optional, Tuple

import fitz

from core.pdf_core import dosya_ac, ilerleme

ProgressCallback = Optional[Callable[[int], None]]
MessageCallback = Optional[Callable[[str], None]]


def pdf_metin_cikar(
    pdf_yolu: str,
    *,
    progress_callback: ProgressCallback = None,
    message_callback: MessageCallback = None,
) -> List[Tuple[int, str]]:
    """(sayfa_no 1-tabanlı, metin) listesi."""
    belge = dosya_ac(pdf_yolu)
    sonuc: List[Tuple[int, str]] = []
    try:
        for i in range(belge.page_count):
            ilerleme(
                progress_callback,
                int((i / max(belge.page_count, 1)) * 100),
                message_callback,
                f"Metin okunuyor: sayfa {i + 1}",
            )
            metin = belge[i].get_text("text").strip()
            if metin:
                sonuc.append((i + 1, metin))
    finally:
        belge.close()
    return sonuc


def pdf_tam_metin(pdf_yolu: str, **kwargs: Any) -> str:
    parcalar = pdf_metin_cikar(pdf_yolu, **kwargs)
    return "\n\n".join(f"[Sayfa {s}]\n{t}" for s, t in parcalar)


def metin_parcala(
    metin: str,
    *,
    parca_boyutu: int = 3500,
    bindirme: int = 400,
) -> List[str]:
    if not metin.strip():
        return []
    parcalar: List[str] = []
    bas = 0
    uzunluk = len(metin)
    while bas < uzunluk:
        bit = min(bas + parca_boyutu, uzunluk)
        parcalar.append(metin[bas:bit])
        bas = bit - bindirme if bit < uzunluk else uzunluk
    return parcalar
