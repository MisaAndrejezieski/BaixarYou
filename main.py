import os
import subprocess
import sys
import threading
import time
from tkinter import filedialog, messagebox

import customtkinter as ctk
import yt_dlp

# ==============================
# CONFIGURAÇÃO
# ==============================

# Se estiver rodando como .exe, pega o diretório do executável
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Pasta inicial = diretório do programa (mas só será usada se você não escolher outra)
SAVE_DIR = BASE_DIR

LOG_FILE = os.path.join(BASE_DIR, "download_errors.log")

# Apaga log se tiver mais de 7 dias
if os.path.exists(LOG_FILE):
    idade = time.time() - os.path.getmtime(LOG_FILE)
    if idade > 7 * 24 * 60 * 60:
        os.remove(LOG_FILE)

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")


class VideoDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("📥 BaixarYou - Downloader")
        self.geometry("650x500")
        self.resizable(False, False)

        self.downloading = False
        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Baixar Vídeos da Internet", font=("Arial", 26, "bold")).pack(pady=20)

        self.url_entry = ctk.CTkEntry(
            self, width=550, height=45,
            placeholder_text="Cole a URL do YouTube, Instagram, TikTok...",
            font=("Arial", 14)
        )
        self.url_entry.pack(pady=10)

        self.download_btn = ctk.CTkButton(
            self, text="⬇️ Baixar Vídeo",
            command=self.start_download,
            width=250, height=45, font=("Arial", 14, "bold")
        )
        self.download_btn.pack(pady=15)

        self.abrir_pasta_btn = ctk.CTkButton(
            self, text="📂 Abrir Pasta",
            command=self.abrir_pasta,
            width=250, height=45, font=("Arial", 14, "bold")
        )
        self.abrir_pasta_btn.pack(pady=10)

        self.mudar_pasta_btn = ctk.CTkButton(
            self, text="🗂️ Escolher Pasta",
            command=self.mudar_pasta,
            width=250, height=45, font=("Arial", 14, "bold")
        )
        self.mudar_pasta_btn.pack(pady=10)

        self.label_pasta = ctk.CTkLabel(
            self, text=f"📁 Pasta atual: {SAVE_DIR}",
            font=("Arial", 11), text_color="gray"
        )
        self.label_pasta.pack(pady=15)

    def mudar_pasta(self):
        global SAVE_DIR
        pasta = filedialog.askdirectory(title="Escolha a pasta para salvar os vídeos")
        if pasta:
            SAVE_DIR = pasta
            self.label_pasta.configure(text=f"📁 Pasta atual: {SAVE_DIR}")

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Aviso", "Cole uma URL válida.")
            return

        if self.downloading:
            messagebox.showinfo("Aviso", "Já existe um download em andamento.")
            return

        self.downloading = True
        self.download_btn.configure(state="disabled", text="Baixando...")

        threading.Thread(target=self.download_video, args=(url,), daemon=True).start()

    def download_video(self, url):
        try:
            ydl_opts = {
                'outtmpl': os.path.join(SAVE_DIR, '%(title)s.%(ext)s'),
                'format': 'best[ext=mp4]',
                'quiet': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)

            self.download_sucesso()

        except Exception as e:
            self.download_erro(str(e))

    def download_sucesso(self):
        messagebox.showinfo("✅ Sucesso", f"Vídeo baixado com sucesso!\n\nVerifique a pasta:\n{SAVE_DIR}")
        self.reset_ui()

    def download_erro(self, erro):
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"{time.ctime()} - {erro}\n")
        except:
            pass

        messagebox.showerror("❌ Erro", f"Não foi possível baixar o vídeo:\n{erro[:200]}")
        self.reset_ui()

    def reset_ui(self):
        self.downloading = False
        self.download_btn.configure(state="normal", text="⬇️ Baixar Vídeo")
        self.url_entry.delete(0, "end")

    def abrir_pasta(self):
        try:
            if os.name == "nt":
                os.startfile(SAVE_DIR)
            else:
                subprocess.run(["xdg-open", SAVE_DIR])
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")


if __name__ == "__main__":
    app = VideoDownloader()
    app.mainloop()
