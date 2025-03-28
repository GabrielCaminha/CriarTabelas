import plotly.graph_objects as go
import plotly.subplots as sp
import pandas as pd
import sqlite3
import streamlit as st

# Conectar ao banco de dados SQLite
conn = sqlite3.connect('equipamentos.db')
cursor = conn.cursor()

# Recuperar os dados do banco de dados
query = """
    SELECT local_name, equipamento_name, categoria, quantidade
    FROM itens_equipamentos
"""
df = pd.read_sql(query, conn)

# Fechar conexão com o banco de dados
conn.close()

# Adicionar filtro para os locais na sidebar
local_nome = st.sidebar.selectbox("Selecione o Local", df["local_name"].unique())

# Filtrar os dados com base no local 
df_filtrado = df[df["local_name"] == local_nome]

# Processar os dados para visualização
itens_classificados = {}
for _, row in df_filtrado.iterrows():
    equipamento = row["equipamento_name"]
    categoria = row["categoria"]
    quantidade = row["quantidade"]
    
    if equipamento not in itens_classificados:
        itens_classificados[equipamento] = {"Segurança": 0, "Importante": 0, "Normal": 0}
    
    if categoria == "Segurança":
        itens_classificados[equipamento]["Segurança"] += quantidade
    elif categoria == "Importante":
        itens_classificados[equipamento]["Importante"] += quantidade
    elif categoria == "Normal":
        itens_classificados[equipamento]["Normal"] += quantidade

# Converter os dados para um DataFrame para facilitar a manipulação 
dados = []
for equip, dados_equip in itens_classificados.items():
    total_itens = sum(dados_equip.values())
    dados.append({
        "Equipamento": equip,
        "Segurança": dados_equip["Segurança"],
        "Importante": dados_equip["Importante"],
        "Normal": dados_equip["Normal"],
        "Total": total_itens
    })

df_equipamentos = pd.DataFrame(dados)

# Criar gráficos
bar_fig = go.Figure()
bar_fig.add_trace(go.Bar(x=df_equipamentos["Equipamento"], y=df_equipamentos["Segurança"], name="Segurança", marker_color="gold"))
bar_fig.add_trace(go.Bar(x=df_equipamentos["Equipamento"], y=df_equipamentos["Importante"], name="Importante", marker_color="dodgerblue"))
bar_fig.add_trace(go.Bar(x=df_equipamentos["Equipamento"], y=df_equipamentos["Normal"], name="Normal", marker_color="forestgreen"))
bar_fig.update_layout(title=f"Distribuição de Itens - {local_nome}", barmode="stack", xaxis_title="Equipamento", yaxis_title="Quantidade de Itens", template="plotly_dark")

categoria_soma = df_equipamentos[["Segurança", "Importante", "Normal"]].sum()
pie_fig = go.Figure(data=[go.Pie(labels=categoria_soma.index, values=categoria_soma.values, marker=dict(colors=["gold", "dodgerblue", "forestgreen"]))])

stacked_bar_fig = go.Figure()
stacked_bar_fig.add_trace(go.Bar(x=["Segurança", "Importante", "Normal"], y=categoria_soma.values, name="Total por Categoria", marker_color=["gold", "dodgerblue", "forestgreen"]))
stacked_bar_fig.update_layout(title="Total de Itens por Categoria", barmode="stack", xaxis_title="Categoria", yaxis_title="Quantidade de Itens", template="plotly_dark")

total_itens = df_equipamentos["Total"].sum()
num_equipamentos = len(df_equipamentos)

info_fig_total_itens = go.Figure()
info_fig_total_itens.add_trace(go.Indicator(mode="number+delta", value=total_itens))

info_fig_num_equipamentos = go.Figure()
info_fig_num_equipamentos.add_trace(go.Indicator(mode="number+delta", value=num_equipamentos))

# Subplots para exibição da dashboard
fig = sp.make_subplots(
    rows=2, cols=3, subplot_titles=("Total de Itens Inspecionados", "Número de Equipamentos Inspecionados", "Distribuição de Itens", "Distribuição Percentual", "Total de Itens por Categoria"),
    column_widths=[0.33, 0.33, 0.33], row_heights=[0.5, 0.5],
    specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "bar"}], [{"type": "pie"}, {"type": "bar"}, None]]
)

# Adicionar as traces nos subgráficos
fig.add_trace(info_fig_total_itens.data[0], row=1, col=1)
fig.add_trace(info_fig_num_equipamentos.data[0], row=1, col=2)
fig.add_trace(bar_fig.data[0], row=1, col=3)
fig.add_trace(bar_fig.data[1], row=1, col=3)
fig.add_trace(bar_fig.data[2], row=1, col=3)
fig.add_trace(pie_fig.data[0], row=2, col=1)
fig.add_trace(stacked_bar_fig.data[0], row=2, col=2)

# Ajuste do layout do gráfico
fig.update_layout(
    title_text=f"Dashboard de Itens - {local_nome}",
    template="plotly_dark",
    showlegend=False,
    height=900,
    width=1200,
    margin=dict(l=40, r=40, t=40, b=40),
    font=dict(size=12)
)

# Exibir o gráfico na dashboard
st.plotly_chart(fig)


