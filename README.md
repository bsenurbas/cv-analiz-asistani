\# Yapay Zeka Destekli CV Analiz Asistanı



> Kocaeli Üniversitesi — Yazılım Mühendisliği Bölümü  

> Bitirme Tezi \& Veri Madenciliği Dönem Projesi — 2026



\## Proje Hakkında



Ham CV metinlerini yapılandırılmış veriye dönüştüren, iş ilanlarıyla anlamlı biçimde eşleştiren ve bu eşleştirmeleri açıklanabilir çıktılarla sunan yapay zeka destekli bir karar destek sistemi.



\## Ekip



| İsim | Rol |

|---|---|

| Buse Nur Baş | Backend, LLM/MCP, API |

| Sude Çokyaşar | Veri, RAG, UI |



\## Teknoloji Yığını



\- \*\*Platform:\*\* Dify (self-host)

\- \*\*LLM:\*\* Anthropic Claude API

\- \*\*Vektör DB:\*\* ChromaDB

\- \*\*Baseline Model:\*\* TF-IDF (scikit-learn)

\- \*\*UI:\*\* Streamlit

\- \*\*Ölçüm:\*\* Python (NDCG, F1, Pearson)



\## Klasör Yapısı

cv-analiz-asistani/

├── data/

│   ├── raw/          # Ham CV ve iş ilanı dosyaları

│   └── processed/    # JSON'a dönüştürülmüş veriler

├── notebooks/        # Jupyter notebook'lar (EDA)

├── src/              # Python kaynak kodları

├── visuals/          # Grafik çıktıları

├── reports/          # Final raporları

└── docs/             # Anket sonuçları, ek belgeler

## Kullanılan Yapay Zeka Araçları



Bu projede Dify platformu ve Anthropic Claude API, CV yapılandırma ve eşleştirme gerekçelendirmesi aşamalarında kullanılmıştır. Detaylar için `reports/` klasörüne bakınız.



