import os
import re
import threading
import subprocess
from tkinter import messagebox

import customtkinter as ctk
import yt_dlp

# ==============================
# CONFIGURAÇÃO
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "videos")
os.makedirs(SAVE_DIR, exist_ok=True)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class VideoDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Downloader YouTube & Instagram")
        self.geometry("600x450")
        self.resizable(False, False)

        self.downloading = False
        self.last_file = None

        self.create_widgets()

    # ==============================
    # INTERFACE
    # ==============================

    def create_widgets(self):
        ctk.CTkLabel(
            self,
            text="Baixar Vídeos",
            font=("Arial", 26, "bold")
        ).pack(pady=20)

        self.url_entry = ctk.CTkEntry(
            self,
            width=500,
            height=45,
            placeholder_text="Cole a URL do YouTube ou Instagram",
            font=("Arial", 14)
        )
        self.url_entry.pack(pady=10)

        self.download_btn = ctk.CTkButton(
            self,
            text="Baixar Vídeo",
            command=self.start_download,
            width=250,
            height=45,
            font=("Arial", 14, "bold")
        )
        self.download_btn.pack(pady=15)

        self.exibir_btn = ctk.CTkButton(
            self,
            text="▶️ Exibir Vídeo",
            command=self.exibir_video,
            width=250,
            height=45,
            font=("Arial", 14, "bold"),
            state="disabled"
        )
        self.exibir_btn.pack(pady=10)

        ctk.CTkLabel(
            self, 
            text=f"📁 Salvando em: {SAVE_DIR}", 
            font=("Arial", 11),
            text_color="gray"
        ).pack(pady=15)

    # ==============================
    # VALIDAÇÃO URL
    # ==============================

    def validar_url(self, url):
        padroes = [
            r'^https?://(www\.)?(youtube\.com|youtu\.be)/',
            r'^https?://(www\.)?instagram\.com/',
            r'^https?://(www\.)?(youtu\.be)/',
        ]
        return any(re.match(p, url) for p in padroes)

    # ==============================
    # DOWNLOAD
    # ==============================

    def start_download(self):
        url = self.url_entry.get().strip()

        if not self.validar_url(url):
            messagebox.showwarning(
                "URL inválida", 
                "Cole um link válido do YouTube ou Instagram.\n\nExemplos:\n• https://youtube.com/watch?v=...\n• https://instagram.com/p/..."
            )
            return

        if self.downloading:
            messagebox.showinfo("Aviso", "Já existe um download em andamento!")
            return

        self.downloading = True
        self.download_btn.configure(state="disabled", text="⏬ Baixando...")

        threading.Thread(target=self.download_video, args=(url,), daemon=True).start()

    def download_video(self, url):
        try:
            ydl_opts = {
                'outtmpl': os.path.join(SAVE_DIR, '%(title)s.%(ext)s'),
                'noplaylist': True,
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
                'quiet': True,
                'no_warnings': False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                self.last_file = filename

            self.download_sucesso()

        except Exception as e:
            self.download_erro(str(e))

    def download_sucesso(self):
        messagebox.showinfo("✅ Sucesso", f"Vídeo baixado com sucesso!\n\nVerifique a pasta:\n{SAVE_DIR}")
        self.exibir_btn.configure(state="normal")
        self.reset_ui()

    def download_erro(self, erro):
        if "Unsupported URL" in erro:
            msg = "URL não suportada. Verifique se o link é do YouTube ou Instagram."
        elif "Video unavailable" in erro:
            msg = "Vídeo indisponível. Pode ser privado ou removido."
        else:
            msg = f"Erro no download:\n{erro[:200]}"
        
        messagebox.showerror("❌ Erro", msg)
        self.reset_ui()

    def reset_ui(self):
        self.downloading = False
        self.download_btn.configure(state="normal", text="Baixar Vídeo")
        self.url_entry.delete(0, "end")

    # ==============================
    # EXIBIR VÍDEO
    # ==============================

    def exibir_video(self):
        if self.last_file and os.path.exists(self.last_file):
            try:
                if os.name == "nt":  # Windows
                    os.startfile(self.last_file)
                elif os.name == "posix":  # Linux/Mac
                    subprocess.run(["xdg-open", self.last_file])
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível abrir o vídeo:\n{e}")
        else:
            messagebox.showwarning("Aviso", "Nenhum vídeo disponível para exibir.")


if __name__ == "__main__":
    app = VideoDownloader()
    app.mainloop()
