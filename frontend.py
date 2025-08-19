# frontend.py

import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Importa as funções do backend
import backend as be

st.set_page_config(page_title="Gestão da Clínica", page_icon="🩺", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #111827;
        color: #F3F4F6;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #E5E7EB;
    }

    .stButton>button {
        background-color: #2563EB;
        color: white;
        border-radius: 8px;
        padding: 0.5em 1em;
        border: none;
    }

    .stButton>button:hover {
        background-color: #1D4ED8;
    }

    .stDataFrame th, .stDataFrame td {
        color: #F3F4F6 !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        background-color: #1F2937;
        border-radius: 10px;
        padding: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        color: #D1D5DB !important;
    }

    .stTabs [aria-selected="true"] {
        background-color: #2563EB !important;
        color: white !important;
        border-radius: 6px;
    }

    .stSidebar {
        background-color: #1F2937;
    }

    .stMarkdown {
        color: #F3F4F6;
    }

    .st-expanderHeader {
        color: #F3F4F6 !important;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def get_color_map(_profissionais):
    """Cria um mapa de cores consistente para cada profissional."""
    colors = ["#FF4B4B", "#17A2B8", "#FFC107", "#28A745", "#6F42C1", "#FD7E14", "#7928CA"]
    return {prof: colors[i % len(colors)] for i, prof in enumerate(_profissionais)}

NOME_PLANILHA = "Banco de Dados - Clínica"
client = be.conectar_gspread()

if 'agenda' not in st.session_state and client:
    st.session_state.agenda, st.session_state.materiais, st.session_state.ficha = be.carregar_dados_online(client, NOME_PLANILHA)

def recarregar():
    keys_to_keep = ['client']
    for key in list(st.session_state.keys()):
        if key not in keys_to_keep:
            del st.session_state[key]
    st.cache_data.clear(); st.cache_resource.clear(); st.rerun()

st.sidebar.title("Navegação")
pagina_selecionada = st.sidebar.radio("Escolha uma página:", ["📊 Dashboard", "🗓️ Agenda Visual", "📦 Baixa Material", "📊 Status do Estoque", "⚙️ Configurações"], label_visibility="collapsed")
if st.sidebar.button("Recarregar Dados da Nuvem", use_container_width=True, type="primary"):
    recarregar()

if "agenda" not in st.session_state:
    st.info("Clique em 'Recarregar Dados da Nuvem' para iniciar o sistema.")
    st.stop()
if st.session_state.agenda.empty:
    st.warning("Sua planilha de agendamentos está vazia. Adicione dados através do Google Forms para começar a análise.")
    st.stop()


profissionais_unicos = sorted(st.session_state.agenda['Profissional Responsável'].dropna().unique())
color_map = get_color_map(profissionais_unicos)
with st.sidebar.expander("📅 Período de Análise", expanded=True):
    periodo_opts = ["Hoje", "Este Mês", "Mês Passado", "Este Ano", "Últimos 7 dias", "Últimos 30 dias", "Personalizado..."]
    periodo_selecionado = st.selectbox("Selecionar Período Rápido", options=periodo_opts, index=3)
    today = datetime.now().date()
    if periodo_selecionado == "Hoje": data_inicio, data_fim = today, today
    elif periodo_selecionado == "Este Mês": data_inicio, data_fim = today.replace(day=1), today
    elif periodo_selecionado == "Mês Passado": last_month_end = today.replace(day=1) - timedelta(days=1); data_inicio, data_fim = last_month_end.replace(day=1), last_month_end
    elif periodo_selecionado == "Este Ano": data_inicio, data_fim = today.replace(month=1, day=1), today
    elif periodo_selecionado == "Últimos 7 dias": data_inicio, data_fim = today - timedelta(days=6), today
    elif periodo_selecionado == "Últimos 30 dias": data_inicio, data_fim = today - timedelta(days=29), today
    else:
        min_data, max_data = st.session_state.agenda['Data do Atendimento'].dropna().min().date(), st.session_state.agenda['Data do Atendimento'].dropna().max().date()
        date_range_value = st.date_input("Selecione o Período Personalizado", [min_data, max_data], min_value=min_data, max_value=max_data)
        if isinstance(date_range_value, (list, tuple)) and len(date_range_value) == 2: data_inicio, data_fim = date_range_value
        else: data_inicio = data_fim = date_range_value
with st.sidebar.expander("Outros Filtros"):
    profissionais_selecionados = st.multiselect("Profissionais", profissionais_unicos, default=profissionais_unicos)
    procedimentos_selecionados = st.multiselect("Procedimentos", sorted(st.session_state.agenda['Procedimento Realizado'].dropna().unique()), default=sorted(st.session_state.agenda['Procedimento Realizado'].dropna().unique()))

agenda_filtrada = st.session_state.agenda[(st.session_state.agenda['Data do Atendimento'].dt.date >= data_inicio) & (st.session_state.agenda['Data do Atendimento'].dt.date <= data_fim) & (st.session_state.agenda['Profissional Responsável'].isin(profissionais_selecionados)) & (st.session_state.agenda['Procedimento Realizado'].isin(procedimentos_selecionados))]
df_financeiro, df_consumo, agenda_com_preco_filtrada = be.calcular_financeiro(agenda_filtrada, st.session_state.materiais, st.session_state.ficha)

if pagina_selecionada == "📊 Dashboard":
    st.title("⚕️ Dashboard de Gestão")


    with st.sidebar.expander("🎯 Metas e Objetivos"):
        meta_faturamento = st.number_input(
            "Defina sua meta de faturamento (R$)",
            min_value=1, value=10000, step=500
        )

    # Abas do dashboard
    tab1, tab2, tab3 = st.tabs(["📊 Visão Geral", "💰 Análise Financeira", "👥 Análise de Clientes"])


    with tab1:
        st.markdown("""
    <style>
        :root {
            --color-primary: #FACC15;     /* amarelo vibrante */
            --color-bg-card: #1E293B;    /* azul escuro (background do card) */
            --color-text-title: #E0E7FF; /* azul claro para títulos */
            --color-text-value: #F3F4F6; /* cinza claro para valores */
            --color-text-delta: #A5F3FC; /* azul claro para deltas */
            --color-bg-page: #0F172A;    /* fundo da página (escuro) */
        }
        .metric-card {
            background-color: var(--color-bg-card);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25);
            text-align: center;
            color: var(--color-text-value);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin-bottom: 20px;
        }
        .metric-title {
            font-size: 20px;
            font-weight: 600;
            color: var(--color-primary);
            margin-bottom: 12px;
        }
        .metric-value {
            font-size: 32px;
            font-weight: 700;
            color: var(--color-text-value);
            margin-bottom: 8px;
        }
        .metric-delta {
            font-size: 16px;
            color: var(--color-text-delta);
        }
        progress {
            width: 100%;
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
            background-color: #334155; /* tom mais escuro para fundo da barra */
            margin-top: 10px;
            margin-bottom: 15px;
        }
        progress::-webkit-progress-bar {
            background-color: #334155;
        }
        progress::-webkit-progress-value {
            background-color: var(--color-primary);
        }
        progress::-moz-progress-bar {
            background-color: var(--color-primary);
        }
    </style>
    """, unsafe_allow_html=True)

        st.markdown("### 📈 Resumo do Período")
        st.divider()

        if agenda_filtrada.empty:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")
        else:
            duracao_periodo = max((data_fim - data_inicio).days, 1)
            periodo_anterior_fim = data_inicio - timedelta(days=1)
            periodo_anterior_inicio = data_inicio - timedelta(days=duracao_periodo)

            agenda_periodo_anterior = st.session_state.agenda[
                (st.session_state.agenda['Data do Atendimento'].dt.date >= periodo_anterior_inicio) &
                (st.session_state.agenda['Data do Atendimento'].dt.date <= periodo_anterior_fim)
            ]

            _, _, agenda_com_preco_anterior = be.calcular_financeiro(
                agenda_periodo_anterior, st.session_state.materiais, st.session_state.ficha)

            total_receita_anterior = agenda_com_preco_anterior['Preco Venda (R$)'].sum() if not agenda_com_preco_anterior.empty else 0
            total_lucro_anterior = agenda_com_preco_anterior['Lucro Atendimento (R$)'].sum() if not agenda_com_preco_anterior.empty else 0
            total_atendimentos_anterior = agenda_com_preco_anterior.shape[0] if not agenda_com_preco_anterior.empty else 0

            total_receita_atual = agenda_com_preco_filtrada['Preco Venda (R$)'].sum()
            total_lucro_atual = agenda_com_preco_filtrada['Lucro Atendimento (R$)'].sum()
            total_atendimentos_atual = agenda_com_preco_filtrada.shape[0]

            delta_receita = ((total_receita_atual - total_receita_anterior) / total_receita_anterior
                             if total_receita_anterior > 0 else (1 if total_receita_atual > 0 else 0))
            delta_lucro = ((total_lucro_atual - total_lucro_anterior) / total_lucro_anterior
                           if total_lucro_anterior > 0 else (1 if total_lucro_atual > 0 else 0))
            delta_atendimentos = ((total_atendimentos_atual - total_atendimentos_anterior) / total_atendimentos_anterior
                                  if total_atendimentos_anterior > 0 else (1 if total_atendimentos_atual > 0 else 0))


            col1, col2, col3 = st.columns(3, gap="large")

            with col1:
                st.markdown(f"""
            <div class="metric-card" style="background-color: #1E3A8A; color: #DDE6F2;">
                <div class="metric-title" style="color: #F3E88B;">Receita Total</div>
                <div class="metric-value" style="color: #E0E7FF;">R$ {total_receita_atual:,.2f}</div>
                <div class="metric-delta" style="color: #A3D9A5;">{delta_receita:.1%} em relação ao período anterior</div>
            </div>
            """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
            <div class="metric-card" style="background-color: #1E3A8A; color: #D1FAE5;">
                <div class="metric-title" style="color: #F3E88B;">Lucro Total</div>
                <div class="metric-value" style="color: #E0E7FF;">R$ {total_lucro_atual:,.2f}</div>
                <div class="metric-delta" style="color: #A3D9A5;">{delta_lucro:.1%} em relação ao período anterior</div>
            </div>
            """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
            <div class="metric-card" style="background-color: #1E3A8A; color: #E9D7FF;">
                <div class="metric-title" style="color: #F3E88B;">Atendimentos</div>
                <div class="metric-value" style="color: #E0E7FF;">{total_atendimentos_atual}</div>
                <div class="metric-delta" style="color: #A3D9A5;">{delta_atendimentos:.1%} em relação ao período anterior</div>
            </div>
            """, unsafe_allow_html=True)
            df_mes = agenda_com_preco_filtrada.copy()
            df_mes['Data do Atendimento'] = pd.to_datetime(df_mes['Data do Atendimento'])
            df_mes['Ano-Mes'] = df_mes['Data do Atendimento'].dt.to_period('M').astype(str)


            df_mes_agrupado = df_mes.groupby('Ano-Mes').agg({
                'Preco Venda (R$)': 'sum',
                'Lucro Atendimento (R$)': 'sum'
            }).reset_index()


            df_long = df_mes_agrupado.melt(id_vars='Ano-Mes', value_vars=['Preco Venda (R$)', 'Lucro Atendimento (R$)'],
                                        var_name='Tipo', value_name='Valor')

            # Gráfico de colunas agrupadas
            fig = px.bar(df_long, x='Ano-Mes', y='Valor', color='Tipo', barmode='group',
                        title='Receita e Lucro Mensal',
                        labels={'Ano-Mes': 'Mês', 'Valor': 'Valor (R$)', 'Tipo': 'Métrica'})

            fig.update_layout(
                xaxis_tickangle=-45,
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis_tickprefix='R$ ',
                legend_title_text='',
                margin=dict(l=40, r=40, t=40, b=80)
            )

            st.plotly_chart(fig, use_container_width=True)
            progresso = min(1.0, total_receita_atual / meta_faturamento) if meta_faturamento > 0 else 0

            st.markdown(f"""
                <style>
                .progress-container {{
                    background-color: #111827;
                    border-radius: 10px;
                    padding: 15px;
                    margin-top: 30px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                }}
                .progress-bar {{
                    height: 25px;
                    width: 100%;
                    background-color: #374151;
                    border-radius: 8px;
                    overflow: hidden;
                    margin-top: 10px;
                }}
                .progress-fill {{
                    height: 100%;
                    width: {progresso*100:.1f}%;
                    background: linear-gradient(90deg, #3b82f6, #06b6d4);
                    transition: width 1s ease-in-out;
                    border-radius: 8px;
                }}
                .progress-text {{
                    color: #e5e7eb;
                    font-weight: 500;
                    margin-top: 5px;
                }}
                </style>

                <div class="progress-container">
                    <div class="metric-title">Progresso da Meta</div>
                    <div class="progress-bar">
                        <div class="progress-fill"></div>
                    </div>
                    <div class="progress-text">{progresso:.1%} da meta de R$ {meta_faturamento:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

    with tab2:
        st.header("💰 Análise Financeira por Procedimento")
        st.divider()
        st.dataframe(df_financeiro, use_container_width=True)


    with tab3:
        st.header("👥 Análise de Clientes (CRM)")
        st.divider()

        df_analise_clientes = be.calcular_analise_clientes(agenda_com_preco_filtrada)

        if df_analise_clientes.empty:
            st.warning("Nenhum cliente encontrado para os filtros selecionados.")
        else:
            col1, col2 = st.columns(2, gap="large")

            if 'Genero' in df_analise_clientes.columns and not df_analise_clientes['Genero'].dropna().empty:
                with col1:
                    st.subheader("Distribuição por Genero")

                    # Contagem agrupada
                    df_genero = df_analise_clientes['Genero'].value_counts().reset_index()
                    df_genero.columns = ['Genero', 'count']  # <- IMPORTANTE!


                    fig_genero = px.pie(
                        df_genero,
                        names='Genero',
                        values='count',
                        height=300,

                    )
                    st.plotly_chart(fig_genero, use_container_width=True)
            else:
                st.info("Sem dados disponíveis para a análise de Genero.")

            # Gráfico de distribuição por faixa etária
            if 'Idade' in df_analise_clientes.columns and not df_analise_clientes['Idade'].dropna().empty:
                with col2:
                    st.subheader("Distribuição por Faixa Etária")
                    bins = [0, 18, 25, 35, 45, 60, 100]
                    labels = ['0-18', '19-25', '26-35', '36-45', '46-60', '60+']
                    df_analise_clientes['Faixa Etária'] = pd.cut(
                        df_analise_clientes['Idade'], bins=bins, labels=labels, right=False)
                    df_faixa_etaria = df_analise_clientes['Faixa Etária'].value_counts().sort_index().reset_index()
                    df_faixa_etaria.columns = ['Faixa Etária', 'count']
                    fig_faixa = px.bar(df_faixa_etaria, x='Faixa Etária', y='count', height=300)
                    st.plotly_chart(fig_faixa, use_container_width=True)

            st.divider()
            st.subheader("Detalhes por Cliente")

            # Formatação das colunas da tabela
            st.dataframe(
                df_analise_clientes.style.format({
                    "Total Gasto (R$)": "R$ {:,.2f}",
                    "Ticket Médio (R$)": "R$ {:,.2f}",
                    "Última Visita": "{:%d/%m/%Y}",
                    "Idade": "{:.0f}"
                }),
                use_container_width=True
            )

elif pagina_selecionada == "🗓️ Agenda Visual":
    st.title("🗓️ Agenda Visual da Semana")
    dia_selecionado = st.date_input("Selecione uma data para ver a semana correspondente", datetime.now(), key="agenda_visual_date")
    start_of_week = dia_selecionado - timedelta(days=(dia_selecionado.weekday() + 1) % 7)
    end_of_week = start_of_week + timedelta(days=6)
    st.header(f"Semana de {start_of_week.strftime('%d/%m')} a {end_of_week.strftime('%d/%m/%Y')}", divider="rainbow")
    agenda_semana = st.session_state.agenda[(st.session_state.agenda['Data do Atendimento'].dt.date >= start_of_week) & (st.session_state.agenda['Data do Atendimento'].dt.date <= end_of_week)].copy()
    agenda_semana['Horário do Atendimento'] = agenda_semana['Horário do Atendimento'].astype(str)
    agenda_semana = agenda_semana.sort_values(by='Horário do Atendimento')
    dias_da_semana_str = ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
    dias_semana = [(start_of_week + timedelta(days=i)) for i in range(7)]
    cols = st.columns(7)
    for i, dia in enumerate(dias_semana):
        with cols[i]:
            st.markdown(f"**<p style='text-align: center;'>{dias_da_semana_str[i]}</p>**", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; font-size: 24px;'>{dia.day}</p>", unsafe_allow_html=True)
            st.markdown("---")
            agendamentos_dia = agenda_semana[agenda_semana['Data do Atendimento'].dt.date == dia]
            if agendamentos_dia.empty: st.caption("Sem agendamentos")
            else:
                for _, agendamento in agendamentos_dia.iterrows():
                    prof_color = color_map.get(agendamento['Profissional Responsável'], '#808080')
                    with st.container(border=True): st.markdown(f"""<div style="border-left: 5px solid {prof_color}; padding-left: 10px; border-radius: 5px;"><strong>⏰ {agendamento['Horário do Atendimento']}</strong><br>👤 {agendamento['Nome do Cliente']}<br><small><i>{agendamento['Procedimento Realizado']}</i></small></div>""", unsafe_allow_html=True)
    st.sidebar.markdown("---"); st.sidebar.subheader("Legenda de Profissionais");
    for prof, cor in color_map.items(): st.sidebar.markdown(f"<span style='color:{cor};'>●</span> {prof}", unsafe_allow_html=True)

elif pagina_selecionada == "📦 Baixa Material":
    st.title("📦 Baixa Material")
    st.info("Esta página mostra os atendimentos realizados que ainda não tiveram seus materiais deduzidos do estoque.")
    hoje = datetime.now().date()
    agenda_com_status = st.session_state.agenda.copy()
    agenda_com_status['Estoque Deduzido'] = agenda_com_status['Estoque Deduzido'].fillna('NÃO').str.upper()
    atendimentos_pendentes = agenda_com_status[(agenda_com_status['Data do Atendimento'].dt.date < hoje) & (agenda_com_status['Estoque Deduzido'] == 'NÃO')]
    if atendimentos_pendentes.empty:
        st.success("🎉 Tudo certo! Não há atendimentos passados com baixa de estoque pendente.")
    else:
        st.subheader("Atendimentos com Baixa de Estoque Pendente")
        st.dataframe(atendimentos_pendentes[['Data do Atendimento', 'Nome do Cliente', 'Procedimento Realizado']], use_container_width=True)
        st.markdown("---")
        st.subheader("Total de Materiais a Serem Deduzidos")
        _, df_consumo_pendente, _ = be.calcular_financeiro(atendimentos_pendentes, st.session_state.materiais, st.session_state.ficha)
        st.dataframe(df_consumo_pendente[['Material', 'Quantidade Usada']], use_container_width=True)
        if st.button("Confirmar Baixa de Estoque e Marcar Atendimentos como Processados", type="primary", use_container_width=True):
            with st.spinner("Processando baixas de estoque..."):
                materiais_atual = st.session_state.materiais.set_index('Material')
                consumo_para_deduzir = df_consumo_pendente.set_index('Material')
                materiais_atual['Quantidade em Estoque'] = materiais_atual['Quantidade em Estoque'].subtract(consumo_para_deduzir['Quantidade Usada'], fill_value=0)
                if be.salvar_dados_gsheet(client, NOME_PLANILHA, "Materiais", materiais_atual.reset_index()):
                    st.session_state.materiais = materiais_atual.reset_index().copy()
                    agenda_atualizada = st.session_state.agenda.copy()
                    indices_para_atualizar = atendimentos_pendentes.index
                    agenda_atualizada.loc[indices_para_atualizar, 'Estoque Deduzido'] = 'SIM'
                    if be.salvar_dados_gsheet(client, NOME_PLANILHA, "Respostas ao formulário 1", agenda_atualizada):
                        st.session_state.agenda = agenda_atualizada.copy()
                        st.success("Baixa de estoque realizada com sucesso!")
                        st.rerun()

elif pagina_selecionada == "📊 Status do Estoque":
    st.title("📊 Status do Estoque Atual")
    st.info("Este painel mostra a quantidade exata de cada material na sua prateleira neste momento.")
    df_estoque_status = st.session_state.materiais.copy()
    if 'Quantidade em Estoque' in df_estoque_status.columns and 'Estoque Mínimo' in df_estoque_status.columns:
        def get_status(row):
            if row['Quantidade em Estoque'] <= 0: return "🚨 Crítico (ZERADO)"
            elif row['Quantidade em Estoque'] <= row['Estoque Mínimo']: return "⚠️ Atenção (REPOR)"
            return "✅ OK"
        df_estoque_status['Status'] = df_estoque_status.apply(get_status, axis=1)
        max_stock_value = (df_estoque_status['Estoque Mínimo'] * 3).max()
        if max_stock_value == 0: max_stock_value = 100
        st.dataframe(df_estoque_status[['Status', 'Material', 'Quantidade em Estoque', 'Estoque Mínimo']], use_container_width=True,
                     column_config={"Status": st.column_config.TextColumn("Status", width="medium"), "Quantidade em Estoque": st.column_config.ProgressColumn("Nível do Estoque", format="%d un", min_value=0, max_value=int(max_stock_value))})
    else: st.warning("Adicione as colunas 'Quantidade em Estoque' e 'Estoque Mínimo' na sua planilha de Materiais.")
#Materiais alteraçao e salvamento
elif pagina_selecionada == "⚙️ Configurações":
    st.title("⚙️ Configurações e Cadastros"); st.info("Use os formulários para adicionar novos itens e a tabela para editar os existentes.")
    with st.expander("➕ Adicionar Novo Material"):
        with st.form("form_novo_material", clear_on_submit=True):
            novo_material = st.text_input("Nome do Material"); novo_preco = st.number_input("Preço Unitário de Custo (R$)", min_value=0.0, format="%.2f")
            estoque_inicial = st.number_input("Quantidade em Estoque Inicial", min_value=0, step=1); estoque_minimo = st.number_input("Estoque Mínimo", min_value=0, step=1)
            if st.form_submit_button("Adicionar Material", use_container_width=True):
                if novo_material:
                    nova_linha = pd.DataFrame([{"Material": novo_material, "Preco Unitario (R$)": novo_preco, "Quantidade em Estoque": estoque_inicial, "Estoque Mínimo": estoque_minimo}])
                    st.session_state.materiais = pd.concat([st.session_state.materiais, nova_linha], ignore_index=True)
                    if be.salvar_dados_gsheet(client, NOME_PLANILHA, "Materiais", st.session_state.materiais): recarregar()
                else: st.warning("O nome do material não pode ser vazio.")
    st.header("Gerenciar Materiais Existentes", divider="rainbow")
    st.data_editor(st.session_state.materiais, num_rows="dynamic", use_container_width=True, key="materiais_editor")
    if st.button("Salvar Alterações nos Materiais", use_container_width=True):
     try:
        edited_rows = st.session_state["materiais_editor"].get("edited_rows", {})
        if edited_rows:

            df_materiais_final = st.session_state.materiais.copy()
            for idx, changes in edited_rows.items():
                for col, new_val in changes.items():
                    df_materiais_final.at[idx, col] = new_val
        else:
            df_materiais_final = st.session_state.materiais.copy()

        if be.salvar_dados_gsheet(client, NOME_PLANILHA, "Materiais", df_materiais_final):
            recarregar()
     except Exception as e:
        st.error(f"Erro ao processar alterações nos materiais: {e}")
    #Ficha tecnica alteraçao e salvamento
    st.markdown("---")
    with st.expander("➕ Adicionar Novo Item na Ficha Técnica"):
        with st.form("form_nova_ficha", clear_on_submit=True):
            procedimento_opts = st.session_state.ficha['Procedimento'].unique().tolist()
            procedimento = st.selectbox("Procedimento (selecione um existente ou digite um novo)", options=procedimento_opts + ['--- NOVO PROCEDIMENTO ---']);
            if procedimento == '--- NOVO PROCEDIMENTO ---': procedimento = st.text_input("Nome do Novo Procedimento")
            material = st.selectbox("Material", options=st.session_state.materiais['Material'].unique())
            quantidade = st.number_input("Quantidade Usada", min_value=0.0, step=0.1, format="%.2f")
            preco_venda = st.number_input("Preço de Venda do Procedimento (R$)", min_value=0.0, format="%.2f")
            if st.form_submit_button("Adicionar Item na Ficha", use_container_width=True):
                if procedimento and material:
                    nova_linha_ficha = pd.DataFrame([{"Procedimento": procedimento, "Material": material, "Quantidade Usada": quantidade, "Preco de Venda (R$)": preco_venda}])
                    st.session_state.ficha = pd.concat([st.session_state.ficha, nova_linha_ficha], ignore_index=True)
                    if be.salvar_dados_gsheet(client, NOME_PLANILHA, "Ficha Técnica", st.session_state.ficha_editor): recarregar()
    st.header("Gerenciar Ficha Técnica Existente", divider="rainbow")
    st.data_editor(st.session_state.ficha, num_rows="dynamic", use_container_width=True, key="ficha_editor")
    if st.button("Salvar Alterações na Ficha Técnica", use_container_width=True):
     try:
        edited_rows = st.session_state["ficha_editor"].get("edited_rows", {})
        if edited_rows:
            df_ficha_final = st.session_state.ficha.copy()
            for idx, changes in edited_rows.items():
                for col, new_val in changes.items():
                    df_ficha_final.at[idx, col] = new_val
        else:
            df_ficha_final = st.session_state.ficha.copy()

        if be.salvar_dados_gsheet(client, NOME_PLANILHA, "Ficha Técnica", df_ficha_final):
            recarregar()
     except Exception as e:
        st.error(f"Erro ao processar alterações na ficha técnica: {e}")

    st.markdown("---")
    st.header("Gerenciar Agendamentos (Edição/Deleção)", divider="rainbow")
    st.info("Para adicionar novos agendamentos, use o Google Form. Esta seção é para corrigir ou deletar registros existentes.")
    st.data_editor(st.session_state.agenda, num_rows="dynamic", hide_index=True, use_container_width=True, key="agenda_editor")
    if st.button("Salvar Alterações na Agenda", use_container_width=True):
     try:
        edited_rows = st.session_state["agenda_editor"].get("edited_rows", {})
        if edited_rows:
            df_agenda_final = st.session_state.agenda.copy()
            for idx, changes in edited_rows.items():
                for col, new_val in changes.items():
                    df_agenda_final.at[idx, col] = new_val
        else:
            df_agenda_final = st.session_state.agenda.copy()

        if be.salvar_dados_gsheet(client, NOME_PLANILHA, "Respostas ao formulário 1", df_agenda_final):
            recarregar()
     except Exception as e:
        st.error(f"Erro ao processar alterações na agenda: {e}")

    st.download_button("📄 Baixar Relatório (Excel)", df_financeiro.to_csv(index=False).encode('utf-8'), file_name="relatorio.csv", mime='text/csv')