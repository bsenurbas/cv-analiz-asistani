import json
import logging
import os

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DIFY_BASE_URL = "https://api.dify.ai/v1"
KARSILASTIRMA_API_KEY = os.getenv("KARSILASTIRMA_API_KEY")


def _json_ciktisini_temizle(cikti: str) -> dict:
    temiz = cikti.replace("```json", "").replace("```", "").strip()
    return json.loads(temiz)


def cv_karsilastir(cv1_metni: str, cv2_metni: str, ilan_metni: str) -> dict:
    if not KARSILASTIRMA_API_KEY:
        raise RuntimeError("KARSILASTIRMA_API_KEY .env dosyasinda bulunamadi.")

    try:
        yanit = requests.post(
            f"{DIFY_BASE_URL}/workflows/run",
            headers={
                "Authorization": f"Bearer {KARSILASTIRMA_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "inputs": {
                    "cv1_metni": cv1_metni,
                    "cv2_metni": cv2_metni,
                    "ilan_metni": ilan_metni,
                },
                "response_mode": "blocking",
                "user": "streamlit",
            },
            timeout=120,
        )
        yanit.raise_for_status()
        veri = yanit.json()

        ham_cikti = veri["data"]["outputs"]["karsilastirma_sonucu"]
        return _json_ciktisini_temizle(ham_cikti)

    except requests.RequestException as exc:
        logger.exception("CV karsilastirma API baglantisi basarisiz oldu.")
        raise RuntimeError("Dify CV karsilastirma API baglantisi kurulamadi.") from exc

    except (KeyError, json.JSONDecodeError) as exc:
        logger.exception("CV karsilastirma yaniti beklenen JSON formatinda degil.")
        raise RuntimeError("Dify CV karsilastirma yaniti beklenen formatta gelmedi.") from exc