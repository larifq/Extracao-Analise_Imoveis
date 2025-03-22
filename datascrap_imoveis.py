import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import re
import os
import csv
from html import unescape
from urllib.parse import unquote, urlparse

class Extrator_de_Dados():

    def __init__(self):
        self.driver = False
        self.now = datetime.now()
        self.urls_extraidas = {}
        self.dados_extraidos = {}


    def carrega_dados_extraidos(self, dir:str="./dados_extraidos/1_bronze/"):
        for file in os.listdir(dir):
            pass


    def retorna_elemento_da_pagina(self, xpath:str) -> object:
        return self.driver.find_element(By.XPATH, xpath)


    def se_houver_elemento_clicar_nele(self, xpath:str):
        try:
            elemento = self.retorna_elemento_da_pagina(xpath)  # Tenta localizar o elemento
            elemento.click()  # Se encontrado, clica nele
            return True
        except NoSuchElementException:
            return False


    def extrair_urls_desta_pesquisa(self, url_da_pesquisa:str) -> list:
        """
        Entra com um link da pesquisa, exemplo, URL da pesquisa realizado em São Paulo com 2 dorm com preço máximo de R$ 2.000
        Retorna uma lista de URL dos imóveis encontrados.
        Retorna vazio caso nao encontrar
        """

        # Valida se o argumento da URL é uma string
        if not isinstance(url_da_pesquisa, str):
            raise TypeError(f"Esperado uma URL de argumento string, mas foi recebido {type(url_da_pesquisa).__name__}: {url_da_pesquisa}")

        html_da_pagina = testa_e_retorna_responseText(url_da_pesquisa)
        dominio, imobiliaria = identifica_anunciante_do_url(url_da_pesquisa)
        lista_de_links = []

        match imobiliaria:
            case "chavesnamao":
                # Os links dos imoveis do CHAVESNAMAO são armazenados no <script> do código HTML no formato JSON
                SEPARADOR_DOS_LINKS_NO_HTML = '<script type="application/ld+json">'
                
                html_separados:list = html_da_pagina.split(SEPARADOR_DOS_LINKS_NO_HTML)
                html_separados.pop(0)
                
                for item in html_separados:
                    json_in_html = item.split("</script>")[0]
                    try:
                        especific_url = json.loads(json_in_html)
                    except json.JSONDecodeError as e:
                        char_pos = e.pos
                        json_string_truncada = json_in_html[:char_pos]  # Cortar a string até o ponto do erro
                        especific_url = json.loads(json_string_truncada)
                    if "object" in especific_url:
                        especific_url = especific_url["object"]["url"]
                        lista_de_links.append(especific_url)

            case "quintoandar":
                PADRAO_INICIO = 'data-testid="house-card-container-rent"><a href="'
                PADRAO_FIM = '\?'
                return retorna_lista_de_urls_separando_html(html_da_pagina, dominio, PADRAO_INICIO, PADRAO_FIM)

            #case "olx":
                #PADRAO_INICIO = 'data-testid="house-card-container-rent"><a href="'
                #PADRAO_FIM = '"'
                #return retorna_lista_de_urls_separando_html(html_da_pagina, dominio, PADRAO_INICIO, PADRAO_FIM)

            case "lopes":
                PADRAO_INICIO = 'class="lead-button" href="'
                PADRAO_FIM = '"'
                return retorna_lista_de_urls_separando_html(html_da_pagina, dominio, PADRAO_INICIO, PADRAO_FIM)

            case _:
                raise ImobiliariaNaoCadastrada(f"O programa ainda não tem a imobiliaria {imobiliaria} mapeada para extração de urls da página de pesquisa")
        hoje = self.now.strftime("%Y-%m-%d")
        if not hoje in self.urls_extraidas:
            self.urls_extraidas[hoje]=[]

        self.urls_extraidas[hoje].extend(lista_de_links)
        return lista_de_links


    def extrair_dados_imobiliarios_desta_url(self, url_do_imovel:str, acessar_pagina_repetida=False) -> dict:
        """
        A partir da URL DO IMOVEL, a função abrirá o selenium e extrairás as informações do imóvel retornando um dicionário.
        """

        # Valida se o argumento da URL é uma string
        if not isinstance(url_do_imovel, str):
            raise TypeError(f"Esperado uma URL de argumento string, mas foi recebido {type(url_do_imovel).__name__}: {url_do_imovel}")

        dominio, imobiliaria = identifica_anunciante_do_url(url_do_imovel)
        if acessar_pagina_repetida and url_do_imovel in self.dados_extraidos[imobiliaria]:
            print(url_do_imovel + "já foi extraído anteriormente")
            return

        # Cria dicionário inicial
        dict_dados_obtidos = {
            'url':url_do_imovel,
            'imobiliaria':imobiliaria,
            'data_extracao':self.now
            }

        XPATHS_CLICAR = []

        match imobiliaria:
            case "chavesnamao":
                XPATHS_CLICAR = [
                "/html/body/main/article/section[2]/div/div[1]/div/span/svg"
                ]
                XPATHS_INFO = {
                    "ALUGUEL":      "/html/body/main/article/section[2]/div/table/tbody/tr[1]/td[1]/p[2]/b",
                    "CONDOMINIO":   "/html/body/main/article/section[2]/div/table/tbody/tr[2]/td[2]/p",
                    "IPTU":         "/html/body/main/article/section[2]/div/table/tbody/tr[3]/td[2]/p",
                    "ALUGUEL_COND": "/html/body/main/article/section[2]/div/table/tbody/tr[4]/td[2]/p",
                    "ENDERECO":     "/html/body/main/article/section[2]/div/address/span/h2/b",
                    "TITULO":       "/html/body/main/article/section[2]/div/span/h1",
                    "INFO_1":       "/html/body/main/article/section[2]/div/ul/li[1]/p",
                    "INFO_2":       "/html/body/main/article/section[2]/div/ul/li[2]/p",
                    "INFO_3":       "/html/body/main/article/section[2]/div/ul/li[3]/p",
                    "INFO_4":       "/html/body/main/article/section[2]/div/ul/li[4]/p",
                    "INFO_5":       "/html/body/main/article/section[2]/div/ul/li[5]/p",
                    "INFO_6":       "/html/body/main/article/section[2]/div/ul/li[6]/p",
                    "ATUALIZACAO":  "/html/body/main/article/section[2]/div/div[1]/div/p[1]",
                    "DESCRICAO":    "/html/body/main/article/section[2]/div/div[1]/div/p[2]",
                    "ANUNCIANTE":   "/html/body/main/article/section[2]/aside/div[2]/span/span[2]/a/span/h2/b",
                    "ESPACO_PRIV":  "/html/body/main/article/section[2]/div/div[2]/span[1]/ul",
                    "AREA_COMUM":   "/html/body/main/article/section[2]/div/div[2]/span[2]/ul"
                }
            case "quintoandar":
                XPATHS_CLICAR = [
                    "/html/body/div[1]/div/div/div[2]/div/div/div/div[4]/main/section/div/div[1]/div/div[3]/div/div[3]/div[1]/div[2]/svg"
                    ]
                XPATHS_INFO = {
                    "TITULO":            "/html/body/div[1]/div/div/div[2]/div/div/div/div[2]/div/h1",
                    "TEMPO_PUBLICADO":   "/html/body/div[1]/div/div/div[2]/div/div/div/div[4]/main/section/div/div[1]/div/section/div/div[2]/div/div/small/span",
                    "DESCRICAO":         "/html/body/div[1]/div/div/div[2]/div/div/div/div[4]/main/section/div/div[1]/div/section/div/div[3]/div/div/div/p[2]",
                    "ALUGUEL":           "/html/body/div[1]/div/div/div[2]/div/div/div/div[4]/main/section/div/div[2]/section/div/ul/li[1]/div/div/p",
                    "CONDOMINIO":        "/html/body/div[1]/div/div/div[2]/div/div/div/div[4]/main/section/div/div[2]/section/div/ul/li[2]/div/div/p",
                    "IPTU":              "/html/body/div[1]/div/div/div[2]/div/div/div/div[4]/main/section/div/div[2]/section/div/ul/li[3]/div/div/p",
                    "SEGURO_INCENDIO":   "/html/body/div[1]/div/div/div[2]/div/div/div/div[4]/main/section/div/div[2]/section/div/ul/li[4]/div/div/p",
                    "TOTAL":             "/html/body/div[1]/div/div/div[2]/div/div/div/div[4]/main/section/div/div[2]/section/div/ul/li[7]/div/div/h4",
                    "ENDERECO":          "/html/body/div[1]/div/div/div[2]/div/div/div/div[4]/main/section/div/div[1]/div/div[2]/div/div/div/div[1]",
                    "AREA":              "/html/body/div[1]/div/div/div[2]/div/div/div/div[4]/main/section/div/div[1]/div/section/div/div[1]/div/div/div[1]/div/div/p",
                    "QUARTOS":           "/html/body/div[1]/div/div/div[2]/div/div/div/div[4]/main/section/div/div[1]/div/section/div/div[1]/div/div/div[2]/div/div/p",
                    "BANHEIROS":         "/html/body/div[1]/div/div/div[2]/div/div/div/div[4]/main/section/div/div[1]/div/section/div/div[1]/div/div/div[3]/div/div/p",
                    "GARAGENS":          "/html/body/div[1]/div/div/div[2]/div/div/div/div[4]/main/section/div/div[1]/div/section/div/div[1]/div/div/div[4]/div/div/p",
                    "ANDAR":             "/html/body/div[1]/div/div/div[2]/div/div/div/div[4]/main/section/div/div[1]/div/section/div/div[1]/div/div/div[5]/div/div/p",
                    "ACEITA_PET":        "/html/body/div[1]/div/div/div[2]/div/div/div/div[4]/main/section/div/div[1]/div/section/div/div[1]/div/div/div[6]/div/div/p",
                    "MOBILIADO":         "/html/body/div[1]/div/div/div[2]/div/div/div/div[4]/main/section/div/div[1]/div/section/div/div[1]/div/div/div[7]/div/div/p",
                    "ESTACAO_PROX":      "/html/body/div[1]/div/div/div[2]/div/div/div/div[4]/main/section/div/div[1]/div/section/div/div[1]/div/div/div[8]/div/div/p",
                    "ITENS_DISP":        "/html/body/div[1]/div/div/div[2]/div/div/div/div[4]/main/section/div/div[1]/div/section/div/div[4]/div/div/div/div[1]",
                    "ITENS_INDISP":      "/html/body/div[1]/div/div/div[2]/div/div/div/div[4]/main/section/div/div[1]/div/section/div/div[4]/div/div/div/div[2]",
                    "NOME_CONDOMINIO":   "/html/body/div[1]/div/div/div[2]/div/div/div/div[4]/main/section/div/div[1]/div/div[3]/div/div[3]/div[2]/div/div/div/div/div[1]/h2/span",
                    # itens de condominio, por ora, ainda nao funcionam
                    "COND_ITENS_DISP":   "/html/body/div[1]/div/div/div[2]/div/div/div/div[4]/main/section/div/div[1]/div/div[3]/div/div[3]/div[2]/div/div/div/div/div[3]/div[1]/div[1]/p[2]",
                    "COND_ITENS_INDISP": "/html/body/div[1]/div/div/div[2]/div/div/div/div[4]/main/section/div/div[1]/div/div[3]/div/div[3]/div[2]/div/div/div/div/div[3]/div[1]/p[2]",
                    "COMPRA":            "/html/body/div[1]/div/div/div[2]/div/div/div/div[4]/main/section/div/div[1]/div/div[4]/div/section/div/p[2]",
                }
            case "lopes":
                XPATHS_CLICAR = [
                    "/html/body/app-root/lps-product/main/div[1]/div[1]/div[3]/lps-expansive-text/div/lps-ui-button/button"
                    ]
                XPATHS_INFO = {
                    "TITULO":     "/html/body/app-root/lps-product/main/div[1]/div[1]/div[1]/div/h1",
                    "TOTAL":      "/html/body/app-root/lps-product/main/div[1]/div[1]/div[2]/lps-product-price/main/div[1]/p[2]",
                    "ALUGUEL":    "/html/body/app-root/lps-product/main/div[1]/div[1]/div[2]/lps-product-price/main/div[1]/div/lps-product-price-complementary/p",
                    "AREA_TOTAL": "/html/body/app-root/lps-product/main/div[1]/div[1]/lps-attributes/ul/li[1]/div/p[2]",
                    "AREA_CONST": "/html/body/app-root/lps-product/main/div[1]/div[1]/lps-attributes/ul/li[2]/div/p[2]",
                    "QUARTOS":    "/html/body/app-root/lps-product/main/div[1]/div[1]/lps-attributes/ul/li[3]/div/p[2]",
                    "BANHEIROS":  "/html/body/app-root/lps-product/main/div[1]/div[1]/lps-attributes/ul/li[4]/div/p[2]",
                    "ANDAR":      "/html/body/app-root/lps-product/main/div[1]/div[1]/lps-attributes/ul/li[5]/div/p[2]",
                    "DESCRICAO":  "/html/body/app-root/lps-product/main/div[1]/div[1]/div[3]/lps-expansive-text/div/div",
                    "INST_COND":  "/html/body/app-root/lps-product/main/div[1]/div[1]/lps-feature-grid/main",
                    "COD_IMOVEL": "/html/body/app-root/lps-product/main/div[1]/div[2]/lps-product-lead/main/div[2]/div"
                }
            case _:
                raise ImobiliariaNaoCadastrada(f"O programa ainda não tem a imobiliaria {imobiliaria} mapeada para extração de dados da página do imovel")

        # Iniciar Selenium e acessar a url do imovel
        if not self.driver:
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.driver.get(url_do_imovel)

        # Se houver XPATH necessários para clicar para a visualização de dados
        if XPATHS_CLICAR:
            for xpath in XPATHS_CLICAR:
                # Clica em cada um dos xpath
                self.se_houver_elemento_clicar_nele(xpath)

        # Para cada XPATH_INFO será extraído suas informações (se houver o elemento)
        for nome, xpath in XPATHS_INFO.items():
            try:
                elemento = self.driver.find_element(By.XPATH, xpath)
                valor = elemento.text.strip()
                dict_dados_obtidos[nome] = valor
            except:
                dict_dados_obtidos[nome] = "N/A"
                print(f'Aviso: Elemento XPATH não localizado no URL fornecido: {nome}')

        # Salva os dados obtidos em atributo do objeto
        if not imobiliaria in self.dados_extraidos:
            self.dados_extraidos[imobiliaria]=[]
        self.dados_extraidos[imobiliaria].append(dict_dados_obtidos)

        # retorna os dados obtidos
        return dict_dados_obtidos
    

    def salvar_dados_extraidos(self, dir:str="./dados_extraidos/1_bronze/", clear_cache=True):
        os.makedirs(dir, exist_ok=True)
        self.now = datetime.now()

        for data, lista_urls in self.urls_extraidas.items():
            path = os.path.join(dir, f'{data}.txt')
            adicionar_cabecalho = not os.path.exists(path)
            with open(path, "a", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                if adicionar_cabecalho:
                    writer.writerow(["DATA", "URL"])
                for url in lista_urls:
                    writer.writerow([data, url])

        for imobiliaria, dados_imoveis in self.dados_extraidos.items():
            path = os.path.join(dir, f"{imobiliaria}.csv")
            adicionar_cabecalho = not os.path.exists(path)
            with open(path, "a", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=dados_imoveis[0].keys(), quoting=csv.QUOTE_ALL)
                if adicionar_cabecalho:
                    writer.writeheader()
                writer.writerows(dados_imoveis)

        if clear_cache:
            self.urls_extraidas = {}
            self.dados_extraidos = {}
        return


    def exit(self):
        self.driver.quit()  # Fechar o navegador
        self.driver = False



class ImobiliariaNaoCadastrada(Exception):
    """Exceção personalizada para valores de imobiliarias ainda não mapeadas"""
    pass


class AcessoNegado(Exception):
    """Exceção personalizada para acessos negados"""
    pass


class NotFoundError(Exception):
    """Exceção personalizada para recursos não encontrados"""
    pass



def testa_e_retorna_responseText(url:str):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)

    # Verifica se o status code indica que o acesso foi negado
    if response.status_code in [401, 403]:
        raise AcessoNegado(f"Acesso negado! Código {response.status_code} - {response.reason}")
    return response.text


