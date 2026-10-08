import re
from pathlib import  Path
from pypdf import PdfReader

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

def clean_text(text:str) -> str:
    text = re.sub(r"-\s*\n\s*", "", text)
    return " ".join(text.split())

def chunk_text(
        text:str,
        chunk_size: int = CHUNK_SIZE,
        overlap: int = CHUNK_OVERLAP,

)-> list[str]:

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap

    return chunks

def extract_chunks(pdf_path: str | Path) -> list[dict]:
    reader = PdfReader(pdf_path)

    chunks = []
    chunk_index = 0

    for page_number, page in enumerate(reader.pages,start=1):
        text = page.extract_text()
        if not text:
            continue
        text = clean_text(text)
        page_chunks = chunk_text(text)

        for chunk in page_chunks:
            chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "page_number": page_number,
                        "content": chunk,
                    }
                )
            chunk_index += 1

    return chunks






