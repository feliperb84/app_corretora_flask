from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

# Configuração da conexão
conexao = psycopg2.connect(
    host="localhost",
    user="postgres",  # Substituir pelo seu usuário do PostgreSQL
    password="admin",  # Substituir pela sua senha do PostgreSQL
    database="AMERICA"
)

cursor = conexao.cursor()

def cadastrar_cliente(conexao):
    nome = input("Nome do cliente: ")
    cpf_cnpj = input("CPF/CNPJ do cliente: ")
    telefone = input("Telefone do cliente: ")
    email = input("Email do cliente: ")

    sql = "INSERT INTO Clientes (Nome, CPF_CNPJ, Telefone, Email) VALUES (%s, %s, %s, %s)"
    valores = (nome, cpf_cnpj, telefone, email)
    
    cursor = conexao.cursor()
    cursor.execute(sql, valores)
    conexao.commit()
    
    print("Cliente cadastrado com sucesso!")

def cadastrar_apolice(conexao):
    nr_apolice = input("Número da apólice: ")
    tipo_seguro = input("Tipo de seguro: ")
    dt_vencimento = input("Data de vencimento (DD/MM/AAAA): ")
    seguradora = input("Seguradora: ")
    cliente_cpf = input("CPF do cliente: ")

    sql = "INSERT INTO Apolices (NR_Apolice, Tipo_Seguro, Dt_Vencimento, Seguradora, Cliente_cpf) VALUES (%s, %s, %s, %s, %s)"
    valores = (nr_apolice, tipo_seguro, dt_vencimento, seguradora, cliente_cpf)
    
    cursor = conexao.cursor()
    cursor.execute(sql, valores)
    conexao.commit()
    
    print("Apólice cadastrada com sucesso!")

def consultar_apolices_por_cliente(conexao):
    cpf_cnpj = input("Digite o CPF/CNPJ do cliente: ")

    sql = """
    SELECT Apolices.NR_Apolice, Apolices.Tipo_Seguro, Apolices.Dt_Vencimento, Apolices.Seguradora
    FROM Apolices
    JOIN Clientes ON Apolices.Cliente_ID = Clientes.ID
    WHERE Clientes.CPF_CNPJ = %s
    """
    cursor = conexao.cursor()
    cursor.execute(sql, (cpf_cnpj,))
    apolices = cursor.fetchall()

    if apolices:
        print(f"Apólices do cliente {cpf_cnpj}:")
        for apolice in apolices:
            print(f"Apólice: {apolice[0]}, Tipo: {apolice[1]}, Vencimento: {apolice[2]}, Seguradora: {apolice[3]}")
    else:
        print("Nenhuma apólice encontrada para esse cliente.")

def consultar_apolices_vencimento_mes(conexao):
    mes = input("Digite o mês (MM): ")
    ano = input("Digite o ano (AAAA): ")
    
    sql = """
    SELECT Clientes.Nome, Apolices.NR_Apolice, Apolices.Tipo_Seguro, Apolices.Dt_Vencimento, Apolices.Seguradora
    FROM Apolices
    JOIN Clientes ON Apolices.Cliente_ID = Clientes.ID
    WHERE EXTRACT(MONTH FROM Apolices.Dt_Vencimento) = %s
    AND EXTRACT(YEAR FROM Apolices.Dt_Vencimento) = %s
    """
    cursor = conexao.cursor()
    cursor.execute(sql, (mes, ano))
    apolices = cursor.fetchall()

    if apolices:
        print(f"Apólices com vencimento no mês {mes}/{ano}:")
        for apolice in apolices:
            print(f"Cliente: {apolice[0]}, Apólice: {apolice[1]}, Tipo: {apolice[2]}, Vencimento: {apolice[3]}, Seguradora: {apolice[4]}")
    else:
        print(f"Nenhuma apólice com vencimento no mês {mes}/{ano}.")

def menu_principal(conexao):
    while True:
        print("\n--- Menu Principal ---")
        print("1. Cadastrar Cliente")
        print("2. Cadastrar Apólice")
        print("3. Consultar Apólices por Cliente (CPF/CNPJ)")
        print("4. Consultar Apólices com Vencimento em um Mês")
        print("5. Sair")

        opcao = input("Escolha uma opção: ")

        if opcao == '1':
            cadastrar_cliente(conexao)
        elif opcao == '2':
            cadastrar_apolice(conexao)
        elif opcao == '3':
            consultar_apolices_por_cliente(conexao)
        elif opcao == '4':
            consultar_apolices_vencimento_mes(conexao)
        elif opcao == '5':
            print("Saindo...")
            break
        else:
            print("Opção inválida!")

if __name__ == "__main__":
    try:
        conexao = psycopg2.connect(
            host="localhost",
            user="postgres",
            password="admin",
            database="AMERICA"
        )
        menu_principal(conexao)
    finally:
        if conexao:
            conexao.close()