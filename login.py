import tkinter as tk
from tkinter import messagebox, simpledialog
import json
import os
import menu  # Seu menu.py

USUARIOS_FILE = "usuarios.json"

def carregar_usuarios():
    if not os.path.exists(USUARIOS_FILE):
        with open(USUARIOS_FILE, "w") as f:
            json.dump([], f)
    with open(USUARIOS_FILE, "r") as f:
        return json.load(f)

def salvar_usuarios(usuarios):
    with open(USUARIOS_FILE, "w") as f:
        json.dump(usuarios, f, indent=4)

def verificar_usuario(usuario, senha, usuarios):
    for user in usuarios:
        if user["usuario"] == usuario and user["senha"] == senha:
            return user
    return None

def login(entry_usuario, entry_senha):
    usuarios = carregar_usuarios()
    usuario = entry_usuario.get().strip()
    senha = entry_senha.get().strip()
    user_data = verificar_usuario(usuario, senha, usuarios)
    if user_data:
        root.destroy()
        pergunta_area(user_data)
    else:
        messagebox.showerror("Erro", "Usuário ou senha incorretos.")

def atualizar_lista(usuarios, lista_usuarios):
    lista_usuarios.delete(0, tk.END)
    for user in usuarios:
        bots_str = ", ".join(user['bots'])
        lista_usuarios.insert(tk.END, f"{user['usuario']} - Nível: {user['nivel']} - Bots: {bots_str}")

def editar_usuario(usuarios, usuario_logado, lista_usuarios):
    selecionado = lista_usuarios.curselection()
    if not selecionado:
        return

    usuario = lista_usuarios.get(selecionado[0]).split(" - ")[0]
    if usuario == "maximo":
        messagebox.showerror("Erro", "Não é permitido editar o usuário 'maximo'.")
        return

    user = next((u for u in usuarios if u['usuario'] == usuario), None)
    if not user:
        return

    senha = simpledialog.askstring("Nova senha", "Nova senha (deixe em branco para manter):", show="*")
    senha = senha if senha else user['senha']

    niveis = ["basico", "admin"]
    if usuario_logado == "dev":
        niveis.append("dev")

    nivel = simpledialog.askstring("Nível", f"Nível novo ({', '.join(niveis)}):")
    if nivel not in niveis:
        messagebox.showerror("Erro", "Nível inválido.")
        return

    bots = simpledialog.askstring("Bots", "Bots (pz, pk, pg):")
    bots_list = [b.strip() for b in bots.split(",")] if bots else []

    user['senha'] = senha
    user['nivel'] = nivel
    user['bots'] = bots_list

    salvar_usuarios(usuarios)
    atualizar_lista(usuarios, lista_usuarios)

