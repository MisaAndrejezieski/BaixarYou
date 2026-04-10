import os
import subprocess
import threading
from tkinter import messagebox

import customtkinter as ctk
import yt_dlp

# Pasta onde os vídeos serão salvos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "videos")
os.makedirs(SAVE_DIR, exist_ok=True)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class VideoDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Downloader de Vídeos")
        self.geometry("600x400")
        self.resizable(False, False)

        self.downloading = False
        self.last_file = None

        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Cole a URL do vídeo", font=("Arial", 20, "bold")).pack(pady=20)

        self.url_entry = ctk.CTkEntry(self, width=500, height=40, placeholder_text="https://...")
        self.url_entry.pack(pady=10)

        self.download_btn = ctk.CTkButton(self, text="Baixar Vídeo", command=self.start_download, width=200, height=40)
        self.download_btn.pack(pady=15)

        self.exibir_btn = ctk.CTkButton(self, text="Abrir Último Vídeo", command=self.exibir_video, width=200, height=40, state="disabled")
        self.exibir_btn.pack(pady=10)

        ctk.CTkLabel(self, text=f"📁 Pasta de downloads: {SAVE_DIR}", font=("Arial", 11), text_color="gray").pack(pady=15)

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
                'format': 'best',
                'merge_output_format': 'mp4',
                'quiet': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                self.last_file = filename

            self.download_sucesso()

        except Exception as e:
            self.download_erro(str(e))

    def download_sucesso(self):
        messagebox.showinfo("Sucesso", f"Vídeo baixado com sucesso!\n\nVerifique a pasta:\n{SAVE_DIR}")
        self.exibir_btn.configure(state="normal")
        self.reset_ui()

    def download_erro(self, erro):
        messagebox.showerror("Erro", f"Não foi possível baixar o vídeo:\n{erro[:200]}")
        self.reset_ui()

    def reset_ui(self):
        self.downloading = False
        self.download_btn.configure(state="normal", text="Baixar Vídeo")
        self.url_entry.delete(0, "end")

    def exibir_video(self):
        if self.last_file and os.path.exists(self.last_file):
            try:
                if os.name == "nt":  # Windows
                    os.startfile(self.last_file)
                else:  # Linux/Mac
                    subprocess.run(["xdg-open", self.last_file])
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível abrir o vídeo:\n{e}")
        else:
            messagebox.showwarning("Aviso", "Nenhum vídeo disponível para abrir.")


if __name__ == "__main__":
    app = VideoDownloader()
    app.mainloop()
