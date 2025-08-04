import requests
import os

VERSAO_ATUAL = "1.0.0"  # sua versão local

URL_VERSAO = "https://raw.githubusercontent.com/pietroo28/pz-app/main/versao.txt"
URL_ARQUIVOS = {
    "pz.py": "https://raw.githubusercontent.com/pietroo28/pz-app/main/pz.py",
    "pk.py": "https://raw.githubusercontent.com/pietroo28/pz-app/main/pk.py",
    "menu.py": "https://raw.githubusercontent.com/pietroo28/pz-app/main/menu.py",
    # adicione os outros arquivos aqui
}

def check_update():
    try:
        resposta = requests.get(URL_VERSAO)
        resposta.raise_for_status()
        versao_online = resposta.text.strip()

        if versao_online != VERSAO_ATUAL:
            print(f"Nova versão disponível: {versao_online}. Atualizando...")
            for arquivo, url in URL_ARQUIVOS.items():
                baixar_arquivo(arquivo, url)
            print("Atualização concluída! Reinicie o programa.")
            # opcional: sair ou reiniciar o app aqui
        else:
            print("Você está com a versão mais recente.")

    except Exception as e:
        print("Erro ao checar atualização:", e)

def baixar_arquivo(nome_arquivo, url):
    try:
        r = requests.get(url)
        r.raise_for_status()
        with open(nome_arquivo, "wb") as f:
            f.write(r.content)
        print(f"{nome_arquivo} atualizado.")
    except Exception as e:
        print(f"Erro ao baixar {nome_arquivo}: {e}")