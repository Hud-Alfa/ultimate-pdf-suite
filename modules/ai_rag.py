"""RAG — FAISS + LangChain."""

from __future__ import annotations

import hashlib
import pickle
from pathlib import Path
from typing import Any, Callable, List, Optional

from core.ai_settings import AISettings
from modules.ai_llm import baglanti_kontrol, sohbet_tamamla
from modules.ai_pdf_text import pdf_tam_metin

ProgressCallback = Optional[Callable[[int], None]]
MessageCallback = Optional[Callable[[str], None]]


def _onbellek_yolu(pdf_yolu: str) -> Path:
    ozet = hashlib.md5(Path(pdf_yolu).resolve().as_posix().encode()).hexdigest()
    klasor = Path.home() / ".ultimate_pdf_suite" / "rag_cache"
    klasor.mkdir(parents=True, exist_ok=True)
    return klasor / f"{ozet}.faiss.pkl"


def _embedding_olustur(ayarlar: AISettings):
    try:
        from langchain_community.embeddings import OllamaEmbeddings, OpenAIEmbeddings
    except ImportError as exc:
        raise ImportError("RAG için: pip install langchain-community") from exc

    if ayarlar.saglayici == "openai" and ayarlar.api_anahtari:
        return OpenAIEmbeddings(openai_api_key=ayarlar.api_anahtari)
    return OllamaEmbeddings(
        base_url=ayarlar.ollama_adres.rstrip("/"),
        model=ayarlar.ollama_model,
    )


def indeks_olustur(
    pdf_yolu: str,
    ayarlar: AISettings,
    *,
    progress_callback: ProgressCallback = None,
    message_callback: MessageCallback = None,
    **kwargs: Any,
) -> str:
    """PDF için FAISS indeksi oluşturur; önbellek yolunu döndürür."""
    baglanti_kontrol(ayarlar)

    onbellek = _onbellek_yolu(pdf_yolu)
    pdf_mtime = Path(pdf_yolu).stat().st_mtime

    if onbellek.is_file():
        try:
            with open(onbellek, "rb") as f:
                veri = pickle.load(f)
            if veri.get("mtime") == pdf_mtime:
                if message_callback:
                    message_callback("Önbellekten indeks yüklendi.")
                return str(onbellek)
        except (pickle.PickleError, OSError):
            pass

    try:
        from langchain_community.vectorstores import FAISS
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError as exc:
        raise ImportError(
            "RAG için: pip install langchain-community langchain-text-splitters faiss-cpu"
        ) from exc

    if progress_callback:
        progress_callback(10)
    if message_callback:
        message_callback("PDF metni çıkarılıyor…")

    tam = pdf_tam_metin(pdf_yolu, progress_callback=progress_callback, message_callback=message_callback)
    if not tam.strip():
        raise ValueError("PDF'den metin çıkarılamadı (taranmış görsel olabilir — önce OCR deneyin).")

    bolucu = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)
    parcalar = bolucu.split_text(tam)

    if message_callback:
        message_callback(f"{len(parcalar)} parça gömülüyor…")

    emb = _embedding_olustur(ayarlar)
    vektor = FAISS.from_texts(parcalar, emb)

    with open(onbellek, "wb") as f:
        pickle.dump({"mtime": pdf_mtime, "store": vektor, "parcalar": len(parcalar)}, f)

    if progress_callback:
        progress_callback(100)
    return str(onbellek)


def _vektor_yukle(onbellek_yolu: str):
    with open(onbellek_yolu, "rb") as f:
        veri = pickle.load(f)
    return veri["store"]


def rag_soru(
    soru: str,
    onbellek_yolu: str,
    ayarlar: AISettings,
    *,
    progress_callback: ProgressCallback = None,
    message_callback: MessageCallback = None,
    **kwargs: Any,
) -> str:
    baglanti_kontrol(ayarlar)
    vektor = _vektor_yukle(onbellek_yolu)
    docs = vektor.similarity_search(soru, k=5)
    baglam = "\n\n---\n\n".join(d.page_content for d in docs)

    if message_callback:
        message_callback("Yanıt üretiliyor…")

    return sohbet_tamamla(
        ayarlar,
        [
            {
                "role": "system",
                "content": (
                    "Sen bir PDF asistanısın. Yalnızca verilen bağlamı kullan. "
                    "Bilmiyorsan 'Belgede bulamadım' de. Türkçe yanıt ver."
                ),
            },
            {
                "role": "user",
                "content": f"Bağlam:\n{baglam}\n\nSoru: {soru}",
            },
        ],
        sicaklik=0.2,
    )
