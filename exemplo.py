from datascrap_imoveis import Extrator_de_Dados


URL = "https://www.chavesnamao.com.br/apartamentos-para-alugar/sp-sao-paulo/brooklin/1-quarto/?filtro=bai:[53754],pmax:3000,cnd:true"

programa_do_erick = Extrator_de_Dados()
lista_de_urls = programa_do_erick.extrair_urls_desta_pesquisa(URL)
print(lista_de_urls)

um_url_de_imovel = lista_de_urls[2]
dic_info_imovel = programa_do_erick.extrair_dados_imobiliarios_desta_url(um_url_de_imovel)
print(dic_info_imovel)

programa_do_erick.salvar_dados_extraidos()
