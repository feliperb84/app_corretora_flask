from flask import Flask, request, jsonify, render_template, url_for,redirect, session, flash
import os
import psycopg2
import re
from dotenv import load_dotenv
from datetime import datetime, timedelta


app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Troque por uma chave segura!  inicio implementação de login

# Usuário e senha para login (pode mudar para buscar do banco de dados, se preferir)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'senha123'

# Rota para o login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and request.form['password'] == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))  # Redireciona para a dashboard
        else:
            flash('Usuário ou senha incorretos.', 'danger')
    return render_template('login.html')

# Rota para logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da conta.', 'info')
    return redirect(url_for('login'))


#final da implementação de login

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

# Carrega variáveis do .env
load_dotenv()

# Configuração da conexão com o PostgreSQL
def criar_conexao():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=os.getenv("DB_PORT")
    )

# inicio 2° teste dashboard
@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    hoje = datetime.today()

    # Conexão com o banco de dados
    conn = criar_conexao()
    cursor = conn.cursor()

    # Consulta para contar o total de clientes
    cursor.execute("SELECT COUNT(*) FROM clientes")
    total_clientes = cursor.fetchone()[0]

    # Consulta para contar o total de apólices
    cursor.execute("SELECT COUNT(*) FROM apolices WHERE dt_vencimento >= %s", (hoje,))
    total_apolices = cursor.fetchone()[0]

    # Calculando apólices que vencem na semana
    semana_futura = hoje + timedelta(days=7)

    # Consulta para obter as apólices que vencem na próxima semana
    cursor.execute("""
        SELECT a.dt_vencimento, c.nome, a.tipo_seguro, a.seguradora 
        FROM apolices a
        JOIN clientes c ON a.cliente_id = c.id
        WHERE a.dt_vencimento BETWEEN %s AND %s
        ORDER BY Dt_Vencimento ASC;
    """, (hoje, semana_futura))
    
    apolices_vencimento = cursor.fetchall()

    # Preparando os dados formatados para exibição
    apolices_formatadas = []
    for apolice in apolices_vencimento:
        data_vencimento, cliente_nome, tipo_seguro, seguradora_nome = apolice
        
        # Extraindo primeiro nome de cliente e seguradora
        cliente_primeiro_nome = cliente_nome.split(' ')[0]
        seguradora_primeiro_nome = seguradora_nome.split(' ')[0]
        
        # Adicionando apólice formatada à lista
        apolices_formatadas.append({
            'data_vencimento': data_vencimento.strftime('%d/%m'),  # Formatando a data
            'cliente_nome': cliente_primeiro_nome,
            'tipo_seguro': tipo_seguro,
            'seguradora_nome': seguradora_primeiro_nome
        })

    # Fechando conexão
    cursor.close()
    conn.close()

    # Renderizando a página com os dados
    return render_template('index.html', 
                        total_clientes=total_clientes, 
                        total_apolices=total_apolices, 
                        apolices_vencimento=apolices_formatadas)
#final 2° teste dash

# Rota para sair
@app.route('/sair')
def sair():
    return render_template('sair.html')

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

# Rota para cadastrar cliente
@app.route('/clientes/cadastrar', methods=['GET', 'POST'])
def cadastrar_cliente():
    if request.method == 'POST':
        nome = request.form['nome'].upper()
        cpf_cnpj = request.form['cpf_cnpj']
        telefone = request.form['telefone'].upper()
        email = request.form['email'].upper()

# Verificação de campos obrigatórios
        if not nome or not cpf_cnpj:
            return '''
            <h2>O campo Nome e CPF/CNPJ são obrigatórios.</h2>
            <a href="/clientes/cadastrar">Voltar</a>
            '''

        # Validação do CPF/CNPJ
        if not validar_cpf_cnpj(cpf_cnpj):
            return render_template('erro_cpf_invalido.html')
            
        # Verifica se o cliente já existe
        cliente_existente = verificar_cliente_existente(cpf_cnpj)
        if cliente_existente:
            return render_template('cliente_existe.html')

        # Cadastra novo cliente se não existir
        conexao = criar_conexao()
        cursor = conexao.cursor()
        sql = "INSERT INTO Clientes (Nome, CPF_CNPJ, Telefone, Email) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (nome, cpf_cnpj, telefone, email))
        conexao.commit()
        conexao.close()
        
        return render_template('success.html', mensagem="Cliente cadastrado com sucesso!")

    return render_template('cadastrar_cliente.html')

