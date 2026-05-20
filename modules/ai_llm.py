"""Birleşik LLM istemcisi — OpenAI, Anthropic, Ollama."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

from core.ai_settings import AISettings


class AIHizmetHatasi(RuntimeError):
    pass


def _mesajlar(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [{"role": m["role"], "content": m["content"]} for m in messages]


def ollama_calisiyor_mu(ayarlar: AISettings, zaman_asimi: int = 3) -> bool:
    try:
        req = Request(f"{ayarlar.ollama_adres.rstrip('/')}/api/tags", method="GET")
        with urlopen(req, timeout=zaman_asimi) as yanit:
            return yanit.status == 200
    except (URLError, TimeoutError, OSError):
        return False


def baglanti_kontrol(ayarlar: AISettings) -> None:
    if not ayarlar.hazir_mi():
        raise AIHizmetHatasi(
            "API anahtarı veya Ollama modeli tanımlı değil.\n"
            "Üst bölümden OpenAI/Anthropic anahtarı girin veya yerel Ollama seçin.\n"
            "Şu an anahtar vermeden yalnızca «Karşılaştırma (metinsel)» tam yerel çalışır."
        )
    if ayarlar.saglayici == "ollama" and not ollama_calisiyor_mu(ayarlar):
        raise AIHizmetHatasi(
            f"Ollama'ya bağlanılamadı ({ayarlar.ollama_adres}).\n"
            "Ollama'yı başlatın: ollama serve — ve modeli indirin: ollama pull llama3.2"
        )
    if ayarlar.saglayici in ("openai", "anthropic") and not ayarlar.api_anahtari.strip():
        raise AIHizmetHatasi(
            f"{ayarlar.saglayici_etiket()} için API anahtarı gerekli. "
            "Anahtarı üst ayar bölümüne girin veya Ollama'ya geçin."
        )


def sohbet_tamamla(
    ayarlar: AISettings,
    messages: List[Dict[str, str]],
    *,
    sicaklik: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    baglanti_kontrol(ayarlar)
    msgs = _mesajlar(messages)

    if ayarlar.saglayici == "ollama":
        return _ollama_sohbet(ayarlar, msgs, sicaklik=sicaklik)
    if ayarlar.saglayici == "openai":
        return _openai_sohbet(ayarlar, msgs, sicaklik=sicaklik, max_tokens=max_tokens)
    if ayarlar.saglayici == "anthropic":
        return _anthropic_sohbet(ayarlar, msgs, sicaklik=sicaklik, max_tokens=max_tokens)
    raise AIHizmetHatasi(f"Bilinmeyen sağlayıcı: {ayarlar.saglayici}")


def _ollama_sohbet(ayarlar: AISettings, messages: List[Dict[str, str]], *, sicaklik: float) -> str:
    import urllib.request

    govde = json.dumps(
        {
            "model": ayarlar.ollama_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": sicaklik},
        }
    ).encode("utf-8")
    req = Request(
        f"{ayarlar.ollama_adres.rstrip('/')}/api/chat",
        data=govde,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=300) as yanit:
            veri = json.loads(yanit.read().decode("utf-8"))
    except URLError as exc:
        raise AIHizmetHatasi(f"Ollama hatası: {exc}") from exc
    return veri.get("message", {}).get("content", "").strip()


def _openai_sohbet(
    ayarlar: AISettings,
    messages: List[Dict[str, str]],
    *,
    sicaklik: float,
    max_tokens: int,
) -> str:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise AIHizmetHatasi("pip install openai") from exc

    istemci = OpenAI(api_key=ayarlar.api_anahtari)
    yanit = istemci.chat.completions.create(
        model=ayarlar.model or "gpt-4o-mini",
        messages=messages,
        temperature=sicaklik,
        max_tokens=max_tokens,
    )
    return (yanit.choices[0].message.content or "").strip()


def _anthropic_sohbet(
    ayarlar: AISettings,
    messages: List[Dict[str, str]],
    *,
    sicaklik: float,
    max_tokens: int,
) -> str:
    try:
        import anthropic
    except ImportError as exc:
        raise AIHizmetHatasi("pip install anthropic") from exc

    sistem = ""
    iletiler = []
    for m in messages:
        if m["role"] == "system":
            sistem += m["content"] + "\n"
        else:
            iletiler.append({"role": m["role"], "content": m["content"]})

    istemci = anthropic.Anthropic(api_key=ayarlar.api_anahtari)
    olustur_kw: dict = {
        "model": ayarlar.anthropic_model,
        "max_tokens": max_tokens,
        "messages": iletiler,
        "temperature": sicaklik,
    }
    if sistem.strip():
        olustur_kw["system"] = sistem.strip()
    yanit = istemci.messages.create(**olustur_kw)
    parcalar = [b.text for b in yanit.content if hasattr(b, "text")]
    return "\n".join(parcalar).strip()
