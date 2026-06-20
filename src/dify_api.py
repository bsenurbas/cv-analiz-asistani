import requests
import json
import os
import tempfile
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import time
from datetime import datetime

load_dotenv()

DIFY_API_KEY       = os.getenv("DIFY_API_KEY")
ESLESTIRME_API_KEY = os.getenv("ESLESTIRME_API_KEY")
IK_ASISTAN_API_KEY = os.getenv("IK_ASISTAN_API_KEY")
DIFY_BASE_URL      = "https://api.dify.ai/v1"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Yardımcı ──────────────────────────────────────────────
def _gecici_dosyaya_yaz(content: bytes, filename: str) -> str:
    uzanti = os.path.splitext(filename)[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=uzanti)
    tmp.write(content)
    tmp.close()
    return tmp.name


# ── CV Metni Yapılandır (Dify workflow) ───────────────────
def cv_yapilandir(cv_metni: str) -> dict:
    """CV metnini Dify workflow'una gönderir, JSON döner."""
    yanit = requests.post(
        f"{DIFY_BASE_URL}/workflows/run",
        headers={
            "Authorization": f"Bearer {DIFY_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "inputs": {"cv_metni": cv_metni},
            "response_mode": "blocking",
            "user": "cv-analiz-sistemi"
        },
        timeout=60
    )
    print("Dify yanıtı:", yanit.status_code, yanit.text)
    yanit.raise_for_status()
    veri = yanit.json()
    print("Ham çıktı:", json.dumps(veri, indent=2, ensure_ascii=False))
    cikti = veri["data"]["outputs"]["cv_json"]
    cikti = cikti.replace("```json", "").replace("```", "").strip()
    return json.loads(cikti)


# ── Endpoint 1: CV Analiz ─────────────────────────────────
@app.post("/api/cv/analyze")
async def analyze_cv(file: UploadFile = File(...)):
    from src.cv_reader import cv_metin_al
    content = await file.read()
    tmp_path = _gecici_dosyaya_yaz(content, file.filename)
    try:
        metin = cv_metin_al(tmp_path)
        sonuc = cv_yapilandir(metin)
    finally:
        os.unlink(tmp_path)
    return sonuc


# ── Endpoint 2: CV Karşılaştırma ─────────────────────────
@app.post("/api/cv/compare")
async def compare_cvs(
    cv1: UploadFile = File(...),
    cv2: UploadFile = File(...),
    job_desc: str = Form("")
):
    from src.cv_reader import cv_metin_al
    from src.karsilastirma_api import cv_karsilastir
    tmp1 = _gecici_dosyaya_yaz(await cv1.read(), cv1.filename)
    tmp2 = _gecici_dosyaya_yaz(await cv2.read(), cv2.filename)
    try:
        metin1 = cv_metin_al(tmp1)
        metin2 = cv_metin_al(tmp2)
        sonuc = cv_karsilastir(metin1, metin2, job_desc)
    finally:
        os.unlink(tmp1)
        os.unlink(tmp2)
    return sonuc

