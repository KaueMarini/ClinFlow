# backend.py

import pandas as pd
import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

@st.cache_resource(ttl=300)
def conectar_gspread():
    """Conecta ao Google Sheets de forma segura."""
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'])
        return gspread.authorize(creds)
    except (FileNotFoundError, KeyError):
        try:
            creds = Credentials.from_service_account_file(".streamlit/credentials.json", scopes=['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'])
            return gspread.authorize(creds)
        except FileNotFoundError:
            st.error("ERRO: Arquivo 'credentials.json' não encontrado. Configure os secrets no Streamlit Cloud.")
            return None
        except Exception as e:
            st.error(f"Erro de autenticação com Google: {e}")
            return None

@st.cache_data(ttl=60)
def carregar_dados_online(_client, nome_planilha):
    """Carrega, limpa e prepara os dados das 3 abas da Planilha Google."""
    try:
        spreadsheet = _client.open(nome_planilha)
        agenda = get_as_dataframe(spreadsheet.worksheet("Respostas ao formulário 1"), evaluate_formulas=True, header=0).dropna(how='all')
        materiais = get_as_dataframe(spreadsheet.worksheet("Materiais"), evaluate_formulas=True, header=0).dropna(how='all')
        ficha = get_as_dataframe(spreadsheet.worksheet("Ficha Técnica"), evaluate_formulas=True, header=0).dropna(how='all')

        # Limpeza da Agenda
        agenda.columns = [str(col).strip() for col in agenda.columns]
        agenda['Data do Atendimento'] = pd.to_datetime(agenda['Data do Atendimento'], dayfirst=True, errors='coerce')
        if 'Idade' in agenda.columns: agenda['Idade'] = pd.to_numeric(agenda['Idade'], errors='coerce')
        if 'Genero' in agenda.columns: agenda['Genero'] = agenda['Genero'].astype(str).str.strip()
        if 'Estoque Deduzido' not in agenda.columns:
            agenda['Estoque Deduzido'] = 'NÃO'
        else:
            agenda['Estoque Deduzido'] = agenda['Estoque Deduzido'].fillna('NÃO').astype(str).str.strip().str.upper()
            agenda.loc[agenda['Estoque Deduzido'] == '', 'Estoque Deduzido'] = 'NÃO'

        # Limpeza de Materiais
        materiais.columns = [str(col).strip() for col in materiais.columns]
        materiais['Preco Unitario (R$)'] = pd.to_numeric(materiais['Preco Unitario (R$)'], errors='coerce').fillna(0)
        if 'Quantidade em Estoque' in materiais.columns: materiais['Quantidade em Estoque'] = pd.to_numeric(materiais['Quantidade em Estoque'], errors='coerce').fillna(0)
        if 'Estoque Mínimo' in materiais.columns: materiais['Estoque Mínimo'] = pd.to_numeric(materiais['Estoque Mínimo'], errors='coerce').fillna(0)
        if not materiais.empty and 'Material' in materiais.columns:
            materiais = materiais.groupby('Material', as_index=False).agg({
                'Preco Unitario (R$)': 'first', 'Quantidade em Estoque': 'sum', 'Estoque Mínimo': 'first'
            })

        # Limpeza da Ficha Técnica
        ficha.columns = [str(col).strip() for col in ficha.columns]
        ficha['Quantidade Usada'] = pd.to_numeric(ficha['Quantidade Usada'], errors='coerce').fillna(0)
        ficha['Preco de Venda (R$)'] = pd.to_numeric(ficha['Preco de Venda (R$)'], errors='coerce').fillna(0)

        return agenda, materiais, ficha
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar dados da Planilha: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def salvar_dados_gsheet(client, nome_planilha, nome_aba, df_para_salvar):
    """Função centralizada e segura para salvar dataframes no Google Sheets."""
    with st.spinner(f"Salvando dados na aba '{nome_aba}'..."):
        try:
            worksheet = client.open(nome_planilha).worksheet(nome_aba)
            df_limpo = df_para_salvar.astype(str).replace(['nan', 'NaT', '<NA>', 'None'], '')
            set_with_dataframe(worksheet, df_limpo, include_index=False, resize=True)
            st.toast(f"✅ Dados da aba '{nome_aba}' salvos com sucesso!", icon="🎉")
            return True
        except Exception as e:
            st.error(f"Falha ao salvar na aba '{nome_aba}': {e}")
            return False

