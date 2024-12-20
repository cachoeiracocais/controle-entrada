import streamlit as st
import pandas as pd
from datetime import datetime
import pygsheets
import hashlib
import unicodedata
import re  # Para validação e formatação do CPF

import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Caminhos e chaves sensíveis
google_credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
usuarios_file = os.getenv("USUARIOS_FILE")


# Configuração inicials
st.set_page_config(page_title="📝 Gerenciamento de Entrada e Saída", layout="wide")
st.title("☀️🏕️ Seja Bem-Vindo | Cachoeira de Cocais Queda do Véu")

# Funções auxiliares

# Função para criar hash de senha
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# Conexão com Google Sheets
def conectar_google_sheets(sheet_name):
    gc = pygsheets.authorize(service_file = google_credentials_path)
    sh = gc.open(sheet_name)
    worksheet = sh[0]  # Primeira aba da planilha
    return worksheet

# Função para salvar dados no Google Sheets
def salvar_dados_no_sheets(worksheet, df):
    # Somente adicionar novas linhas, não sobrepor o banco inteiro
    range_inicial = (1, 1)
    for index, row in df.iterrows():
        worksheet.append_table([row.tolist()], start=range_inicial)

def formatar_cpf(cpf):
    cpf = re.sub(r'\D', '', cpf)  # Remove tudo que não for número
    if len(cpf) == 11:
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    return cpf

# Inicializar estado para os campos do formulário
if "form_data" not in st.session_state:
    st.session_state.form_data = {
        "nome": "",
        "cpf": "",
        "placa": "",
        "acompanhantes": 0,
        "criancas": 0,
        "tipo_pagamento": "Dinheiro",
        "pais": "",
        "cep": "",
        "telefone": "",
        "observacoes": "",
    }

# Conectar ao Google Sheets
worksheet = conectar_google_sheets("Controle_Clientes")

# Recuperar dados existentes do Google Sheets
dados_clientes = worksheet.get_as_df()  # Tente obter como DataFrame

# Filtrar apenas dados do dia atual
data_hoje = datetime.now().date()
dados_clientes['Horário de Entrada'] = pd.to_datetime(dados_clientes['Horário de Entrada'])
dados_clientes['Horário de Saída'] = pd.to_datetime(dados_clientes['Horário de Saída'])
dados_clientes_atual = dados_clientes[(dados_clientes['Horário de Entrada'].dt.date == data_hoje) |
                                      (dados_clientes['Horário de Saída'].dt.date == data_hoje)]

# Dividir o app em duas abas
abas = st.sidebar.radio("Selecione a Página", ["Entrada Clientes", "Saída Clientes"])

