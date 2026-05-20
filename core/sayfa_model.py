"""Sayfa referansları — ön izlemeden işlemlere aktarılır."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

SayfaPlani = List[Tuple[str, int]]  # (dosya_yolu, 0_tabanlı_sayfa)


@dataclass(frozen=True)
class SayfaRef:
    dosya: str
    sayfa: int  # 0 tabanlı

    def etiket(self) -> str:
        return f"{Path(self.dosya).name} — s.{self.sayfa + 1}"

    def tup(self) -> Tuple[str, int]:
        return (self.dosya, self.sayfa)


def plana_cevir(sayfalar: Sequence[SayfaRef]) -> SayfaPlani:
    return [s.tup() for s in sayfalar]


def tek_dosyadan_indeksler(sayfalar: Sequence[SayfaRef]) -> List[int]:
    """Tek PDF için 0 tabanlı seçili sayfa indeksleri."""
    if not sayfalar:
        return []
    dosya = sayfalar[0].dosya
    return [s.sayfa for s in sayfalar if s.dosya == dosya]


def metne_cevir(sayfalar: Sequence[SayfaRef], *, tek_dosya: str) -> str:
    """1 tabanlı virgüllü sayfa metni (tek dosya)."""
    indeksler = sorted(
        s.sayfa + 1 for s in sayfalar if s.dosya == tek_dosya
    )
    if not indeksler:
        return ""
    return ",".join(str(n) for n in indeksler)


def metinden_sec(
    metin: str,
    tum_sayfalar: Sequence[SayfaRef],
    *,
    tek_dosya: str,
) -> List[SayfaRef]:
    """Metinden seçim — galeri öğeleriyle eşleştirir."""
    from core.pdf_core import sayfa_listesi_coz

    if not metin.strip():
        return []
    dosya_sayfalari = [s for s in tum_sayfalar if s.dosya == tek_dosya]
    if not dosya_sayfalari:
        return []
    toplam = max(s.sayfa for s in dosya_sayfalari) + 1
    indeksler = set(sayfa_listesi_coz(metin, toplam))
    return [s for s in dosya_sayfalari if s.sayfa in indeksler]
