"""Sayfa yönetimi panelleri."""

from __future__ import annotations

from core.sayfa_model import plana_cevir

from PyQt6.QtWidgets import QLineEdit

from modules import organization as org
from gui.panels.base import TemelAracPaneli
from gui.sayfa_galerisi import SayfaGalerisiPaneli


class BirlestirPaneli(TemelAracPaneli):
    def __init__(self, **kw):
        super().__init__(
            "Birleştir",
            "Sayfa Yönetimi",
            "PDF'leri birleştirin. Sağdaki galeride sayfaları sürükleyerek sıralayın, "
            "istenmeyen sayfayı «Çıkar» ile kaldırın.",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._dosyalar, _ = self._dosya_alani("PDF dosyaları", coklu=True, onizle=True)
        self._cikti = self._kaydet_alani("Birleşik PDF")
        self._onizleme_ayarla(SayfaGalerisiPaneli.MOD_SIRA)

    def islem_hazirla(self):
        dosyalar = self._coklu_dosya(self._dosyalar)
        kwargs = self._birlestirme_plani_kwargs()
        plan = kwargs.get("sayfa_plani")
        if plan and len(plan) < 1:
            raise ValueError("Birleştirilecek en az bir sayfa kalmalı.")
        return (
            org.birlestir,
            [dosyalar, self._metin_zorunlu(self._cikti, "Çıktı")],
            kwargs,
        )


class AyirPaneli(TemelAracPaneli):
    def __init__(self, **kw):
        super().__init__(
            "Ayır",
            "Sayfa Yönetimi",
            "Virgülle ayrılmış aralıklar her biri ayrı PDF olur (ör. 1-3,5,8-10).",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._kaynak, _ = self._dosya_alani("Kaynak PDF", onizle=True)
        self._aralik = QLineEdit()
        self._aralik.setPlaceholderText("ör. 1-3,5,8-10")
        self._satir_ekle("Sayfa aralıkları", self._aralik)
        self._klasor, _ = self._dosya_alani("Çıktı klasörü", klasor=True)
        self._onizleme_bagla_secim(self._aralik)

    def islem_hazirla(self):
        return (
            org.ayir,
            [
                self._metin_zorunlu(self._kaynak, "Kaynak"),
                self._sayfa_metni_veya_secim(
                    self._aralik,
                    zorunlu_mesaj="Aralık girin veya ön izlemeden sayfa seçin.",
                ),
                self._metin_zorunlu(self._klasor, "Çıktı klasörü"),
            ],
            {},
        )


class SayfaSilPaneli(TemelAracPaneli):
    def __init__(self, **kw):
        super().__init__(
            "Sil",
            "Sayfa Yönetimi",
            "Silinecek sayfaları metin kutusuna yazın veya ön izlemede tıklayarak seçin.",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._kaynak, _ = self._dosya_alani("Kaynak PDF", onizle=True)
        self._sayfalar = QLineEdit()
        self._sayfalar.setPlaceholderText("ör. 2,5,8-10 veya galeriden seçin")
        self._satir_ekle("Silinecek sayfalar", self._sayfalar)
        self._cikti = self._kaydet_alani("Çıktı PDF")
        self._onizleme_bagla_secim(self._sayfalar)

    def islem_hazirla(self):
        kaynak = self._metin_zorunlu(self._kaynak, "Kaynak")
        kwargs = self._secim_plani_kwargs(kaynak)
        if kwargs:
            return (
                org.sayfa_sil,
                [kaynak, "", self._metin_zorunlu(self._cikti, "Çıktı")],
                kwargs,
            )
        return (
            org.sayfa_sil,
            [
                kaynak,
                self._sayfa_metni_veya_secim(
                    self._sayfalar,
                    zorunlu_mesaj="Silinecek sayfaları girin veya ön izlemeden seçin.",
                ),
                self._metin_zorunlu(self._cikti, "Çıktı"),
            ],
            {},
        )


class AyiklaPaneli(TemelAracPaneli):
    def __init__(self, **kw):
        super().__init__(
            "Ayıkla",
            "Sayfa Yönetimi",
            "Kalacak sayfaları metinle veya ön izlemede tıklayarak seçin (sıra korunur).",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._kaynak, _ = self._dosya_alani("Kaynak PDF", onizle=True)
        self._sayfalar = QLineEdit()
        self._sayfalar.setPlaceholderText("ör. 1,3,5-7 veya galeriden seçin")
        self._satir_ekle("Alınacak sayfalar", self._sayfalar)
        self._cikti = self._kaydet_alani("Çıktı PDF")
        self._onizleme_bagla_secim(self._sayfalar)

    def islem_hazirla(self):
        kaynak = self._metin_zorunlu(self._kaynak, "Kaynak")
        secili = self._onizleme.secili_refs()
        if secili:
            return (
                org.ayikla,
                [kaynak, "", self._metin_zorunlu(self._cikti, "Çıktı")],
                {"sayfa_plani": plana_cevir(secili)},
            )
        return (
            org.ayikla,
            [
                kaynak,
                self._sayfa_metni_veya_secim(
                    self._sayfalar,
                    zorunlu_mesaj="Alınacak sayfaları girin veya ön izlemeden seçin.",
                ),
                self._metin_zorunlu(self._cikti, "Çıktı"),
            ],
            {},
        )
