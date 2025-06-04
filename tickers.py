from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

def obter_tikers():
    # Configurações do Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Executa o navegador em segundo plano
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Usa WebDriver Manager para baixar e configurar o ChromeDriver automaticamente
    service = Service(ChromeDriverManager().install())

    # Inicializa o navegador
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Acessa a página dos FIIs
    url = "https://www.fundsexplorer.com.br/ranking"
    driver.get(url)

    # Aguarda um tempo para garantir que os dados sejam carregados (ajuste se necessário)
    time.sleep(5)

    # Encontra a tabela e extrai os dados
    table = driver.find_element(By.TAG_NAME, "table")
    html_content = table.get_attribute("outerHTML")

    # Fecha o navegador
    driver.quit()

    # Converte a tabela para um DataFrame Pandas
    df = pd.read_html(html_content)[0]
    return df[df.columns[0]].dropna().tolist()

