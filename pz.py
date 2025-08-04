# CÓDIGO COMPLETO ATUALIZADO
# Inclui log lateral, seleção dinâmica de colunas, tempo entre mensagens e inserção de variáveis na mensagem

import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, scrolledtext
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import re
import random
import urllib

# --- Variáveis globais ---
DDDs_VALIDOS = {...}  # Substitua pelo dicionário completo de DDDs
planilha = None
colunas_planilha = []
mensagem_modelo = ""
limite_envio = 0
tempo_min = 10
tempo_max = 20
arquivos = []

# --- Funções ---
def log(texto):
    log_area.insert(tk.END, texto + "\n")
    log_area.see(tk.END)

def formatar_numero(numero):
    numero = re.sub(r'\D', '', str(numero))
    if len(numero) == 8:
        numero = '9' + numero
    if len(numero) == 9:
        numero = '31' + numero
    if len(numero) == 10 and numero[2] != '9':
        numero = numero[:2] + '9' + numero[2:]
    if len(numero) == 11 and numero[:2] in DDDs_VALIDOS and numero[2] == '9':
        return '55' + numero
    if len(numero) == 13 and numero.startswith('55'):
        return numero
    return None

def selecionar_planilha():
    global planilha, colunas_planilha
    planilha = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    if planilha:
        try:
            df = pd.read_excel(planilha, skiprows=1)
            df.columns = df.columns.str.strip()
            colunas_planilha = list(df.columns)
            listbox_colunas.delete(0, tk.END)
            for col in colunas_planilha:
                listbox_colunas.insert(tk.END, col)
            label_planilha.config(text=f"🗂 Planilha: {planilha.split('/')[-1]}")
            log("✅ Planilha e colunas carregadas.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao ler a planilha: {e}")
            log("❌ Erro ao carregar a planilha.")

def selecionar_midia():
    global arquivos
    arquivos = filedialog.askopenfilenames(filetypes=[("Imagens e Vídeos", "*.*")])
    if arquivos:
        label_midia.config(text=f"Mídia: {len(arquivos)} arquivos")
        log("✅ Mídias selecionadas.")

def inserir_variavel(event):
    try:
        selecionada = listbox_colunas.get(listbox_colunas.curselection())
    except:
        return
    variavel = f"{{{selecionada}}}"
    if hasattr(definir_mensagem_popup, 'txt_msg_widget'):
        widget = definir_mensagem_popup.txt_msg_widget
        widget.insert(tk.INSERT, variavel)
        widget.focus()

def definir_mensagem_popup():
    global definir_mensagem_popup, mensagem_modelo

    definir_mensagem_popup = tk.Toplevel(root)
    definir_mensagem_popup.title("Definir Mensagem")
    definir_mensagem_popup.geometry("450x300")
    definir_mensagem_popup.resizable(False, False)

    tk.Label(definir_mensagem_popup, text="Digite a mensagem (use {coluna} como variável):").pack(pady=5)
    txt_msg = tk.Text(definir_mensagem_popup, width=55, height=10)
    txt_msg.pack(padx=10)
    txt_msg.insert(tk.END, mensagem_modelo)
    definir_mensagem_popup.txt_msg_widget = txt_msg

    def salvar():
        global mensagem_modelo
        mensagem_modelo = txt_msg.get("1.0", tk.END).strip()
        label_mensagem.config(text=f"💬 Mensagem ({len(mensagem_modelo)} chars)")
        log("✅ Mensagem personalizada salva.")
        definir_mensagem_popup.destroy()

    tk.Button(definir_mensagem_popup, text="Salvar", command=salvar).pack(pady=10)

def definir_limite():
    global limite_envio
    limite = simpledialog.askinteger("Limite", "Número máximo de envios:", minvalue=1)
    if limite:
        limite_envio = limite
        label_limite.config(text=f"📊 Limite: {limite_envio}")
        log(f"✅ Limite definido: {limite_envio}")

def definir_tempo_min():
    global tempo_min
    valor = simpledialog.askinteger("Tempo mínimo", "Tempo mínimo (segundos):", minvalue=1)
    if valor:
        tempo_min = valor
        label_tempo_min.config(text=f"⏱ Mínimo: {tempo_min}s")
        log(f"✅ Tempo mínimo definido: {tempo_min}s")

def definir_tempo_max():
    global tempo_max
    valor = simpledialog.askinteger("Tempo máximo", "Tempo máximo (segundos):", minvalue=1)
    if valor:
        tempo_max = valor
        label_tempo_max.config(text=f"⏱ Máximo: {tempo_max}s")
        log(f"✅ Tempo máximo definido: {tempo_max}s")

