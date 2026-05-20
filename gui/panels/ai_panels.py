"""Akıllı araçlar panelleri."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from modules import ai_tools as ai
from gui.panels.base import TemelAracPaneli
from gui.panels.ai_ayarlar import AiAyarlarCercevesi
from gui.sayfa_galerisi import SayfaGalerisiPaneli


class _AiTemel(TemelAracPaneli):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ai_ayar: AiAyarlarCercevesi | None = None

    def _ai_ust_kur(self) -> AiAyarlarCercevesi:
        self._ai_ayar = AiAyarlarCercevesi()
        self._form.insertRow(0, "", self._ai_ayar)
        self._onizleme.hide()
        return self._ai_ayar


class IntelligencePaneli(_AiTemel):
    def __init__(self, **kw):
        super().__init__(
            "Intelligence",
            "Akıllı Araçlar",
            "PDF ile sohbet edin (RAG). Önce indeksleyin, sonra soru sorun.",
            **kw,
        )
        self._indeks_yolu: str = ""

    def _form_olustur(self) -> None:
        self._ai_ust_kur()
        self._kaynak, _ = self._dosya_alani("PDF", onizle=True, yardim="Sohbet edilecek belge.")
        self._indeks_btn = QPushButton("PDF'i indeksle (RAG)")
        self._indeks_btn.setObjectName("secondaryButton")
        self._indeks_btn.clicked.connect(self._indeksle)
        self._form.addRow("", self._indeks_btn)

        self._sohbet = QTextEdit()
        self._sohbet.setReadOnly(True)
        self._sohbet.setPlaceholderText("Sohbet geçmişi…")
        self._sohbet.setMinimumHeight(220)
        self._form.addRow("Sohbet", self._sohbet)

        soru_satir = QHBoxLayout()
        self._soru = QLineEdit()
        self._soru.setPlaceholderText("Belge hakkında sorunuzu yazın…")
        self._gonder = QPushButton("Gönder")
        self._gonder.setObjectName("primaryButton")
        self._gonder.clicked.connect(self._soru_gonder)
        soru_satir.addWidget(self._soru, stretch=1)
        soru_satir.addWidget(self._gonder)
        w = QWidget()
        w.setLayout(soru_satir)
        self._form.addRow("", w)

        self._baslat.hide()
        self._onizleme_ayarla(SayfaGalerisiPaneli.MOD_IZLEME)

    def _indeksle(self) -> None:
        try:
            kaynak = self._metin_zorunlu(self._kaynak, "PDF")
            ayarlar = self._ai_ayar.ayarlar() if self._ai_ayar else None
            paket = (ai.intelligence_indeks, [kaynak], {"ayarlar": ayarlar})
            self.islem_istendi.emit(paket)
        except ValueError as exc:
            self._durum_goster(str(exc), hata=True)

    def _soru_gonder(self) -> None:
        soru = self._soru.text().strip()
        if not soru:
            return
        if not self._indeks_yolu:
            self._durum_goster("Önce PDF'i indeksleyin.", hata=True)
            return
        self._sohbet.append(f"\n\n**Siz:** {soru}")
        ayarlar = self._ai_ayar.ayarlar() if self._ai_ayar else None
        paket = (
            ai.intelligence_soru,
            [soru, self._indeks_yolu],
            {"ayarlar": ayarlar},
        )
        self.islem_istendi.emit(paket)

    def islem_hazirla(self):
        raise ValueError("Bu panel doğrudan indeksle veya gönder kullanır.")

    def islem_bitti(self, sonuc) -> None:
        if isinstance(sonuc, str) and sonuc.endswith(".pkl"):
            self._indeks_yolu = sonuc
            self._durum_goster("İndeks hazır. Soru sorabilirsiniz.")
            self._sohbet.append("\n\n**Sistem:** PDF indekslendi. Soru yazabilirsiniz.")
        else:
            self._sohbet.append(f"\n\n**Asistan:** {sonuc}")
            self._durum_goster("Yanıt alındı.")
        self._soru.clear()


class OzetPaneli(_AiTemel):
    def __init__(self, **kw):
        super().__init__(
            "Yapay Zeka Özet",
            "Akıllı Araçlar",
            "Uzun PDF'leri bölüm bölüm okuyup yönetici özeti üretir.",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._ai_ust_kur()
        self._kaynak, _ = self._dosya_alani("PDF", onizle=True)
        self._sonuc = QTextEdit()
        self._sonuc.setReadOnly(True)
        self._sonuc.setMinimumHeight(200)
        self._form.addRow("Özet", self._sonuc)
        self._baslat.setText("Özet oluştur")

    def islem_hazirla(self):
        ayarlar = self._ai_ayar.ayarlar() if self._ai_ayar else None
        return (
            ai.yapay_zeka_ozet,
            [self._metin_zorunlu(self._kaynak, "PDF")],
            {"ayarlar": ayarlar},
        )

    def islem_bitti(self, sonuc) -> None:
        self._sonuc.setPlainText(str(sonuc))
        super().islem_bitti(sonuc)


class CeviriPaneli(_AiTemel):
    def __init__(self, **kw):
        super().__init__(
            "Çeviri",
            "Akıllı Araçlar",
            "PDF metin bloklarını LLM ile çevirir (yapılandırılmış sayfalar).",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._ai_ust_kur()
        self._kaynak, _ = self._dosya_alani("PDF", onizle=True)
        self._dil = QComboBox()
        self._dil.addItems(
            ["İngilizce", "Almanca", "Fransızca", "Arapça", "İspanyolca", "Rusça"]
        )
        self._satir_ekle("Hedef dil", self._dil)
        self._cikti = self._kaydet_alani("Çevrilmiş PDF")

    def islem_hazirla(self):
        ayarlar = self._ai_ayar.ayarlar() if self._ai_ayar else None
        return (
            ai.ceviri,
            [
                self._metin_zorunlu(self._kaynak, "PDF"),
                self._dil.currentText(),
                self._metin_zorunlu(self._cikti, "Çıktı"),
            ],
            {"ayarlar": ayarlar},
        )


class KarsilastirmaPaneli(_AiTemel):
    def __init__(self, **kw):
        super().__init__(
            "Karşılaştırma",
            "Akıllı Araçlar",
            "İki PDF arasındaki farkları metinsel (ve isteğe bağlı anlamsal) gösterir.",
            **kw,
        )

    def _form_olustur(self) -> None:
        self._ai_ust_kur()
        self._a, _ = self._dosya_alani("PDF A")
        self._b, _ = self._dosya_alani("PDF B")
        self._mod = QComboBox()
        self._mod.addItem("Metinsel diff (anahtarsız)", "metinsel")
        self._mod.addItem("Metinsel + anlamsal özet (API)", "anlamsal")
        self._satir_ekle("Mod", self._mod, yardim="Metinsel mod API gerektirmez.")
        self._sonuc = QTextEdit()
        self._sonuc.setReadOnly(True)
        self._sonuc.setMinimumHeight(240)
        self._form.addRow("Sonuç", self._sonuc)

    def islem_hazirla(self):
        ayarlar = self._ai_ayar.ayarlar() if self._ai_ayar else None
        return (
            ai.karsilastir,
            [self._metin_zorunlu(self._a, "PDF A"), self._metin_zorunlu(self._b, "PDF B")],
            {"mod": self._mod.currentData(), "ayarlar": ayarlar},
        )

    def islem_bitti(self, sonuc) -> None:
        if isinstance(sonuc, dict):
            metin = sonuc.get("ozet", "") + "\n\n"
            if sonuc.get("anlamsal_ozet"):
                metin += "=== Anlamsal özet ===\n" + sonuc["anlamsal_ozet"] + "\n\n"
            if sonuc.get("anlamsal_uyari"):
                metin += "=== Uyarı ===\n" + sonuc["anlamsal_uyari"] + "\n\n"
            metin += "=== Diff ===\n" + sonuc.get("diff_metin", "")
            self._sonuc.setPlainText(metin)
        super().islem_bitti(sonuc)
