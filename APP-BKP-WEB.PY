from flask import Flask, request, jsonify, render_template
import psycopg2

app = Flask(__name__)

# Configuração da conexão com o PostgreSQL
def criar_conexao():
    return psycopg2.connect(
        host="localhost",
        user="postgres",
        password="admin",
        database="AMERICA"
    )

# Página inicial com o menu principal
@app.route('/')
def index():
    return '''
    <h1>Bem-vindo à Cia América Corretora de Seguros!</h1>
    <ul>
        <li><a href="/clientes/cadastrar">1. Cadastrar Cliente</a></li>
        <li><a href="/apolices/cadastrar">2. Cadastrar Apólice</a></li>
        <li><a href="/apolices/consulta/cliente">3. Consultar Apólices por Cliente (CPF/CNPJ)</a></li>
        <li><a href="/apolices/consulta/vencimento">4. Relatório de Renovações (MM/AAAA)</a></li>
        <li><a href="/sair">5. Sair</a></li>
    </ul>
    '''

# Rota para sair
@app.route('/sair')
def sair():
    return '''
    <h1>Obrigado por utilizar o sistema!</h1>
    <a href="/">Voltar ao Menu</a>
    '''

# Verificar se cliente já existe
def verificar_cliente_existente(cpf_cnpj):
    conexao = criar_conexao()
    cursor = conexao.cursor()
    sql = "SELECT * FROM Clientes WHERE CPF_CNPJ = %s"
    cursor.execute(sql, (cpf_cnpj,))
    cliente = cursor.fetchone()
    conexao.close()
    return cliente

# Verificar se apólice já existe
def verificar_apolice_existente(nr_apolice):
    conexao = criar_conexao()
    cursor = conexao.cursor()
    sql = "SELECT * FROM Apolices WHERE NR_Apolice = %s"
    cursor.execute(sql, (nr_apolice,))
    apolice = cursor.fetchone()
    conexao.close()
    return apolice

# Rota para cadastrar clientes
@app.route('/clientes/cadastrar', methods=['GET', 'POST'])
def cadastrar_cliente():
    if request.method == 'POST':
        dados = request.form
        nome = dados['nome']
        cpf_cnpj = dados['cpf_cnpj']
        telefone = dados['telefone']
        email = dados['email']

        # Verifica se o cliente já existe
        cliente_existente = verificar_cliente_existente(cpf_cnpj)
        if cliente_existente:
            return f'''
            <h2>O cliente {cliente_existente[1]} já está cadastrado com CPF/CNPJ {cpf_cnpj}.</h2>
            <a href="/apolices/cadastrar">Cadastrar Apólice para {cliente_existente[1]}</a><br>
            <a href="/">Voltar ao Menu</a>
            '''
        
        # Cadastra novo cliente se não existir
        conexao = criar_conexao()
        cursor = conexao.cursor()
        sql = "INSERT INTO Clientes (Nome, CPF_CNPJ, Telefone, Email) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (nome, cpf_cnpj, telefone, email))
        conexao.commit()
        conexao.close()

        return '''
        <h2>Cliente cadastrado com sucesso!</h2>
        <a href="/">Voltar ao Menu</a>
        '''

    return '''
    <h2>Cadastro de Cliente</h2>
    <form method="POST">
        Nome: <input type="text" name="nome"><br>
        CPF/CNPJ: <input type="text" name="cpf_cnpj"><br>
        Telefone: <input type="text" name="telefone"><br>
        Email: <input type="text" name="email"><br>
        <input type="submit" value="Cadastrar Cliente">
    </form>
    <a href="/">Voltar ao Menu</a>
    '''

# Rota para cadastrar apólices
@app.route('/apolices/cadastrar', methods=['GET', 'POST'])
def cadastrar_apolice():
    if request.method == 'POST':
        dados = request.form
        nr_apolice = dados['nr_apolice']
        tipo_seguro = dados['tipo_seguro']
        dt_vencimento = dados['dt_vencimento']
        seguradora = dados['seguradora']
        cliente_cpf = dados['cliente_cpf']

        # Verifica se a apólice já existe
        apolice_existente = verificar_apolice_existente(nr_apolice)
        if apolice_existente:
            return f'''
            <h2>A apólice {nr_apolice} já está cadastrada no sistema.</h2>
            <a href="/apolices/cadastrar">Cadastrar Nova Apólice</a><br>
            <a href="/">Voltar ao Menu</a>
            '''

        # Cadastra nova apólice se não existir
        conexao = criar_conexao()
        cursor = conexao.cursor()
        sql = "INSERT INTO Apolices (NR_Apolice, Tipo_Seguro, Dt_Vencimento, Seguradora, Cliente_cpf) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql, (nr_apolice, tipo_seguro, dt_vencimento, seguradora, cliente_cpf))
        conexao.commit()
        conexao.close()

        return '''
        <h2>Apólice cadastrada com sucesso!</h2>
        <a href="/">Voltar ao Menu</a>
        '''

    return '''
    <h2>Cadastro de Apólice</h2>
    <form method="POST">
        Número da Apólice: <input type="text" name="nr_apolice"><br>
        Tipo de Seguro: <input type="text" name="tipo_seguro"><br>
        Data de Vencimento: <input type="date" name="dt_vencimento"><br>
        Seguradora: <input type="text" name="seguradora"><br>
        CPF do Cliente: <input type="text" name="cliente_cpf"><br>
        <input type="submit" value="Cadastrar Apólice">
    </form>
    <a href="/">Voltar ao Menu</a>
    '''

