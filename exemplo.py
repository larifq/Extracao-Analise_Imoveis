from datascrap_imoveis import Extrator_de_Dados

# URL de pesquisa de uma site de imobiliaria
# Exemplo, no site chavesnamao, filtro de alugar apartamentos em brooklin SP com valor maximo de ate R$ 3.000
# Copiar a URL após confirmar pesquisar.
URL = "https://www.chavesnamao.com.br/apartamentos-para-alugar/sp-sao-paulo/brooklin/1-quarto/?filtro=bai:[53754],pmax:3000,cnd:true"

programa_do_erick = Extrator_de_Dados()

# Ao inserir a URL DA PESQUISA, o comando abaixo retornará todas as URL de imóveis encontrado com a pesquisa realizada.
lista_de_urls = programa_do_erick.extrair_urls_desta_pesquisa(URL)
print(lista_de_urls)

url_de_imovel = lista_de_urls[0]

# Ao inserir a URL DE UM IMOVEL, a função abrirá o selenium e extrairá as informações e dados do imóvel
dic_info_imovel = programa_do_erick.extrair_dados_imobiliarios_desta_url(url_de_imovel, acessar_pagina_repetida=False, avisar_caso_xpath_nao_existir=True)
print(dic_info_imovel)

# O comando abaixo gravará em formato TXT e CSV as informações extraídas
programa_do_erick.salvar_dados_extraidos()