def iniciar_envio():
    global planilha, mensagem_modelo, limite_envio

    if not planilha or not mensagem_modelo or not arquivos or not limite_envio:
        messagebox.showerror("Erro", "Todos os campos devem estar preenchidos.")
        return

    try:
        df = pd.read_excel(planilha, skiprows=1)
        df.columns = df.columns.str.strip()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao ler planilha: {e}")
        return

    contatos = []
    for _, linha in df.iterrows():
        nome = str(linha.get("Paciente", "")).strip()
        telefones = str(linha.get("Telefones", ""))
        numeros = re.findall(r'\(\d{2}\)\s?\d{4,5}-\d{4}', telefones)
        if nome and numeros:
            contatos.append((nome, numeros, linha))

    if not contatos:
        log("⚠ Nenhum contato válido.")
        return

    navegador = webdriver.Chrome()
    navegador.get("https://web.whatsapp.com/")
    log("🔐 Aguardando login no WhatsApp Web...")
    WebDriverWait(navegador, 600).until(EC.presence_of_element_located((By.ID, "side")))
    log("✅ WhatsApp Web conectado.")

    enviados = 0
    for nome_completo, numeros, dados in contatos:
        if enviados >= limite_envio:
            break
        for numero in numeros:
            telefone = formatar_numero(numero)
            if not telefone:
                log(f"❌ Número inválido: {numero}")
                continue

            navegador.get(f"https://web.whatsapp.com/send?phone={telefone}")
            try:
                WebDriverWait(navegador, 30).until(EC.presence_of_element_located((By.XPATH, '//div[@title="Anexar"]')))
                navegador.find_element(By.XPATH, '//div[@title="Anexar"]').click()
                input_arquivo = navegador.find_element(By.XPATH, '//input[@accept="image/*,video/*,video/mp4,video/3gpp,video/quicktime"]')
                input_arquivo.send_keys('\n'.join(arquivos))
                time.sleep(2)

                campo = WebDriverWait(navegador, 30).until(EC.presence_of_element_located((By.XPATH, '//footer//*[@contenteditable="true"]')))
                mensagem_final = mensagem_modelo
                for col in colunas_planilha:
                    valor = str(dados.get(col, "")).strip()
                    mensagem_final = mensagem_final.replace(f"{{{col}}}", valor)
                mensagem_final = mensagem_final.replace("{nome}", nome_completo.split()[0])

                campo.send_keys(mensagem_final)
                campo.send_keys(Keys.ENTER)
                enviados += 1
                log(f"📤 Enviado para {nome_completo} - {telefone} [{enviados}/{limite_envio}]")
                time.sleep(random.uniform(tempo_min, tempo_max))
                break
            except Exception as e:
                log(f"⚠ Erro com {telefone}: {e}")
    navegador.quit()
    log("🏁 Envio finalizado.")

# --- Interface Gráfica ---
root = tk.Tk()
root.title("📤 Envio de Mídias WhatsApp")
root.geometry("900x500")
root.resizable(False, False)

frame_left = tk.Frame(root, padx=10, pady=10)
frame_left.pack(side="left", fill="y")

tk.Button(frame_left, text="1. Selecionar Planilha", width=25, command=selecionar_planilha).pack(pady=5)
tk.Button(frame_left, text="2. Selecionar Mídia", width=25, command=selecionar_midia).pack(pady=5)
tk.Button(frame_left, text="3. Definir Mensagem", width=25, command=definir_mensagem_popup).pack(pady=5)
tk.Button(frame_left, text="4. Definir Limite", width=25, command=definir_limite).pack(pady=5)
tk.Button(frame_left, text="5. Tempo entre envios", width=25, command=lambda: [definir_tempo_min(), definir_tempo_max()]).pack(pady=5)
tk.Button(frame_left, text="🚀 Iniciar Envio", width=25, bg="green", fg="white", command=iniciar_envio).pack(pady=20)

label_planilha = tk.Label(frame_left, text="🗂 Planilha: Nenhuma")
label_planilha.pack()
label_midia = tk.Label(frame_left, text="🎞 Mídia: Nenhuma")
label_midia.pack()
label_mensagem = tk.Label(frame_left, text="💬 Mensagem: Nenhuma")
label_mensagem.pack()
label_limite = tk.Label(frame_left, text="📊 Limite: Não definido")
label_limite.pack()
label_tempo_min = tk.Label(frame_left, text="⏱ Mínimo: 10s")
label_tempo_min.pack()
label_tempo_max = tk.Label(frame_left, text="⏱ Máximo: 20s")
label_tempo_max.pack()

frame_right = tk.Frame(root, padx=5, pady=5)
frame_right.pack(side="left", fill="both", expand=True)

log_area = scrolledtext.ScrolledText(frame_right, wrap=tk.WORD, width=65, height=14)
log_area.pack(fill="x")

tk.Label(frame_right, text="🔧 Variáveis disponíveis (clique para inserir):").pack()
listbox_colunas = tk.Listbox(frame_right, height=14)
listbox_colunas.pack(fill="both", expand=True)
listbox_colunas.bind("<Double-1>", inserir_variavel)


root.mainloop()