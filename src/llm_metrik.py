import pandas as pd
import numpy as np
import requests
import json
import os
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.metrics import ndcg_score
from dotenv import load_dotenv

load_dotenv()
# Kendi çalışma dizininize göre burayı ayarlayabilirsiniz
os.chdir(r"C:\Users\bsenu\OneDrive\Masaüstü\Kişisel Projeler\cv-analiz-asistani")

DIFY_API_KEY = os.getenv("ESLESTIRME_API_KEY")  # Eşleştirme workflow key
DIFY_BASE_URL = "https://api.dify.ai/v1"

# ── Veri yükle ───────────────────────────────────────
df_cv = pd.read_csv("data/raw/Resume.csv")

# Excel yerine artık doğrudan yeni temiz CSV dosyanızı okuyoruz:
insan_raw = pd.read_csv("docs/insan_degerlendirmesi_guncel.csv")

# ── İnsan değerlendirmesini parse et ────────────────
ilanlar = []
for _, row in insan_raw.iterrows():
    ilan_adi = str(row["ilan"]).strip() if pd.notna(row["ilan"]) else ""
    aciklama_metni = str(row["aciklama"]).strip() if pd.notna(row["aciklama"]) else None
    cv_id = row["cv_id"]
    sira = row["insan_sirasi"]

    # "Job" içeren ve gerekli alanları dolu olan satırları ekle
    if ilan_adi and "Job" in ilan_adi and pd.notna(cv_id) and pd.notna(sira):
        ilanlar.append({
            "ilan": ilan_adi,
            "aciklama": aciklama_metni if aciklama_metni and aciklama_metni != "nan" else ilan_adi,
            "cv_id": int(cv_id),
            "insan_sirasi": int(sira)
        })

df_ilanlar = pd.DataFrame(ilanlar)
print(f"Toplam kayıt: {len(df_ilanlar)}")
print(f"İş ilanı sayısı: {df_ilanlar['ilan'].nunique()}")

# ── Dify Eşleştirme API çağrısı ──────────────────────
def dify_skorla(ilan_metni: str, cv_listesi: list) -> list:
    """Gönderilen CV listesini dinamik olarak formatlar ve API'ye gönderir."""
    
    # ÇÖZÜM BURADA: LLM'in iş ilanını görmezden gelmesini kesin olarak engellemek için
    # ilanı, CV listesi değişkeninin en tepesine BÜYÜK HARFLERLE gömüyoruz.
    cv_metni = f"=== JOB DESCRIPTION (EVALUATE CANDIDATES AGAINST THIS) ===\n{ilan_metni[:800]}\n==========================================================\n\n"
    
    for i, cv in enumerate(cv_listesi, 1):
        cv_metni += f"\n--- Candidate {i} ---\n{cv[:1500]}\n"
    
    yanit = requests.post(
        f"{DIFY_BASE_URL}/workflows/run",
        headers={
            "Authorization": f"Bearer {os.getenv('SKORLAMA_API_KEY')}",
            "Content-Type": "application/json"
        },
        json={
            "inputs": {
                "ilan_metni": ilan_metni[:800], # Orijinal değişkeni bozmamak için bırakıyoruz
                "cv_listesi": cv_metni          # İş ilanı ile güçlendirilmiş CV metnini gönderiyoruz
            },
            "response_mode": "blocking",
            "user": "h2-test"
        },
        timeout=120
    )
    
    veri = yanit.json()
    
    if "data" not in veri or "outputs" not in veri["data"] or "skorlama_sonucu" not in veri["data"]["outputs"]:
        print(f"\n[DIFY API HATASI]: {veri}")
        raise ValueError("Dify API'den beklenen skorlama_sonucu dönmedi.")

    cikti = veri["data"]["outputs"]["skorlama_sonucu"]
    
    if not cikti or cikti.strip() == "":
        raise ValueError("LLM tamamen boş bir yanıt döndürdü.")

    cikti_temiz = cikti.replace("```json", "").replace("```", "").strip()
    
    try:
        parsed = json.loads(cikti_temiz)
        return [s["skor"] for s in parsed["skorlar"]]
    except json.JSONDecodeError:
        print(f"\n[JSON ÇÖZÜMLEME HATASI] LLM'in ürettiği bozuk çıktı:\n{cikti}\n")
        raise ValueError("LLM geçerli bir JSON üretmedi.")

# ── Her ilan için LLM skoru hesapla ─────────────────
print("\nLLM skorları hesaplanıyor...")
llm_skorlar_listesi = []

for ilan_adi in df_ilanlar["ilan"].unique():
    ilan_data = df_ilanlar[df_ilanlar["ilan"] == ilan_adi].sort_values("insan_sirasi")
    aciklama = ilan_data["aciklama"].dropna().iloc[0] if not ilan_data["aciklama"].dropna().empty else ilan_adi

    print(f"\n  {ilan_adi}:")
    # Tüm CV'leri topla
    cv_metinleri = []
    gecerli_rows = []
    for _, row in ilan_data.iterrows():
        cv_satir = df_cv[df_cv["ID"] == row["cv_id"]]
        if not cv_satir.empty:
            cv_metinleri.append(str(cv_satir["Resume_str"].values[0]))
            gecerli_rows.append(row)

    if len(cv_metinleri) < 2:
        continue

    # ── CV'leri Dify prompt yapısına uygun olarak 5'erli paketler (chunk) halinde gönderiyoruz ──
    chunk_size = 5
    for i in range(0, len(cv_metinleri), chunk_size):
        chunk_cv = cv_metinleri[i : i + chunk_size]
        chunk_rows = gecerli_rows[i : i + chunk_size]
        
        try:
            skorlar = dify_skorla(aciklama, chunk_cv)
            
            for row, skor in zip(chunk_rows, skorlar):
                llm_skorlar_listesi.append({
                    "ilan": ilan_adi,
                    "cv_id": row["cv_id"],
                    "insan_sirasi": row["insan_sirasi"],
                    "llm_skoru": skor
                })
                print(f"    CV {row['cv_id']}: LLM={skor}, İnsan sırası={row['insan_sirasi']}")
        except Exception as e:
            print(f"  HATA (Grup {i//chunk_size + 1}): {e}")

