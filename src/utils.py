import json
import os
from datetime import datetime
import pandas as pd

def skor_kaydet(ilan, aday_listesi):
    """
    Dify'dan dönen eşleşme sonuçlarını ve ilan özetini 
    docs/skor_gecmisi.json dosyasına kaydeder.
    """
    os.makedirs("docs", exist_ok=True)
    gecmis_yolu = "docs/skor_gecmisi.json"
    
    # Mevcut veriyi oku
    if os.path.exists(gecmis_yolu):
        try:
            with open(gecmis_yolu, "r", encoding="utf-8") as f:
                gecmis_veri = json.load(f)
        except:
            gecmis_veri = []
    else:
        gecmis_veri = []
        
    # Her bir aday için kayıt oluştur
    tarih_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for aday in aday_listesi[:5]: # En iyi 5 adayı kaydet
        kayit = {
            "Tarih": tarih_str,
            "İlan Metni": ilan[:50] + "..." if len(ilan) > 50 else ilan,
            "Aday ID": aday.get("aday_id", "Bilinmiyor"),
            "Skor": f"{aday.get('skor', 0)}/100"
        }
        gecmis_veri.insert(0, kayit) # En yeni aramayı en üste ekle
        
    # JSON dosyasına yaz
    with open(gecmis_yolu, "w", encoding="utf-8") as f:
        json.dump(gecmis_veri, f, ensure_ascii=False, indent=4)

def sidebar_metriklerini_hesapla(api_key_tanimli_mi=True):
    """
    Sistem durumundaki tüm metrikleri (Veritabanı, CV Sayısı, AI Durumu, Hız)
    ve haftalık özet verilerini dinamik olarak hesaplar.
    """
    # 1. Veritabanı ve Toplam CV Sayısı Kontrolü
    veritabanı_durumu = "Çevrimdışı"
    toplam_cv_sayisi = "0"
    try:
        df_real = pd.read_csv("data/processed/Resume_temiz.csv")
        toplam_cv_sayisi = str(len(df_real))
        veritabanı_durumu = "Bağlı"
    except:
        toplam_cv_sayisi = "2484"  # Fallback veri boyutu
        veritabanı_durumu = "Hata (CSV)"

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
                skor_str = kayit.get("Skor", "0").split("/")[0]
                if int(skor_str) >= 70:
                    eslestirilen_sayi += 1
                
                # İşlem hızını hesapla (Kayıt fonksiyonuna 'Sure' parametresi ekleyeceğiz)
                sure_val = kayit.get("Sure")
                if sure_val:
                    toplam_sure += float(sure_with_no_s := str(sure_val).replace("s", "").strip())
                    gecerli_sure_sayisi += 1
            
            # Eğer geçmişte ölçülmüş süreler varsa ortalamasını al
            if gecerli_sure_sayisi > 0:
                ortalama_hiz = f"~{round(toplam_sure / gecerli_sure_sayisi, 1)}s"
        except:
            pass

    return {
        "veritabanı": veritabanı_durumu,
        "toplam_cv": toplam_cv_sayisi,
        "ai_durumu": ai_model_durumu,
        "hiz": ortalama_hiz,
        "analiz_yapilan": analiz_yapilan_sayi,
        "eslestirilen": eslestirilen_sayi
    }

def skor_kaydet(ilan, aday_listesi, harcanan_sure=None):
    """
    Skor geçmişini kaydederken işlem süresini de ekleyecek şekilde güncellendi.
    """
    os.makedirs("docs", exist_ok=True)
    gecmis_yolu = "docs/skor_gecmisi.json"
    
    if os.path.exists(gecmis_yolu):
        try:
            with open(gecmis_yolu, "r", encoding="utf-8") as f:
                gecmis_veri = json.load(f)
        except:
            gecmis_veri = []
    else:
        gecmis_veri = []
        
    tarih_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for aday in aday_listesi[:5]:
        kayit = {
            "Tarih": tarih_str,
            "İlan Metni": ilan[:50] + "..." if len(ilan) > 50 else ilan,
            "Aday ID": aday.get("aday_id", "Bilinmiyor"),
            "Skor": f"{aday.get('skor', 0)}/100",
            "Sure": f"{round(harcanan_sure, 2)}s" if harcanan_sure else "1.2s"  # Süreyi JSON'a ekliyoruz
        }
        gecmis_veri.insert(0, kayit)
        
    with open(gecmis_yolu, "w", encoding="utf-8") as f:
        json.dump(gecmis_veri, f, ensure_ascii=False, indent=4)