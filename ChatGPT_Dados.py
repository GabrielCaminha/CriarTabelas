import openai
import tkinter as tk
from tkinter import filedialog
import pandas as pd
import sqlite3

def get_local_name(df):
    """Função para recuperar o nome do local lido da planilha."""
    return df.iloc[2, 0] if pd.notna(df.iloc[2, 0]) else "Local não informado"

def get_equipamento_name(df):
    """Função para recuperar o nome do equipamento a partir da célula A7."""
    cell_value = df.iloc[6, 0] if pd.notna(df.iloc[6, 0]) else ""
    if ":" in cell_value:
        return cell_value.split(":", 1)[1].strip()
    return "Equipamento não informado"

# Função para selecionar o arquivo
root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename(title="Selecione a planilha Excel", filetypes=[("Excel files", "*.xls;*.xlsx")])

if not file_path:
    print("Nenhum arquivo selecionado.")
    exit()

# Ler a planilha
df = pd.read_excel(file_path, sheet_name=0, header=None)

# Obter o nome do local
local_name = get_local_name(df)

# Obter o nome do equipamento
equipamento_name = get_equipamento_name(df)

linha_equipamentos = 18

# Coletar equipamentos
equipamentos = []
coluna_index = 7  # Começar na coluna H
while coluna_index < df.shape[1] and pd.notna(df.iloc[linha_equipamentos, coluna_index]):
    equipamentos.append(df.iloc[linha_equipamentos, coluna_index])
    coluna_index += 1

# Criar dicionário de itens por equipamento
itens_por_equipamento = {equip: [] for equip in equipamentos}
itens = df.iloc[19:, 1].dropna()

# Associar itens aos equipamentos
for index, item in enumerate(itens):
    item_nome = str(item).strip().lower()
    if not item_nome or item_nome == "avaliação final dos equipamentos":
        break
    row = df.iloc[19 + index]
    for equip_idx, equip in enumerate(equipamentos, start=7):
        valor = row[equip_idx]
        if pd.notna(valor) and isinstance(valor, str) and valor.strip().lower() != "na":
            itens_por_equipamento[equip].append(item_nome)

# Configurar API do OpenAI (alterar a chave API para o codigo final)
API_KEY = "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"
client = openai.OpenAI(api_key=API_KEY)

# Criar o texto dos dados para os equipamentos
dados_equipamentos_texto = ""
for equip, itens in itens_por_equipamento.items():
    if itens:
        dados_equipamentos_texto += f"Equipamento: {equip}\n" + "\n".join([f"- {item}" for item in itens]) + "\n\n"

# Criar o prompt com base no formato original fornecido
prompt = f"""
Classifique os seguintes itens para cada equipamento nas categorias abaixo, nao adicione nenhuma informação a mais alem do que é pedido, leia todos os itens de cada equipamento, eles podem ser diferentes, o seu total de itens de cada equipamento deve ser igual ao informado na entrada:

- **Segurança**: Itens essenciais para a segurança e prevenção de riscos.
- **Importante**: Itens necessários para o funcionamento adequado, mas sem impacto direto na segurança.
- **Normal**: Itens comuns, sem impacto crítico.

Liste a quantidade de itens em cada categoria por equipamento no formato abaixo, considerando que os itens podem variar por equipamento, a sua resposta deve ser exatamente como no formato abaixo, nada mais nada menos:

Equipamento: <nome do equipamento>
Segurança: <quantidade>
Importante: <quantidade>
Normal: <quantidade>

Dados a serem analisados:
{dados_equipamentos_texto}
"""

# Enviar para o GPT
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "system", "content": "Você é um assistente de análise de equipamentos."},
              {"role": "user", "content": prompt}]
)

# Salvar resposta em banco de dados SQLite
response_content = response.choices[0].message.content

# Criar conexão com o banco de dados
conn = sqlite3.connect('equipamentos.db')
cursor = conn.cursor()

# Criar a tabela 
cursor.execute('''CREATE TABLE IF NOT EXISTS itens_equipamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    local_name TEXT,
                    equipamento_name TEXT,
                    categoria TEXT,
                    quantidade INTEGER
                 )''')

# Inserir dados na tabela
for line in response_content.split("\n"):
    if "Equipamento:" in line:
        equipamento = line.split(":")[1].strip()
    elif "Segurança:" in line:
        categoria = "Segurança"
        quantidade = int(line.split(":")[1].strip())
        cursor.execute("INSERT INTO itens_equipamentos (local_name, equipamento_name, categoria, quantidade) VALUES (?, ?, ?, ?)", 
                       (local_name, equipamento, categoria, quantidade))
    elif "Importante:" in line:
        categoria = "Importante"
        quantidade = int(line.split(":")[1].strip())
        cursor.execute("INSERT INTO itens_equipamentos (local_name, equipamento_name, categoria, quantidade) VALUES (?, ?, ?, ?)", 
                       (local_name, equipamento, categoria, quantidade))
    elif "Normal:" in line:
        categoria = "Normal"
        quantidade = int(line.split(":")[1].strip())
        cursor.execute("INSERT INTO itens_equipamentos (local_name, equipamento_name, categoria, quantidade) VALUES (?, ?, ?, ?)", 
                       (local_name, equipamento, categoria, quantidade))

# Commit e fechar conexão
conn.commit()
conn.close()

print("Resposta processada e salva no banco de dados com sucesso!")
