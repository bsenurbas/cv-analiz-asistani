import streamlit as st
import pandas as pd
import time
import random
import requests
import json
import logging
import os
import sys
from dotenv import load_dotenv
import io
import numpy as np
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Proje kök dizinini path'e ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.cv_reader import cv_metin_al
from src.dify_api import cv_yapilandir
from src.karsilastirma_api import cv_karsilastir
from utils import skor_kaydet
from utils import skor_kaydet, sidebar_metriklerini_hesapla

DIFY_API_KEY = os.getenv("DIFY_API_KEY")
ESLESTIRME_API_KEY = os.getenv("ESLESTIRME_API_KEY")
IK_ASISTAN_API_KEY = os.getenv("IK_ASISTAN_API_KEY")
DIFY_BASE_URL = "https://api.dify.ai/v1"

@st.cache_resource
def kategori_modelini_yukle():
    df = pd.read_csv("data/processed/Resume_temiz.csv")
    df["temiz_metin"] = df["temiz_metin"].fillna("").astype(str)

    vektorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=5000,
        sublinear_tf=True,
    )
    X = vektorizer.fit_transform(df["temiz_metin"])
    y = df["Category"]

    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X, y)

    return vektorizer, model


def kategori_tahmin_et(cv_metni: str) -> tuple[str, float]:
    vektorizer, model = kategori_modelini_yukle()
    X = vektorizer.transform([cv_metni])

    kategori = model.predict(X)[0]

    if hasattr(model, "predict_proba"):
        olasiliklar = model.predict_proba(X)[0]
        guven = float(np.max(olasiliklar))
    else:
        guven = 0.0

    return kategori, guven


def beceri_radar_figuru(beceriler: list[str]):
    beceri_metni = " ".join(str(b).lower() for b in beceriler)

    eksenler = {
        "Programlama": ["python", "sql", "c#", "c", "javascript", "java"],
        "AI / Veri": ["machine learning", "deep learning", "nlp", "rag", "llm", "pandas", "numpy", "scikit"],
        "Web": ["html", "css", "streamlit", "react", "django", "flask"],
        "Araclar": ["git", "github", "linux", "docker", "vector", "database"],
        "Test": ["pytest", "unittest", "test", "automation"],
    }

    skorlar = []
    for kelimeler in eksenler.values():
        eslesen = sum(1 for kelime in kelimeler if kelime in beceri_metni)
        skorlar.append(min(100, int(eslesen / max(len(kelimeler), 1) * 100)))

    etiketler = list(eksenler.keys())
    acilar = np.linspace(0, 2 * np.pi, len(etiketler), endpoint=False).tolist()

    skorlar += skorlar[:1]
    acilar += acilar[:1]

    fig, ax = plt.subplots(figsize=(4.6, 4.2), subplot_kw={"polar": True})
    fig.patch.set_facecolor("#111318")
    ax.set_facecolor("#111318")
    ax.plot(acilar, skorlar, color="#00b4ff", linewidth=2)
    ax.fill(acilar, skorlar, color="#00b4ff", alpha=0.25)
    ax.set_xticks(acilar[:-1])
    ax.set_xticklabels(etiketler, color="#c5d8ea", fontsize=9)
    ax.set_ylim(0, 100)
    ax.tick_params(colors="#7a8ba0", labelsize=8)
    ax.spines["polar"].set_color("#1f2d40")
    ax.set_title("Beceri Radar Grafiği", color="#dce8f0", pad=16, fontsize=11, fontweight="bold")
    ax.grid(color="#263244", alpha=0.7)

    return fig


