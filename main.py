import os
import tkinter as tk
from tkinter import messagebox
from login import verificar_usuario, carregar_usuarios, pergunta_area
import menu

SESSAO_FILE = "sessao.txt"

def salvar_sessao(usuario):
    with open(SESSAO_FILE, "w") as f:
        f.write(usuario)

def carregar_sessao():
    if os.path.exists(SESSAO_FILE):
        with open(SESSAO_FILE, "r") as f:
            return f.read().strip()
    return None

def apagar_sessao():
    if os.path.exists(SESSAO_FILE):
        os.remove(SESSAO_FILE)

def realizar_login():
    usuario = entry_usuario.get().strip()
    senha = entry_senha.get().strip()
    usuarios = carregar_usuarios()
    user_data = verificar_usuario(usuario, senha, usuarios)
    
    if user_data:
        salvar_sessao(usuario)
        root.destroy()
        pergunta_area(user_data)
    else:
        messagebox.showerror("Erro", "Usuário ou senha incorretos.")

def main():
    global root, entry_usuario, entry_senha

    usuario_logado_nome = carregar_sessao()
    if usuario_logado_nome:
        usuarios = carregar_usuarios()
        user_data = next((u for u in usuarios if u['usuario'] == usuario_logado_nome), None)
        if user_data:
            pergunta_area(user_data)
            return
        else:
            apagar_sessao()  # Usuário da sessão não existe mais

    root = tk.Tk()
    root.title("Tela de Login")
    root.geometry("400x300")

    tk.Label(root, text="Usuário:").pack(pady=5)
    entry_usuario = tk.Entry(root)
    entry_usuario.pack(pady=5)

    tk.Label(root, text="Senha:").pack(pady=5)
    entry_senha = tk.Entry(root, show="*")
    entry_senha.pack(pady=5)

    btn_login = tk.Button(root, text="Entrar", command=realizar_login)
    btn_login.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()
