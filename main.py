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

# Tema pastel (light + cores suaves)
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")  # pode trocar por "blue", "purple", etc.


class VideoDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("📥 BaixarYou - Downloader")
        self.geometry("650x450")
        self.resizable(False, False)

        self.downloading = False
        self.last_file = None

        self.create_widgets()

    def create_widgets(self):
        # Título
        ctk.CTkLabel(self, text="Baixar Vídeos da Internet", font=("Arial", 26, "bold")).pack(pady=20)

        # Campo de URL
        self.url_entry = ctk.CTkEntry(
            self, width=550, height=45,
            placeholder_text="Cole a URL do YouTube, Instagram, TikTok...",
            font=("Arial", 14)
        )
        self.url_entry.pack(pady=10)

        # Botão de download
        self.download_btn = ctk.CTkButton(
            self, text="⬇️ Baixar Vídeo",
            command=self.start_download,
            width=250, height=45, font=("Arial", 14, "bold")
        )
        self.download_btn.pack(pady=15)

        # Botão para abrir pasta
        self.abrir_pasta_btn = ctk.CTkButton(
            self, text="📂 Abrir Pasta de Downloads",
            command=self.abrir_pasta,
            width=250, height=45, font=("Arial", 14, "bold")
        )
        self.abrir_pasta_btn.pack(pady=10)

        # Label da pasta
        ctk.CTkLabel(
            self, text=f"📁 Salvando em: {SAVE_DIR}",
            font=("Arial", 11), text_color="gray"
        ).pack(pady=15)

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
                ydl.extract_info(url, download=True)

            self.download_sucesso()

        except Exception as e:
            self.download_erro(str(e))

    def download_sucesso(self):
        messagebox.showinfo("✅ Sucesso", f"Vídeo baixado com sucesso!\n\nVerifique a pasta:\n{SAVE_DIR}")
        self.reset_ui()

    def download_erro(self, erro):
        messagebox.showerror("❌ Erro", f"Não foi possível baixar o vídeo:\n{erro[:200]}")
        self.reset_ui()

    def reset_ui(self):
        self.downloading = False
        self.download_btn.configure(state="normal", text="⬇️ Baixar Vídeo")
        self.url_entry.delete(0, "end")

    def abrir_pasta(self):
        try:
            if os.name == "nt":  # Windows
                os.startfile(SAVE_DIR)
            else:  # Linux/Mac
                subprocess.run(["xdg-open", SAVE_DIR])
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")


if __name__ == "__main__":
    app = VideoDownloader()
    app.mainloop()
