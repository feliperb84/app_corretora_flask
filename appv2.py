from flask import Flask, request, jsonify, render_template
import psycopg2
import re

app = Flask(__name__)

# Função para validar CPF/CNPJ
def validar_cpf_cnpj(cpf_cnpj):
    cpf_cnpj = re.sub(r'\D', '', cpf_cnpj)  # Remove caracteres não numéricos
    if len(cpf_cnpj) == 11:  # Validação simples de CPF
        return validar_cpf(cpf_cnpj)
    elif len(cpf_cnpj) == 14:  # Validação simples de CNPJ
        return validar_cnpj(cpf_cnpj)
    return False

# Validação simples de CPF
def validar_cpf(cpf):
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    digito1 = resto if resto < 10 else 0
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    digito2 = resto if resto < 10 else 0
    return cpf[-2:] == f'{digito1}{digito2}'

# Validação simples de CNPJ
def validar_cnpj(cnpj):
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False
    return True  # Aqui, a validação do CNPJ seria mais completa em um sistema real.

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
        nome = dados['nome'].upper()
        cpf_cnpj = dados['cpf_cnpj']
        telefone = dados['telefone'].upper()
        email = dados['email'].upper()

        # Verificação de campos obrigatórios
        if not nome or not cpf_cnpj:
            return '''
            <h2>O campo Nome e CPF/CNPJ são obrigatórios.</h2>
            <a href="/clientes/cadastrar">Voltar</a>
            '''

        # Validação do CPF/CNPJ
        if not validar_cpf_cnpj(cpf_cnpj):
            return '''
            <h2>CPF/CNPJ inválido. Por favor, insira um válido.</h2>
            <a href="/clientes/cadastrar">Voltar</a>
            '''

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
        nr_apolice = dados['nr_apolice'].upper()
        tipo_seguro = dados['tipo_seguro'].upper()
        dt_vencimento = dados['dt_vencimento']
        seguradora = dados['seguradora'].upper()
        cliente_cpf = dados['cliente_cpf'].upper()

        # Verificação de campos obrigatórios
        if not nr_apolice or not tipo_seguro or not dt_vencimento or not seguradora or not cliente_cpf:
            return '''
            <h2>Todos os campos são obrigatórios.</h2>
            <a href="/apolices/cadastrar">Voltar</a>
            '''

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

