"""Paylaşılan yapay zeka API ayarları bileşeni."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.ai_settings import AISettings, ayarlari_kaydet, ayarlari_yukle
from gui.widgets.yardim_ipucu import YardimButonu

BILGI_METNI = (
    "Şu an API anahtarı vermeniz zorunlu değil. OpenAI/Anthropic özellikleri anahtar "
    "girildiğinde çalışır. Ücretsiz yerel deneme için Ollama kurup «Yerel Ollama» "
    "seçin (localhost:11434). Karşılaştırma (metinsel) anahtarsız çalışır."
)


class AiAyarlarCercevesi(QFrame):
    """Tüm AI panellerinde üstte gösterilen ayarlar."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("aiSettingsBox")
        self._ayarlar = ayarlari_yukle()

        kok = QVBoxLayout(self)
        kok.setContentsMargins(12, 12, 12, 12)
        kok.setSpacing(10)

        ust = QHBoxLayout()
        baslik = QLabel("Yapay zeka bağlantısı")
        baslik.setObjectName("aiSettingsTitle")
        ust.addWidget(baslik)
        ust.addWidget(
            YardimButonu(
                "OpenAI veya Anthropic API anahtarı girebilir, ya da ücretsiz "
                "yerel Ollama kullanabilirsiniz. Ayarlar bilgisayarınıza kaydedilir."
            )
        )
        ust.addStretch()
        kok.addLayout(ust)

        bilgi = QLabel(BILGI_METNI)
        bilgi.setObjectName("aiInfoBanner")
        bilgi.setWordWrap(True)
        kok.addWidget(bilgi)

        satir1 = QHBoxLayout()
        self._saglayici = QComboBox()
        self._saglayici.addItem("Yerel Ollama (ücretsiz)", "ollama")
        self._saglayici.addItem("OpenAI", "openai")
        self._saglayici.addItem("Anthropic", "anthropic")
        satir1.addWidget(QLabel("Sağlayıcı"))
        satir1.addWidget(self._saglayici, stretch=1)
        kok.addLayout(satir1)

        self._api = QLineEdit()
        self._api.setEchoMode(QLineEdit.EchoMode.Password)
        self._api.setPlaceholderText("sk-… (OpenAI / Anthropic — şimdilik boş bırakılabilir)")
        kok.addWidget(QLabel("API anahtarı"))
        kok.addWidget(self._api)

        self._model = QLineEdit()
        self._model.setPlaceholderText("gpt-4o-mini veya claude-3-5-haiku-20241022")
        kok.addWidget(QLabel("Bulut model adı"))
        kok.addWidget(self._model)

        ollama_satir = QHBoxLayout()
        self._ollama_adres = QLineEdit()
        self._ollama_adres.setPlaceholderText("http://localhost:11434")
        self._ollama_model = QLineEdit()
        self._ollama_model.setPlaceholderText("llama3.2")
        ollama_satir.addWidget(self._ollama_adres, stretch=2)
        ollama_satir.addWidget(self._ollama_model, stretch=1)
        kok.addWidget(QLabel("Ollama adres / model"))
        kok.addLayout(ollama_satir)

        kaydet = QPushButton("Ayarları kaydet")
        kaydet.setObjectName("secondaryButton")
        kaydet.clicked.connect(self._kaydet)
        kok.addWidget(kaydet, alignment=Qt.AlignmentFlag.AlignRight)

        self._formdan_yukle()

    def _formdan_yukle(self) -> None:
        a = self._ayarlar
        idx = self._saglayici.findData(a.saglayici)
        self._saglayici.setCurrentIndex(idx if idx >= 0 else 0)
        self._api.setText(a.api_anahtari)
        self._model.setText(a.model)
        self._ollama_adres.setText(a.ollama_adres)
        self._ollama_model.setText(a.ollama_model)

    def _kaydet(self) -> None:
        self._ayarlar = AISettings(
            saglayici=self._saglayici.currentData(),
            api_anahtari=self._api.text().strip(),
            model=self._model.text().strip() or "gpt-4o-mini",
            ollama_adres=self._ollama_adres.text().strip() or "http://localhost:11434",
            ollama_model=self._ollama_model.text().strip() or "llama3.2",
            anthropic_model="claude-3-5-haiku-20241022",
        )
        ayarlari_kaydet(self._ayarlar)

    def ayarlar(self) -> AISettings:
        self._kaydet()
        return self._ayarlar
