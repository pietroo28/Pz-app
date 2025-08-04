import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import re
import random

# ---------------------------
DDDs_VALIDOS = {
    '11','12','13','14','15','16','17','18','19',
    '21','22','24','27','28',
    '31','32','33','34','35','37','38',
    '41','42','43','44','45','46',
    '47','48','49',
    '51','53','54','55',
    '61','62','64','63','65','66','67',
    '68','69',
    '71','73','74','75','77','79',
    '81','82','83','84','85','86','87','88','89',
    '91','92','93','94','95','96','97','98','99'
}

def formatar_numero(numero):
    numero = re.sub(r'\D', '', str(numero))
    if len(numero) == 8:
        numero = '9' + numero
    if len(numero) == 9:
        numero = '31' + numero
    if len(numero) == 10 and numero[2] != '9':
        numero = numero[:2] + '9' + numero[2:]
    if len(numero) == 11:
        if numero[:2] in DDDs_VALIDOS and numero[2] == '9':
            return '55' + numero
    if len(numero) == 13 and numero.startswith('55'):
        return numero
    return None

def mostrar_progresso(atual, total):
    barra_tamanho = 20
    progresso = int((atual / total) * barra_tamanho)
    restante = barra_tamanho - progresso
    porcentagem = (atual / total) * 100
    barra = '█' * progresso + '░' * restante
    print(f"📤 Progresso: [{barra}] {porcentagem:.0f}% ({atual}/{total})")

# Variáveis globais
planilha = None
arquivos = []
mensagem_modelo = ""
limite_envio = 0
tempo_min = 10
tempo_max = 20
colunas_planilha = []

def selecionar_planilha():
    global planilha, colunas_planilha
    planilha = filedialog.askopenfilename(
        title="Selecione a planilha", 
        filetypes=[("Excel files", "*.xlsx *.xls")]
    )
    if planilha:
        try:
            df_tmp = pd.read_excel(planilha, skiprows=1)
            colunas_planilha = list(df_tmp.columns.str.strip())
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao ler colunas da planilha: {e}")
            colunas_planilha = []
            listbox_colunas.delete(0, tk.END)
            status_text.set("❌ Erro ao ler colunas da planilha.")
            label_arquivo.config(text="Arquivo: Nenhum")
            return
        
        listbox_colunas.delete(0, tk.END)
        for col in colunas_planilha:
            listbox_colunas.insert(tk.END, col)
        
        status_text.set("✅ Planilha selecionada. Colunas carregadas.")
        label_arquivo.config(text=f"Arquivo: {planilha.split('/')[-1]}")
    else:
        status_text.set("❌ Nenhuma planilha selecionada.")
        listbox_colunas.delete(0, tk.END)
        colunas_planilha.clear()
        label_arquivo.config(text="Arquivo: Nenhum")

def selecionar_midia():
    global arquivos
    arquivos = filedialog.askopenfilenames(title="Selecione imagens e/ou vídeos")
    if arquivos:
        label_midia.config(text=f"Arquivos selecionados: {len(arquivos)}")
        status_text.set("✅ Arquivos de mídia selecionados.")
    else:
        label_midia.config(text="Arquivos selecionados: Nenhum")
        status_text.set("❌ Nenhum arquivo selecionado.")

def inserir_variavel(event):
    # Insere a variável selecionada no campo de mensagem (onde estiver o cursor)
    try:
        selection = listbox_colunas.get(listbox_colunas.curselection())
    except:
        return
    var = "{" + selection + "}"

    if hasattr(definir_mensagem_popup, 'txt_msg_widget') and definir_mensagem_popup.txt_msg_widget.winfo_exists():
        text_widget = definir_mensagem_popup.txt_msg_widget
        pos = text_widget.index(tk.INSERT)
        text_widget.insert(pos, var)
        text_widget.focus()
    else:
        global mensagem_modelo
        mensagem_modelo += var
        label_mensagem.config(text=f"Mensagem definida ({len(mensagem_modelo)} caracteres)")
        status_text.set("✅ Variável adicionada na mensagem (janela mensagem fechada).")

def definir_limite():
    global limite_envio
    limite = simpledialog.askinteger("Limite", "Defina o número máximo de envios:", minvalue=1)
    if limite:
        limite_envio = limite
        label_limite.config(text=f"Limite: {limite_envio}")
        status_text.set(f"✅ Limite definido: {limite_envio}")

def definir_tempo_min():
    global tempo_min
    valor = simpledialog.askinteger("Tempo mínimo", "Defina o tempo mínimo entre envios (segundos):", minvalue=0)
    if valor is not None:
        tempo_min = valor
        label_tempo_min.config(text=f"Tempo mínimo: {tempo_min}s")
        status_text.set(f"✅ Tempo mínimo definido: {tempo_min}s")

