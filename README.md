# Ultimate PDF Suite

> **Demo / deneysel sürüm** — Bu proje henüz kapsamlı şekilde test edilmemiştir. Üretim ortamında veya kritik belgelerde kullanmadan önce kendi testlerinizi yapın. Hata ve eksikler beklenir.

Windows için PyQt6 tabanlı masaüstü PDF aracı. Birleştirme, düzenleme, güvenlik, dönüştürme, OCR ve **Akıllı Araçlar** (yapay zeka) tek uygulamada toplanır.

**Depo:** [github.com/Hud-Alfa/ultimate-pdf-suite](https://github.com/Hud-Alfa/ultimate-pdf-suite)

## Hızlı başlangıç

1. **Python 3.10+** kurulu olsun ([python.org](https://www.python.org/downloads/)).
2. Proje klasöründe:

```powershell
cd premium_pdf_suit
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Sanal ortam kullanmak zorunlu değil; doğrudan `pip install -r requirements.txt` ve `python main.py` da yeterlidir.

## Ne için ne gerekir?

| Özellik | Python paketleri (`pip`) | Ek yazılım (isteğe bağlı) |
|--------|---------------------------|---------------------------|
| Sayfa yönetimi, düzenleme, güvenlik | PyQt6, PyMuPDF | — |
| Word/Excel/PPT → PDF | — | **LibreOffice** veya **Microsoft Office** |
| HTML → PDF | pdfkit | **wkhtmltopdf** ([indir](https://wkhtmltopdf.org/downloads.html)) |
| OCR (aranabilir PDF) | pytesseract, ocrmypdf | **Tesseract** + dil paketleri |
| Tara (tarayıcıdan PDF) | comtypes | Windows’ta WIA uyumlu tarayıcı |
| Akıllı Araçlar (çoğu) | openai, anthropic, langchain, faiss-cpu | **Ollama** *veya* bulut API anahtarı |
| Karşılaştırma (metinsel) | — | **Hiçbir API gerekmez** |

`requirements.txt` yalnızca Python bağımlılıklarını listeler. LibreOffice, Tesseract, wkhtmltopdf ve Ollama ayrı kurulur; aşağıda adımlar var.

---

## Harici yazılımlar

### LibreOffice (Office → PDF)

Word, Excel, PowerPoint dosyalarını PDF’e çevirmek için:

1. [LibreOffice](https://www.libreoffice.org/download/download/) indirip kurun.
2. Varsayılan yol: `C:\Program Files\LibreOffice\program\soffice.exe`

Alternatif: yüklü **Microsoft Office** (Windows COM) aynı işi yapabilir.

### wkhtmltopdf (HTML → PDF)

1. [wkhtmltopdf Windows sürümü](https://wkhtmltopdf.org/downloads.html) kurun.
2. `wkhtmltopdf.exe` sistem **PATH**’inde olmalı (veya pdfkit’in bulabildiği bir konumda).

### Tesseract (OCR)

1. [UB-Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) Windows kurulumu.
2. Kurulumda **Turkish** (`tur`) dil paketini seçin; İngilizce için `eng`.
3. Ortam değişkeni (örnek):

```powershell
[System.Environment]::SetEnvironmentVariable("TESSDATA_PREFIX", "C:\Program Files\Tesseract-OCR\tessdata", "User")
```

PATH’e `C:\Program Files\Tesseract-OCR` ekleyin.

### Tarayıcı (Tara)

Windows **Tara** aracı, bağlı bir WIA uyumlu tarayıcı bekler. Sürücüler Windows Ayarlar → Yazıcılar ve tarayıcılar üzerinden kurulmalıdır.

---

## Akıllı Araçlar (yapay zeka)

Sol menü → **Akıllı Araçlar**:

| Araç | Ne yapar? | API / Ollama gerekir mi? |
|------|-----------|---------------------------|
| **Intelligence** | PDF ile RAG sohbet (soru-cevap) | Evet (Ollama veya bulut) |
| **Yapay Zeka Özet** | Uzun PDF’ten yönetici özeti | Evet |
| **Çeviri** | Metni çevirip yeni PDF üretir | Evet |
| **Karşılaştırma** | İki PDF farkı | **Metinsel:** hayır · **Anlamsal:** evet |

Her AI panelinin üstünde **Yapay zeka bağlantısı** ayarları vardır. Tercihler şuraya kaydedilir:

```
%USERPROFILE%\.ultimate_pdf_suite\ai_settings.json
```

API anahtarı **şimdilik zorunlu değildir**. Bulut (OpenAI / Anthropic) özellikleri anahtar girildiğinde çalışır. Ücretsiz yerel kullanım için **Ollama** önerilir.

### Seçenek A — Yerel Ollama (önerilen, ücretsiz)

Ollama, bilgisayarınızda küçük bir LLM sunucusu çalıştırır (`localhost:11434`). Veriler varsayılan olarak makinenizde kalır; OpenAI/Anthropic anahtarı gerekmez.

1. **Ollama kurulumu**  
   - [https://ollama.com](https://ollama.com) → Windows için indirip kurun.

2. **Model indirin** (uygulama varsayılanı `llama3.2`):

```powershell
ollama pull llama3.2
```

Diğer örnekler: `ollama pull mistral`, `ollama pull qwen2.5:7b`. Türkçe için genelde `llama3.2` veya `qwen2.5` yeterlidir.

3. **Ollama’nın çalıştığını doğrulayın**  
   Kurulumdan sonra genelde arka planda çalışır. Elle başlatmak için:

```powershell
ollama serve
```

Tarayıcıda veya PowerShell’de:

```powershell
curl http://localhost:11434/api/tags
```

Model listesi JSON olarak dönmeli.

4. **Uygulamada ayar**  
   - Sağlayıcı: **Yerel Ollama (ücretsiz)**  
   - Ollama adresi: `http://localhost:11434` (varsayılan)  
   - Ollama modeli: indirdiğiniz ad, örn. `llama3.2`  
   - **Kaydet**

5. **Intelligence (RAG) akışı**  
   - PDF seçin → **PDF’i indeksle** (FAISS vektör indeksi; ilk seferde biraz sürebilir)  
   - Sorunuzu yazıp gönderin  

İndeks önbelleği PDF ile aynı klasörde `.ultimate_pdf_suite_cache` altında tutulabilir (modül ayarına bağlı).

### Seçenek B — OpenAI veya Anthropic (bulut)

1. [OpenAI API](https://platform.openai.com/api-keys) veya [Anthropic Console](https://console.anthropic.com/) üzerinden anahtar oluşturun.  
2. Uygulamada sağlayıcıyı seçin, **API anahtarı** alanına yapıştırın.  
3. Model adı örnekleri:  
   - OpenAI: `gpt-4o-mini`  
   - Anthropic: `claude-3-5-haiku-20241022`  

### API anahtarı olmadan neler çalışır?

- Tüm **Sayfa Yönetimi**, **Düzenleme**, **Güvenlik**, çoğu **dönüştürme** (harici yazılımlar kuruluysa).  
- **Karşılaştırma → Metinsel** modu (`difflib`, tamamen yerel).  
- Intelligence / Özet / Çeviri / anlamsal karşılaştırma için **Ollama** veya bulut anahtarı gerekir.

### Ollama sorun giderme

| Belirti | Olası çözüm |
|--------|----------------|
| «Ollama'ya bağlanılamadı» | `ollama serve` çalışıyor mu? Güvenlik duvarı 11434’ü engelliyor mu? |
| Model bulunamadı | `ollama pull <model_adı>` ile indirin; paneldeki ad birebir aynı olsun |
| Çok yavaş | Daha küçük model deneyin; PDF’i önce küçültün veya özet için sayfa sınırı kullanın |
| RAG indeks hatası | `pip install langchain-community faiss-cpu` tekrar kurun |

---

## Proje yapısı (kısa)

```
main.py                 # Giriş noktası
core/                   # PDF çekirdek, AI ayarları
modules/                # İş mantığı (organization, ai_tools, …)
gui/                    # Arayüz, paneller, QThread worker
requirements.txt        # pip bağımlılıkları
```

---

## Güvenlik notu

- **Kilit Aç** yalnızca **bilinen şifre** ile çalışır; şifre kırma yoktur.  

---

## Geliştirici

**Hud-Alfa** — [GitHub](https://github.com/Hud-Alfa)

## Lisans ve katkı

Bu depo **test edilmemiş bir demo** olarak paylaşılmıştır. Sorun bildirirken `python main.py` hata metnini ve kullandığınız menü aracını belirtin.
