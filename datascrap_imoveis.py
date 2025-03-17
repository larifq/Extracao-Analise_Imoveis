import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import re
from html import unescape
from urllib.parse import unquote, urlparse

class Extrator_de_Dados():

    def __init__(self):
        self.driver = False


    def identifica_anunciante_do_url(self, url:str) -> str:
        netloc = urlparse(url).netloc  # "https://www.exemplo.com.br/contatos/index.html" -> "www.exemplo.com.br" 
        partes = netloc.split('.')  # "www.exemplo.com.br" -> ['www', 'exemplo', 'com', 'br']
        
        if partes[0] == "www":
            partes.pop(0) # ['exemplo', 'com', 'br']

        imobiliaria = partes[0] # 'exemplo'
        
        return netloc, imobiliaria # 'www.exemplo.com.br' , 'exemplo'


    def extrair_urls_desta_pesquisa(self, url_da_pesquisa:str) -> list:
        """
        Entra com um link da pesquisa, exemplo, URL da pesquisa realizado em São Paulo com 2 dorm com preço máximo de R$ 2.000
        Retorna uma lista de URL dos imóveis encontrados.
        Retorna vazio caso nao encontrar
        """
        if not isinstance(url_da_pesquisa, str):
            raise TypeError(f"Esperado uma URL de argumento string, mas foi recebido {type(url_da_pesquisa).__name__}: {url_da_pesquisa}")

        html_da_pagina = testa_e_retorna_responseText(url_da_pesquisa)
        dominio, imobiliaria = self.identifica_anunciante_do_url(url_da_pesquisa)
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
                PADRAO_FIM = '"'
                return retorna_lista_de_urls_separando_html(html_da_pagina, dominio, PADRAO_INICIO, PADRAO_FIM)

            case "olx":
                PADRAO_INICIO = 'data-testid="house-card-container-rent"><a href="'
                PADRAO_FIM = '"'
                return retorna_lista_de_urls_separando_html(html_da_pagina, dominio, PADRAO_INICIO, PADRAO_FIM)

            case "lopes":
                PADRAO_INICIO = 'class="lead-button" href="'
                PADRAO_FIM = '"'
                return retorna_lista_de_urls_separando_html(html_da_pagina, dominio, PADRAO_INICIO, PADRAO_FIM)

            case _:
                raise ImobiliariaNaoCadastrada(imobiliaria)

        return lista_de_links


    def extrair_dados_imobiliarios_desta_url(self, url_do_imovel:str) -> dict:
        if not isinstance(url_do_imovel, str):
            raise TypeError(f"Esperado uma URL de argumento string, mas foi recebido {type(url_do_imovel).__name__}: {url_do_imovel}")
        testa_e_retorna_responseText(url_do_imovel)
        if not self.driver:
            chrome_options = Options()
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.driver.get(url_do_imovel)
        imobiliaria = self.identifica_anunciante_do_url(url_do_imovel)
        dict_dados_obtidos = {'url':url_do_imovel,
                    'imobiliaria':imobiliaria}

        match imobiliaria:
            case "chavesnamao":
                XP_BOTAO_EXPANDIR_DESCRICAO = "/html/body/main/article/section[2]/div/div[1]/div/span/svg"
                try:
                    elemento = self.driver.find_element(By.XPATH, XP_BOTAO_EXPANDIR_DESCRICAO)  # Tenta localizar o elemento
                    elemento.click()  # Se encontrado, clica nele
                except NoSuchElementException:
                    pass
                XP_PATHS = {
                "ALUGUEL": "/html/body/main/article/section[2]/div/table/tbody/tr[1]/td[1]/p[2]/b",
                "CONDOMINIO": "/html/body/main/article/section[2]/div/table/tbody/tr[2]/td[2]/p",
                "IPTU": "/html/body/main/article/section[2]/div/table/tbody/tr[3]/td[2]/p",
                "ALUGUEL_CONDOMINIO": "/html/body/main/article/section[2]/div/table/tbody/tr[4]/td[2]/p",
                "ENDERECO": "/html/body/main/article/section[2]/div/address/span/h2/b",
                "TITULO": "/html/body/main/article/section[2]/div/span/h1",
                "AREA": "/html/body/main/article/section[2]/div/ul/li[1]/p/b",
                #"AREA_UTIL_TOTAL": "/html/body/main/article/section[2]/div/ul/li[1]/p/b", # idem ao de cima
                "QUARTOS": "/html/body/main/article/section[2]/div/ul/li[2]/p/b",
                "SUITES": "/html/body/main/article/section[2]/div/ul/li[3]/p/b",
                "GARAGENS": "/html/body/main/article/section[2]/div/ul/li[3]/p/b",
                "BANHEIROS": "/html/body/main/article/section[2]/div/ul/li[4]/p/b",
                "ATUALIZACAO_REF": "/html/body/main/article/section[2]/div/div[1]/div/p[1]",
                "DESCRICAO": "/html/body/main/article/section[2]/div/div[1]/div/p[2]",
                "ANUNCIANTE": "/html/body/main/article/section[2]/aside/div[2]/span/span[2]/a/span/h2/b",
                "ESPACO_PRIVATIVO": "/html/body/main/article/section[2]/div/div[2]/span[1]/ul",
                "AREA_COMUM": "/html/body/main/article/section[2]/div/div[2]/span[2]/ul"
                }
            case _:
                raise ImobiliariaNaoCadastrada(imobiliaria)

        for nome, xpath in XP_PATHS.items():
            try:
                elemento = self.driver.find_element(By.XPATH, xpath)
                valor = elemento.text.strip()
                dict_dados_obtidos[nome] = valor
            except:
                pass

        return dict_dados_obtidos
    
    
    def exit(self):
        self.driver.quit()  # Fechar o navegador



