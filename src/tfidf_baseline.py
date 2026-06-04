import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score
import os

os.chdir(r"C:\Users\bsenu\OneDrive\Masaüstü\Kişisel Projeler\cv-analiz-asistani")

# ── 1. Veri yükle ────────────────────────────────────
df = pd.read_csv("data/processed/Resume_temiz.csv")
print("Veri yüklendi:", df.shape)

# ── 2. TF-IDF vektörize et ───────────────────────────
vektorizer = TfidfVectorizer(
    ngram_range=(1, 2),
    max_features=5000,
    sublinear_tf=True
)
df["temiz_metin"] = df["temiz_metin"].fillna("").astype(str)
X = vektorizer.fit_transform(df["temiz_metin"])
y = df["Category"]
print("TF-IDF matris boyutu:", X.shape)

# ── 3. Train/test split ──────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ── 4. Model eğit ───────────────────────────────────
model = LogisticRegression(max_iter=1000, random_state=42)
model.fit(X_train, y_train)
print("Model eğitildi.")

# ── 5. Değerlendir ──────────────────────────────────
y_pred = model.predict(X_test)
f1 = f1_score(y_test, y_pred, average="weighted")
print(f"\nF1 Score (weighted): {f1:.4f}")
print("\nDetaylı Rapor:")
print(classification_report(y_test, y_pred))

# ── 6. Grafik ───────────────────────────────────────
rapor = classification_report(y_test, y_pred, output_dict=True)
kategoriler = [k for k in rapor.keys() if k not in ["accuracy", "macro avg", "weighted avg"]]
f1_skorlar = [rapor[k]["f1-score"] for k in kategoriler]

plt.figure(figsize=(12, 7))
plt.barh(kategoriler, f1_skorlar, color="#6B3FA0")
plt.axvline(x=f1, color="red", linestyle="--", label=f"Ortalama F1: {f1:.2f}")
plt.title("TF-IDF Modeli — Kategori Bazında F1 Skorları", fontsize=14, fontweight="bold")
plt.xlabel("F1 Score")
plt.ylabel("Kategori")
plt.legend()
plt.tight_layout()
plt.savefig("visuals/tfidf_f1_skorlar.png", dpi=150)
plt.show()
print("Grafik kaydedildi.")