# Rota para consultar apólices de um cliente por CPF/CNPJ
@app.route('/apolices/consulta/cliente', methods=['GET', 'POST'])
def consultar_apolices_por_cliente():
    if request.method == 'POST':
        cpf_cnpj = request.form['cpf_cnpj']

        conexao = criar_conexao()
        cursor = conexao.cursor()

        # Verificar se o cliente existe no banco de dados
        sql_cliente = "SELECT ID, Nome FROM Clientes WHERE CPF_CNPJ = %s"
        cursor.execute(sql_cliente, (cpf_cnpj,))
        cliente = cursor.fetchone()

        if not cliente:
            conexao.close()
            return f'''
            <h2>O cliente com CPF/CNPJ {cpf_cnpj} não está cadastrado no sistema.</h2>
            <a href="/clientes/cadastrar">Cadastrar Novo Cliente</a><br>
            <a href="/">Voltar ao Menu</a>
            '''

        # Consultar as apólices associadas ao cliente
        sql_apolices = """
        SELECT Apolices.NR_Apolice, Apolices.Tipo_Seguro, Apolices.Dt_Vencimento, Apolices.Seguradora
        FROM Apolices
        JOIN Clientes ON Apolices.Cliente_ID = Clientes.ID
        WHERE Clientes.CPF_CNPJ = %s
        """
        cursor.execute(sql_apolices, (cpf_cnpj,))
        apolices = cursor.fetchall()
        conexao.close()

        if apolices:
            resultado = f'<h2>Apólices do Cliente {cliente[1]}</h2><ul>'
            for apolice in apolices:
                resultado += f"<li>Número da Apólice: {apolice[0]}, Tipo de Seguro: {apolice[1]}, Data de Vencimento: {apolice[2]}, Seguradora: {apolice[3]}</li>"
            resultado += '</ul>'
            return resultado + '<a href="/">Voltar ao Menu</a>'
        else:
            return f'''
            <h2>Nenhuma apólice encontrada para o cliente {cliente[1]}.</h2>
            <a href="/apolices/cadastrar">Cadastrar Nova Apólice</a><br>
            <a href="/">Voltar ao Menu</a>
            '''

    return '''
    <h2>Consulta de Apólices por Cliente (CPF/CNPJ)</h2>
    <form method="POST">
        CPF/CNPJ do Cliente: <input type="text" name="cpf_cnpj"><br>
        <input type="submit" value="Consultar Apólices">
    </form>
    <a href="/">Voltar ao Menu</a>
    '''



# Rota para consultar apólices com vencimento em um mês específico
@app.route('/apolices/consulta/vencimento', methods=['GET', 'POST'])
def consultar_apolices_vencimento_mes():
    if request.method == 'POST':
        mes = request.form['mes']
        ano = request.form['ano']

        conexao = criar_conexao()
        cursor = conexao.cursor()
        sql = """
        SELECT Clientes.Nome, Apolices.NR_Apolice, Apolices.Tipo_Seguro, Apolices.Dt_Vencimento, Apolices.Seguradora
        FROM Apolices
        JOIN Clientes ON Apolices.Cliente_ID = Clientes.ID
        WHERE EXTRACT(MONTH FROM Apolices.Dt_Vencimento) = %s
        AND EXTRACT(YEAR FROM Apolices.Dt_Vencimento) = %s
        """
        cursor.execute(sql, (mes, ano))
        apolices = cursor.fetchall()
        conexao.close()

        if apolices:
            resultado = '<h2>Apólices com Vencimento no Mês</h2><ul>'
            for apolice in apolices:
                resultado += f"<li>Cliente: {apolice[0]}, Número da Apólice: {apolice[1]}, Tipo de Seguro: {apolice[2]}, Data de Vencimento: {apolice[3]}, Seguradora: {apolice[4]}</li>"
            resultado += '</ul>'
            return resultado + '<a href="/">Voltar ao Menu</a>'
        else:
            return '''
            <h2>Nenhuma apólice encontrada com vencimento nesse mês/ano.</h2>
            <a href="/">Voltar ao Menu</a>
            '''

    return '''
    <h2>Consulta de Apólices com Vencimento em um Mês</h2>
    <form method="POST">
        Mês: <input type="text" name="mes"><br>
        Ano: <input type="text" name="ano"><br>
        <input type="submit" value="Consultar Apólices">
    </form>
    <a href="/">Voltar ao Menu</a>
    '''

if __name__ == "__main__":
    app.run(debug=True)