# Rota para consultar apólices de um cliente por CPF/CNPJ com opções de editar, excluir e cadastrar nova apólice
@app.route('/apolices/consulta/cliente', methods=['GET', 'POST'])
def consultar_apolices_por_cliente():
    if request.method == 'POST':
        cpf_cnpj = request.form['cpf_cnpj']

        conexao = criar_conexao()
        cursor = conexao.cursor()

        # Verificar se o cliente existe no banco de dados
        sql_cliente = "SELECT ID, Nome, CPF_CNPJ, Telefone, Email FROM Clientes WHERE CPF_CNPJ = %s"
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
        WHERE Apolices.Cliente_ID = %s
        """
        cursor.execute(sql_apolices, (cliente[0],))
        apolices = cursor.fetchall()
        conexao.close()

        resultado = f'''
        <h2>Dados do Cliente</h2>
        <p><b>Nome:</b> {cliente[1]}</p>
        <p><b>CPF/CNPJ:</b> {cliente[2]}</p>
        <p><b>Telefone:</b> {cliente[3]}</p>
        <p><b>Email:</b> {cliente[4]}</p>
        <a href="/clientes/editar/{cliente[0]}">Editar Cliente</a> |
        <a href="/clientes/excluir/{cliente[0]}" onclick="return confirm('Tem certeza que deseja excluir este cliente?')">Excluir Cliente</a>
        <hr>
        <h2>Apólices</h2>
        '''
        
        if apolices:
            resultado += '<ul>'
            for apolice in apolices:
                resultado += f"""
                <li>
                <b>Número da Apólice:</b> {apolice[0]}<br>
                <b>Tipo de Seguro:</b> {apolice[1]}<br>
                <b>Data de Vencimento:</b> {apolice[2]}<br>
                <b>Seguradora:</b> {apolice[3]}<br>
                <a href="/apolices/editar/{apolice[0]}">Editar Apólice</a> |
                <a href="/apolices/excluir/{apolice[0]}" onclick="return confirm('Tem certeza que deseja excluir esta apólice?')">Excluir Apólice</a>
                </li><br>
                """
            resultado += '</ul>'
        else:
            resultado += '<p>Nenhuma apólice encontrada para esse cliente.</p>'

        # Adicionar a opção de cadastrar nova apólice para este cliente
        resultado += f'''
        <a href="/apolices/cadastrar?cliente_id={cliente[0]}">Cadastrar Nova Apólice para {cliente[1]}</a><br>
        <a href="/">Voltar ao Menu</a>
        '''

        return resultado

    return '''
    <h2>Consulta de Apólices por Cliente (CPF/CNPJ)</h2>
    <form method="POST">
        CPF/CNPJ do Cliente: <input type="text" name="cpf_cnpj"><br>
        <input type="submit" value="Consultar Apólices">
    </form>
    <a href="/">Voltar ao Menu</a>
    '''


# Rota para editar cliente
@app.route('/clientes/editar/<int:id>', methods=['GET', 'POST'])
def editar_cliente(id):
    conexao = criar_conexao()
    cursor = conexao.cursor()

    if request.method == 'POST':
        nome = request.form['nome'].upper()
        cpf_cnpj = request.form['cpf_cnpj']
        telefone = request.form['telefone'].upper()
        email = request.form['email'].upper()

        sql = "UPDATE Clientes SET Nome = %s, CPF_CNPJ = %s, Telefone = %s, Email = %s WHERE ID = %s"
        cursor.execute(sql, (nome, cpf_cnpj, telefone, email, id))
        conexao.commit()
        conexao.close()

        return f'<h2>Cliente atualizado com sucesso!</h2><a href="/">Voltar ao Menu</a>'
    
    # Exibe o formulário com os dados atuais
    sql_cliente = "SELECT Nome, CPF_CNPJ, Telefone, Email FROM Clientes WHERE ID = %s"
    cursor.execute(sql_cliente, (id,))
    cliente = cursor.fetchone()
    conexao.close()

    return f'''
    <h2>Editar Cliente</h2>
    <form method="POST">
        Nome: <input type="text" name="nome" value="{cliente[0]}"><br>
        CPF/CNPJ: <input type="text" name="cpf_cnpj" value="{cliente[1]}"><br>
        Telefone: <input type="text" name="telefone" value="{cliente[2]}"><br>
        Email: <input type="text" name="email" value="{cliente[3]}"><br>
        <input type="submit" value="Salvar">
    </form>
    <a href="/">Voltar ao Menu</a>
    '''

# Rota para excluir cliente
@app.route('/clientes/excluir/<int:id>', methods=['GET'])
def excluir_cliente(id):
    conexao = criar_conexao()
    cursor = conexao.cursor()

    sql_apolices = "DELETE FROM Apolices WHERE Cliente_ID = %s"
    cursor.execute(sql_apolices, (id,))
    
    sql_cliente = "DELETE FROM Clientes WHERE ID = %s"
    cursor.execute(sql_cliente, (id,))
    
    conexao.commit()
    conexao.close()

    return f'<h2>Cliente e apólices excluídos com sucesso!</h2><a href="/">Voltar ao Menu</a>'

# Rota para editar apólice
@app.route('/apolices/editar/<nr_apolice>', methods=['GET', 'POST'])
def editar_apolice(nr_apolice):
    conexao = criar_conexao()
    cursor = conexao.cursor()

    if request.method == 'POST':
        novo_nr_apolice = request.form['nr_apolice'].upper()
        tipo_seguro = request.form['tipo_seguro'].upper()
        dt_vencimento = request.form['dt_vencimento']
        seguradora = request.form['seguradora'].upper()

        # Atualiza a apólice, incluindo o número
        sql = """
        UPDATE Apolices 
        SET NR_Apolice = %s, Tipo_Seguro = %s, Dt_Vencimento = %s, Seguradora = %s 
        WHERE NR_Apolice = %s
        """
        cursor.execute(sql, (novo_nr_apolice, tipo_seguro, dt_vencimento, seguradora, nr_apolice))
        conexao.commit()
        conexao.close()

        return f'<h2>Apólice atualizada com sucesso!</h2><a href="/">Voltar ao Menu</a>'
    
    # Exibe o formulário com os dados atuais da apólice
    sql_apolice = "SELECT NR_Apolice, Tipo_Seguro, Dt_Vencimento, Seguradora FROM Apolices WHERE NR_Apolice = %s"
    cursor.execute(sql_apolice, (nr_apolice,))
    apolice = cursor.fetchone()
    conexao.close()

    return f'''
    <h2>Editar Apólice</h2>
    <form method="POST">
        Número da Apólice: <input type="text" name="nr_apolice" value="{apolice[0]}"><br>
        Tipo de Seguro: <input type="text" name="tipo_seguro" value="{apolice[1]}"><br>
        Data de Vencimento: <input type="date" name="dt_vencimento" value="{apolice[2]}"><br>
        Seguradora: <input type="text" name="seguradora" value="{apolice[3]}"><br>
        <input type="submit" value="Salvar">
    </form>
    <a href="/">Voltar ao Menu</a>
    '''


# Rota para excluir apólice
@app.route('/apolices/excluir/<nr_apolice>', methods=['GET'])
def excluir_apolice(nr_apolice):
    conexao = criar_conexao()
    cursor = conexao.cursor()

    sql = "DELETE FROM Apolices WHERE NR_Apolice = %s"
    cursor.execute(sql, (nr_apolice,))
    conexao.commit()
    conexao.close()

    return f'<h2>Apólice excluída com sucesso!</h2><a href="/">Voltar ao Menu</a>'

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
        ORDER BY Apolices.Dt_Vencimento ASC
        """
        cursor.execute(sql, (mes, ano))
        apolices = cursor.fetchall()
        conexao.close()

        if apolices:
            # Formatando o título com mês e ano
            resultado = f'<h2>Renovações de {mes}/{ano}</h2>'
            
            # Criando a tabela com os cabeçalhos
            resultado += '''
            <table border="1">
                <thead>
                    <tr>
                        <th>Data de Vencimento</th>
                        <th>Nome do Cliente</th>
                        <th>Tipo de Seguro</th>
                        <th>Seguradora</th>
                        <th>Número da Apólice</th>
                    </tr>
                </thead>
                <tbody>
            '''
            
            # Preenchendo a tabela com os dados das apólices
            for apolice in apolices:
                resultado += f'''
                <tr>
                    <td>{apolice[3].strftime('%d/%m/%Y')}</td>
                    <td>{apolice[0]}</td>
                    <td>{apolice[2]}</td>
                    <td>{apolice[4]}</td>
                    <td>{apolice[1]}</td>
                </tr>
                '''
            
            # Fechando a tabela
            resultado += '''
                </tbody>
            </table>
            '''
            
            # Botão para imprimir o relatório
            resultado += '''
            <br>
            <button onclick="window.print()">Imprimir Relatório</button>
            <br>
            <a href="/">Voltar ao Menu</a>
            '''
            return resultado
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
