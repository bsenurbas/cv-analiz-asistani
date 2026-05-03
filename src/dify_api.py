import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

DIFY_API_KEY = os.getenv("DIFY_API_KEY")
DIFY_BASE_URL = "https://api.dify.ai/v1"

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
    yanit.raise_for_status()
    veri = yanit.json()
    print("Ham çıktı:", json.dumps(veri, indent=2, ensure_ascii=False))
    cikti = veri["data"]["outputs"]["cv_json"]
    cikti = cikti.replace("```json", "").replace("```", "").strip()
    return json.loads(cikti)


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