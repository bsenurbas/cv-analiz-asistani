import pandas as pd
import random
import os

os.chdir(r"C:\Users\bsenu\OneDrive\Masaüstü\Kişisel Projeler\cv-analiz-asistani")

random.seed(42)

df_cv = pd.read_csv("data/raw/Resume.csv")
df_insan = pd.read_excel("docs/insan_degerlendirmesi.xlsx")

# Mevcut ilan-kategori eşleşmeleri
ilan_kategori = {
    "Job 1 (HR Manager)": "HR",
    "Job 2 (İK Uzmanı)": "HR",
    "Job 3 (Executive Chef)": "CHEF",
    "Job 4 (Mutfak Şefi)": "CHEF",
    "Job 5 (Senior Accountant)": "ACCOUNTANT",
    "Job 6 (Genel Muhasebe Uzmanı)": "ACCOUNTANT",
    "Job 7 (Personal Trainer)": "FITNESS",
    "Job 8 (Pilates/Grup Eğitmeni)": "FITNESS",
    "Job 9 (IT Support & Systems)": "INFORMATION-TECHNOLOGY",
    "Job 10 (Sistem ve Ağ Yöneticisi)": "INFORMATION-TECHNOLOGY"
}

# Her ilan için alakasız 2 kategori
alakasiz_kategori = {
    "HR": ["CHEF", "INFORMATION-TECHNOLOGY"],
    "CHEF": ["INFORMATION-TECHNOLOGY", "ACCOUNTANT"],
    "ACCOUNTANT": ["FITNESS", "CHEF"],
    "FITNESS": ["ACCOUNTANT", "HR"],
    "INFORMATION-TECHNOLOGY": ["CHEF", "FITNESS"]
}

# İnsan değerlendirmesini parse et
ilanlar = []
simdiki_ilan = None
simdiki_aciklama = None

for _, row in df_insan.iterrows():
    col0 = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
    cv_id = row.iloc[2] if pd.notna(row.iloc[2]) else None
    sira = row.iloc[3] if pd.notna(row.iloc[3]) else None
    aciklama = str(row.iloc[7]) if pd.notna(row.iloc[7]) and str(row.iloc[7]) != "nan" else None

    if col0 and col0 != "nan" and "Job" in col0:
        simdiki_ilan = col0
    if aciklama:
        simdiki_aciklama = aciklama

    if simdiki_ilan and cv_id and sira:
        ilanlar.append({
            "ilan": simdiki_ilan,
            "aciklama": simdiki_aciklama,
            "cv_id": int(cv_id),
            "insan_sirasi": int(sira)
        })

df_ilanlar = pd.DataFrame(ilanlar)

# Her ilana 2 alakasız CV ekle (insan sırası 6 ve 7 — en düşük)
yeni_kayitlar = []
for ilan_adi, grup in df_ilanlar.groupby("ilan"):
    ana_kategori = ilan_kategori.get(ilan_adi, "HR")
    alakasiz = alakasiz_kategori.get(ana_kategori, ["CHEF", "FITNESS"])
    aciklama = grup["aciklama"].dropna().iloc[0] if not grup["aciklama"].dropna().empty else ilan_adi

    mevcut_idler = set(grup["cv_id"].tolist())

    for i, kat in enumerate(alakasiz):
        kat_cvler = df_cv[df_cv["Category"] == kat]
        kat_cvler = kat_cvler[~kat_cvler["ID"].isin(mevcut_idler)]
        if kat_cvler.empty:
            continue
        secilen = kat_cvler.sample(1, random_state=42+i).iloc[0]
        yeni_kayitlar.append({
            "ilan": ilan_adi,
            "aciklama": aciklama,
            "cv_id": int(secilen["ID"]),
            "insan_sirasi": 6 + i  # 6. ve 7. sıra — en düşük uyum
        })
        mevcut_idler.add(int(secilen["ID"]))

df_yeni = pd.DataFrame(yeni_kayitlar)
df_guncel = pd.concat([df_ilanlar, df_yeni], ignore_index=True)
df_guncel = df_guncel.sort_values(["ilan", "insan_sirasi"]).reset_index(drop=True)

print(f"Eski kayıt sayısı: {len(df_ilanlar)}")
print(f"Eklenen kayıt sayısı: {len(df_yeni)}")
print(f"Yeni toplam: {len(df_guncel)}")
print("\nÖrnek — Job 2 (İK Uzmanı):")
print(df_guncel[df_guncel["ilan"] == "Job 2 (İK Uzmanı)"][["cv_id", "insan_sirasi"]])

# Kaydet
df_guncel.to_csv("docs/insan_degerlendirmesi_guncel.csv", index=False)
print("\nKaydedildi: docs/insan_degerlendirmesi_guncel.csv")