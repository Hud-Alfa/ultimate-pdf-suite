"""Akıllı araçlar — RAG sohbet, özet, çeviri, karşılaştırma."""

from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import fitz

from core.ai_settings import AISettings, ayarlari_yukle
from core.pdf_core import dosya_ac, dosya_kaydet, ilerleme
from modules.ai_llm import AIHizmetHatasi, baglanti_kontrol, sohbet_tamamla
from modules.ai_pdf_text import metin_parcala, pdf_metin_cikar, pdf_tam_metin
from modules.ai_rag import indeks_olustur, rag_soru

ProgressCallback = Callable[[int], None]
MessageCallback = Callable[[str], None]


def _ayarlar(kwargs: dict) -> AISettings:
    if "ayarlar" in kwargs and kwargs["ayarlar"] is not None:
        return kwargs["ayarlar"]
    return ayarlari_yukle()


def intelligence_indeks(
    kaynak: str,
    *,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    """RAG indeksi oluştur; önbellek yolu döner."""
    return indeks_olustur(
        kaynak,
        _ayarlar(kwargs),
        progress_callback=progress_callback,
        message_callback=message_callback,
    )


def intelligence_soru(
    soru: str,
    indeks_yolu: str,
    *,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    return rag_soru(
        soru,
        indeks_yolu,
        _ayarlar(kwargs),
        progress_callback=progress_callback,
        message_callback=message_callback,
    )


def yapay_zeka_ozet(
    kaynak: str,
    *,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    ayarlar = _ayarlar(kwargs)
    baglanti_kontrol(ayarlar)

    if message_callback:
        message_callback("PDF okunuyor…")
    tam = pdf_tam_metin(kaynak, progress_callback=progress_callback, message_callback=message_callback)
    parcalar = metin_parcala(tam, parca_boyutu=4000)

    if not parcalar:
        raise ValueError("Özetlenecek metin yok.")

    ara_ozetler: List[str] = []
    toplam = len(parcalar)
    for i, parca in enumerate(parcalar):
        ilerleme(
            progress_callback,
            int((i / toplam) * 80),
            message_callback,
            f"Bölüm {i + 1}/{toplam} özetleniyor…",
        )
        ozet = sohbet_tamamla(
            ayarlar,
            [
                {
                    "role": "system",
                    "content": "Sen bir belge özetleme uzmanısın. Türkçe, maddeler halinde özet yaz.",
                },
                {"role": "user", "content": f"Bu bölümü özetle:\n\n{parca}"},
            ],
            sicaklik=0.3,
        )
        ara_ozetler.append(ozet)

    if message_callback:
        message_callback("Yönetici özeti birleştiriliyor…")

    birlesik = sohbet_tamamla(
        ayarlar,
        [
            {
                "role": "system",
                "content": (
                    "Bölüm özetlerinden tek bir yönetici özeti oluştur. "
                    "Giriş, bulgular, sonuç başlıkları kullan. Türkçe."
                ),
            },
            {
                "role": "user",
                "content": "\n\n".join(f"### Bölüm {i+1}\n{o}" for i, o in enumerate(ara_ozetler)),
            },
        ],
        sicaklik=0.3,
    )
    ilerleme(progress_callback, 100, message_callback, "Özet tamamlandı.")
    return birlesik


def ceviri(
    kaynak: str,
    hedef_dil: str,
    cikti: str,
    *,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    ayarlar = _ayarlar(kwargs)
    baglanti_kontrol(ayarlar)

    kaynak_belge = dosya_ac(kaynak)
    yeni = fitz.open()
    try:
        toplam = kaynak_belge.page_count
        for i in range(toplam):
            ilerleme(
                progress_callback,
                int((i / max(toplam, 1)) * 90),
                message_callback,
                f"Sayfa {i + 1} çevriliyor…",
            )
            sayfa = kaynak_belge[i]
            bloklar = sayfa.get_text("dict").get("blocks", [])
            yeni_sayfa = yeni.new_page(width=sayfa.rect.width, height=sayfa.rect.height)

            for blok in bloklar:
                if blok.get("type") != 0:
                    continue
                for satir in blok.get("lines", []):
                    for span in satir.get("spans", []):
                        metin = span.get("text", "").strip()
                        if not metin:
                            continue
                        cevirilmis = sohbet_tamamla(
                            ayarlar,
                            [
                                {
                                    "role": "system",
                                    "content": (
                                        f"Metni {hedef_dil} diline çevir. "
                                        "Yalnızca çeviriyi yaz; açıklama ekleme."
                                    ),
                                },
                                {"role": "user", "content": metin},
                            ],
                            sicaklik=0.2,
                            max_tokens=1024,
                        )
                        x0, y0, x1, y1 = span["bbox"]
                        boyut = span.get("size", 11)
                        yeni_sayfa.insert_textbox(
                            fitz.Rect(x0, y0, x1, y1 + 4),
                            cevirilmis,
                            fontsize=boyut,
                            fontname="helv",
                            color=(0, 0, 0),
                        )

        dosya_kaydet(yeni, cikti, garbage=4, deflate=True)
    finally:
        kaynak_belge.close()
        yeni.close()

    ilerleme(progress_callback, 100, message_callback, "Çeviri PDF kaydedildi.")
    return cikti


def karsilastir(
    dosya_a: str,
    dosya_b: str,
    *,
    mod: str = "metinsel",
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    if message_callback:
        message_callback("Metinler çıkarılıyor…")

    metin_a = pdf_tam_metin(dosya_a, progress_callback=lambda p: progress_callback and progress_callback(p // 2))
    metin_b = pdf_tam_metin(dosya_b, progress_callback=lambda p: progress_callback and progress_callback(50 + p // 2))

    satirlar_a = metin_a.splitlines()
    satirlar_b = metin_b.splitlines()
    diff = list(
        difflib.unified_diff(
            satirlar_a,
            satirlar_b,
            fromfile=Path(dosya_a).name,
            tofile=Path(dosya_b).name,
            lineterm="",
        )
    )
    diff_metin = "\n".join(diff)

    benzerlik = difflib.SequenceMatcher(None, metin_a, metin_b).ratio()
    sonuc: Dict[str, Any] = {
        "benzerlik_orani": round(benzerlik * 100, 1),
        "diff_metin": diff_metin,
        "ozet": f"Metinsel benzerlik: %{benzerlik * 100:.1f}",
    }

    if mod == "anlamsal":
        try:
            ayarlar = _ayarlar(kwargs)
            baglanti_kontrol(ayarlar)
            if message_callback:
                message_callback("Anlamsal analiz (LLM)…")
            llm_ozet = sohbet_tamamla(
                ayarlar,
                [
                    {
                        "role": "system",
                        "content": "İki belge arasındaki farkları Türkçe madde madde açıkla.",
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Belge A ({Path(dosya_a).name}):\n{metin_a[:12000]}\n\n"
                            f"Belge B ({Path(dosya_b).name}):\n{metin_b[:12000]}"
                        ),
                    },
                ],
                sicaklik=0.2,
            )
            sonuc["anlamsal_ozet"] = llm_ozet
        except AIHizmetHatasi as exc:
            sonuc["anlamsal_uyari"] = str(exc)

    ilerleme(progress_callback, 100, message_callback, "Karşılaştırma tamamlandı.")
    return sonuc


# Eski isimler
intelligence_analiz = intelligence_indeks
