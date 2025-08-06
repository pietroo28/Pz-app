import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import urllib
import time
import re
import random
import threading

DDDs_VALIDOS = {
    '11', '12', '13', '14', '15', '16', '17', '18', '19',
    '21', '22', '24', '27', '28',
    '31', '32', '33', '34', '35', '37', '38',
    '41', '42', '43', '44', '45', '46',
    '47', '48', '49',
    '51', '53', '54', '55',
    '61', '62', '63', '64',
    '65', '66', '67',
    '68', '69',
    '71', '73', '74', '75', '77', '79',
    '81', '82', '83', '84', '85', '86', '87', '88', '89',
    '91', '92', '93', '94', '95', '96', '97', '98', '99'
}

def formatar_numero(numero):
    numero = re.sub(r'\D', '', str(numero))
    if len(numero) < 8 or len(numero) > 13:
        return None
    if len(numero) == 8:
        numero = '9' + numero
    if len(numero) == 9:
        numero = '31' + numero
    if len(numero) == 10 and numero[2] != '9':
        return None
    if len(numero) == 10 and numero[2] == '9':
        numero = numero[:2] + '9' + numero[2:]
    if len(numero) == 11:
        ddd = numero[:2]
        if ddd not in DDDs_VALIDOS or numero[2] != '9':
            return None
        return numero
    if len(numero) == 13 and numero.startswith('55'):
        ddd = numero[2:4]
        if ddd not in DDDs_VALIDOS or numero[4] != '9':
            return None
        return numero[2:]
    return None

def mostrar_progresso(atual, total):
    barra_tamanho = 20
    progresso = int((atual / total) * barra_tamanho)
    restante = barra_tamanho - progresso
    porcentagem = (atual / total) * 100
    barra = '█' * progresso + '░' * restante
    print(f"📤 Progresso: [{barra}] {porcentagem:.0f}% ({atual}/{total})")

