import fitz  # PyMuPDF
from docx import Document
import os

def pdf_oku(dosya_yolu: str) -> str:
    """PDF dosyasından ham metin çıkarır."""
    belge = fitz.open(dosya_yolu)
    metin_parcalari = []
    for sayfa in belge:
        metin_parcalari.append(sayfa.get_text())
    return "\n".join(metin_parcalari).strip()


def docx_oku(dosya_yolu: str) -> str:
    """Word dosyasından ham metin çıkarır."""
    belge = Document(dosya_yolu)
    paragraflar = [p.text for p in belge.paragraphs if p.text.strip()]
    return "\n".join(paragraflar)


def cv_metin_al(dosya_yolu: str) -> str:
    """Dosya uzantısına göre doğru okuyucu seçer."""
    uzanti = os.path.splitext(dosya_yolu)[1].lower()
    if uzanti == ".pdf":
        return pdf_oku(dosya_yolu)
    elif uzanti in [".docx", ".doc"]:
        return docx_oku(dosya_yolu)
    else:
        raise ValueError(f"Desteklenmeyen format: {uzanti}")


if __name__ == "__main__":
    print("cv_reader.py hazır. cv_metin_al('dosya.pdf') ile kullanın.")