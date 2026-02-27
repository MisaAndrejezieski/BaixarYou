import os
import re
import threading
import customtkinter as ctk
from tkinter import messagebox
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
        self.geometry("600x350")
        self.resizable(False, False)

        self.downloading = False

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
            width=450,
            placeholder_text="Cole a URL do YouTube ou Instagram"
        )
        self.url_entry.pack(pady=10)

        self.download_btn = ctk.CTkButton(
            self,
            text="Baixar Vídeo",
            command=self.start_download,
            width=200,
            height=40
        )
        self.download_btn.pack(pady=15)

        self.progress = ctk.CTkProgressBar(self, width=450)
        self.status_label = ctk.CTkLabel(self, text="")

    # ==============================
    # VALIDAÇÃO URL
    # ==============================

    def validar_url(self, url):
        padroes = [
            r'^https?://(www\.)?(youtube\.com|youtu\.be)/',
            r'^https?://(www\.)?instagram\.com/',
        ]
        return any(re.match(p, url) for p in padroes)

    # ==============================
    # DOWNLOAD
    # ==============================

    def start_download(self):
        url = self.url_entry.get().strip()

        if not self.validar_url(url):
            messagebox.showwarning("URL inválida", "Cole um link válido do YouTube ou Instagram.")
            return

        if self.downloading:
            return

        self.downloading = True
        self.download_btn.configure(state="disabled")
        self.progress.pack(pady=10)
        self.status_label.pack()

        threading.Thread(target=self.download_video, args=(url,), daemon=True).start()

    def download_video(self, url):
        try:
            ydl_opts = {
                'outtmpl': os.path.join(SAVE_DIR, '%(title)s.%(ext)s'),
                'progress_hooks': [self.atualizar_progresso],
                'noplaylist': True,

                # MELHOR QUALIDADE DISPONÍVEL
                'format': 'bestvideo+bestaudio/best',

                # Junta e salva como mp4
                'merge_output_format': 'mp4',
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            messagebox.showinfo("Sucesso", "Vídeo baixado com sucesso!")

        except Exception as e:
            messagebox.showerror("Erro", str(e))

        finally:
            self.downloading = False
            self.download_btn.configure(state="normal")
            self.progress.pack_forget()
            self.status_label.pack_forget()
            self.url_entry.delete(0, "end")

    # ==============================
    # PROGRESSO
    # ==============================

    def atualizar_progresso(self, d):
        if d['status'] == 'downloading':
            percentual = d.get('_percent_str', '0%').strip()
            try:
                valor = float(percentual.replace('%', '')) / 100
                self.progress.set(valor)
            except:
                pass
            self.status_label.configure(text=f"Baixando... {percentual}")


if __name__ == "__main__":
    app = VideoDownloader()
    app.mainloop()
    