class App:
    def __init__(self, master):
        self.master = master
        self.master.title("Envio de Mensagens WhatsApp")
        self.df = None

        tk.Button(master, text="📂 Selecionar Planilha", command=self.selecionar_planilha).grid(row=0, column=0, padx=10, pady=10)

        self.label_colunas = tk.Label(master, text="Colunas disponíveis:")
        self.label_colunas.grid(row=1, column=0, sticky="w", padx=10)
        self.text_colunas = scrolledtext.ScrolledText(master, height=5, width=50)
        self.text_colunas.grid(row=2, column=0, padx=10, columnspan=2)

        self.label_total_pacientes = tk.Label(master, text="Total de pacientes: 0")
        self.label_total_pacientes.grid(row=3, column=0, sticky="w", padx=10)

        tk.Label(master, text="Mensagem com variáveis:").grid(row=4, column=0, sticky="w", padx=10)
        self.mensagem_entry = tk.Text(master, height=5, width=50)
        self.mensagem_entry.grid(row=5, column=0, padx=10, pady=5, columnspan=2)

        tk.Label(master, text="Tempo mínimo (s):").grid(row=6, column=0, sticky="w", padx=10)
        tk.Label(master, text="Tempo máximo (s):").grid(row=7, column=0, sticky="w", padx=10)
        self.tempo_min = tk.Entry(master)
        self.tempo_max = tk.Entry(master)
        self.tempo_min.grid(row=6, column=1, padx=10)
        self.tempo_max.grid(row=7, column=1, padx=10)

        tk.Label(master, text="Limite de mensagens a enviar:").grid(row=8, column=0, sticky="w", padx=10)
        self.limite_entry = tk.Entry(master)
        self.limite_entry.grid(row=8, column=1, padx=10)

        tk.Button(master, text="🚀 Iniciar Envio", command=self.iniciar_envio_thread).grid(row=9, column=0, columnspan=2, pady=15)

    def selecionar_planilha(self):
        arquivo = filedialog.askopenfilename(title="Selecione a planilha", filetypes=[("Excel files", "*.xlsx")])
        if not arquivo:
            messagebox.showerror("Erro", "Nenhum arquivo selecionado.")
            return

        try:
            self.df = pd.read_excel(arquivo, skiprows=1)
            self.df.columns = self.df.columns.str.strip()
            colunas = self.df.columns.tolist()

            self.text_colunas.delete("1.0", tk.END)
            for col in colunas:
                self.text_colunas.insert(tk.END, f"{col}\n")

            total_pacientes = len(self.df)
            self.label_total_pacientes.config(text=f"Total de pacientes: {total_pacientes}")
            messagebox.showinfo("Planilha Carregada", f"Total de pacientes: {total_pacientes}")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao ler planilha: {e}")

    def iniciar_envio_thread(self):
        threading.Thread(target=self.iniciar_envio).start()

    def iniciar_envio(self):
        if self.df is None:
            messagebox.showerror("Erro", "Nenhuma planilha carregada.")
            return

        if not any("paciente" in c.lower() for c in self.df.columns):
            messagebox.showerror("Erro", "A planilha precisa ter uma coluna 'Paciente'.")
            return
        if not any("telefone" in c.lower() for c in self.df.columns):
            messagebox.showerror("Erro", "A planilha precisa ter uma coluna 'Telefones'.")
            return

        mensagem = self.mensagem_entry.get("1.0", tk.END).strip()
        if not mensagem:
            messagebox.showerror("Erro", "Digite uma mensagem personalizada.")
            return

        try:
            tempo_min = int(self.tempo_min.get())
            tempo_max = int(self.tempo_max.get())
            limite = int(self.limite_entry.get())
        except:
            messagebox.showerror("Erro", "Verifique os campos numéricos.")
            return

        if tempo_min > tempo_max:
            messagebox.showerror("Erro", "Tempo mínimo deve ser menor que o máximo.")
            return

        navegador = webdriver.Chrome()
        navegador.get("https://web.whatsapp.com/")
        print("⏳ Aguardando login no WhatsApp Web...")
        WebDriverWait(navegador, 600).until(EC.presence_of_element_located((By.ID, "side")))
        print("✅ WhatsApp carregado!")

        enviados = 0
        total_para_enviar = min(len(self.df), limite)

        for idx, linha in self.df.iterrows():
            if enviados >= limite:
                break

            try:
                nome_completo = str(linha.get("Paciente", "")).strip()
                primeiro_nome = nome_completo.split()[0] if nome_completo else "Paciente"
                telefones = str(linha.get("Telefones", "")).strip()
                numeros = re.findall(r'\(\d{2}\)\s?\d{4,5}-\d{4}', telefones)
                if not numeros:
                    print(f"❌ {primeiro_nome}: Nenhum número encontrado.")
                    continue

                dados = {col.strip(): str(linha[col]) for col in self.df.columns if pd.notna(linha[col])}
                dados["nome"] = primeiro_nome
                dados["nome_completo"] = nome_completo

                # ➕ Extrair data_formatada e hora_formatada
                data_bruta = str(linha.get("Data", "")).strip()
                match = re.match(r"(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})", data_bruta)
                if match:
                    dados["data_formatada"] = match.group(1)
                    dados["hora_formatada"] = match.group(2)
                else:
                    dados["data_formatada"] = "DATA_INVÁLIDA"
                    dados["hora_formatada"] = "HORA_INVÁLIDA"

                numero_valido_enviado = False

                for numero in numeros:
                    numero_formatado = formatar_numero(numero)
                    if not numero_formatado:
                        print(f"❌ {primeiro_nome}: Número inválido {numero}")
                        continue

                    try:
                        mensagem_final = mensagem.format(**dados)
                    except KeyError as e:
                        print(f"⚠ {primeiro_nome}: Variável ausente na planilha: {e}")
                        break

                    texto = urllib.parse.quote(mensagem_final)
                    link = f"https://web.whatsapp.com/send?phone=55{numero_formatado}&text={texto}"
                    navegador.get(link)

                    WebDriverWait(navegador, 20).until(
                        EC.presence_of_element_located((By.XPATH, '//footer//*[@contenteditable="true"]'))
                    )
                    time.sleep(5)
                    campo_mensagem = navegador.find_element(By.XPATH, '//footer//*[@contenteditable="true"]')
                    campo_mensagem.send_keys(Keys.ENTER)

                    enviados += 1
                    numero_valido_enviado = True
                    mostrar_progresso(enviados, total_para_enviar)

                    tempo_espera = random.uniform(tempo_min, tempo_max)
                    print(f"⏳ Aguardando {tempo_espera:.1f} segundos antes do próximo envio...\n")
                    time.sleep(tempo_espera)

                    if enviados >= limite:
                        break

                if not numero_valido_enviado:
                    print(f"⚠ {primeiro_nome}: Nenhum número válido foi enviado.")

            except Exception as e:
                print(f"⚠ Erro com {primeiro_nome}: {e}")
                continue

        navegador.quit()
        print(f"\n🏁 Envio concluído! Total enviado: {enviados}")
        messagebox.showinfo("Finalizado", f"Envio concluído com {enviados} mensagens.")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
