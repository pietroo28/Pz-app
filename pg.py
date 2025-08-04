import tkinter as tk
from tkinter import messagebox, filedialog
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import urllib
import pandas as pd
import re
import random
import threading

print("✅ Script iniciado")


def formatar_numero(numero):
    numero = re.sub(r'\D', '', str(numero))
    if len(numero) == 8:
        numero = '9' + numero
    if len(numero) == 9:
        numero = '31' + numero
    if len(numero) == 10 and numero[2] != '9':
        numero = numero[:2] + '9' + numero[2:]
    if len(numero) == 11:
        return '55' + numero
    if len(numero) == 13 and numero.startswith('55'):
        return numero
    return None


def fechar_modal_sim_entendi(driver):
    for _ in range(10):
        try:
            botoes = driver.find_elements(By.XPATH, "//button[contains(text(), 'Sim, Entendi')]")
            if botoes:
                for botao in botoes:
                    if botao.is_displayed() and botao.is_enabled():
                        driver.execute_script("arguments[0].scrollIntoView(true);", botao)
                        driver.execute_script("arguments[0].click();", botao)
                        print("✅ Modal 'Sim, Entendi' fechado.")
                        time.sleep(1)
                        return
        except Exception as e:
            print(f"Tentativa de fechar modal falhou: {e}")
        time.sleep(1)


def pegar_chave_pix(driver_sistema, codigo_paciente, data_vencimento):
    try:
        # Tentar clicar no botão "limpar seleção"
        try:
            limpar_selecao = WebDriverWait(driver_sistema, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="paciente_off"]'))
            )
            limpar_selecao.click()
            print("🔄 Seleção anterior limpa.")
            time.sleep(2)
        except (TimeoutException, NoSuchElementException):
            print("⚠ Nenhuma seleção anterior encontrada.")

        # Buscar o paciente
        campo_busca = WebDriverWait(driver_sistema, 10).until(
            EC.element_to_be_clickable((By.ID, "codgo"))
        )
        campo_busca.clear()
        campo_busca.click()
        print(f"🔎 Inserindo código do paciente: {codigo_paciente}")
        campo_busca.send_keys(codigo_paciente + Keys.ENTER)
        time.sleep(3)

        fechar_modal_sim_entendi(driver_sistema)
        time.sleep(3)

        # Acessar página de pagamentos
        WebDriverWait(driver_sistema, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="header"]/div/div/div/ul/li[2]/a'))
        ).click()
        time.sleep(2)

        # Procurar linha da parcela com a data certa
        linhas = driver_sistema.find_elements(By.XPATH, "//table//tr")

        encontrou = False
        for linha in linhas:
            try:
                if data_vencimento in linha.text:
                    botao_pix = linha.find_element(By.XPATH, ".//img[contains(@src, 'pix')]")
                    driver_sistema.execute_script("arguments[0].scrollIntoView(true);", botao_pix)
                    botao_pix.click()
                    print(f"✅ Botão PIX clicado para data {data_vencimento}")
                    encontrou = True
                    break
            except Exception as e:
                print(f"⚠ Erro ao processar linha da tabela: {e}")

        if not encontrou:
            print(f"❌ Não foi encontrada uma linha com data {data_vencimento}")
            return None

        # Esperar o modal carregar e pegar chave
        chave_pix_input = WebDriverWait(driver_sistema, 10).until(
            EC.presence_of_element_located((By.ID, "codcopiacola"))
        )
        chave_pix = chave_pix_input.get_attribute("value")

        # Fechar modal
        try:
            fechar_botao = WebDriverWait(driver_sistema, 5).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[4]/div/div/div[1]/button'))
            )
            fechar_botao.click()
            print("✅ Modal PIX fechado.")
            time.sleep(2)
        except TimeoutException:
            print("⚠ Botão para fechar modal PIX não encontrado.")

        return chave_pix

    except Exception as e:
        print(f"❌ Erro ao pegar chave PIX para código {codigo_paciente}: {e}")
        return None


