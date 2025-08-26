import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models

MODEL_NAME = "models/text-embedding-004"
COLLECTION_NAME = "hubspot_docs"

load_dotenv()
print("Carregando chave de API do Google...")
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    print("SDK do Google AI configurado com sucesso.")
except Exception as e:
    print(f"Erro ao configurar o SDK do Google. Verifique sua chave de API no arquivo .env. Erro: {e}")
    exit()

qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)
print("Cliente Qdrant inicializado.")

try:
    with open('hubspot_docs_chunks.json', 'r', encoding='utf-8') as f:
        chunks_data = json.load(f)
    print(f"Arquivo 'hubspot_docs_chunks.json' lido. Total de {len(chunks_data)} chunks.")
except FileNotFoundError:
    print("Erro: 'hubspot_docs_chunks.json' não encontrado. Rode 'chunker.py' primeiro.")
    exit()

print("\nIniciando a geração de embeddings com o Google AI e o upload para o Qdrant...")
points_to_upload = []
for i, chunk in enumerate(chunks_data):
    content = chunk['content']
    print(f"Processando chunk {i+1}/{len(chunks_data)}...")

    try:
        embedding_result = genai.embed_content(
            model=MODEL_NAME,
            content=content,
            task_type="retrieval_document"
        )
        embedding = embedding_result['embedding']

        points_to_upload.append(
            models.PointStruct(
                id=i,
                vector=embedding,
                payload={"text": content}
            )
        )
        print(f"  - Embedding gerado para o chunk {i+1}.")
    except Exception as e:
        print(f"  - Ocorreu um erro ao gerar o embedding com a API do Google: {e}")
        break

if len(points_to_upload) == len(chunks_data):
    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=points_to_upload,
        wait=True
    )
    print("\n--- Upload Concluído! ---")
    print(f"{len(points_to_upload)} vetores foram enviados para a coleção '{COLLECTION_NAME}' no Qdrant.")
else:
    print("\nO processo foi interrompido devido a um erro. O upload para o Qdrant foi cancelado.")