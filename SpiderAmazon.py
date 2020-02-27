import csv
import smtplib
import pyodbc
import requests
from bs4 import BeautifulSoup


class SipderAmazon:

    def __init__(self):

        # o arquivo deve estar na pasta onde este programa será executado
        self.nomeArquivo = 'lista_de_desejos.txt'

        # a lib requests envia um user agent válido para o servidor web
        # você pode obter um acessando o site abaixo e consultado o seu:
        #  https://www.whatismybrowser.com/detect/what-is-my-user-agent
        self.browserHeader ={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'}

        # objeto do pyodbc que sera usado para conectar com o banco de dados
        self.conexao = None


    def capturar(self):
        # decidi guardar na base o descricao do item, a url pesquisada, a data e hora da consulta e
        # o preco do site no momento da consulta
        sqlInsert = "INSERT INTO tb_produtos (descricao, url, data, hora, preco) VALUES " \
                    " (?, ?, date(now()), time(now()), ?)"

        # vamos abrir o arquivo para leitura, lembrando que ele precisa estar no padrao definido no artigo
        print("[i] Abrindo arquivo...")
        print("-" * 80)
        with open(self.nomeArquivo, mode='r', encoding='utf-8') as dados:
            arquivo = csv.reader(dados, delimiter=';')
            next(arquivo) # pulando a primeira linha do arquivo
            linhas = list(tuple(linha) for linha in arquivo)

        # abrir conexão com o banco de dados e gerar o cursor que sera usado para executar o SQL de insercao de dados
        print('[i] Conectando com o banco de dados...')
        print("-" * 80)
        self.conexao = self.conectarBancoSQL()
        cursor = self.conexao.cursor()

        # para cada linha do arquivo, vamos pesquisar a URL correspondente
        for linha in linhas:
            url = linha[0] # o primeiro campo do arquivo e a URL
            pagina = requests.get(url, headers=self.browserHeader) # vamos enviar a requisicao da pagina para o servidor web
            soup = BeautifulSoup(pagina.content, 'html.parser')  # vamos usar o html.parser para devolver ao BS a estrutura da página
            produto = soup.find(id="productTitle").get_text() # vamos procurar no codigo fonte da pagina o id com o nome do produto
            produto = produto.strip() # limpando os espacos no nome do produto, equivale ao "trim"
            preco = soup.find(id="priceblock_ourprice").get_text() # vamos procurar agora o preco
            preco = preco.strip().replace('R$', '').replace('.', '').replace(',', '.') # para inserir no banco o preco precisa estar no padrao americano
            show = produto + '| Preço atual: ' + preco # essa variavel e criada apenas para dar um feedback visual ao usuario da execucao do codigo
            print("[i] Consultando {} ".format(show))
            print("-" * 80)
            preco_atual = float(preco) # convertendo o preco para float para poder gravar no banco de dados
            alvo = float(linha[1]) # consulta no arquivo o preco alvo e converte para float para poder comparar

            param = produto, url, preco_atual # montando a lista de parametros para o nosso prepare do nosso SQL
            cursor.execute(sqlInsert, param) # inserindo na base de dados
            if preco_atual <= alvo:
                self.enviarEmail('thiagonce@gmail.com', produto, url)


    def conectarBancoSQL(self):
        servidor = 'localhost'
        banco = 'base_pessoal'
        passwd = 'senha do banco de dados'
        userbd = 'usuario do banco de dados'
        conexao = None
        try:
            self.conexao = pyodbc.connect(
                "driver=MySQL ODBC 8.0 Driver Unicode;SERVER=" + self.servidor + ';DATABASE=' + self.banco + ';UID=' + self.userbd + ';PWD=' + self.passwd,
                autocommit=True)
            print("[i] Conectado com o banco de dados.")
            print("-" * 80)
        except (pyodbc.Error, pyodbc.OperationalError) as ex:
            print(ex.args[0], ex.args[1])
            self.conexao = None

    def enviarEmail(self, para, assunto, url):
        server = smtplib.SMTP('smtp.gmail.com', 587)
        para = para.strip()
        assunto = assunto.strip()
        url = url.strip()

        # apenas para encurtar o titulo do e-mail -- normalmente os nomes dos itens sao muito grandes!!!
        if len(assunto) > 25:
            topo = assunto[0:25] + '...'
        else:
            topo = assunto

        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login('seu_email_do_gmail@gmail.com', 'a senha que voce criou para este app')
        assunto = '[Spider_Amazon] O preço caiu! item: ' + self.topo
        corpo = 'Acesse agora para ver ' + self.assunto + '\nlink: ' + self.url
        msg = f"Subject: {assunto}\n\n{corpo}"
        server.sendmail(
            'seu_email_do_gmail@gmail.com',
            self.para,
            msg.encode('utf8')
        )
        print('[i] E-mail enviado!')
        print("-" * 80)
        server.quit()

# ---------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------
amz = SipderAmazon()
amz.capturar()