def abrir_edicao_usuarios(usuario_logado, nivel_logado):
    usuarios = carregar_usuarios()

    janela = tk.Tk()
    janela.title("Edição de Usuários")
    janela.geometry("600x400")

    lista_usuarios = tk.Listbox(janela, width=50)
    lista_usuarios.pack(pady=10)

    def adicionar_usuario():
        novo = simpledialog.askstring("Usuário", "Nome do novo usuário:")
        if not novo:
            return

        if any(u['usuario'] == novo for u in usuarios):
            messagebox.showerror("Erro", "Usuário já existe.")
            return

        senha = simpledialog.askstring("Senha", f"Senha para {novo}:", show="*")
        if not senha:
            return

        niveis = ["basico", "admin"]
        if nivel_logado == "dev":
            niveis.append("dev")

        nivel = simpledialog.askstring("Nível", f"Nível ({', '.join(niveis)}):")
        if nivel not in niveis:
            messagebox.showerror("Erro", "Nível inválido.")
            return

        if nivel == "dev" and any(u['nivel'] == 'dev' for u in usuarios):
            messagebox.showerror("Erro", "Já existe um usuário dev.")
            return

        bots = simpledialog.askstring("Bots", "Bots permitidos (pz, pk, pg):")
        bots_list = [b.strip() for b in bots.split(",")] if bots else []

        usuarios.append({
            "usuario": novo,
            "senha": senha,
            "nivel": nivel,
            "bots": bots_list
        })

        salvar_usuarios(usuarios)
        atualizar_lista(usuarios, lista_usuarios)

    def excluir_usuario():
        selecionado = lista_usuarios.curselection()
        if not selecionado:
            return
        usuario = lista_usuarios.get(selecionado[0]).split(" - ")[0]
        if usuario == usuario_logado:
            messagebox.showerror("Erro", "Você não pode excluir o usuário logado.")
            return

        for i, u in enumerate(usuarios):
            if u['usuario'] == usuario:
                del usuarios[i]
                break
        salvar_usuarios(usuarios)
        atualizar_lista(usuarios, lista_usuarios)

    def editar():
        editar_usuario(usuarios, usuario_logado, lista_usuarios)

    frame = tk.Frame(janela)
    frame.pack(pady=10)

    tk.Button(frame, text="Adicionar", command=adicionar_usuario).grid(row=0, column=0, padx=5)
    tk.Button(frame, text="Editar", command=editar).grid(row=0, column=1, padx=5)
    tk.Button(frame, text="Excluir", command=excluir_usuario).grid(row=0, column=2, padx=5)
    tk.Button(janela, text="Fechar", command=janela.destroy).pack(pady=10)

    atualizar_lista(usuarios, lista_usuarios)
    janela.mainloop()

def pergunta_area(user_data):
    usuario = user_data["usuario"]
    nivel = user_data["nivel"].strip().lower()

    escolha = tk.Tk()
    escolha.title("Escolha a Área")
    escolha.geometry("300x180")

    tk.Label(escolha, text=f"Olá, {usuario}! Para onde deseja ir?", font=("Arial", 12)).pack(pady=10)

    def ir_menu():
        escolha.destroy()
        abrir_menu(user_data)

    def ir_edicao():
        escolha.destroy()
        abrir_edicao_usuarios(usuario, nivel)

    tk.Button(escolha, text="Menu", width=20, command=ir_menu).pack(pady=5)

    if nivel in ["admin", "dev"]:
        tk.Button(escolha, text="Edição de Usuários", width=20, command=ir_edicao).pack(pady=5)

    escolha.mainloop()

def abrir_menu(usuario):
    try:
        menu.menu(usuario["bots"])
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir o menu: {e}")

def main():
    global root
    root = tk.Tk()
    root.title("Pz Bot Login")
    root.geometry("400x300")
    root.configure(bg="#f0f8ff")

    canvas = tk.Canvas(root, width=400, height=300, bg="white", highlightthickness=0)
    canvas.place(x=0, y=0)
    canvas.create_rectangle(0, 0, 400, 60, fill="#4db8ff", outline="")
    canvas.create_text(20, 30, text="Pz bot", anchor="w", font=("Arial", 20, "bold"), fill="black")

    frame = tk.Frame(root, bg="white")
    frame.place(relx=0.5, rely=0.5, anchor="center")

    entry_usuario = tk.Entry(frame, font=("Arial", 12), width=25, justify="center")
    entry_usuario.insert(0, "login")
    entry_usuario.pack(pady=10)

    entry_senha = tk.Entry(frame, font=("Arial", 12), width=25, justify="center", show="*")
    entry_senha.insert(0, "senha")
    entry_senha.pack(pady=10)

    btn_login = tk.Button(frame, text="Entrar", font=("Arial", 12, "bold"),
                          bg="#4db8ff", fg="black", bd=0,
                          activebackground="#3399ff", width=20, height=2,
                          relief="flat", command=lambda: login(entry_usuario, entry_senha))
    btn_login.pack(pady=15)

    root.mainloop()

if __name__ == "__main__":
    main()
