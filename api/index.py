import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import httpx
from bs4 import BeautifulSoup
import google.generativeai as genai
from qdrant_client import QdrantClient, models

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def scrape_url(url: str) -> str:
    print(f"Iniciando scraping avançado com Browserless /scrape para: {url}")
    browserless_api_key = os.getenv("BROWSERLESS_API_KEY")
    if not browserless_api_key:
        raise HTTPException(status_code=500, detail="Chave da API do Browserless não configurada.")
    api_url = f"https://production-sfo.browserless.io/scrape?token={browserless_api_key}"
    payload = {"url": url, "elements": [{"selector": "article[data-test-id='docs-content']"}]}
    try:
        response = httpx.post(api_url, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        if data.get('data') and data['data'][0].get('results'):
            full_text = "\n".join([result['text'] for result in data['data'][0]['results']])
            print("Conteúdo extraído com sucesso via Browserless /scrape.")
            return full_text
        else:
            print("AVISO: O seletor não retornou resultados no endpoint /scrape.")
            return ""
    except Exception as exc:
        print(f"Ocorreu um erro ao chamar a API do Browserless: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

def chunk_text(text: str) -> list[str]:
    print("Iniciando a fragmentação do texto com a função nativa...")
    if not text:
        return []
    
    chunk_size = 1000
    chunk_overlap = 200
    
    paragraphs = text.split('\n')
    chunks = []
    current_chunk = ""

    for p in paragraphs:
        if len(current_chunk) + len(p) + 1 < chunk_size:
            current_chunk += p + "\n"
        else:
            chunks.append(current_chunk)
            current_chunk = current_chunk[-chunk_overlap:] + p + "\n"
    
    if current_chunk:
        chunks.append(current_chunk)
        
    print(f"Texto dividido em {len(chunks)} chunks.")
    return chunks

def vectorize_and_store(chunks: list[str]):
    print("Iniciando a vetorização e armazenamento no Qdrant...")
    if not chunks:
        print("Nenhum chunk para vetorizar.")
        return

    qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
    collection_name = "hubspot_docs"
    vector_size = 768

    try:
        qdrant_client.get_collection(collection_name=collection_name)
        print(f"Coleção '{collection_name}' já existe. Adicionando novo conhecimento.")
    except Exception:
        print(f"Coleção '{collection_name}' não encontrada. Criando uma nova.")
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
        )
    
    result = genai.embed_content(
        model='models/text-embedding-004',
        content=chunks,
        task_type="retrieval_document"
    )
    embeddings = result['embedding']
    
    qdrant_client.upsert(
        collection_name=collection_name,
        points=models.Batch(
            ids=[int(time.time() * 1000) + i for i in range(len(chunks))],
            vectors=embeddings,
            payloads=[{"text": chunk} for chunk in chunks]
        )
    )
    print(f"{len(chunks)} novos vetores ADICIONADOS ao Qdrant.")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class URLItem(BaseModel):
    url: HttpUrl

@app.get("/api")
def read_root():
    return {"message": "API de Ingestão de Conhecimento está funcionando!"}

@app.post("/api/add-knowledge")
async def add_knowledge(item: URLItem):
    try:
        scraped_text = scrape_url(str(item.url))
        if not scraped_text:
            raise HTTPException(status_code=400, detail="Não foi possível extrair conteúdo da URL fornecida.")
        
        text_chunks = chunk_text(scraped_text)
        if not text_chunks:
            raise HTTPException(status_code=400, detail="O conteúdo extraído estava vazio ou não pôde ser dividido.")
            
        vectorize_and_store(text_chunks)
        
        return {"status": "success", "message": f"Conhecimento da URL {item.url} adicionado com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro interno: {str(e)}")