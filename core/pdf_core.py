"""Ortak PyMuPDF (fitz) işlemleri — tüm modüller buradan yararlanır."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, List, Optional, Tuple

import fitz


def dosya_ac(yol: str) -> fitz.Document:
    """PDF belgesini açar."""
    if not os.path.isfile(yol):
        raise FileNotFoundError(f"Dosya bulunamadı: {yol}")
    return fitz.open(yol)


def dosya_kaydet(belge: fitz.Document, hedef: str, **secenekler: Any) -> None:
    """Belgeyi diske yazar."""
    hedef_yolu = Path(hedef)
    hedef_yolu.parent.mkdir(parents=True, exist_ok=True)
    belge.save(str(hedef_yolu), **secenekler)


def sayfa_sayisi(belge: fitz.Document) -> int:
    return belge.page_count


def belge_kapat(belge: fitz.Document) -> None:
    belge.close()


def mm_to_pt(mm: float) -> float:
    """Milimetreyi PDF noktasına çevirir."""
    return mm * 72.0 / 25.4


def sayfa_listesi_coz(
    metin: str,
    toplam: int,
    *,
    bos_ise_tumu: bool = False,
) -> List[int]:
    """
    '1,3,5-7' gibi ifadeleri 0 tabanlı sayfa indekslerine çevirir (giriş 1 tabanlı).
    """
    metin = (metin or "").strip()
    if not metin:
        if bos_ise_tumu and toplam > 0:
            return list(range(toplam))
        return []

    if metin.lower() in ("tumu", "tümü", "all", "*"):
        return list(range(toplam))

    sonuc: set[int] = set()
    for parca in metin.replace(" ", "").split(","):
        if not parca:
            continue
        if "-" in parca:
            bas, bit = parca.split("-", 1)
            s1, s2 = int(bas), int(bit)
            if s1 > s2:
                s1, s2 = s2, s1
            for n in range(s1, s2 + 1):
                if 1 <= n <= toplam:
                    sonuc.add(n - 1)
        else:
            n = int(parca)
            if 1 <= n <= toplam:
                sonuc.add(n - 1)

    if not sonuc:
        raise ValueError(f"Geçerli sayfa bulunamadı (toplam {toplam} sayfa).")
    return sorted(sonuc)


def aralik_segmentleri_coz(metin: str, toplam: int) -> List[List[int]]:
    """
    '1-3,5,8-10' → her virgül ayrımı ayrı bir çıktı dosyası için sayfa listesi.
    """
    metin = (metin or "").strip()
    if not metin:
        raise ValueError("En az bir sayfa aralığı girin (ör. 1-3,5-8).")

    segmentler: List[List[int]] = []
    for parca in metin.split(","):
        parca = parca.strip()
        if not parca:
            continue
        sayfalar = sayfa_listesi_coz(parca, toplam, bos_ise_tumu=False)
        if sayfalar:
            segmentler.append(sayfalar)

    if not segmentler:
        raise ValueError("Geçerli aralık bulunamadı.")
    return segmentler


def ilerleme(
    callback: Optional[Any],
    yuzde: int,
    mesaj: Optional[Any] = None,
    metin: str = "",
) -> None:
    if callback:
        callback(max(0, min(100, int(yuzde))))
    if mesaj and metin:
        mesaj(metin)
