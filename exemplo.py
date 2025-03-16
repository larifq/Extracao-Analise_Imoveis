from datascrap_imoveis import Extrator_de_Dados


URL = "https://www.chavesnamao.com.br/apartamentos-para-alugar/sp-sao-paulo/brooklin/1-quarto/?filtro=bai:[53754],pmax:3000,cnd:true"

programa_do_erick = Extrator_de_Dados()
lista = programa_do_erick.extrair_urls_desta_pesquisa(URL)
print(lista)
dic1 = programa_do_erick.extrair_dados_imobiliarios_desta_url(lista[1])
print(dic1)
