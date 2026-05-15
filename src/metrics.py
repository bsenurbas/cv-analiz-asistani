import json
import os
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
os.chdir(r"C:\Users\bsenu\OneDrive\Masaüstü\Kişisel Projeler\cv-analiz-asistani")

DIFY_API_KEY = os.getenv("DIFY_API_KEY")
DIFY_BASE_URL = "https://api.dify.ai/v1"

# ── Veri yükle ───────────────────────────────────────
with open("data/processed/ground_truth.json", "r", encoding="utf-8") as f:
    ground_truth_listesi = json.load(f)

df = pd.read_csv("data/raw/Resume.csv")
print(f"Ground truth yüklendi: {len(ground_truth_listesi)} CV")
print(f"Ham veri seti yüklendi: {len(df)} CV\n")


# ── Dify API çağrısı ─────────────────────────────────
def dify_cv_al(cv_metni: str) -> dict:
    yanit = requests.post(
        f"{DIFY_BASE_URL}/workflows/run",
        headers={
            "Authorization": f"Bearer {DIFY_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "inputs": {"cv_metni": cv_metni},
            "response_mode": "blocking",
            "user": "metrik-test"
        },
        timeout=90
    )
    yanit.raise_for_status()
    veri = yanit.json()
    cikti = veri["data"]["outputs"]["cv_json"]
    cikti = cikti.replace("```json", "").replace("```", "").strip()
    return json.loads(cikti)


# ── Alan doğruluğu hesapla ───────────────────────────
def alan_dogrulugu(gercek: dict, model: dict) -> dict:
    sonuc = {}

    # 1. Deneyim var mı
    g_deneyim = gercek.get("deneyim", [])
    m_deneyim = model.get("deneyim", [])
    sonuc["deneyim_mevcut"] = (len(g_deneyim) > 0) == (len(m_deneyim) > 0)

    # 2. Deneyim sayısı ±3 tolerans
    sonuc["deneyim_sayisi"] = abs(len(g_deneyim) - len(m_deneyim)) <= 3

    # 3. Toplam deneyim yılı ±5 tolerans
    g_yil = float(gercek.get("toplam_deneyim_yil") or 0)
    m_yil = float(model.get("toplam_deneyim_yil") or 0)
    sonuc["deneyim_yil"] = abs(g_yil - m_yil) <= 5.0

    # 4. Teknik beceriler var mı
    g_beceri = set(b.lower() for b in gercek.get("teknik_beceriler", []))
    m_beceri = set(b.lower() for b in model.get("teknik_beceriler", []))
    sonuc["beceri_mevcut"] = (len(g_beceri) > 0) == (len(m_beceri) > 0)

    # 5. Beceri sayısı ±5 tolerans
    sonuc["beceri_sayisi"] = abs(len(g_beceri) - len(m_beceri)) <= 5

    # 6. JSON yapısı geçerli mi (tüm zorunlu alanlar var mı)
    zorunlu = ["kisisel", "egitim", "deneyim", "teknik_beceriler", "toplam_deneyim_yil"]
    sonuc["json_yapisi"] = all(alan in model for alan in zorunlu)

    return sonuc

# ── Ana test döngüsü ─────────────────────────────────
print("=" * 50)
print("H1 METRİĞİ ÖLÇÜMÜ BAŞLIYOR")
print("=" * 50 + "\n")

toplam_dogru = 0
toplam_alan = 0
sonuclar = []
hatalar = []

for gt in ground_truth_listesi:
    cv_id = gt["id"]
    cv_satir = df.iloc[[cv_id - 1]]

    if cv_satir.empty:
        print(f"⚠️  CV {cv_id} bulunamadı, atlanıyor...")
        continue

    cv_metni = cv_satir["Resume_str"].values[0][:4000]

    print(f"🔄 CV {cv_id} işleniyor...", end=" ", flush=True)

    try:
        model_ciktisi = dify_cv_al(cv_metni)
        alan_sonuc = alan_dogrulugu(gt, model_ciktisi)

        dogru = sum(alan_sonuc.values())
        toplam = len(alan_sonuc)
        oran = dogru / toplam * 100

        toplam_dogru += dogru
        toplam_alan += toplam

        sonuclar.append({
            "cv_id": cv_id,
            "dogru": dogru,
            "toplam": toplam,
            "oran": oran,
            "detay": alan_sonuc
        })

        emoji = "✅" if oran >= 75 else "⚠️"
        print(f"{emoji} {oran:.1f}% ({dogru}/{toplam} alan)")

        # Başarısız alanları göster
        basarisiz = [k for k, v in alan_sonuc.items() if not v]
        if basarisiz:
            print(f"   ❌ Başarısız alanlar: {', '.join(basarisiz)}")

    except Exception as e:
        print(f"❌ HATA: {e}")
        hatalar.append({"cv_id": cv_id, "hata": str(e)})

# ── Sonuç raporu ─────────────────────────────────────
print("\n" + "=" * 50)
genel_oran = toplam_dogru / toplam_alan * 100 if toplam_alan > 0 else 0

print(f"GENEL JSON ALAN DOĞRULUĞU: {genel_oran:.1f}%")
print(f"Hedef (H1):                ≥ %85")
print(f"Durum: {'✅ BAŞARILI' if genel_oran >= 85 else '❌ HEDEFİN ALTINDA'}")
print(f"Test edilen CV: {len(sonuclar)}/{len(ground_truth_listesi)}")
if hatalar:
    print(f"Hatalı CV: {len(hatalar)}")
print("=" * 50)

# ── Dosyaya kaydet ────────────────────────────────────
os.makedirs("docs", exist_ok=True)
with open("docs/metrik_sonuclari.txt", "w", encoding="utf-8") as f:
    f.write(f"H1 Metriği — JSON Alan Doğruluğu\n")
    f.write(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    f.write(f"{'='*40}\n\n")
    for s in sonuclar:
        f.write(f"CV {s['cv_id']:2d}: {s['oran']:5.1f}%  ({s['dogru']}/{s['toplam']} alan)\n")
        basarisiz = [k for k, v in s['detay'].items() if not v]
        if basarisiz:
            f.write(f"        Başarısız: {', '.join(basarisiz)}\n")
    f.write(f"\n{'='*40}\n")
    f.write(f"GENEL DOĞRULUK: {genel_oran:.1f}%\n")
    f.write(f"Hedef (H1):     ≥ %85\n")
    f.write(f"Durum:          {'BAŞARILI' if genel_oran >= 85 else 'HEDEFİN ALTINDA'}\n")

print("\n✅ Sonuçlar docs/metrik_sonuclari.txt dosyasına kaydedildi.")