def definir_tempo_max():
    global tempo_max
    valor = simpledialog.askinteger("Tempo máximo", "Defina o tempo máximo entre envios (segundos):", minvalue=0)
    if valor is not None:
        tempo_max = valor
        label_tempo_max.config(text=f"Tempo máximo: {tempo_max}s")
        status_text.set(f"✅ Tempo máximo definido: {tempo_max}s")

def iniciar_envio():
    global planilha, arquivos, mensagem_modelo, limite_envio, tempo_min, tempo_max

    if not planilha or not arquivos or not mensagem_modelo or not limite_envio:
        messagebox.showerror("Erro", "Todos os campos devem ser preenchidos antes de iniciar.")
        return

    if tempo_min > tempo_max:
        messagebox.showerror("Erro", "Tempo mínimo não pode ser maior que o máximo.")
        return

    try:
        df = pd.read_excel(planilha, skiprows=1)
        df.columns = df.columns.str.strip()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao ler a planilha: {e}")
        return

    contatos_validos = []
    for _, linha in df.iterrows():
        nome = str(linha.get("Paciente", "")).strip()
        telefones_raw = str(linha.get("Telefones", ""))
        numeros = re.findall(r'\(\d{2}\)\s?\d{4,5}-\d{4}', telefones_raw)
        if nome and numeros:
            contatos_validos.append((nome, numeros, linha))

    if not contatos_validos:
        messagebox.showwarning("Aviso", "Nenhum contato válido encontrado.")
        return

    if limite_envio > len(contatos_validos):
        limite_envio = len(contatos_validos)

    navegador = webdriver.Chrome()
    navegador.get("https://web.whatsapp.com/")
    WebDriverWait(navegador, 600).until(EC.presence_of_element_located((By.ID, "side")))

    enviados = 0
    for nome_completo, numeros, linha_data in contatos_validos:
        if enviados >= limite_envio:
            break
        primeiro_nome = nome_completo.split()[0] if nome_completo else "Paciente"
        for numero_original in numeros:
            telefone = formatar_numero(numero_original)
            if not telefone:
                continue

            navegador.get(f"https://web.whatsapp.com/send?phone={telefone}")

            try:
                WebDriverWait(navegador, 30).until(EC.presence_of_element_located((By.XPATH, '//div[@title="Anexar"]')))
                time.sleep(2)
                navegador.find_element(By.XPATH, '//div[@title="Anexar"]').click()
                time.sleep(1)

                input_arquivo = navegador.find_element(By.XPATH, '//input[@accept="image/*,video/*,video/mp4,video/3gpp,video/quicktime"]')
                input_arquivo.send_keys('\n'.join(arquivos))
                time.sleep(3)

                campo_mensagem = WebDriverWait(navegador, 30).until(
                    EC.presence_of_element_located((By.XPATH, '//footer//*[@contenteditable="true"]'))
                )

                # Formatar mensagem substituindo variáveis entre chaves por valores da linha atual
                msg = mensagem_modelo
                for col in colunas_planilha:
                    valor = str(linha_data.get(col, "")).strip()
                    msg = msg.replace(f"{{{col}}}", valor)
                # Caso falte {nome} usa primeiro nome
                msg = msg.replace("{nome}", primeiro_nome)

                campo_mensagem.send_keys(msg)
                campo_mensagem.send_keys(Keys.ENTER)

                enviados += 1
                mostrar_progresso(enviados, limite_envio)

                tempo_espera = random.uniform(tempo_min, tempo_max)
                print(f"⏳ Aguardando {tempo_espera:.1f}s...")
                time.sleep(tempo_espera)
                break
            except Exception as e:
                print(f"❌ Erro com {primeiro_nome} ({telefone}): {e}")

    navegador.quit()
    messagebox.showinfo("Concluído", "Envio finalizado com sucesso!")

# ---------------------------
# Interface
# ---------------------------
# ... (mantém o código anterior até a parte da interface)

root = tk.Tk()
root.title("Envio de Mídias com WhatsApp")
root.geometry("700x500")  # mais largo para caber duas colunas
root.resizable(False, False)
root.config(bg="#f7f7f7")

status_text = tk.StringVar()
status_text.set("🔒 Aguardando configuração...")

# Título
tk.Label(root, text="📤 Envio de Mídias WhatsApp", font=("Helvetica", 16, "bold"), bg="#f7f7f7").pack(pady=10)

# Frame principal com duas colunas
frame_principal = tk.Frame(root, bg="#f7f7f7")
frame_principal.pack(padx=20, pady=10, fill="both", expand=True)

# Frame botoes - coluna 0
frame_botoes = tk.Frame(frame_principal, bg="#f7f7f7")
frame_botoes.grid(row=0, column=0, sticky="nw")