def calcular_financeiro(df_agenda, materiais, ficha_tecnica):
    """Função vetorizada para calcular finanças e consumo."""
    if df_agenda.empty: return pd.DataFrame(), pd.DataFrame(), df_agenda.copy()
    custo_map = ficha_tecnica.merge(materiais, on='Material', how='left').fillna(0)
    custo_map['Custo_Item'] = custo_map['Quantidade Usada'] * custo_map['Preco Unitario (R$)']
    custo_final_map = custo_map.groupby('Procedimento')['Custo_Item'].sum()
    preco_map = ficha_tecnica.drop_duplicates(subset=['Procedimento']).set_index('Procedimento')['Preco de Venda (R$)']
    agenda_com_calculos = df_agenda.copy()
    agenda_com_calculos['Custo Atendimento (R$)'] = agenda_com_calculos['Procedimento Realizado'].map(custo_final_map).fillna(0)
    agenda_com_calculos['Preco Venda (R$)'] = agenda_com_calculos['Procedimento Realizado'].map(preco_map).fillna(0)
    agenda_com_calculos['Lucro Atendimento (R$)'] = agenda_com_calculos['Preco Venda (R$)'] - agenda_com_calculos['Custo Atendimento (R$)']
    df_financeiro = agenda_com_calculos.groupby('Procedimento Realizado').agg(Qtd_Realizada=('Procedimento Realizado', 'count'), Receita_Total_RS=('Preco Venda (R$)', 'sum'), Custo_Total_RS=('Custo Atendimento (R$)', 'sum'), Lucro_Total_RS=('Lucro Atendimento (R$)', 'sum')).reset_index().rename(columns={'Procedimento Realizado': 'Procedimento', 'Receita_Total_RS': 'Receita Total (R$)', 'Custo_Total_RS': 'Custo Total (R$)', 'Lucro_Total_RS': 'Lucro Total (R$)', 'Qtd_Realizada': 'Qtd Realizada'})
    consumo_agenda = agenda_com_calculos.merge(ficha_tecnica[['Procedimento', 'Material', 'Quantidade Usada']], left_on='Procedimento Realizado', right_on='Procedimento', how='left')
    df_consumo = consumo_agenda.groupby('Material')['Quantidade Usada'].sum().reset_index()
    if not df_consumo.empty:
        df_consumo = pd.merge(df_consumo, materiais, on='Material', how='left').fillna(0)
        df_consumo['Custo Total (R$)'] = df_consumo['Quantidade Usada'] * df_consumo['Preco Unitario (R$)']
    return df_financeiro, df_consumo, agenda_com_calculos

def calcular_analise_clientes(agenda_com_preco):
    """Calcula as métricas de CRM por cliente."""
    if agenda_com_preco.empty or 'Nome do Cliente' not in agenda_com_preco.columns: return pd.DataFrame()
    analise_clientes = agenda_com_preco.groupby('Nome do Cliente').agg(Total_Gasto_RS=('Preco Venda (R$)', 'sum'), Total_Visitas=('Data do Atendimento', 'count'), Ultima_Visita=('Data do Atendimento', 'max')).reset_index().rename(columns={'Nome do Cliente': 'Cliente','Total_Gasto_RS': 'Total Gasto (R$)','Total_Visitas': 'Nº de Visitas','Ultima_Visita': 'Última Visita'})
    if 'Idade' in agenda_com_preco.columns:
        idade_map = agenda_com_preco.dropna(subset=['Idade']).groupby('Nome do Cliente')['Idade'].first()
        analise_clientes = analise_clientes.merge(idade_map, left_on='Cliente', right_index=True, how='left')
    if 'Genero' in agenda_com_preco.columns:
        genero_map = agenda_com_preco.dropna(subset=['Genero']).groupby('Nome do Cliente')['Genero'].first()
        analise_clientes = analise_clientes.merge(genero_map, left_on='Cliente', right_index=True, how='left')
    analise_clientes['Ticket Médio (R$)'] = analise_clientes.apply(lambda row: row['Total Gasto (R$)'] / row['Nº de Visitas'] if row['Nº de Visitas'] > 0 else 0, axis=1)
    analise_clientes = analise_clientes.sort_values(by='Total Gasto (R$)', ascending=False)
    col_order = ['Cliente', 'Total Gasto (R$)', 'Nº de Visitas', 'Ticket Médio (R$)'];
    if 'Idade' in analise_clientes.columns: col_order.append('Idade')
    if 'Genero' in analise_clientes.columns: col_order.append('Genero')
    col_order.append('Última Visita')
    return analise_clientes.reindex(columns=col_order).fillna('')