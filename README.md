# ClinFlow - Dashboard de Gestão para Clínicas ⚕️

Um dashboard interativo construído com Streamlit e Python para a gestão completa de agendamentos, finanças, clientes e estoque de uma clínica, utilizando o Google Sheets como um banco de dados dinâmico e de fácil acesso.

## 🚀 Acesso ao Vivo

**[Clique aqui para acessar o dashboard](https://clinflow.streamlit.app/)**



## ✨ Principais Funcionalidades

* **📊 Dashboard de Gestão:** Uma visão geral com os KPIs mais importantes, incluindo receita, lucro, número de atendimentos e progresso em relação a metas.
* **💰 Análise Financeira:** Detalhamento do faturamento, custos e lucro por cada procedimento realizado.
* **👥 Análise de Clientes (CRM):** Informações sobre os clientes, como total gasto, número de visitas, ticket médio e distribuição por gênero e faixa etária.
* **🗓️ Agenda Visual:** Um calendário semanal que exibe todos os agendamentos de forma clara e organizada por profissional.
* **📦 Baixa de Material:** Ferramenta para gerenciar o consumo de estoque com base nos procedimentos realizados.
* **📊 Status do Estoque:** Painel para monitorar os níveis atuais de materiais, com alertas visuais para itens que precisam de reposição.
* **⚙️ Configurações:** Interface para cadastrar e editar materiais, procedimentos (Ficha Técnica) e corrigir registros de agendamentos.

##  workflow Fluxo de Uso

O sistema foi projetado para ser simples e integrado, seguindo o fluxo:

1.  **Registrar um Novo Atendimento:**
    * Toda nova consulta ou procedimento é registrado através do formulário Google Forms.
    * **Link do Formulário:** [Registrar Novo Atendimento](https://docs.google.com/forms/d/e/1FAIpQLSdf3vVaoIpJ21K1JR2cHYzsp-dqZtZzxxOoqhbWCmoJbOTmgA/viewform)

2.  **Centralização dos Dados:**
    * As respostas do formulário são salvas automaticamente na Planilha Google, que funciona como o banco de dados central do sistema.
    * **Link do Banco de Dados:** [Planilha Google - Banco de Dados](https://docs.google.com/spreadsheets/d/19KdDmRbM0cIbEZwQlunllGa6iJKfn5jSDUXlKuv731A/edit?usp=sharing)

3.  **Análise e Gestão no Dashboard:**
    * O dashboard ClinFlow lê os dados diretamente da planilha em tempo real para gerar todos os gráficos e análises.

### Nota sobre a Baixa de Estoque

A seção **"📦 Baixa Material"** foi projetada para mostrar **apenas atendimentos de dias anteriores** que ainda não tiveram seus materiais deduzidos do estoque. Isso é uma regra de negócio para garantir que apenas atendimentos já consolidados entrem no controle de consumo, evitando que consultas do dia corrente, que ainda podem ser alteradas ou canceladas, apareçam na lista de baixa.

## 💻 Tecnologias Utilizadas

* **Python**
* **Streamlit** - Para a criação do dashboard interativo.
* **Pandas** - Para manipulação e análise de dados.
* **Plotly** - Para a criação dos gráficos.
* **Gspread** - Para a integração com o Google Sheets.
* **Google Cloud Platform** - Para autenticação via Service Account.