df_llm = pd.DataFrame(llm_skorlar_listesi)

if df_llm.empty:
    print("❌ LLM skoru hesaplanamadı.")
    exit()

# İnsan skoruna çevir
maks_sira = df_llm.groupby("ilan")["insan_sirasi"].transform("max")
df_llm["insan_skoru"] = maks_sira - df_llm["insan_sirasi"] + 1

# ── H2: Pearson Korelasyon ───────────────────────────
r, p = stats.pearsonr(df_llm["insan_skoru"], df_llm["llm_skoru"])
print(f"\nPearson Korelasyon (LLM vs İnsan): r={r:.3f}, p={p:.4f}")

# ── H3: NDCG@5 ──────────────────────────────────────
ndcg_degerler = []
for ilan in df_llm["ilan"].unique():
    d = df_llm[df_llm["ilan"] == ilan]
    if len(d) >= 2:
        try:
            n = ndcg_score([d["insan_skoru"].tolist()], [d["llm_skoru"].tolist()], k=min(5, len(d)))
            ndcg_degerler.append(n)
        except:
            pass

ndcg_ort = np.mean(ndcg_degerler) if ndcg_degerler else 0
print(f"NDCG@5 (LLM): {ndcg_ort:.3f}")

# ── Grafik ───────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Scatter
axes[0].scatter(df_llm["insan_skoru"], df_llm["llm_skoru"],
                color="#1D6FA4", alpha=0.6, s=60, edgecolors="white", linewidth=0.5)
z = np.polyfit(df_llm["insan_skoru"], df_llm["llm_skoru"], 1)
x_line = np.linspace(df_llm["insan_skoru"].min(), df_llm["insan_skoru"].max(), 100)
axes[0].plot(x_line, np.poly1d(z)(x_line), "r--", alpha=0.8, linewidth=2, label=f"r={r:.3f}")
axes[0].set_title("LLM Skoru vs İnsan Değerlendirmesi", fontsize=13, fontweight="bold")
axes[0].set_xlabel("İnsan Skoru"); axes[0].set_ylabel("LLM Skoru")
axes[0].legend(); axes[0].grid(True, alpha=0.3)

# NDCG bar
ilan_isimleri = [i.split("(")[1].replace(")", "") if "(" in i else i for i in df_llm["ilan"].unique()]
axes[1].bar(range(len(ndcg_degerler)), ndcg_degerler, color="#1D6FA4", alpha=0.8)
axes[1].axhline(y=0.6, color="red", linestyle="--", alpha=0.7, label="Hedef (0.60)")
axes[1].axhline(y=ndcg_ort, color="orange", linestyle="-.", alpha=0.7, label=f"Ort. ({ndcg_ort:.2f})")
axes[1].set_title("LLM — İlan Bazında NDCG@5", fontsize=13, fontweight="bold")
axes[1].set_ylabel("NDCG@5"); axes[1].set_xticks(range(len(ilan_isimleri)))
axes[1].set_xticklabels(ilan_isimleri, rotation=45, ha="right", fontsize=9)
axes[1].legend(); axes[1].grid(True, alpha=0.3, axis="y"); axes[1].set_ylim(0, 1.1)

plt.tight_layout()
os.makedirs("visuals", exist_ok=True)
plt.savefig("visuals/llm_metrik.png", dpi=150, bbox_inches="tight")
plt.show()
print("Grafik kaydedildi: visuals/llm_metrik.png")

# ── Sonuç özeti ──────────────────────────────────────
print("\n" + "="*50)
print("H2 ve H3 METRİK SONUÇLARI — LLM")
print("="*50)
print(f"Pearson r:   {r:.3f}  →  H2 {'✅' if abs(r) >= 0.70 else '❌'} (≥ 0.70)")
print(f"NDCG@5:      {ndcg_ort:.3f}  →  H3 {'✅' if ndcg_ort >= 0.60 else '❌'} (≥ 0.60)")
print("="*50)

# Dosyaya ekle
os.makedirs("docs", exist_ok=True)
with open("docs/metrik_sonuclari.txt", "a", encoding="utf-8") as f:
    f.write(f"\n\nH2 ve H3 Metrikleri — LLM Model\n{'='*40}\n")
    f.write(f"Pearson r:  {r:.3f}  → {'BASARILI' if abs(r) >= 0.70 else 'HEDEFIN ALTINDA'}\n")
    f.write(f"NDCG@5:     {ndcg_ort:.3f}  → {'BASARILI' if ndcg_ort >= 0.60 else 'HEDEFIN ALTINDA'}\n")
print("Sonuçlar docs/metrik_sonuclari.txt dosyasına eklendi.")