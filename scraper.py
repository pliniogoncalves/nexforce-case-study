import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

urls_para_coletar = [
    "https://developers.hubspot.com/docs/api/overview",
    "https://developers.hubspot.com/docs/guides/apps/private-apps/overview",
    "https://developers.hubspot.com/docs/api/working-with-hubspot/authentication"
]

print("Iniciando o scraper multi-URL...")

service = ChromeService(ChromeDriverManager().install())
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--log-level=3') 
driver = webdriver.Chrome(service=service, options=options)

todo_o_conteudo = ""

try:
    for url in urls_para_coletar:
        print(f"\nBuscando conteúdo de: {url}")
        driver.get(url)
        print("Aguardando a página carregar...")
        time.sleep(5)

        page_html = driver.page_source
        soup = BeautifulSoup(page_html, 'html.parser')
        
        main_content = soup.find('article', attrs={'data-test-id': 'docs-content'})

        if main_content:
            text_content = main_content.get_text(separator='\n', strip=True)
           
            todo_o_conteudo += text_content + "\n\n--- FIM DA PÁGINA ---\n\n"
            print(f"Sucesso! Conteúdo de {len(text_content)} caracteres adicionado.")
        else:
            print(f"AVISO: Não foi possível encontrar o conteúdo principal para a URL: {url}")
    
    file_path = 'hubspot_docs.txt'
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(todo_o_conteudo)

    print(f"\n--- PROCESSO FINALIZADO ---")
    print(f"Conteúdo de {len(urls_para_coletar)} URLs foi combinado e salvo em '{file_path}'")
    print(f"Tamanho total do arquivo: {len(todo_o_conteudo)} caracteres.")

except Exception as e:
    print(f"Ocorreu um erro durante a execução do Selenium: {e}")

finally:
    driver.quit()