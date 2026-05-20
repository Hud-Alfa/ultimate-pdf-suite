"""Güvenlik ve optimizasyon — koru, kilit aç, imzala, küçült, iyileştir, onar."""

from __future__ import annotations

import io
import os
from typing import Any, Callable, Optional

import fitz

from core.pdf_core import dosya_ac, dosya_kaydet, ilerleme

ProgressCallback = Callable[[int], None]
MessageCallback = Callable[[str], None]


def koru(
    kaynak: str,
    cikti: str,
    sifre: str,
    *,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    """AES-256 ile PDF şifreler."""
    if len(sifre) < 4:
        raise ValueError("Şifre en az 4 karakter olmalıdır.")

    belge = dosya_ac(kaynak)
    try:
        ilerleme(progress_callback, 30, message_callback, "AES-256 şifreleme uygulanıyor…")
        izinler = (
            fitz.PDF_PERM_PRINT
            | fitz.PDF_PERM_COPY
            | fitz.PDF_PERM_ANNOTATE
            | fitz.PDF_PERM_ACCESSIBILITY
        )
        belge.save(
            cikti,
            encryption=fitz.PDF_ENCRYPT_AES_256,
            user_pw=sifre,
            owner_pw=sifre,
            permissions=izinler,
            garbage=4,
            deflate=True,
        )
    finally:
        belge.close()

    ilerleme(progress_callback, 100, message_callback, "PDF korundu.")
    return cikti


def kilit_ac(
    kaynak: str,
    cikti: str,
    sifre: str,
    *,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    """Bilinen şifreyle korumayı kaldırır (şifre kırma değildir)."""
    if not sifre:
        raise ValueError("Mevcut PDF şifresini girin.")

    belge = fitz.open(kaynak)
    try:
        if belge.is_encrypted or belge.needs_pass:
            ilerleme(progress_callback, 20, message_callback, "Şifre doğrulanıyor…")
            sonuc = belge.authenticate(sifre)
            if not sonuc:
                raise ValueError("Şifre hatalı. Yalnızca doğru şifreyle kilit açılabilir.")

        ilerleme(progress_callback, 60, message_callback, "Koruma kaldırılıyor…")
        belge.save(cikti, encryption=fitz.PDF_ENCRYPT_NONE, garbage=4, deflate=True)
    finally:
        belge.close()

    ilerleme(progress_callback, 100, message_callback, "Kilit açıldı — şifresiz PDF kaydedildi.")
    return cikti


def imzala(
    kaynak: str,
    cikti: str,
    *,
    imza_yolu: str,
    son_sayfa: bool = True,
    sayfa_no: int = 1,
    x: float = 72,
    y: float = 650,
    genislik: float = 150,
    yukseklik: float = 60,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    """Görsel imza damgasını PDF'e ekler (görsel onay; PKI sertifikası değil)."""
    if not imza_yolu or not os.path.isfile(imza_yolu):
        raise FileNotFoundError("İmza görseli seçin (PNG veya JPG).")

    belge = dosya_ac(kaynak)
    try:
        if son_sayfa:
            hedef = belge.page_count - 1
        else:
            hedef = max(0, min(sayfa_no - 1, belge.page_count - 1))

        ilerleme(
            progress_callback,
            40,
            message_callback,
            f"İmza ekleniyor (sayfa {hedef + 1})…",
        )
        sayfa = belge[hedef]
        dik = fitz.Rect(x, y, x + genislik, y + yukseklik)
        sayfa.insert_image(dik, filename=imza_yolu, overlay=True, keep_proportion=True)
        dosya_kaydet(belge, cikti, garbage=4, deflate=True)
    finally:
        belge.close()

    ilerleme(progress_callback, 100, message_callback, "İmza eklendi.")
    return cikti


def kucult(
    kaynak: str,
    cikti: str,
    *,
    dpi_hedef: int = 96,
    metadata_temizle: bool = True,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    """Metadata temizler ve görselleri hedef DPI'ya düşürerek sıkıştırır."""
    belge = dosya_ac(kaynak)
    try:
        if metadata_temizle:
            ilerleme(progress_callback, 15, message_callback, "Metadata temizleniyor…")
            belge.set_metadata({})

        ilerleme(progress_callback, 40, message_callback, "Görseller sıkıştırılıyor…")
        try:
            belge.rewrite_images(
                dpi_threshold=int(dpi_hedef) + 30,
                dpi_target=int(dpi_hedef),
                quality=60,
            )
        except (AttributeError, TypeError):
            pass

        ilerleme(progress_callback, 80, message_callback, "Kaydediliyor…")
        dosya_kaydet(belge, cikti, garbage=4, deflate=True, clean=True)
    finally:
        belge.close()

    ilerleme(progress_callback, 100, message_callback, "Küçültme tamamlandı.")
    return cikti


def iyilestir(
    kaynak: str,
    cikti: str,
    *,
    kontrast: float = 1.35,
    parlaklik: float = 1.05,
    cozunurluk: float = 2.0,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    """Taranmış/soluk sayfaların kontrastını artırır (Pillow)."""
    try:
        from PIL import Image, ImageEnhance
    except ImportError as exc:
        raise ImportError("İyileştirme için Pillow gerekir: pip install Pillow") from exc

    kaynak_belge = dosya_ac(kaynak)
    yeni = fitz.open()
    try:
        toplam = kaynak_belge.page_count
        for i in range(toplam):
            ilerleme(
                progress_callback,
                int((i / max(toplam, 1)) * 85),
                message_callback,
                f"Sayfa {i + 1} iyileştiriliyor…",
            )
            sayfa = kaynak_belge[i]
            mat = fitz.Matrix(cozunurluk, cozunurluk)
            pix = sayfa.get_pixmap(matrix=mat, alpha=False)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            img = ImageEnhance.Contrast(img).enhance(kontrast)
            img = ImageEnhance.Brightness(img).enhance(parlaklik)

            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85, optimize=True)
            buf.seek(0)

            yeni_sayfa = yeni.new_page(width=sayfa.rect.width, height=sayfa.rect.height)
            yeni_sayfa.insert_image(yeni_sayfa.rect, stream=buf.read())

        dosya_kaydet(yeni, cikti, garbage=4, deflate=True)
    finally:
        kaynak_belge.close()
        yeni.close()

    ilerleme(progress_callback, 100, message_callback, "İyileştirme tamamlandı.")
    return cikti


def onar(
    kaynak: str,
    cikti: str,
    *,
    progress_callback: Optional[ProgressCallback] = None,
    message_callback: Optional[MessageCallback] = None,
    **kwargs: Any,
) -> str:
    """Bozuk XREF / yapı sorunlarını yeniden kayıtla düzeltmeye çalışır."""
    ilerleme(progress_callback, 20, message_callback, "PDF açılıyor…")
    belge = None
    son_hata: Optional[Exception] = None

    for yontem in ("normal", "onarma"):
        try:
            if yontem == "normal":
                belge = fitz.open(kaynak)
            else:
                with open(kaynak, "rb") as f:
                    veri = f.read()
                belge = fitz.open(stream=veri, filetype="pdf")
            break
        except Exception as exc:  # noqa: BLE001
            son_hata = exc
            if belge:
                belge.close()
            belge = None

    if belge is None:
        raise ValueError(f"PDF onarılamadı: {son_hata}")

    try:
        ilerleme(progress_callback, 50, message_callback, "Yapı yeniden yazılıyor…")
        belge.save(
            cikti,
            garbage=4,
            deflate=True,
            clean=True,
            expand=0,
            pretty=False,
        )
    finally:
        belge.close()

    ilerleme(progress_callback, 100, message_callback, "Onarım tamamlandı.")
    return cikti
