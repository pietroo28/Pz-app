import tkinter as tk
import subprocess

# Classe para botões arredondados usando Canvas
class RoundedButton(tk.Canvas):
    def __init__(self, parent, width, height, cornerradius, bg_color, fg_color, text, font, command=None):
        super().__init__(parent, width=width, height=height, highlightthickness=0, bg=parent['bg'])
        self.command = command
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.cornerradius = cornerradius
        self.text = text
        self.font = font
        self.draw_rounded_rect()
        self.text_id = self.create_text(width//2, height//2, text=text, fill=fg_color, font=font)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def draw_rounded_rect(self):
        w = int(self['width'])
        h = int(self['height'])
        r = self.cornerradius
        # Quatro cantos arredondados
        self.create_arc((0, 0, 2*r, 2*r), start=90, extent=90, fill=self.bg_color, outline=self.bg_color)
        self.create_arc((w-2*r, 0, w, 2*r), start=0, extent=90, fill=self.bg_color, outline=self.bg_color)
        self.create_arc((0, h-2*r, 2*r, h), start=180, extent=90, fill=self.bg_color, outline=self.bg_color)
        self.create_arc((w-2*r, h-2*r, w, h), start=270, extent=90, fill=self.bg_color, outline=self.bg_color)
        # Retângulos para completar o botão
        self.create_rectangle((r, 0, w-r, h), fill=self.bg_color, outline=self.bg_color)
        self.create_rectangle((0, r, w, h-r), fill=self.bg_color, outline=self.bg_color)

    def _on_press(self, event):
        self.config(cursor="hand2")
        self.move(self.text_id, 1, 1)

    def _on_release(self, event):
        self.config(cursor="")
        self.move(self.text_id, -1, -1)
        if self.command:
            self.command()

# -------------------------------------------------
# Aqui você deve passar a lista de bots permitidos do usuário
BOTS_PERMITIDOS = ["pz", "pk", "pg"]  # Exemplo, deve vir do login
# -------------------------------------------------

# Criar a janela principal
root = tk.Tk()
root.title("Sistema Pz")
root.geometry("500x350")
root.resizable(False, False)
root.configure(bg="#f0f0f0")

# Label título
label = tk.Label(root, text="Escolha a função desejada:", font=("Arial", 14), bg="#f0f0f0")
label.pack(pady=10)

# Funções dos botões
def executar_pz():
    root.destroy()
    subprocess.run(["python", "pz.py"])
    print("Executar pz.py")

def executar_pk():
    root.destroy()
    subprocess.run(["python", "pk.py"])
    print("Executar pk.py")

def executar_pg():
    root.destroy()
    subprocess.run(["python", "pg.py"])
    print("Executar pg.py")

# Botão Pz - mensagem texto
if "pz" in BOTS_PERMITIDOS:
    btn_pz = RoundedButton(root, width=300, height=50, cornerradius=25,
                        bg_color="#3498db", fg_color="black",
                        text="Pz", font=("Arial", 16, "bold"), command=executar_pz)
    btn_pz.pack(pady=(10, 0))

    # Label abaixo do botão pz
    label_pz = tk.Label(root, text="mensagem de texto", font=("Arial", 12), bg="#f0f0f0")
    label_pz.pack(pady=(0,10))

# Botão Pk - mensagem vídeo/foto
if "pk" in BOTS_PERMITIDOS:
    btn_pk = RoundedButton(root, width=300, height=50, cornerradius=25,
                        bg_color="#3498db", fg_color="black",
                        text="Pk", font=("Arial", 16, "bold"), command=executar_pk)
    btn_pk.pack(pady=(10, 0))

    # Label abaixo do botão pk
    label_pk = tk.Label(root, text="mensagem de vídeo/foto", font=("Arial", 12), bg="#f0f0f0")
    label_pk.pack(pady=(0, 10))

# Botão Pg - cobrança (substitui o botão fechar se presente)
if "pg" in BOTS_PERMITIDOS:
    btn_pg = RoundedButton(root, width=300, height=50, cornerradius=25,
                        bg_color="#3498db", fg_color="black",
                        text="Cobrança", font=("Arial", 16, "bold"), command=executar_pg)
    btn_pg.pack(pady=(10, 0))
    # Não cria botão fechar, pois pg substitui ele

else:
    # Botão fechar (voltar) aparece só se não houver pg
    def voltar():
        root.destroy()
        print("Fechar menu")

    btn_voltar = RoundedButton(root, width=180, height=40, cornerradius=20,
                            bg_color="#3498db", fg_color="black",
                            text="fechar", font=("Arial", 14, "bold"), command=voltar)
    btn_voltar.pack(pady=15)

# Labels das exigências pz.py e pk.py ao lado direito (estilo simples)
label_requisitos = tk.Label(root, 
    text="Requisitos mínimos:\n- colunas chamadas 'Telefones', 'Paciente'\n- cabeçalho",
    font=("Arial", 10), justify="left", bg="#f0f0f0"
)
label_requisitos.place(x=320, y=250)

root.mainloop()