def retorna_lista_de_urls_separando_html(html:str, dominio:str, padrao_inicio:str, padrao_final:str='"') -> list:
    lista_de_links = []
    if not padrao_inicio in html:
        raise NotFoundError(f'O argumento "padrao_inicio":"{padrao_inicio}" não foi encontrado no corpo HTML.') 
    html_separado_em_lista = html.split(padrao_inicio)
    html_separado_em_lista.pop(0)
    for item in html_separado_em_lista:
        texto = re.search(f'(.*?){padrao_final}',item)
        url_final = texto.group(1)
        url_final = unescape(url_final)
        url_final = unquote(url_final)
        url_final = 'https://' + dominio + url_final
        lista_de_links.append(url_final)
    return lista_de_links


def identifica_anunciante_do_url(url:str) -> tuple[str, str]:
    """
    Entra com URL e retorna o DOMINIO e a IMOBILIARIA
    """
    # "https://www.exemplo.com.br/contatos/index.html" -> "www.exemplo.com.br" 
    netloc = urlparse(url).netloc
    
    # "www.exemplo.com.br" -> ['www', 'exemplo', 'com', 'br']
    partes = netloc.split('.')
    
    if partes[0] == "www":
        # ['www', 'exemplo', 'com', 'br'] -> ['exemplo', 'com', 'br']
        partes.pop(0)

    # ['exemplo', 'com', 'br'] -> 'exemplo'
    imobiliaria = partes[0]
    
    # 'www.exemplo.com.br' , 'exemplo'
    return netloc, imobiliaria