# ── Yardımcı: Geçmiş Kaydetme ──────────────────────────────
def skor_kaydet(job_desc: str, en_iyi_aday_id: str, en_iyi_skor: str, harcanan_sure: float):
    gecmis_yolu = "docs/skor_gecmisi.json"
    os.makedirs(os.path.dirname(gecmis_yolu), exist_ok=True)
    
    # Tarih formatına saniyeyi de ekledik (Örn: 2026-05-20 23:28:35)
    tarih = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ozet = job_desc[:55] + "..." if len(job_desc) > 55 else job_desc
    
    yeni_kayit = {
        "Tarih": tarih,
        "İlan Metni": ozet,
        "Aday ID": str(en_iyi_aday_id),
        "Skor": f"{en_iyi_skor}/100",
        "Sure": f"{harcanan_sure:.2f}s"
    }
    
    try:
        if os.path.exists(gecmis_yolu):
            with open(gecmis_yolu, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []
            
        data.insert(0, yeni_kayit) # En yeni kayıt en başa
        
        with open(gecmis_yolu, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Geçmiş kaydetme hatası:", str(e))


def tfidf_hesapla(job_desc: str) -> list:
    csv_path = "data/processed/Resume_temiz.csv"
    if not os.path.exists(csv_path):
        return []
        
    try:
        df_cv = pd.read_csv(csv_path)
        cv_metinleri = df_cv["temiz_metin"].fillna("").tolist()
        vektorizer = TfidfVectorizer(max_features=3000, sublinear_tf=True)
        matris = vektorizer.fit_transform([job_desc] + cv_metinleri)
        benzerlikler = cosine_similarity(matris[0:1], matris[1:])[0]
        top5_idx = benzerlikler.argsort()[-5:][::-1]
        
        sonuclar = []
        for idx in top5_idx:
            pct = int(benzerlikler[idx] * 100)
            cv_id = str(df_cv.iloc[idx].get("ID", f"#{idx}"))
            kategori = str(df_cv.iloc[idx].get("Category", "Belirsiz"))
            sonuclar.append({
                "cv_id": cv_id,
                "kategori": kategori,
                "skor": pct
            })
        return sonuclar
    except Exception as e:
        print("TF-IDF Hatası:", str(e))
        return []

# ── Endpoint 3: İş İlanı Eşleştirme ──────────────────────
@app.post("/api/matching")
def job_matching(body: dict):
    if not ESLESTIRME_API_KEY:
        raise HTTPException(status_code=500, detail="ESLESTIRME_API_KEY bulunamadı.")
        
    job_desc = body.get("job_desc", "")
    baslangic_zamani = time.time()
    
    yanit = requests.post(
        f"{DIFY_BASE_URL}/workflows/run",
        headers={"Authorization": f"Bearer {ESLESTIRME_API_KEY}"},
        json={"inputs": {"ilan_metni": job_desc}, "response_mode": "blocking", "user": "react-user"},
        timeout=120
    )
    
    if yanit.status_code != 200:
         raise HTTPException(status_code=yanit.status_code, detail=yanit.text)
         
    veri = yanit.json()
    
    try:
        eslesme_ham = veri["data"]["outputs"]["eslesme_sonucu"]
        eslesme_ham = eslesme_ham.replace("```json", "").replace("```", "").strip()
        eslesme_sonuc = json.loads(eslesme_ham)
    except KeyError:
        raise HTTPException(status_code=500, detail=f"Dify yanıtında 'eslesme_sonucu' bulunamadı.")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"JSON Parse Hatası: {str(e)}")

    # 3. TF-IDF Sonuçlarını İlave Et
    tfidf_sonuclari = tfidf_hesapla(job_desc)
    eslesme_sonuc["tfidf_sonuclari"] = tfidf_sonuclari

    bitis_zamani = time.time()
    harcanan_sure = bitis_zamani - baslangic_zamani
    
    adaylar = eslesme_sonuc.get("adaylar", [])
    if adaylar:
        # Listenin ilk sırasındaki aday en iyi adaydır
        en_iyi_aday = adaylar[0]
        en_iyi_id = en_iyi_aday.get("aday_id", "-")
        en_iyi_skor = en_iyi_aday.get("skor", 0)
    else:
        en_iyi_id = "-"
        en_iyi_skor = 0

    skor_kaydet(job_desc, en_iyi_id, en_iyi_skor, harcanan_sure)

    return eslesme_sonuc
@app.get("/api/matching/history")
def get_matching_history():
    gecmis_yolu = "docs/skor_gecmisi.json"
    if os.path.exists(gecmis_yolu):
        try:
            with open(gecmis_yolu, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data[:5] # Sadece son 5 kaydı döndür
        except:
            return []
    return []

# ── Endpoint 4: İK Asistanı ───────────────────────────────
@app.post("/api/assistant/chat")
async def assistant_chat(body: dict):
    yanit = requests.post(
        f"{DIFY_BASE_URL}/chat-messages",
        headers={"Authorization": f"Bearer {IK_ASISTAN_API_KEY}"},
        json={
            "inputs": {},
            "query": body.get("message"),
            "response_mode": "blocking",
            "conversation_id": body.get("conversation_id", ""),
            "user": "react-user"
        },
        timeout=60
    )
    return yanit.json()

# ──  Sidebar Metrikleri (YENİ) ────────────────
@app.get("/api/metrics")
def get_metrics():
    import pandas as pd
    
    api_key_tanimli_mi = bool(DIFY_API_KEY)
    
    # 1. Veritabanı ve Toplam CV Sayısı Kontrolü
    veritabani_durumu = "Çevrimdışı"
    toplam_cv_sayisi = "0"
    try:
        df_real = pd.read_csv("data/processed/Resume_temiz.csv")
        toplam_cv_sayisi = str(len(df_real))
        veritabani_durumu = "Bağlı"
    except:
        toplam_cv_sayisi = "2484"  # Fallback veri boyutu
        veritabani_durumu = "Hata (CSV)"

    # 2. AI Modeli Durumu Kontrolü
    ai_model_durumu = "Aktif" if api_key_tanimli_mi else "Çevrimdışı"

    # 3. Skor Geçmişinden Dinamik Metrikleri ve Ortalama İşlem Hızını Hesapla
    analiz_yapilan_sayi = 0
    eslestirilen_sayi = 0
    toplam_sure = 0
    gecerli_sure_sayisi = 0
    ortalama_hiz = "~1.2s"  # Varsayılan başlangıç değeri

    gecmis_yolu = "docs/skor_gecmisi.json"
    if os.path.exists(gecmis_yolu):
        try:
            with open(gecmis_yolu, "r", encoding="utf-8") as f:
                gecmis_data = json.load(f)
                
            analiz_yapilan_sayi = len(gecmis_data)
            
            for kayit in gecmis_data:
                # Eşleşme sayılarını hesapla
                skor_str = str(kayit.get("Skor", "0")).split("/")[0]
                if skor_str.isdigit() and int(skor_str) >= 70:
                    eslestirilen_sayi += 1
                
                # İşlem hızını hesapla
                sure_val = kayit.get("Sure") or kayit.get("Süre")
                if sure_val:
                    sure_with_no_s = str(sure_val).replace("s", "").replace("sn", "").strip()
                    try:
                        toplam_sure += float(sure_with_no_s)
                        gecerli_sure_sayisi += 1
                    except ValueError:
                        pass
            
            # Eğer geçmişte ölçülmüş süreler varsa ortalamasını al
            if gecerli_sure_sayisi > 0:
                ortalama_hiz = f"~{round(toplam_sure / gecerli_sure_sayisi, 1)}s"
        except Exception as e:
            print("Metrik hesaplama hatası:", e)

    return {
        "veritabani": veritabani_durumu,
        "toplam_cv": toplam_cv_sayisi,
        "ai_durumu": ai_model_durumu,
        "hiz": ortalama_hiz,
        "analiz_yapilan": analiz_yapilan_sayi,
        "eslestirilen": eslestirilen_sayi
    }

if __name__ == "__main__":
    test_cv = """
    John Doe
    Software Engineer at ABC Corp (2020-2023)
    Skills: Python, Django, PostgreSQL
    Education: BSc Computer Science, MIT, 2020
    """
    print("Test CV gönderiliyor...")
    sonuc = cv_yapilandir(test_cv)
    print(json.dumps(sonuc, indent=2, ensure_ascii=False))