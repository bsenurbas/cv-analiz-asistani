import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
import requests
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import ndcg_score
from scipy import stats
from dotenv import load_dotenv

load_dotenv()
os.chdir(r"C:\Users\bsenu\OneDrive\Masaüstü\Kişisel Projeler\cv-analiz-asistani")

DIFY_API_KEY = os.getenv("DIFY_API_KEY")

# ── Veriyi parse et ──────────────────────────────────
df_raw = pd.read_excel("docs/insan_degerlendirmesi.xlsx")

# İş ilanlarını ve CV sıralamalarını çıkar
ilanlar = []
simdiki_ilan = None
simdiki_kategori = None
simdiki_aciklama = None

for _, row in df_raw.iterrows():
    # İlan adı sütunu dolu ise yeni ilan başlıyor
    col0 = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
    col1 = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
    cv_id = row.iloc[2] if pd.notna(row.iloc[2]) else None
    sira = row.iloc[3] if pd.notna(row.iloc[3]) else None

    if col0 and col0 != "nan" and "Job" in col0:
        simdiki_ilan = col0
        simdiki_kategori = col1

    # İlan açıklamasını al (İş Açıklaması sütunu)
    if pd.notna(row.iloc[7]) and str(row.iloc[7]) != "nan":
        simdiki_aciklama = str(row.iloc[7])

    if simdiki_ilan and cv_id and sira:
        ilanlar.append({
            "ilan_adi": simdiki_ilan,
            "kategori": simdiki_kategori,
            "cv_id": int(cv_id),
            "insan_sirasi": int(sira)
        })

df_ilanlar = pd.DataFrame(ilanlar)
print(f"Toplam kayıt: {len(df_ilanlar)}")
print(df_ilanlar.head(10))

# İş ilanı açıklamalarını ayrı al
ilan_aciklamalari = {
    "Job 1 (HR Manager)": "Seeking an HR Manager with 5+ years of experience in recruitment, employee relations, and performance management.",
    "Job 2 (İK Uzmanı)": "Personel özlük işleri, bordrolama ve SGK süreçleri konusunda deneyimli İnsan Kaynakları Uzmanı.",
    "Job 3 (Executive Chef)": "Experienced Executive Chef to manage a high-volume kitchen. Proficiency in menu engineering and HACCP safety standards.",
    "Job 4 (Mutfak Şefi)": "Uluslararası mutfakta deneyimli, reçete maliyetlendirme ve mutfak ekip yönetimi yapabilen aşçıbaşı.",
    "Job 5 (Senior Accountant)": "Looking for a Senior Accountant to handle general ledger, tax preparation, and financial reporting.",
    "Job 6 (Genel Muhasebe Uzmanı)": "Tek düzen hesap planına hakim, vergi beyannameleri ve mizan kontrolü süreçlerini yönetecek muhasebeci.",
    "Job 7 (Personal Trainer)": "Certified Fitness Instructor specializing in strength training and weight management.",
    "Job 8 (Pilates/Grup Eğitmeni)": "Grup dersleri ve reformer pilates konusunda uzman fitness eğitmeni.",
    "Job 9 (IT Support & Systems)": "Seeking an IT Specialist with experience in Windows Server, Active Directory, and VMware.",
    "Job 10 (Sistem ve Ağ Yöneticisi)": "Şirket içi sunucu altyapısını yönetecek, Office 365 ve LAN/WAN kurulumu yapabilen bilgi işlem sorumlusu."
}

# ── CV verisi yükle ──────────────────────────────────
df_cv = pd.read_csv("data/processed/Resume_temiz.csv")
print(f"\nCV veri seti: {len(df_cv)} CV")

# ── TF-IDF skoru hesapla ─────────────────────────────
def tfidf_skorla(ilan_metni: str, cv_metinleri: list) -> list:
    tum = [ilan_metni] + cv_metinleri
    vektorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=5000, sublinear_tf=True)
    matris = vektorizer.fit_transform(tum)
    benzerlik = cosine_similarity(matris[0:1], matris[1:])[0]
    return benzerlik.tolist()

# ── Her ilan için TF-IDF ve insan skorlarını hesapla ──
print("\nTF-IDF skorları hesaplanıyor...")

sonuclar = []
for ilan_adi in df_ilanlar["ilan_adi"].unique():
    ilan_df = df_ilanlar[df_ilanlar["ilan_adi"] == ilan_adi].sort_values("insan_sirasi")
    cv_idler = ilan_df["cv_id"].tolist()
    insan_siralari = ilan_df["insan_sirasi"].tolist()

    # CV metinlerini al
    cv_metinleri = []
    gecerli_idler = []
    gecerli_siralar = []
    for i, (cv_id, sira) in enumerate(zip(cv_idler, insan_siralari)):
        cv_satir = df_cv[df_cv["ID"] == cv_id]
        if not cv_satir.empty:
            cv_metinleri.append(str(cv_satir["temiz_metin"].values[0])[:3000])
            gecerli_idler.append(cv_id)
            gecerli_siralar.append(sira)

    if len(cv_metinleri) < 2:
        continue

    # TF-IDF skoru
    ilan_metni = ilan_aciklamalari.get(ilan_adi, ilan_adi)
    tfidf_skorlar = tfidf_skorla(ilan_metni, cv_metinleri)

    # İnsan skoru: sıralamayı skora çevir (1=en iyi → yüksek skor)
    maks = max(gecerli_siralar)
    insan_skorlar = [maks - s + 1 for s in gecerli_siralar]

    for i, (cv_id, sira, tfidf_s, insan_s) in enumerate(zip(gecerli_idler, gecerli_siralar, tfidf_skorlar, insan_skorlar)):
        sonuclar.append({
            "ilan": ilan_adi,
            "cv_id": cv_id,
            "insan_sirasi": sira,
            "insan_skoru": insan_s,
            "tfidf_skoru": round(tfidf_s, 4)
        })

