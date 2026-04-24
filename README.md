
#  Yapay Zeka Destekli CV Analiz Asistanı

> **Kocaeli Üniversitesi** — Yazılım Mühendisliği Bölümü  
> **Bitirme Tezi & Veri Madenciliği Dönem Projesi** — 2026

---

##  Proje Hakkında

Bu proje, ham CV metinlerini (PDF, Docx vb.) NLP teknikleriyle işleyerek yapılandırılmış veriye dönüştüren, adayları iş ilanlarıyla semantik ve istatistiksel yöntemlerle eşleştiren yapay zeka destekli bir **Karar Destek Sistemi**'dir. Sistem, eşleştirme sonuçlarını sadece puanlamakla kalmaz, açıklanabilir (explainable AI) çıktılar sunar.

---

##  Ekip

| İsim | Rol | Uzmanlık Alanı |
| :--- | :--- | :--- |
| **Buse Nur Baş** | Backend & AI Ops | LLM/MCP Entegrasyonu, API Geliştirme |
| **Sude Çokyaşar** | Data & Frontend | Veri İşleme, RAG Mimarisi, UI Tasarımı |

---

##  Teknoloji Yığını

### **Altyapı & Platform**
* **Platform:** [Dify](https://dify.ai/) (Self-hosted)
* **LLM:** Anthropic Claude API
* **Vektör Veritabanı:** ChromaDB (Semantik arama için)

### **Veri Madenciliği & Analitik**
* **Baseline Model:** TF-IDF (scikit-learn)
* **Diller:** Python 3.x
* **Metrikler:** NDCG, F1-Score, Pearson Korelasyonu

### **Arayüz**
* **UI:** Streamlit

---

##  Klasör Yapısı

```bash
cv-analiz-asistani/
├── data/
│   ├── raw/            # Ham CV ve iş ilanı dosyaları (PDF/TXT)
│   └── processed/      # Temizlenmiş ve JSON formatına dönüştürülmüş veriler
├── notebooks/          # EDA (Keşifçi Veri Analizi) ve Model deneyleri
├── src/                # Python kaynak kodları (Processing, Matching, API)
├── visuals/            # Veri görselleştirme ve analiz grafikleri
├── reports/            # Akademik raporlar ve sonuç analizleri
├── docs/               # Anket sonuçları, literatür taraması ve ek belgeler
└── README.md           # Proje ana dökümantasyonu
```

---

##  Yapay Zeka ve Model Kullanımı

Projenin temelinde hibrit bir yaklaşım yatmaktadır:

1.  **Yapılandırma:** Claude API kullanılarak karmaşık CV formatları standart JSON şemalarına dönüştürülür.
2.  **RAG (Retrieval-Augmented Generation):** ChromaDB ve Dify kullanılarak iş tanımına en uygun adayların getirilmesi sağlanır.
3.  **Açıklanabilirlik:** Yapay zeka, bir adayın neden belirli bir işe uygun olduğunu veya hangi yetkinliklerinin eksik olduğunu gerekçelendirir.

> [!TIP]
> Detaylı metodoloji ve model performans analizleri için `reports/` klasöründeki teknik raporları inceleyebilirsiniz.

---

### **Kurulum (Önizleme)**
```bash
# Depoyu klonlayın
git clone https://github.com/kullaniciadi/cv-analiz-asistani.git

# Gerekli kütüphaneleri yükleyin
pip install -r requirements.txt
```
