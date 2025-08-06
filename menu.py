import tkinter as tk
from tkinter import messagebox
import subprocess
import os

# Diretório onde está o menu.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def menu(bots):
    menu_win = tk.Tk()
    menu_win.title("Menu")
    menu_win.geometry("400x300")

    label = tk.Label(menu_win, text="Menu Principal", font=("Arial", 14))
    label.pack(pady=20)

    def abrir_exe(nome_arquivo):
        caminho_exe = os.path.join(BASE_DIR, "emergencia", nome_arquivo)
        try:
            subprocess.Popen([caminho_exe], shell=True)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao executar o programa:\n{e}")

    if "pz" in bots:
        btn_pz = tk.Button(menu_win, text="Pz", command=lambda: abrir_exe("pz.exe"))
        btn_pz.pack(pady=5)

    if "pk" in bots:
        btn_pk = tk.Button(menu_win, text="Pk", command=lambda: abrir_exe("pk.exe"))
        btn_pk.pack(pady=5)

    if "pg" in bots:
        btn_pg = tk.Button(menu_win, text="Cobrança", command=lambda: abrir_exe("pg.exe"))
        btn_pg.pack(pady=5)

    menu_win.mainloop()

if __name__ == "__main__":
    menu(["pz", "pk", "pg"])  # Lista de bots que você quer exibir no menu
