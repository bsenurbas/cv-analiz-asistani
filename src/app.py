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

DIFY_API_KEY = os.getenv("DIFY_API_KEY")
ESLESTIRME_API_KEY = os.getenv("ESLESTIRME_API_KEY")
IK_ASISTAN_API_KEY = os.getenv("IK_ASISTAN_API_KEY")
DIFY_BASE_URL = "https://api.dify.ai/v1"

# ─── Sayfa Yapılandırması ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Destekli - CV Analiz Sistemi | Akıllı İK Paneli",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=Syne:wght@700;800&display=swap');

/* ── Reset & Base ────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
.main .block-container {
    padding: 2rem 2.5rem 3rem;
    max-width: 1200px;
}
.main { background: #0d0f14; }
section[data-testid="stSidebar"] { background: #111318 !important; border-right: 1px solid #1f2330; }

/* ── Scrollbar ───────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0d0f14; }
::-webkit-scrollbar-thumb { background: #2a2f42; border-radius: 3px; }

/* ── Hero Banner ─────────────────────────────── */
.hero-wrap {
    background: linear-gradient(135deg, #0d1b2a 0%, #112240 50%, #0d0f14 100%);
    border: 1px solid #1e3a5f;
    border-radius: 20px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero-wrap::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 300px; height: 300px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(0,180,255,0.12) 0%, transparent 70%);
    pointer-events: none;
}
.hero-wrap::after {
    content: '';
    position: absolute;
    bottom: -40px; left: 40%;
    width: 200px; height: 200px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(100,220,180,0.07) 0%, transparent 70%);
    pointer-events: none;
}
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.6rem;
    font-weight: 800;
    background: linear-gradient(90deg, #e0f4ff 0%, #64dcb4 50%, #00b4ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 0.4rem;
    letter-spacing: -0.5px;
}
.hero-sub {
    color: #7a8ba0;
    font-size: 1.05rem;
    font-weight: 400;
    margin: 0;
}
.hero-badge {
    display: inline-block;
    background: rgba(0,180,255,0.12);
    border: 1px solid rgba(0,180,255,0.3);
    color: #00b4ff;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 50px;
    margin-bottom: 1rem;
}

/* ── Tab Bar ─────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: #111318;
    padding: 6px;
    border-radius: 14px;
    border: 1px solid #1f2330;
    margin-bottom: 1.5rem;
}
.stTabs [data-baseweb="tab"] {
    height: 44px;
    border-radius: 10px;
    padding: 0 22px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    font-size: 0.9rem;
    color: #5a6a7e;
    background: transparent;
    border: none;
    transition: all 0.2s;
}
.stTabs [data-baseweb="tab"]:hover { color: #c5d8ea; background: #181d2a; }
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #0d3a5f, #1a5276) !important;
    color: #e0f4ff !important;
    font-weight: 600;
    box-shadow: 0 2px 12px rgba(0,100,180,0.35);
}
.stTabs [data-baseweb="tab-highlight"] { display: none; }
.stTabs [data-baseweb="tab-border"] { display: none; }

/* ── Cards ───────────────────────────────────── */
.card {
    background: #111318;
    border: 1px solid #1f2330;
    border-radius: 16px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.2rem;
            
}
.card-accent {
    border-left: 3px solid #00b4ff;
}
.card-green {
    border-left: 3px solid #64dcb4;
}
.section-label {
    font-family: 'Syne', sans-serif;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #3a7bd5;
    margin-bottom: 0.6rem;
}
.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: #dce8f0;
    margin-bottom: 1.2rem;
}

/* ── Metric Tiles ────────────────────────────── */
.metric-row { display: flex; gap: 12px; margin-bottom: 1.2rem; flex-wrap: wrap; }
.metric-tile {
    flex: 1;
    min-width: 130px;
    background: #151b28;
    border: 1px solid #1f2d40;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    text-align: center;
}
.metric-val {
    font-family: 'Syne', sans-serif;
    font-size: 1.8rem;
    font-weight: 800;
    color: #00b4ff;
    line-height: 1.1;
}
.metric-lbl {
    font-size: 0.78rem;
    color: #5a6a7e;
    font-weight: 500;
    margin-top: 2px;
}

/* ── Skill Tags ──────────────────────────────── */
.skill-tag {
    display: inline-block;
    background: rgba(0,180,255,0.1);
    border: 1px solid rgba(0,180,255,0.25);
    color: #7ec8e8;
    font-size: 0.8rem;
    font-weight: 500;
    padding: 3px 12px;
    border-radius: 20px;
    margin: 3px 3px 3px 0;
}

