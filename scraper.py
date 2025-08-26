import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

url = "https://developers.hubspot.com/docs/api/overview"

print(f"Buscando conteúdo de: {url} usando Selenium...")

service = ChromeService(ChromeDriverManager().install())

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--log-level=3') 
driver = webdriver.Chrome(service=service, options=options)

try:
    driver.get(url)
    print("Aguardando a página carregar completamente...")
    time.sleep(5)

    page_html = driver.page_source
    soup = BeautifulSoup(page_html, 'html.parser')
    main_content = soup.find('article', attrs={'data-test-id': 'docs-content'})

    if main_content:
        text_content = main_content.get_text(separator='\n', strip=True)
        file_path = 'hubspot_docs.txt'
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text_content)

        print(f"Sucesso! Conteúdo salvo em '{file_path}'")
        print(f"Tamanho do arquivo: {len(text_content)} caracteres.")
    else:
        print("Erro Crítico: O seletor '<article data-test-id=\"docs-content\">' não foi encontrado. Verifique o HTML.")

except Exception as e:
    print(f"Ocorreu um erro durante a execução do Selenium: {e}")

finally:
    driver.quit()