tk.Button(frame_botoes, text="1. Selecionar Planilha", width=25, command=selecionar_planilha).grid(row=0, column=0, pady=4)
tk.Button(frame_botoes, text="2. Selecionar Mídia", width=25, command=selecionar_midia).grid(row=1, column=0, pady=4)
tk.Button(frame_botoes, text="3. Definir Mensagem", width=25, command=lambda: definir_mensagem_popup()).grid(row=2, column=0, pady=4)
tk.Button(frame_botoes, text="4. Definir Limite", width=25, command=definir_limite).grid(row=3, column=0, pady=4)
tk.Button(frame_botoes, text="5. Definir Tempo Mínimo", width=25, command=definir_tempo_min).grid(row=4, column=0, pady=4)
tk.Button(frame_botoes, text="6. Definir Tempo Máximo", width=25, command=definir_tempo_max).grid(row=5, column=0, pady=4)
tk.Button(frame_botoes, text="🚀 Iniciar Envio", bg="green", fg="white", font=("Helvetica", 10, "bold"),
          width=25, command=iniciar_envio).grid(row=6, column=0, pady=15)

# Frame informações - coluna 1
frame_info = tk.Frame(frame_principal, bg="#f7f7f7")
frame_info.grid(row=0, column=1, sticky="nw", padx=40)

label_arquivo = tk.Label(frame_info, text="Arquivo: Nenhum", font=("Arial", 12), bg="#f7f7f7", anchor="w")
label_arquivo.pack(anchor="w", pady=4)

label_midia = tk.Label(frame_info, text="Arquivos selecionados: Nenhum", font=("Arial", 12), bg="#f7f7f7", anchor="w")
label_midia.pack(anchor="w", pady=4)

label_mensagem = tk.Label(frame_info, text="Mensagem: Nenhuma", font=("Arial", 12), bg="#f7f7f7", anchor="w")
label_mensagem.pack(anchor="w", pady=4)

label_limite = tk.Label(frame_info, text="Limite: 0", font=("Arial", 12), bg="#f7f7f7", anchor="w")
label_limite.pack(anchor="w", pady=4)

label_tempo_min = tk.Label(frame_info, text=f"Tempo mínimo: {tempo_min}s", font=("Arial", 12), bg="#f7f7f7", anchor="w")
label_tempo_min.pack(anchor="w", pady=4)

label_tempo_max = tk.Label(frame_info, text=f"Tempo máximo: {tempo_max}s", font=("Arial", 12), bg="#f7f7f7", anchor="w")
label_tempo_max.pack(anchor="w", pady=4)

# Frame colunas da planilha embaixo ocupando as duas colunas
frame_colunas = tk.Frame(root, bg="#f7f7f7")
frame_colunas.pack(padx=20, pady=10, fill='both')

tk.Label(frame_colunas, text="Colunas da Planilha (clique para inserir variável na mensagem):",
         font=("Arial", 10, "italic"), bg="#f7f7f7", anchor="w").pack(anchor="w")

listbox_colunas = tk.Listbox(frame_colunas, height=6)
listbox_colunas.pack(fill='x', pady=5)
listbox_colunas.bind("<Double-Button-1>", inserir_variavel)

# Status
label_status = tk.Label(root, textvariable=status_text, font=("Arial", 10, "italic"), fg="blue", bg="#f7f7f7")
label_status.pack(pady=10)

# (Aqui segue o resto do código, incluindo definir_mensagem_popup e root.mainloop())
# Janela popup para definir mensagem
def definir_mensagem_popup():
    global mensagem_modelo
    global definir_mensagem_popup

    definir_mensagem_popup = tk.Toplevel(root)
    definir_mensagem_popup.title("Definir Mensagem")
    definir_mensagem_popup.geometry("450x300")
    definir_mensagem_popup.resizable(False, False)

    tk.Label(definir_mensagem_popup, text="Digite a mensagem abaixo (use {nome} ou {colunas}):", font=("Arial", 10)).pack(pady=5)
    txt_msg = tk.Text(definir_mensagem_popup, width=55, height=10)
    txt_msg.pack(padx=10)
    txt_msg.insert(tk.END, mensagem_modelo)
    definir_mensagem_popup.txt_msg_widget = txt_msg

    def salvar_mensagem():
        global mensagem_modelo
        mensagem_modelo = txt_msg.get("1.0", tk.END).strip()
        if mensagem_modelo:
            label_mensagem.config(text=f"Mensagem definida ({len(mensagem_modelo)} caracteres)")
            status_text.set("✅ Mensagem definida.")
        else:
            label_mensagem.config(text="Mensagem: Nenhuma")
            status_text.set("❌ Mensagem vazia.")
        definir_mensagem_popup.destroy()

    tk.Button(definir_mensagem_popup, text="Salvar", command=salvar_mensagem).pack(pady=10)

root.mainloop()