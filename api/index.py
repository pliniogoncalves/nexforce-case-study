import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
import google.generativeai as genai
from qdrant_client import QdrantClient, models

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def scrape_url(url: str) -> str:
    print(f"Iniciando scraping para: {url}")
    service = ChromeService(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--log-level=3')
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        driver.get(url)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        content_article = soup.find('article', attrs={'data-test-id': 'docs-content'})
        
        if content_article:
            print("Conteúdo extraído com sucesso.")
            return content_article.get_text(separator='\n', strip=True)
        else:
            print("AVISO: Artigo de conteúdo principal não encontrado.")
            return ""
    finally:
        driver.quit()

def chunk_text(text: str) -> list[str]:
    print("Iniciando a fragmentação do texto...")
    if not text:
        return []
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    
    chunks = text_splitter.split_text(text)
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