class ImobiliariaNaoCadastrada(Exception):
    def __init__(self, imobiliaria):
        super().__init__(f"Valor inválido: este webscrapt não tem a imobiliaria {imobiliaria} mapeada")


class AcessoNegado(Exception):
    """Exceção personalizada para acessos negados"""
    pass

class NotFoundError(Exception):
    """Exceção personalizada para recursos não encontrados"""
    pass



def testa_e_retorna_responseText(url:str):
    cookies = {
    '_cfuvid':'OlNSZkGPxlEi4SkM0_LukFYzU_kTtCoKmE5xOEbMiho-1742075092583-0.0.1.1-604800000',
    '_dd_s':'rum=0&expire=1742091953471',
    '_ga':'GA1.1.441540977.1737060429',
    '_ga_50C013M2CC':'GS1.1.1742088382.4.1.1742090428.59.0.0',
    '_gcl_au':'1.1.150913433.1737060429',
    '_lr_geo_location':'BR',
    '_lr_geo_location_state':'SP',
    '_tt_enable_cookie':'1',
    '_ttp':'XrEF5ZtFl9rimLBNKoXrD4aO-wv.tt.2',
    'cf_clearance':'FD6pRYizmEf8PdR7_8ikxYD2qPcwvhZtzMt7dotq99k-1742076102-1.2.1.1-dYyE3v3hs3UdSDGGvx11CgersAf1b.sciXAkh2bKtQcciKfMUhyLqWQ07ua8lt1yU45faBaRhiFEQgp5CVKv.W._GVpOl6FZCUn0XPh4XqAjMB0z2UAu5c1HMLUyoPYseE5nYzydTFkr7hxytx3sBxo0PYJMW2VTqfdBgTX1qdt8Ok_CyKPYb6NW2UNRhv6R4k7VWml43BZzwfDt6j.1grw634FSJdHKY4KteUHo4cnkvLwz6nbTkapIjj6NAu8Pk5vfKPT3kom4YFOveTwXdyY2TH9395YyFs4wOiW18eiWNOTYOUTlC5lMXmNyfhuEI86DBAL9NxYucNs_re1EZ6QcnnIezYrveB_NxL0VYIM',
    'cto_bundle':'gWjnjF9RWE8ybFRRVXZqT1A5R3phOFhESDZYejVuc0VZTHIzYkJjSDVtQ2xnJTJGaEhnbEdQRkxOVXFjZmF5cVVZMWI0M092Mk9aMkZaTVJLWWw2V2ljZTRtZFFGdVJnSGw3RXJ6c2FxQ2xQWE92NjY0ODFqNUlOdjVXWCUyQk8lMkJCV0k3c01hV21rQ2g5V2MlMkY2VkY3QkV0cm1iRmpQdThncWplMDBGQzE3VUtkQVBhbUt2TDFwMjh5UUt4SjZCM3Y2SVJCcjk0MzBpdmdYc09jUmJsZmY5OHo2akQ0eUElM0QlM0Q',
    'l_id':'9efbf14b-f4cb-45e6-ba45-b664ca8d24fa',
    'mf_b837e449-83ee-457f-9ef5-8f976953f2bc':'||1742069960648||0||||0|0|49.56941',
    'nl_id':'82969c7f-19fa-4e9b-86b1-9a6224fd1f12',
    'nvg83482':'158cfb18ef2f85bf6d60ff264110|2_75',
    'panoramaId':'0d5e2d548971620d36457c2f58c916d539389643ea37dad819adbc89fce7e1f4',
    'panoramaIdType':'panoIndiv',
    'panoramaId_expiry':'1,74267E+12',
    'r_id':'d208f169-18e2-4fcd-86f3-f3871c55afe9',
    's_id':'25d18b13-ef60-4e0a-8b9a-3c741f8d65422025-03-16T01:26:23.393728Z',
    'sf_utm_medium':'organic',
    'sf_utm_source':'google'
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.olx.com.br'
    }
    response = requests.get(url, headers=headers, cookies=cookies)

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
        url_final = 'http://' + dominio + url_final
        lista_de_links.append(url_final)
    return lista_de_links