/* ── Match Score Bar ─────────────────────────── */
.match-bar-wrap { margin: 6px 0 10px; }
.match-bar-label {
    display: flex;
    justify-content: space-between;
    font-size: 0.82rem;
    color: #7a8ba0;
    margin-bottom: 4px;
}
.match-bar-bg {
    background: #1a2030;
    border-radius: 4px;
    height: 8px;
    overflow: hidden;
}
.match-bar-fill {
    height: 100%;
    border-radius: 4px;
    background: linear-gradient(90deg, #1a78c2, #00b4ff);
}
.match-bar-fill.green {
    background: linear-gradient(90deg, #1aaa77, #64dcb4);
}

/* ── Chat ────────────────────────────────────── */
.chat-user-msg {
    background: linear-gradient(135deg, #0d3a5f, #1a5276);
    border: 1px solid #1e5080;
    border-radius: 16px 16px 4px 16px;
    padding: 0.9rem 1.2rem;
    color: #d4ecff;
    font-size: 0.92rem;
    margin-bottom: 12px;
    max-width: 80%;
    margin-left: auto;
}
.chat-bot-msg {
    background: #151b28;
    border: 1px solid #1f2d40;
    border-radius: 16px 16px 16px 4px;
    padding: 0.9rem 1.2rem;
    color: #c5d8ea;
    font-size: 0.92rem;
    margin-bottom: 12px;
    max-width: 80%;
}
.chat-timestamp {
    font-size: 0.7rem;
    color: #3a4a5e;
    margin-top: 3px;
}

/* ── Buttons ─────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #0d5fa0, #0080cc) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.55rem 1.8rem !important;
    transition: all 0.2s !important;
    box-shadow: 0 2px 12px rgba(0,128,204,0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(0,128,204,0.45) !important;
}
.stButton > button[kind="secondary"] {
    background: #1a2030 !important;
    box-shadow: none !important;
}

/* ── File Uploader ───────────────────────────── */
[data-testid="stFileUploader"] {
    background: #111318;
    border: 2px dashed #1f2d40;
    border-radius: 14px;
    padding: 1rem;
    transition: border-color 0.2s;
}
[data-testid="stFileUploader"]:hover { border-color: #0080cc; }

/* ── Text Area & Input ───────────────────────── */
textarea, .stTextArea textarea {
    background: #111318 !important;
    border: 1px solid #1f2d40 !important;
    border-radius: 10px !important;
    color: #c5d8ea !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
}
textarea:focus { border-color: #0080cc !important; box-shadow: 0 0 0 2px rgba(0,128,204,0.15) !important; }

/* ── Tables ──────────────────────────────────── */
[data-testid="stTable"] { border-radius: 12px; overflow: hidden; }
thead tr th {
    background: #151b28 !important;
    color: #5a8aa0 !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
    border-bottom: 1px solid #1f2d40 !important;
}
tbody tr td { background: #111318 !important; color: #c0d4e0 !important; border-bottom: 1px solid #191f2e !important; }
tbody tr:hover td { background: #141a28 !important; }

/* ── Sidebar ─────────────────────────────────── */
.sidebar-metric {
    background: #151b28;
    border: 1px solid #1f2d40;
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.sidebar-metric-icon { font-size: 1.2rem; }
.sidebar-metric-val { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 1.1rem; color: #c5d8ea; }
.sidebar-metric-lbl { font-size: 0.75rem; color: #5a6a7e; }

/* ── Alerts Override ─────────────────────────── */
[data-testid="stAlert"] {
    background: #111318 !important;
    border-radius: 10px !important;
}
.stSuccess { border-left: 3px solid #64dcb4 !important; }
.stWarning { border-left: 3px solid #f5a623 !important; }
.stInfo    { border-left: 3px solid #00b4ff !important; }

/* ── Spinner ─────────────────────────────────── */
.stSpinner > div { border-top-color: #00b4ff !important; }

/* ── Divider ─────────────────────────────────── */
hr { border-color: #1f2330 !important; }

/* ── Chat Input ──────────────────────────────── */
[data-testid="stChatInput"] > div {
    background: #111318 !important;
    border: 1px solid #1f2d40 !important;
    border-radius: 12px !important;
}
[data-testid="stChatInput"] textarea { background: transparent !important; border: none !important; }
[data-testid="stChatMessageContent"] { color: #c5d8ea !important; }
</style>
""", unsafe_allow_html=True)


# ─── Hero Banner ──────────────────────────────────────────────────────────────
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
                cv = st.session_state.get("cv_json", {})
                deneyim = cv.get("toplam_deneyim_yil", 0) or 0
                beceriler = cv.get("teknik_beceriler", [])
                egitim = cv.get("egitim", [])
                
                results_html = '<div class="analysis-card">'
                results_html += f"""
                <div class="metric-row">
                    <div class="metric-tile"><div class="metric-val">{int(deneyim)}</div><div class="metric-lbl">Deneyim (yıl)</div></div>
                    <div class="metric-tile"><div class="metric-val">{len(beceriler)}</div><div class="metric-lbl">Yetenek</div></div>
                    <div class="metric-tile"><div class="metric-val">{len(egitim)}</div><div class="metric-lbl">Eğitim</div></div>
                </div><br>"""
                
                if egitim:
                    ilk = egitim[0]
                    results_html += f'<div style="margin-bottom:12px;"><b>🎓 Eğitim</b><br>{ilk.get("kurum","")}, {ilk.get("bolum","")}, {ilk.get("derece","")}</div>'
                
                results_html += '<div style="margin-bottom:12px;"><b>🛠️ Teknik Beceriler</b><br>'
                results_html += "".join(f'<span class="skill-tag">{s}</span>' for s in beceriler[:12])
                results_html += '</div>'
                
                deneyimler = cv.get("deneyim", [])
                if deneyimler:
                    results_html += '<div style="margin-bottom:12px;"><b>💼 Deneyimler</b><br>'
                    for d in deneyimler:
                        results_html += f'<div style="margin-bottom:6px; color:#c5d8ea;">• {d.get("pozisyon","")}, <span style="color:#5a6a7e;">{d.get("sirket","")} ({d.get("baslangic","")}–{d.get("bitis","günümüz")})</span></div>'
                    results_html += '</div>'
                
                results_html += '</div>'
                st.markdown(results_html, unsafe_allow_html=True)

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

    match_btn = st.button("🔍   En Uygun Adayları Getir", type="primary")

    if match_btn:
        if not job_description.strip():
            st.warning("⚠️   Lütfen bir iş ilanı metni girin.")
        else:
            with st.spinner("Aday havuzunda tarama yapılıyor…"):
                veri = {}
                try:
                    yanit = requests.post(
                        f"{DIFY_BASE_URL}/workflows/run",
                        headers={"Authorization": f"Bearer {ESLESTIRME_API_KEY}", "Content-Type": "application/json"},
                        json={"inputs": {"ilan_metni": job_description}, "response_mode": "blocking", "user": "streamlit"},
                        timeout=120
                    )
                    yanit.raise_for_status()
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
                st.success(f"✅   Eşleştirme tamamlandı! {len(adaylar)} aday değerlendirildi.")
                
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
                        <div style="margin-bottom:14px; padding-bottom:14px; border-bottom:1px solid #1f2330;">
                            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                                <span style="color:#c5d8ea; font-weight:700;">CV #{cv_id}</span>
                                <span style="color:#00b4ff; font-weight:700;">{pct}%</span>
                            </div>
                            <div style="color:#5a6a7e; font-size:0.78rem; margin-bottom:6px;">{kategori}</div>
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
                        guclu = aday.get("guclu_yonler", [])
                        aday_id = aday.get("aday_id", f"#{i+1}")
                        tag = "✅ Önerilir" if skor >= 70 else "⚡ Potansiyel" if skor >= 50 else "❌ Uygun Değil"
                        llm_html += f"""
                        <div style="margin-bottom:14px; padding-bottom:14px; border-bottom:1px solid #1f2330;">
                            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                                <span style="color:#c5d8ea; font-weight:700;">Aday {i+1} | {aday_id}</span>
                                <span style="background:rgba(56,161,105,0.1); border:1px solid rgba(56,161,105,0.25);
                                            color:#64dcb4; font-size:0.72rem; font-weight:600; padding:2px 8px;
                                            border-radius:20px;">{tag} · {skor}/100</span>
                            </div>
                            <div style="color:#5a6a7e; font-size:0.83rem;">{gerekce}</div>
                        </div>"""
                    llm_html += '</div>'
                
                    st.markdown(llm_html, unsafe_allow_html=True)

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
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
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
             background-clip:text;">CV Analiz Asistanı</div>
        <div style="color:#7a8ba0; font-size:0.82rem; margin-top:4px;">CV Analiz Asistanı — Kocaeli Üniversitesi 2026</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown('<div style="color:#5a6a7e; font-size:0.75rem; font-weight:600; letter-spacing:1.5px; text-transform:uppercase; margin-bottom:10px;">SİSTEM DURUMU</div>', unsafe_allow_html=True)

    metrics = [
        ("✅", "Veritabanı", "Bağlı"),
        ("📁", "Toplam CV", "2484"),
        ("🤖", "AI Modeli", "Aktif"),
        ("⚡", "İşlem Hızı", "~1.2s"),
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

    summary_html = """
    <div style="background:#151b28; border:1px solid #1f2d40; border-radius:10px; padding:1rem;">
        <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
            <span style="color:#7a8ba0; font-size:0.82rem;">Yeni Başvuru</span>
            <span style="color:#00b4ff; font-weight:700; font-family:'Syne',sans-serif;">+47</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
            <span style="color:#7a8ba0; font-size:0.82rem;">Analiz Yapılan</span>
            <span style="color:#64dcb4; font-weight:700; font-family:'Syne',sans-serif;">38</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
            <span style="color:#7a8ba0; font-size:0.82rem;">Eşleştirilen</span>
            <span style="color:#f5a623; font-weight:700; font-family:'Syne',sans-serif;">12</span>
        </div>
        <div style="display:flex; justify-content:space-between;">
            <span style="color:#7a8ba0; font-size:0.82rem;">Mülakat Planlanan</span>
            <span style="color:#c5d8ea; font-weight:700; font-family:'Syne',sans-serif;">5</span>
        </div>
    </div>
    """
    st.markdown(summary_html, unsafe_allow_html=True)

    st.divider()
    st.markdown(
        '<div style="color:#2a3540; font-size:0.72rem; text-align:center;">Veri Madenciliği Projesi · 2025</div>',
        unsafe_allow_html=True,
    )
