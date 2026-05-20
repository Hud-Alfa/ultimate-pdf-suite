"""Yapay zeka sağlayıcı ayarları — diske kayıt."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class AISettings:
    saglayici: str = "ollama"  # openai | anthropic | ollama
    api_anahtari: str = ""
    model: str = "gpt-4o-mini"
    ollama_adres: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    anthropic_model: str = "claude-3-5-haiku-20241022"

    def hazir_mi(self) -> bool:
        if self.saglayici == "ollama":
            return bool(self.ollama_model.strip())
        return bool(self.api_anahtari.strip())

    def saglayici_etiket(self) -> str:
        return {"openai": "OpenAI", "anthropic": "Anthropic", "ollama": "Ollama (yerel)"}.get(
            self.saglayici, self.saglayici
        )


def ayarlar_dosyasi() -> Path:
    klasor = Path.home() / ".ultimate_pdf_suite"
    klasor.mkdir(parents=True, exist_ok=True)
    return klasor / "ai_settings.json"


def ayarlari_yukle() -> AISettings:
    yol = ayarlar_dosyasi()
    if not yol.is_file():
        return AISettings()
    try:
        veri = json.loads(yol.read_text(encoding="utf-8"))
        return AISettings(**{k: v for k, v in veri.items() if k in AISettings.__dataclass_fields__})
    except (json.JSONDecodeError, TypeError):
        return AISettings()


def ayarlari_kaydet(ayarlar: AISettings) -> None:
    ayarlar_dosyasi().write_text(
        json.dumps(asdict(ayarlar), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