df_sonuc = pd.DataFrame(sonuclar)
print(f"Hesaplanan kayıt: {len(df_sonuc)}")

# ── Pearson Korelasyon ───────────────────────────────
r, p = stats.pearsonr(df_sonuc["insan_skoru"], df_sonuc["tfidf_skoru"])
print(f"\nPearson Korelasyon (TF-IDF vs İnsan): r={r:.3f}, p={p:.4f}")

# ── NDCG@5 ──────────────────────────────────────────
ndcg_degerler = []
for ilan_adi in df_sonuc["ilan"].unique():
    ilan_data = df_sonuc[df_sonuc["ilan"] == ilan_adi]
    if len(ilan_data) >= 2:
        gercek = [ilan_data["insan_skoru"].tolist()]
        tahmin = [ilan_data["tfidf_skoru"].tolist()]
        try:
            ndcg = ndcg_score(gercek, tahmin, k=min(5, len(ilan_data)))
            ndcg_degerler.append(ndcg)
        except:
            pass

ndcg_ortalama = np.mean(ndcg_degerler) if ndcg_degerler else 0
print(f"NDCG@5 (TF-IDF): {ndcg_ortalama:.3f}")

# ── Grafik 1: Korelasyon scatter ─────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

axes[0].scatter(df_sonuc["insan_skoru"], df_sonuc["tfidf_skoru"],
                color="#6B3FA0", alpha=0.6, s=60, edgecolors="white", linewidth=0.5)
z = np.polyfit(df_sonuc["insan_skoru"], df_sonuc["tfidf_skoru"], 1)
p_fit = np.poly1d(z)
x_line = np.linspace(df_sonuc["insan_skoru"].min(), df_sonuc["insan_skoru"].max(), 100)
axes[0].plot(x_line, p_fit(x_line), "r--", alpha=0.8, linewidth=2, label=f"Trend (r={r:.3f})")
axes[0].set_title("TF-IDF Skoru vs İnsan Değerlendirmesi", fontsize=13, fontweight="bold")
axes[0].set_xlabel("İnsan Skoru")
axes[0].set_ylabel("TF-IDF Skoru")
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# ── Grafik 2: İlan bazında karşılaştırma ─────────────
ilan_isimleri = df_sonuc["ilan"].unique()
tfidf_ndcg_list = []

for ilan in ilan_isimleri:
    data = df_sonuc[df_sonuc["ilan"] == ilan]
    if len(data) >= 2:
        try:
            n = ndcg_score([data["insan_skoru"].tolist()], [data["tfidf_skoru"].tolist()], k=min(5, len(data)))
            tfidf_ndcg_list.append(n)
        except:
            tfidf_ndcg_list.append(0)

kisaltilmis = [i.split("(")[1].replace(")", "") if "(" in i else i for i in ilan_isimleri]
x = np.arange(len(kisaltilmis))
genislik = 0.35

bars = axes[1].bar(x, tfidf_ndcg_list, genislik, label="TF-IDF", color="#6B3FA0", alpha=0.8)
axes[1].axhline(y=0.6, color="red", linestyle="--", alpha=0.7, label="Hedef (0.60)")
axes[1].axhline(y=ndcg_ortalama, color="#1D6FA4", linestyle="-.", alpha=0.7, label=f"Ort. ({ndcg_ortalama:.2f})")
axes[1].set_title("İlan Bazında NDCG@5 Skoru", fontsize=13, fontweight="bold")
axes[1].set_ylabel("NDCG@5")
axes[1].set_xticks(x)
axes[1].set_xticklabels(kisaltilmis, rotation=45, ha="right", fontsize=9)
axes[1].legend()
axes[1].grid(True, alpha=0.3, axis="y")
axes[1].set_ylim(0, 1.1)

plt.tight_layout()
plt.savefig("visuals/model_karsilastirma.png", dpi=150, bbox_inches="tight")
plt.show()
print("\nGrafik kaydedildi: visuals/model_karsilastirma.png")

# ── Özet rapor ───────────────────────────────────────
print("\n" + "="*50)
print("MODEL KARŞILAŞTIRMA ÖZETI")
print("="*50)
print(f"TF-IDF Pearson Korelasyon:  r = {r:.3f}")
print(f"TF-IDF NDCG@5:               {ndcg_ortalama:.3f}")
print(f"H2 Hedefi (≥ 0.70):          {'✅' if abs(r) >= 0.70 else '❌'}")
print(f"H3 Hedefi (≥ 0.60):          {'✅' if ndcg_ortalama >= 0.60 else '❌'}")
print("="*50)

# Kaydet
os.makedirs("docs", exist_ok=True)
with open("docs/metrik_sonuclari.txt", "a", encoding="utf-8") as f:
    f.write(f"\n\nH2 ve H3 Metrikleri — TF-IDF Model\n")
    f.write(f"{'='*40}\n")
    f.write(f"Pearson Korelasyon: r = {r:.3f}\n")
    f.write(f"NDCG@5:             {ndcg_ortalama:.3f}\n")
    f.write(f"H2 (≥ 0.70): {'BASARILI' if abs(r) >= 0.70 else 'HEDEFIN ALTINDA'}\n")
    f.write(f"H3 (≥ 0.60): {'BASARILI' if ndcg_ortalama >= 0.60 else 'HEDEFIN ALTINDA'}\n")
print("Sonuçlar docs/metrik_sonuclari.txt dosyasına eklendi.")