# Rota para cadastrar apólice
@app.route('/apolices/cadastrar', methods=['GET', 'POST'])
def cadastrar_apolice():
    if request.method == 'POST':
        nr_apolice = request.form['nr_apolice'].upper()
        tipo_seguro = request.form['tipo_seguro'].upper()
        dt_vencimento = request.form['dt_vencimento']
        seguradora = request.form['seguradora'].upper()
        cliente_cpf = request.form['cliente_cpf'].upper()

        try:
            conexao = criar_conexao()
            cursor = conexao.cursor()

            # Primeiro, obtenha o ID do cliente com base no CPF fornecido
            sql_cliente = "SELECT ID FROM Clientes WHERE CPF_CNPJ = %s"
            cursor.execute(sql_cliente, (cliente_cpf,))
            resultado = cursor.fetchone()

            if resultado:
                cliente_id = resultado[0]
                # Insira a apólice com o ID do cliente
                sql_apolice = """
                INSERT INTO Apolices (NR_Apolice, Tipo_Seguro, Dt_Vencimento, Seguradora, Cliente_ID)
                VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(sql_apolice, (nr_apolice, tipo_seguro, dt_vencimento, seguradora, cliente_id))
                conexao.commit()
                return render_template('success.html', mensagem="Apólice cadastrada com sucesso!")
            else:
                return render_template('error.html', topmensagem="CPF ou CNPJ não localizado.", mensagem="Faça o cadastro do cliente primeiro", link=url_for('cadastrar_apolice'))

        except Exception as e:
            print(f"Erro ao cadastrar apólice: {e}")  # Loga o erro no console
            if 'violates unique constraint' in str(e):
                return render_template('error.html', topmensagem="Ops! Algo deu errado.", mensagem="A apólice já está cadastrada no sistema.")
            else:
                return render_template('error.html', topmensagem="Cadastro não foi concluído.", mensagem="Existe apólice com mesmo n° já cadastrada para este segurado.")
            
        finally:
            conexao.close()

    return render_template('cadastrar_apolice.html')

# Rota para consultar apólices por cliente e permitir edição/exclusão
@app.route('/apolices/consulta/cliente', methods=['GET', 'POST'])
def consulta_cliente():
    if request.method == 'POST':
        cpf_cnpj = request.form['cpf_cnpj']

        conexao = criar_conexao()
        cursor = conexao.cursor()

        # Obtém o ID e dados do cliente
        sql_cliente = "SELECT ID, Nome, CPF_CNPJ, Telefone, Email FROM Clientes WHERE CPF_CNPJ = %s"
        cursor.execute(sql_cliente, (cpf_cnpj,))
        cliente = cursor.fetchone()

        if cliente:
            cliente_id = cliente[0]

            # Obtém as apólices do cliente
            sql_apolices = """
            SELECT Dt_Vencimento, NR_Apolice, Tipo_Seguro, Seguradora
            FROM Apolices
            WHERE Cliente_ID = %s
            ORDER BY Dt_Vencimento DESC;
            """
            cursor.execute(sql_apolices, (cliente_id,))
            apolices = cursor.fetchall()
            conexao.close()

            # Renderiza a página passando dados do cliente e das apólices
            return render_template('consulta_cliente.html', cliente=cliente, apolices=apolices)

        else:
            conexao.close()
            return render_template('error.html', topmensagem="CPF/CNPJ inexistente", mensagem="Cliente não encontrado.", link=url_for('consulta_cliente'))

    return render_template('consulta_cliente_form.html')

@app.route('/clientes/alterar/<int:id>', methods=['POST'])
def alterar_cliente(id):
    nome = request.form['nome'].upper()
    cpf_cnpj = request.form['cpf_cnpj']
    telefone = request.form['telefone'].upper()
    email = request.form['email'].upper()

    conexao = criar_conexao()
    cursor = conexao.cursor()

    try:
        sql = """
        UPDATE Clientes 
        SET Nome = %s, CPF_CNPJ = %s, Telefone = %s, Email = %s 
        WHERE ID = %s
        """
        cursor.execute(sql, (nome, cpf_cnpj, telefone, email, id))
        conexao.commit()

        return render_template('success.html', mensagem="Dados do cliente alterados com sucesso!")

    except Exception as e:
        conexao.rollback()
        print(f"Erro ao alterar cliente: {e}")
        return render_template('error.html', mensagem="Erro ao alterar dados do cliente.")

    finally:
        conexao.close()

@app.route('/apolices/alterar/<nr_apolice>', methods=['POST'])
def alterar_apolice(nr_apolice):
    dt_vencimento = request.form['dt_vencimento']
    tipo_seguro = request.form['tipo_seguro'].upper()
    seguradora = request.form['seguradora'].upper()

    conexao = criar_conexao()
    cursor = conexao.cursor()

    try:
        sql = """
        UPDATE Apolices
        SET Dt_Vencimento = %s, Tipo_Seguro = %s, Seguradora = %s
        WHERE NR_Apolice = %s
        """
        cursor.execute(sql, (dt_vencimento, tipo_seguro, seguradora, nr_apolice))
        conexao.commit()

        return render_template('success.html', mensagem="Apólice alterada com sucesso!")

    except Exception as e:
        conexao.rollback()
        print(f"Erro ao alterar apólice: {e}")
        return render_template('error.html', mensagem="Erro ao alterar apólice.")

    finally:
        conexao.close()

# Rota para excluir cliente e todas as apólices associadas
@app.route('/clientes/excluir/<int:id>', methods=['POST'])
def excluir_cliente(id):
    conexao = criar_conexao()
    cursor = conexao.cursor()

    try:
        # Excluindo apólices associadas ao cliente
        sql_apolices = "DELETE FROM Apolices WHERE Cliente_ID = %s"
        cursor.execute(sql_apolices, (id,))

        # Excluindo o cliente
        sql_cliente = "DELETE FROM Clientes WHERE ID = %s"
        cursor.execute(sql_cliente, (id,))

        conexao.commit()
        return render_template('success.html', mensagem="Cliente e apólices excluídos com sucesso!")

    except Exception as e:
        conexao.rollback()
        print(f"Erro ao excluir cliente: {e}")
        return render_template('error.html', mensagem="Erro ao excluir cliente e apólices.")

    finally:
        conexao.close()

# Rota para excluir apólice individualmente
@app.route('/apolices/excluir/<nr_apolice>', methods=['POST'])
def excluir_apolice(nr_apolice):
    conexao = criar_conexao()
    cursor = conexao.cursor()

    try:
        sql = "DELETE FROM Apolices WHERE NR_Apolice = %s"
        cursor.execute(sql, (nr_apolice,))

        conexao.commit()
        return render_template('success.html', mensagem="Apólice excluída com sucesso!")

    except Exception as e:
        conexao.rollback()
        print(f"Erro ao excluir apólice: {e}")
        return render_template('error.html', mensagem="Erro ao excluir apólice.")

    finally:
        conexao.close()

# Rota para consultar apólices com vencimento no mês atual
@app.route('/apolices/vencimento', methods=['GET', 'POST'])
def apolices_vencimento():
    if request.method == 'POST':
        # O usuário enviou o formulário com mês e ano
        mes = request.form['mes']
        ano = request.form['ano']
        
        # Consulta no banco de dados
        conexao = criar_conexao()
        cursor = conexao.cursor()
        sql = """
        SELECT Apolices.Dt_Vencimento, Clientes.Nome, Apolices.Tipo_Seguro, Apolices.Seguradora, Apolices.NR_Apolice  
        FROM Apolices
        JOIN Clientes ON Apolices.Cliente_ID = Clientes.ID
        WHERE EXTRACT(MONTH FROM Apolices.Dt_Vencimento) = %s
        AND EXTRACT(YEAR FROM Apolices.Dt_Vencimento) = %s
        ORDER BY Apolices.Dt_Vencimento ASC
        """
        cursor.execute(sql, (mes, ano))
        apolices = cursor.fetchall()
        conexao.close()

        # Exibe o template com a tabela de apólices
        return render_template('apolices_vencimento.html', apolices=apolices)

    # Se for uma requisição GET, mostre o formulário para escolher mês/ano
    return render_template('consulta_apolices_form.html')


if __name__ == '__main__':
    app.run(debug=True)

#_____________até aqui código revisado e funcionando 
