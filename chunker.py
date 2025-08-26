from langchain.text_splitter import RecursiveCharacterTextSplitter
import json

try:
    with open('hubspot_docs.txt', 'r', encoding='utf-8') as f:
        hubspot_docs_text = f.read()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )

    chunks = text_splitter.split_text(hubspot_docs_text)

    chunk_objects = [{"content": chunk} for chunk in chunks]

    output_file_path = 'hubspot_docs_chunks.json'
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(chunk_objects, f, indent=2, ensure_ascii=False)

    print("--- Análise do Resultado ---")
    print(f"Sucesso! O documento foi dividido em {len(chunks)} chunks.")
    print(f"Os chunks foram salvos em '{output_file_path}'.")
    print("\nAmostra do primeiro chunk:")
    print("'" + chunks[0] + "'")
    print("------------------------------")

except FileNotFoundError:
    print("Erro: O arquivo 'hubspot_docs.txt' não foi encontrado. Execute o 'scraper.py' primeiro.")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")