def deneyim_timeline_figuru(deneyimler: list[dict]):
    temiz_deneyimler = [
        d for d in deneyimler
        if d.get("baslangic") is not None
    ]

    if not temiz_deneyimler:
        return None

    fig, ax = plt.subplots(figsize=(6.2, max(2.8, len(temiz_deneyimler) * 0.58)))
    fig.patch.set_facecolor("#111318")
    ax.set_facecolor("#111318")

    for i, d in enumerate(temiz_deneyimler):
        baslangic = int(d.get("baslangic"))
        bitis = int(d.get("bitis") or 2026)
        sure = max(1, bitis - baslangic)

        etiket = f'{d.get("pozisyon", "Pozisyon")} - {d.get("sirket", "Şirket")}'
        ax.barh(i, sure, left=baslangic, color="#64dcb4", alpha=0.85)
        ax.text(baslangic, i, f"  {etiket}", va="center", color="#dce8f0", fontsize=8)

    ax.set_yticks([])
    ax.set_xlabel("Yıl", color="#7a8ba0")
    ax.set_title("Deneyim Zaman Çizelgesi", color="#dce8f0", fontsize=11, fontweight="bold")
    ax.tick_params(colors="#7a8ba0", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#1f2d40")
    ax.grid(axis="x", color="#263244", alpha=0.7)
    fig.tight_layout()

    return fig

# ─── Sayfa Yapılandırması ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Destekli - CV Analiz Sistemi | Akıllı İK Paneli",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── HARİCİ CSS DOSYASINI OKUMA VE YÜKLEME ────────────────────────────────────
# Tasarımın temiz kalması için CSS kodlarını 'style.css' dosyasına taşıdık.
css_dosya_yolu = "src/style.css"  # Proje yapına göre gerekirse "src/style.css" yapabilirsin

if os.path.exists(css_dosya_yolu):
    with open(css_dosya_yolu, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    # Eğer style.css henüz oluşturulmadıysa çökmesini engellemek için yedek güvenli alan
    st.warning("⚠️ 'style.css' dosyası bulunamadı. Lütfen CSS kodlarını bu isimde bir dosyaya taşıyın.")

# ─── HERO BANNER ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap">
    <div class="hero-badge">AI-POWERED</div>
    <div class="hero-title">AI Destekli - CV Analiz Sistemi</div>
    <p class="hero-sub">Yapay Zeka Destekli Özgeçmiş Analiz ve İş İlanı Eşleştirme Sistemi</p>
</div>
""", unsafe_allow_html=True)


# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "📄  CV Yükle & Analiz",
    "🔗  İş İlanı Eşleştir",
    "🤖  İK Asistanı",
])


# ══════════════════════════════════════════════════════════════════════════════
# SEKME 1 — CV Yükle & Analiz
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-label">ADIM 1</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Özgeçmiş Yükle & Analiz Et</div>', unsafe_allow_html=True)

    left, right = st.columns([1, 1], gap="large")

    with left:
        # Not: Markdown div aç/kapat yerine doğrudan CSS ile file_uploader'ı hedefledik
        uploaded_file = st.file_uploader(
            "Özgeçmiş Dosyasını Seçin",
            type=["pdf", "docx"],
            label_visibility="visible"
        )

        analyze_btn = st.button("⚡   Analiz Başlat", type="primary", use_container_width=True)

        if analyze_btn and uploaded_file is None:
            st.warning("⚠️   Lütfen önce bir dosya yükleyin.")

    with right:
        if analyze_btn and uploaded_file is not None:
            with st.spinner("CV okunuyor ve analiz ediliyor..."):
                import tempfile
                uzanti = os.path.splitext(uploaded_file.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=uzanti) as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                
                cv_metni = cv_metin_al(tmp_path)
                os.unlink(tmp_path)
                
                try:
                    cv_json = cv_yapilandir(cv_metni)
                    st.session_state["cv_json"] = cv_json
                    st.session_state["cv_metni"] = cv_metni
                    analiz_basarili = True
                except Exception as e:
                    logger.exception("CV analizi basarisiz oldu.")
                    st.error("CV analiz edilemedi. Lutfen dosya formatini ve Dify API ayarlarini kontrol edip tekrar deneyin.")
                    analiz_basarili = False
            
            if analiz_basarili:
                st.success("✅   Analiz tamamlandı!")

        elif not analyze_btn:
            # Boş Durum Kartı
            st.markdown("""
            <div class="card">
                <div style="text-align:center; padding: 2.5rem 1rem; color: #718096;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">📂</div>
                    <div style="font-size: 1rem; font-weight: 600; color: #2D3748; margin-bottom: 0.5rem;">
                        Analiz sonuçları burada görünecek
                    </div>
                    <div style="font-size: 0.85rem;">
                        Soldan dosya yükleyip "Analiz Başlat"a tıklayın
                    </div>
                </div>
            </div>

            """, unsafe_allow_html=True)

    cv = st.session_state.get("cv_json")
    if cv:
        deneyim = cv.get("toplam_deneyim_yil", 0) or 0
        beceriler = cv.get("teknik_beceriler", [])
        egitim = cv.get("egitim", [])
        deneyimler = cv.get("deneyim", [])
        oneriler = cv.get("oneriler", [])
        kategori, kategori_guven = kategori_tahmin_et(st.session_state.get("cv_metni", ""))

        st.markdown('<div class="section-label" style="margin-top:1.6rem;">PROFIL KARTI</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Analiz Sonucu ve Aday Profili</div>', unsafe_allow_html=True)

        profil_col, analiz_col = st.columns([1.05, 1], gap="large")

        with profil_col:
            egitim_html = ""
            if egitim:
                ilk = egitim[0]
                egitim_html = f'{ilk.get("kurum","")}, {ilk.get("bolum","")}, {ilk.get("derece","")}'
            else:
                egitim_html = "Eğitim bilgisi bulunamadı."

            beceri_html = "".join(f'<span class="skill-tag">{s}</span>' for s in beceriler[:14])
            if not beceri_html:
                beceri_html = '<span style="color:#7a8ba0;">Teknik beceri bulunamadı.</span>'

            deneyim_html = ""
            for d in deneyimler[:4]:
                bitis = d.get("bitis") or "günümüz"
                deneyim_html += (
                    '<div style="margin-bottom:8px; color:#c5d8ea; line-height:1.45;">'
                    '<span style="color:#00b4ff;">•</span> '
                    f'<b>{d.get("pozisyon","")}</b>, '
                    f'<span style="color:#7a8ba0;">{d.get("sirket","")} ({d.get("baslangic","")} - {bitis})</span>'
                    '</div>'
                )
            if not deneyim_html:
                deneyim_html = '<div style="color:#7a8ba0;">Deneyim bilgisi bulunamadı.</div>'

            st.markdown(f"""
            <div class="card">
                <div class="metric-row">
                    <div class="metric-tile"><div class="metric-val">{int(deneyim)}</div><div class="metric-lbl">Deneyim (yıl)</div></div>
                    <div class="metric-tile"><div class="metric-val">{len(beceriler)}</div><div class="metric-lbl">Yetenek</div></div>
                    <div class="metric-tile"><div class="metric-val">{len(egitim)}</div><div class="metric-lbl">Eğitim</div></div>
                </div>
                <div style="margin-top:1rem;">
                    <div class="section-label">EĞİTİM</div>
                    <div style="color:#dce8f0; font-weight:700; line-height:1.45;">{egitim_html}</div>
                </div>
                <div style="margin-top:1.1rem;">
                    <div class="section-label">TEKNİK BECERİLER</div>
                    <div>{beceri_html}</div>
                </div>
                <div style="margin-top:1.1rem;">
                    <div class="section-label">DENEYİMLER</div>
                    {deneyim_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with analiz_col:
            st.markdown(f"""
            <div class="card card-accent">
                <div class="section-label">KATEGORİ TAHMİNİ</div>
                <div style="color:#dce8f0; font-size:1.08rem; font-weight:800; line-height:1.45;">
                    Bu CV en çok şu kategoriye benziyor: {kategori}
                    <span style="color:#00b4ff;">({kategori_guven * 100:.0f}%)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            chart_a, chart_b = st.columns(2, gap="medium")
            with chart_a:
                st.markdown('<div class="card"><div class="section-label">BECERİ RADARI</div>', unsafe_allow_html=True)
                if beceriler:
                    radar_fig = beceri_radar_figuru(beceriler)
                    st.pyplot(radar_fig, clear_figure=False)
                    plt.close(radar_fig)
                else:
                    st.info("Radar grafiği için beceri bulunamadı.")
                st.markdown('</div>', unsafe_allow_html=True)

            with chart_b:
                st.markdown('<div class="card"><div class="section-label">DENEYİM ÇİZELGESİ</div>', unsafe_allow_html=True)
                timeline_fig = deneyim_timeline_figuru(deneyimler)
                if timeline_fig is not None:
                    st.pyplot(timeline_fig, clear_figure=False)
                    plt.close(timeline_fig)
                else:
                    st.info("Zaman çizelgesi için deneyim tarihi bulunamadı.")
                st.markdown('</div>', unsafe_allow_html=True)

        if oneriler:
            st.markdown('<div class="section-label" style="margin-top:1rem;">GÜÇLENDİRME ÖNERİLERİ</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-title">CV\'yi Güçlendirmek İçin Öneriler</div>', unsafe_allow_html=True)

            oneri_cols = st.columns(2, gap="large")
            for i, oneri in enumerate(oneriler):
                oneri_kategori = oneri.get("kategori", "Öneri")
                baslik = oneri.get("baslik", "")
                aciklama = oneri.get("aciklama", "")

                with oneri_cols[i % 2]:
                    st.markdown(f"""
                    <div class="card card-green" style="min-height:178px;">
                        <div class="section-label">{oneri_kategori}</div>
                        <div style="color:#dce8f0; font-size:1rem; font-weight:800; margin-bottom:8px; line-height:1.35;">
                            {baslik}
                        </div>
                        <div style="color:#7a8ba0; font-size:0.9rem; line-height:1.65;">
                            {aciklama}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-label">ADIM 1B</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Iki CV Karsilastir</div>', unsafe_allow_html=True)

    kars_col1, kars_col2 = st.columns([1, 1], gap="large")

    with kars_col1:
        cv1_file = st.file_uploader(
            "Birinci CV",
            type=["pdf", "docx"],
            key="karsilastirma_cv1",
        )

        cv2_file = st.file_uploader(
            "Ikinci CV",
            type=["pdf", "docx"],
            key="karsilastirma_cv2",
        )

    with kars_col2:
        karsilastirma_ilan = st.text_area(
            "Karsilastirma icin is ilani",
            height=150,
            placeholder="Orn: Stratejik IK deneyimi olan, performans yonetimi ve ise alim sureclerini yonetecek IK yoneticisi araniyor...",
            key="karsilastirma_ilan",
        )

        karsilastir_btn = st.button(
            "CV Karsilastir",
            type="primary",
            use_container_width=True,
            disabled=not (cv1_file and cv2_file and karsilastirma_ilan.strip()),
        )

    if karsilastir_btn:
        import tempfile

        tmp_paths = []

        try:
            with st.spinner("Iki CV karsilastiriliyor..."):
                for dosya in [cv1_file, cv2_file]:
                    uzanti = os.path.splitext(dosya.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=uzanti) as tmp:
                        tmp.write(dosya.read())
                        tmp_paths.append(tmp.name)

                cv1_metni = cv_metin_al(tmp_paths[0])
                cv2_metni = cv_metin_al(tmp_paths[1])

                sonuc = cv_karsilastir(
                    cv1_metni=cv1_metni,
                    cv2_metni=cv2_metni,
                    ilan_metni=karsilastirma_ilan,
                )

            st.success("Karsilastirma tamamlandi!")

            daha_uygun = sonuc.get("daha_uygun_cv", "-")
            ozet = sonuc.get("uygunluk_ozeti", "")
            cv1 = sonuc.get("cv1", {})
            cv2 = sonuc.get("cv2", {})

            st.markdown(f"""
            <div class="card card-green">
                <div class="section-label">SONUC</div>
                <div style="color:#dce8f0; font-size:1.1rem; font-weight:700; margin-bottom:8px;">
                    Daha uygun aday: {daha_uygun}
                </div>
                <div style="color:#7a8ba0; font-size:0.9rem;">{ozet}</div>
            </div>
            """, unsafe_allow_html=True)

            skor_col1, skor_col2 = st.columns(2, gap="large")

            with skor_col1:
                st.markdown(f"""
                <div class="card">
                    <div class="section-label">CV 1</div>
                    <div class="metric-val">{cv1.get("skor", "-")}</div>
                    <div style="color:#7a8ba0; margin:8px 0;">{cv1.get("ilanla_uyum", "")}</div>
                    <b>Guclu yonler</b>
                    <ul>{"".join(f"<li>{madde}</li>" for madde in cv1.get("guclu_yonler", []))}</ul>
                    <b>Zayif yonler</b>
                    <ul>{"".join(f"<li>{madde}</li>" for madde in cv1.get("zayif_yonler", []))}</ul>
                </div>
                """, unsafe_allow_html=True)

            with skor_col2:
                st.markdown(f"""
                <div class="card">
                    <div class="section-label">CV 2</div>
                    <div class="metric-val">{cv2.get("skor", "-")}</div>
                    <div style="color:#7a8ba0; margin:8px 0;">{cv2.get("ilanla_uyum", "")}</div>
                    <b>Guclu yonler</b>
                    <ul>{"".join(f"<li>{madde}</li>" for madde in cv2.get("guclu_yonler", []))}</ul>
                    <b>Zayif yonler</b>
                    <ul>{"".join(f"<li>{madde}</li>" for madde in cv2.get("zayif_yonler", []))}</ul>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="card card-accent">
                <div class="section-label">KARAR GEREKCESI</div>
                <div style="color:#c5d8ea;">{sonuc.get("karar_gerekcesi", "")}</div>
            </div>
            """, unsafe_allow_html=True)

        except Exception:
            logger.exception("CV karsilastirma islemi basarisiz oldu.")
            st.error("CV karsilastirma tamamlanamadi. Lutfen dosyalari, is ilani metnini ve Dify API ayarlarini kontrol edin.")

        finally:
            for tmp_path in tmp_paths:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    logger.warning("Gecici dosya silinemedi: %s", tmp_path)
# ══════════════════════════════════════════════════════════════════════════════
# SEKME 2 — İş İlanı Eşleştir
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-label">ADIM 2</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">İş İlanı — CV Uyum Analizi</div>', unsafe_allow_html=True)

    # Giriş Alanı Kartı
    job_description = st.text_area(
        "İş İlanı Metnini Buraya Yapıştırın",
        height=160,
        placeholder="Örn: En az 3 yıl deneyimli, Python ve SQL bilen veri mühendisi aranıyor...",
        label_visibility="collapsed" # Kart içinde temiz görünüm için
    )

    match_btn = st.button("🔍    En Uygun Adayları Getir", type="primary")

    if match_btn:
        if not job_description.strip():
            st.warning("⚠️    Lütfen bir iş ilanı metni girin.")
        else:
            with st.spinner("Aday havuzunda tarama yapılıyor…"):
                baslangic_zamani = time.time()
                try:
                    yanit = requests.post(
                        f"{DIFY_BASE_URL}/workflows/run",
                        headers={"Authorization": f"Bearer {ESLESTIRME_API_KEY}", "Content-Type": "application/json"},
                        json={"inputs": {"ilan_metni": job_description}, "response_mode": "blocking", "user": "streamlit"},
                        timeout=120
                    )
                    bitis_zamani = time.time()  # ⏱️ Süreyi durdur
                    harcanan_sure = bitis_zamani - baslangic_zamani

                    veri = yanit.json()
                    logger.info("Dify eslestirme yaniti alindi.")
                    eslesme_ham = veri["data"]["outputs"]["eslesme_sonucu"]
                    eslesme_ham = eslesme_ham.replace("```json", "").replace("```", "").strip()
                    eslesme_sonuc = json.loads(eslesme_ham)
                    eslesme_basarili = True
                except requests.RequestException:
                    logger.exception("Dify eslestirme API baglantisi basarisiz oldu.")
                    st.error("Baglanti kurulamadi. Lutfen internet baglantisini ve Dify eslestirme API anahtarini kontrol edin.")
                    eslesme_basarili = False
                except (KeyError, json.JSONDecodeError):
                    logger.exception("Dify eslestirme yaniti beklenen formatta degil: %s", veri)
                    st.error("Eslestirme sonucu beklenen formatta gelmedi. Lutfen Dify workflow cikti alanlarini kontrol edin.")
                    eslesme_basarili = False
                except Exception:
                    logger.exception("Eslestirme sirasinda beklenmeyen hata olustu.")
                    st.error("Eslestirme tamamlanamadi. Lutfen daha sonra tekrar deneyin.")
                    eslesme_basarili = False

            if eslesme_basarili:
                adaylar = eslesme_sonuc.get("adaylar", [])
                st.success(f"✅    Eşleştirme tamamlandı! {len(adaylar)} aday değerlendirildi.")
                
                skor_kaydet(job_description, adaylar, harcanan_sure=harcanan_sure)
                
                col_l, col_r = st.columns(2, gap="large")

                with col_l:
                    st.markdown('<div class="section-label">TF-IDF · VEKTÖREL ANALİZ</div>', unsafe_allow_html=True)
                    from sklearn.feature_extraction.text import TfidfVectorizer
                    from sklearn.metrics.pairwise import cosine_similarity
                    import pandas as pd
                    df_cv = pd.read_csv("data/processed/Resume_temiz.csv")
                    cv_metinleri = df_cv["temiz_metin"].fillna("").tolist()
                    vektorizer = TfidfVectorizer(max_features=3000, sublinear_tf=True)
                    matris = vektorizer.fit_transform([job_description] + cv_metinleri)
                    benzerlikler = cosine_similarity(matris[0:1], matris[1:])[0]
                    top5_idx = benzerlikler.argsort()[-5:][::-1]
                    
                    tfidf_html = '<div class="card">'
                    for idx in top5_idx:
                        pct = int(benzerlikler[idx] * 100)
                        cv_id = df_cv.iloc[idx]["ID"]
                        kategori = df_cv.iloc[idx]["Category"]
                        tfidf_html += f"""
                        <div style="margin-bottom:14px; padding-bottom:14px; border-bottom:1px solid #E2E8F0;">
                            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                                <span style="color:#1A202C !important; font-weight:700;">CV #{cv_id}</span>
                                <span style="color:#3182CE; font-weight:700;">{pct}%</span>
                            </div>
                            <div style="color:#718096; font-size:0.78rem; margin-bottom:6px;">{kategori}</div>
                            <div class="match-bar-bg"><div class="match-bar-fill" style="width:{pct}%"></div></div>
                        </div>"""
                    tfidf_html += '</div>'
                    st.markdown(tfidf_html, unsafe_allow_html=True)

                with col_r:
                    st.markdown('<div class="section-label">LLM · ANLAMSAL ANALİZ</div>', unsafe_allow_html=True)
                    llm_html = '<div class="card">'
                    for i, aday in enumerate(adaylar[:5]):
                        skor = aday.get("skor", 0)
                        gerekce = aday.get("gerekce", "")
                        aday_id = aday.get("aday_id", f"#{i+1}")
                        tag = "✅ Önerilir" if skor >= 70 else "⚡ Potansiyel" if skor >= 50 else "❌ Uygun Değil"
                        
                        # Açık temada yeşil badge'i görünür kılmak için arka planı hafif koyulaştırdık
                        llm_html += f"""
                        <div style="margin-bottom:14px; padding-bottom:14px; border-bottom:1px solid #E2E8F0;">
                            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                                <span style="color:#1A202C !important; font-weight:700;">Aday {i+1} | {aday_id}</span>
                                <span style="background:rgba(56,161,105,0.15); border:1px solid rgba(56,161,105,0.3);
                                            color:#276749; font-size:0.72rem; font-weight:700; padding:2px 8px;
                                            border-radius:20px;">{tag} · {skor}/100</span>
                            </div>
                            <div style="color:#4A5568; font-size:0.83rem;">{gerekce}</div>
                        </div>"""
                    llm_html += '</div>'
                    st.markdown(llm_html, unsafe_allow_html=True)

    # ─── GEÇMİŞ EŞLEŞTİRMELER BÖLÜMÜ (🆕 Yeni Eklenen Alan) ───────────────────
    st.markdown('<br><hr>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">GEÇMİŞ EŞLEŞTİRMELER</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Son Yapılan Analiz Kayıtları</div>', unsafe_allow_html=True)
    
    gecmis_yolu = "docs/skor_gecmisi.json"
    if os.path.exists(gecmis_yolu):
        try:
            with open(gecmis_yolu, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data:
                # Son 5 aramayı alıp dataframe'e dönüştür
                df_gecmis = pd.DataFrame(data[:5])
                st.dataframe(
                    df_gecmis, 
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Henüz kaydedilmiş bir eşleştirme geçmişi bulunmuyor.")
        except:
            st.info("Henüz kaydedilmiş bir eşleştirme geçmişi bulunmuyor.")
    else:
        st.info("Henüz kaydedilmiş bir eşleştirme geçmişi bulunmuyor.")

# ══════════════════════════════════════════════════════════════════════════════
# SEKME 3 — İK Asistanı
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-label">ADIM 3</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Akıllı İK Asistanı</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card" style="margin-bottom:1rem;">
        <div style="color:#5a6a7e; font-size:1rem;">
        Adaylar, mülakat soruları, ücret aralıkları veya İK süreçleri hakkında her şeyi sorabilirsiniz.
        Asistan, aday veritabanınıza ve iş ilanlarınıza göre yanıt üretir.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Session state başlat
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Merhaba! 👋 Ben AI Destekli CV Analiz Sistemi İK Asistanınızım. Aday profilleri, mülakat soruları veya işe alım süreçleri hakkında her konuda yardımcı olmaya hazırım.",
            }
        ]

    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = ""

    # Dify chatbot API fonksiyonu
    def generate_response(user_msg: str) -> str:
        try:
            yanit = requests.post(
                f"{DIFY_BASE_URL}/chat-messages",
                headers={
                    "Authorization": f"Bearer {IK_ASISTAN_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "inputs": {},
                    "query": user_msg,
                    "response_mode": "blocking",
                    "conversation_id": st.session_state.conversation_id,
                    "user": "streamlit-user"
                },
                timeout=60
            )
            yanit.raise_for_status()
            veri = yanit.json()

            if "conversation_id" in veri:
                st.session_state.conversation_id = veri["conversation_id"]

            return veri.get("answer", "Uzgunum, su anda yanit uretilemedi. Lutfen sorunuzu tekrar deneyin.")

        except requests.RequestException:
            logger.exception("IK asistani API baglantisi basarisiz oldu.")
            return "Baglanti kurulamadi. Lutfen Dify chatbot API anahtarini ve internet baglantisini kontrol edin."
        except Exception:
            logger.exception("IK asistani yanit uretirken beklenmeyen hata olustu.")
            return "Uzgunum, su anda yanit uretilemedi. Lutfen daha sonra tekrar deneyin."

    # Hızlı sorular
    st.markdown('<div style="margin: 0.5rem 0 0.8rem; color:#3a4a5e; font-size:0.78rem; font-weight:600; letter-spacing:1px;">HIZLI SORULAR</div>', unsafe_allow_html=True)

    quick_cols = st.columns(3)
    quick_questions = [
        "📊 Python developer adaylarını listele",
        "💬 HR pozisyonu için mülakat soruları öner",
        "🔍 Veri bilimi deneyimli aday var mı?",
    ]
    for i, (col, q) in enumerate(zip(quick_cols, quick_questions)):
        with col:
            if st.button(q, key=f"quick_{i}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": q})
                with st.chat_message("user"):
                    st.markdown(q)
                with st.chat_message("assistant"):
                    with st.spinner("Düşünüyorum…"):
                        resp = generate_response(q)
                    st.markdown(resp)
                st.session_state.messages.append({"role": "assistant", "content": resp})

    # Sohbet geçmişi
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Kullanıcı girdisi
    if prompt := st.chat_input("Mesajınızı yazın… (örn: 'Python bilen adayları listele')"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Düşünüyorum…"):
                response = generate_response(prompt)
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

    # Geçmişi temizle
    if len(st.session_state.messages) > 1:
        if st.button("🗑️  Sohbeti Temizle", key="clear_chat"):
            st.session_state.messages = [{"role": "assistant", "content": "Merhaba! 👋 Ben AI Destekli CV Analiz Sistemi İK Asistanınızım. Nasıl yardımcı olabilirim?"}]
            st.session_state.conversation_id = ""
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR ARAYÜZÜ
# ══════════════════════════════════════════════════════════════════════════════
# API key tanımlı mı kontrolünü fonksiyona yolluyoruz
api_kontrol = True if ESLESTIRME_API_KEY else False
sistem_metrikleri = sidebar_metriklerini_hesapla(api_key_tanimli_mi=api_kontrol)

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0 0.5rem;">
        <div style="width:64px; height:64px; border-radius:16px; margin:0 auto 0.75rem;
             background:linear-gradient(135deg,#0d5fa0,#64dcb4); display:flex;
             align-items:center; justify-content:center; color:#ffffff;
             font-family:'Syne',sans-serif; font-size:1.15rem; font-weight:800;">CV</div>
        <div style="font-family:'Syne',sans-serif; font-size:1.2rem; font-weight:800;
             background:linear-gradient(90deg,#e0f4ff,#00b4ff);
             -webkit-background-clip:text; -webkit-text-fill-color:transparent;
             background-clip:text;">AI Destekli - CV Analiz Sistemi</div>
        <div style="color:#7a8ba0; font-size:0.88rem; margin-top:2px;">Yapay Zeka Destekli</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown('<div style="color:#5a6a7e; font-size:0.75rem; font-weight:600; letter-spacing:1.5px; text-transform:uppercase; margin-bottom:10px;">SİSTEM DURUMU</div>', unsafe_allow_html=True)

    # ARTIK BURADAKİ TÜM DEĞERLER SİSTEMDEN ANLIK GELİYOR 🎯
    metrics = [
        ("✅", "Veritabanı", sistem_metrikleri["veritabanı"]),
        ("📁", "Toplam CV", sistem_metrikleri["toplam_cv"]),
        ("🤖", "AI Modeli", sistem_metrikleri["ai_durumu"]),
        ("⚡", "İşlem Hızı", sistem_metrikleri["hiz"]),
    ]
    for icon, label, val in metrics:
        st.markdown(f"""
        <div class="sidebar-metric">
            <div class="sidebar-metric-icon">{icon}</div>
            <div>
                <div class="sidebar-metric-val">{val}</div>
                <div class="sidebar-metric-lbl">{label}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown('<div style="color:#5a6a7e; font-size:0.75rem; font-weight:600; letter-spacing:1.5px; text-transform:uppercase; margin-bottom:10px;">HAFTALIK ÖZET</div>', unsafe_allow_html=True)

    summary_html = f"""
    <div style="background:#151b28; border:1px solid #1f2d40; border-radius:10px; padding:1rem;">
        <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
            <span style="color:#7a8ba0; font-size:0.82rem;">Yeni Başvuru</span>
            <span style="color:#00b4ff; font-weight:700; font-family:'Syne',sans-serif;">+47</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
            <span style="color:#7a8ba0; font-size:0.82rem;">Analiz Yapılan</span>
            <span style="color:#64dcb4; font-weight:700; font-family:'Syne',sans-serif;">{sistem_metrikleri["analiz_yapilan"]}</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
            <span style="color:#7a8ba0; font-size:0.82rem;">Eşleştirilen</span>
            <span style="color:#f5a623; font-weight:700; font-family:'Syne',sans-serif;">{sistem_metrikleri["eslestirilen"]}</span>
        </div>
        <div style="display:flex; justify-content:space-between;">
            <span style="color:#7a8ba0; font-size:0.82rem;">Mülakat Planlanan</span>
            <span style="color:#c5d8ea; font-weight:700; font-family:'Syne',sans-serif;">5</span>
        </div>
    </div>
    """
    st.markdown(summary_html, unsafe_allow_html=True)
    
    # ... Alt kısım aynı ...

    st.divider()
    st.markdown(
        '<div style="color:#3a4a5e; font-size:0.72rem; text-align:center;">Veri Madenciliği Projesi · 2026</div>',
        unsafe_allow_html=True,
    )