def enviar_mensagens_whatsapp(driver_whatsapp, nome, telefone, mensagens):
    for mensagem in mensagens:
        texto = urllib.parse.quote(mensagem)
        link = f"https://web.whatsapp.com/send?phone={telefone}&text={texto}"
        driver_whatsapp.get(link)

        try:
            WebDriverWait(driver_whatsapp, 20).until(
                EC.presence_of_element_located((By.XPATH, "//footer//div[@contenteditable='true'][@data-tab='10']"))
            )
            time.sleep(5)

            campo_mensagem = driver_whatsapp.find_element(By.XPATH, "//footer//div[@contenteditable='true'][@data-tab='10']")
            campo_mensagem.send_keys(Keys.ENTER)
            print(f"✅ Mensagem enviada para {nome} ({telefone})")
            time.sleep(10)
        except Exception as e:
            print(f"❌ Erro ao enviar mensagem para {nome}: {e}")
            # Tenta continuar para próxima mensagem


def processo_envio(min_seg, max_seg, arquivo_excel, status_text):
    driver_sistema = webdriver.Chrome()
    driver_sistema.get("https://software2.orthodonticbrasil.com/index")
    status_text.set("🔑 Faça login manual no sistema e depois clique em 'Continuar'")
    app.btn_continuar_sistema.config(state=tk.NORMAL)

    while not app.continuar_login_sistema:
        time.sleep(3)
    app.continuar_login_sistema = False
    app.btn_continuar_sistema.config(state=tk.DISABLED)

    driver_whatsapp = webdriver.Chrome()
    driver_whatsapp.get("https://web.whatsapp.com/")
    status_text.set("🔒 Faça login no WhatsApp Web e depois clique em 'Continuar'")
    app.btn_continuar_whatsapp.config(state=tk.NORMAL)

    while not app.continuar_login_whatsapp:
        time.sleep(3)
    app.continuar_login_whatsapp = False
    app.btn_continuar_whatsapp.config(state=tk.DISABLED)

    contatos_df = pd.read_excel(arquivo_excel, skiprows=1)

    colunas_esperadas = ["Cód", "Paciente", "Telefone", "Parcela", "Valor", "Data do Vencimento"]
    if not all(col in contatos_df.columns for col in colunas_esperadas):
        messagebox.showerror("Erro", f"Planilha deve conter as colunas: {', '.join(colunas_esperadas)}")
        driver_sistema.quit()
        driver_whatsapp.quit()
        status_text.set("❌ Erro na planilha. Processo cancelado.")
        return

    for i in range(len(contatos_df)):
        try:
            codigo_paciente = str(contatos_df.loc[i, "Cód"]).strip()
            nome_completo = str(contatos_df.loc[i, "Paciente"]).strip()
            nome = nome_completo.split()[0]
            telefones_raw = str(contatos_df.loc[i, "Telefone"])
            telefones = re.findall(r'\(\d{2}\)\s?\d{4,5}-\d{4}', telefones_raw)

            numero_parcela = str(contatos_df.loc[i, "Parcela"]).strip()
            valor_parcela = str(contatos_df.loc[i, "Valor"]).strip()
            data_vencimento = str(contatos_df.loc[i, "Data do Vencimento"]).strip()

            status_text.set(f"🔄 Processando {nome_completo} | Código: {codigo_paciente}")
            print(f"\n🔄 Processando {nome_completo} | Código: {codigo_paciente}")

            if not telefones:
                print(f"⚠ Sem telefone para {nome}")
                continue

            chave_pix = pegar_chave_pix(driver_sistema, codigo_paciente, data_vencimento)
            if not chave_pix:
                print(f"⚠ Não foi possível obter chave PIX para {nome}")
                continue

            mensagem_1 = f"""Olá {nome}, aqui é a Olívia da OrthoDontic. 😃

O vencimento da sua parcela número {numero_parcela} de R${valor_parcela}0 é dia {data_vencimento}.

‼Aproveite o desconto de pontualidade pagando até o vencimento.

Segue abaixo o código PIX QRcode para realizar o pagamento.

⚠ Necessário copiar todo o conteúdo para colar no seu app do banco (a parte azul e a preta com link) 👇:

Desconsidere caso pago."""

            mensagem_2 = chave_pix

            # Aqui enviamos para todos os telefones da linha
            for tel in telefones:
                telefone_formatado = formatar_numero(tel)
                if not telefone_formatado:
                    print(f"⚠ Telefone inválido para {nome}: {tel}")
                    continue

                enviar_mensagens_whatsapp(driver_whatsapp, nome, telefone_formatado, [mensagem_1, mensagem_2])

                wait_time = random.randint(min_seg, max_seg)
                status_text.set(f"Aguardando {wait_time} segundos antes da próxima mensagem...")
                print(f"⏳ Aguardando {wait_time} segundos...")
                time.sleep(wait_time)

        except Exception as e:
            print(f"❌ Erro ao processar linha {i}: {e}")
            continue

    driver_sistema.quit()
    driver_whatsapp.quit()
    status_text.set("✅ Processo finalizado!")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Envio de Mensagens com PIX")
        self.geometry("720x450")
        self.continuar_login_sistema = False
        self.continuar_login_whatsapp = False

        self.status_text = tk.StringVar()
        self.status_text.set("Aguardando iniciar...")

        tk.Label(self, text="Selecione a planilha Excel:").pack(pady=5)
        self.arquivo_path = tk.StringVar()
        tk.Entry(self, textvariable=self.arquivo_path, width=50).pack(pady=5)
        tk.Button(self, text="Buscar arquivo", command=self.buscar_arquivo).pack(pady=5)

        tk.Label(self, text="Intervalo entre mensagens (segundos):").pack(pady=5)
        self.min_intervalo = tk.IntVar(value=30)
        self.max_intervalo = tk.IntVar(value=60)

        frame_intervalo = tk.Frame(self)
        frame_intervalo.pack(pady=5)
        tk.Label(frame_intervalo, text="Mínimo").grid(row=0, column=0)
        tk.Entry(frame_intervalo, textvariable=self.min_intervalo, width=10).grid(row=1, column=0)
        tk.Label(frame_intervalo, text="Máximo").grid(row=0, column=1)
        tk.Entry(frame_intervalo, textvariable=self.max_intervalo, width=10).grid(row=1, column=1)

        self.btn_iniciar = tk.Button(self, text="Iniciar", command=self.iniciar_envio)
        self.btn_iniciar.pack(pady=15)

        tk.Label(self, textvariable=self.status_text).pack(pady=10)

        self.btn_continuar_sistema = tk.Button(self, text="Continuar após login no sistema", command=self.continuar_sistema, state=tk.DISABLED)
        self.btn_continuar_sistema.pack(pady=5)

        self.btn_continuar_whatsapp = tk.Button(self, text="Continuar após login no WhatsApp", command=self.continuar_whatsapp, state=tk.DISABLED)
        self.btn_continuar_whatsapp.pack(pady=5)

    def buscar_arquivo(self):
        arquivo = filedialog.askopenfilename(filetypes=[("Excel files", ".xlsx;.xls")])
        if arquivo:
            self.arquivo_path.set(arquivo)

    def continuar_sistema(self):
        self.continuar_login_sistema = True
        self.status_text.set("Login no sistema confirmado.")

    def continuar_whatsapp(self):
        self.continuar_login_whatsapp = True
        self.status_text.set("Login no WhatsApp confirmado.")

    def iniciar_envio(self):
        min_seg = self.min_intervalo.get()
        max_seg = self.max_intervalo.get()
        arquivo_excel = self.arquivo_path.get()

        if not arquivo_excel:
            messagebox.showerror("Erro", "Selecione um arquivo Excel válido.")
            return
        if min_seg > max_seg:
            messagebox.showerror("Erro", "O intervalo mínimo não pode ser maior que o máximo.")
            return

        self.status_text.set("Preparando para iniciar...")
        threading.Thread(target=processo_envio, args=(min_seg, max_seg, arquivo_excel, self.status_text), daemon=True).start()


if __name__ == "__main__":
    app = App()
    app.mainloop()