if abas == "Entrada Clientes":
    st.title("📍️ Registro de Entrada")

    # Registro de Entrada
    with st.form("registro_entrada"):
        st.subheader("Registrar Entrada")
        st.text("Preencha as informações solicitadas, clique em 'Registrar Entrada', efetue o pagamento, mostre ao funcionário o comprovante e encerre o aplicativo.")

        # Dados obrigatórios
        nome = st.text_input("🙋🏻‍♂️ Nome do Cliente", value=st.session_state.form_data["nome"])
        cpf = st.text_input("🎫 CPF (somente números)", value=st.session_state.form_data["cpf"])
        placa = st.text_input("🚗 Placa do Veículo (caso não se aplique, digite 'OUTROS')", value=st.session_state.form_data["placa"])
        acompanhantes = st.number_input(
            "👨‍👩‍👧‍👦 Número de Acompanhantes (acima de 9 anos)",
            min_value=0,
            step=1,
            value=st.session_state.form_data["acompanhantes"]
        )
        criancas = st.number_input(
            "👩🏾 Número de Crianças (abaixo de 9 anos)",
            min_value=0,
            step=1,
            value=st.session_state.form_data["criancas"]
        )
        tipo_pagamento = st.selectbox(
            "Tipo de Pagamento",
            ["Pix", "Dinheiro"],
            index=["Pix", "Dinheiro"].index(st.session_state.form_data["tipo_pagamento"])
        )

        # Dados opcionais
        cep = st.text_input("🏡 CEP", value=st.session_state.form_data["cep"])
        telefone = st.text_input("📞 Telefone para Contato", value=st.session_state.form_data["telefone"])
        observacoes = st.text_area("Observações ou Comentários (Opcional)", value=st.session_state.form_data["observacoes"])

        # Botão de registro
        botao_registrar = st.form_submit_button("Registrar Entrada")

        if botao_registrar:
            if not nome or not cpf or not placa:
                st.error("Os campos Nome, CPF, Placa, Acompanhantes e Tipo de Pagamento são obrigatórios.")
            else:
                horario_entrada = datetime.now()
                cpf_formatado = formatar_cpf(cpf)
                nome_formatado = unicodedata.normalize("NFKD", nome.strip()).encode("ASCII", "ignore").decode("utf-8").upper()
                valor_total = (1 + acompanhantes) * 15  # R$ 15 por pessoa acima de 9 anos
                novo_cliente = {
                    "Nome": nome_formatado,
                    "CPF": cpf_formatado,
                    "Placa": placa,
                    "Acompanhantes": acompanhantes,
                    "Crianças": criancas,
                    "CEP": cep,
                    "Telefone": telefone,
                    "Horário de Entrada": horario_entrada.strftime('%Y-%m-%d %H:%M:%S'),  # Converter para string
                    "Horário de Saída": None,
                    "Valor Pago": valor_total,
                    "Tipo de Pagamento": tipo_pagamento,
                    "Observações": observacoes
                }

                # Adiciona novo cliente somente como nova linha no Google Sheets
                salvar_dados_no_sheets(worksheet, pd.DataFrame([novo_cliente]))

                # Limpar campos do formulário
                st.session_state.form_data = {
                    "nome": "",
                    "cpf": "",
                    "placa": "",
                    "acompanhantes": 0,
                    "criancas": 0,
                    "tipo_pagamento": "Dinheiro",
                    "cep": "",
                    "telefone": "",
                    "observacoes": "",
                }
                st.success(
                    f"Entrada registrada para {nome_formatado}. 💰 Valor a ser pago: R${valor_total} (Crianças: {criancas} isentas)"
                )

                # Caminho da imagem do QR Code (substitua pelo caminho correto)
                chave_pix = "39410752000166"
                st.text("Copie a chave ou Escaneie o QR Code para pagar")
                st.code(chave_pix, language="text")

elif abas == "Saída Clientes":
    st.title("Acesso Restrito")

    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.subheader("Login de Funcionário")
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            senha_hash = hash_senha(senha)
            # Usuário e senha são armazenados diretamente no Google Sheets para segurança
            if worksheet.cell(1, 2).value == usuario and worksheet.cell(1, 3).value == senha_hash:
                st.session_state.autenticado = True
                st.success("Login bem-sucedido!")
            else:
                st.error("Usuário ou senha inválidos.")
    else:
        st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"autenticado": False}))

        # Registrar saída
        st.subheader("📍➡️ Registrar Saída")

        # Recuperar os registros atuais para o dia de hoje
        dados_clientes_atual = worksheet.get_as_df()  # Recupera todos os registros diretamente do Google Sheets
        dados_clientes_atual['Horário de Entrada'] = pd.to_datetime(dados_clientes_atual['Horário de Entrada'],
                                                                    format='%Y-%m-%d %H:%M:%S')
        dados_clientes_atual['Horário de Saída'] = pd.to_datetime(dados_clientes_atual['Horário de Saída'],
                                                                  format='%Y-%m-%d %H:%M:%S')

        # Filtra apenas os registros com data de entrada na data atual
        dados_clientes_atual = dados_clientes_atual[
            (dados_clientes_atual['Horário de Entrada'].dt.date == data_hoje) |
            (dados_clientes_atual['Horário de Saída'].dt.date == data_hoje)
            ]

        # Selecionar CPFs pendentes de saída
        cpfs_pendentes = dados_clientes_atual[dados_clientes_atual["Horário de Saída"].isna()]["CPF"].unique()
        cpf_selecionado = st.selectbox("Selecione o CPF para registrar saída", options=[""] + list(cpfs_pendentes))

        if st.button("Registrar Saída") and cpf_selecionado:
            cliente = dados_clientes_atual[dados_clientes_atual["CPF"] == cpf_selecionado].iloc[-1]

            if cliente.empty:
                st.error("Não foi possível registrar a saída. Tente novamente.")
            else:
                horario_saida = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Converter para string conforme esperado

                # Atualizar a célula da coluna Horário de Saída para o cliente selecionado
                cliente_id = cliente.name
                worksheet.update_value(f'I{cliente_id + 2}',
                                       horario_saida)

                st.success(f"Saída registrada para o cliente com CPF {cpf_selecionado}.")

        # Exibir dados registrados apenas com data de entrada na data atual
        st.subheader("Dados Registrados")
        st.dataframe(dados_clientes_atual)
