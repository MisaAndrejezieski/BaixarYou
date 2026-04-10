import os
import re
import threading
from functools import partial
from tkinter import messagebox
from typing import Any

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

        self.progress = ctk.CTkProgressBar(self, width=500, height=15)
        self.progress.set(0)

        self.status_label = ctk.CTkLabel(
            self, 
            text="", 
            font=("Arial", 12),
            text_color="lightblue"
        )

        ctk.CTkLabel(
            self, 
            text=f"📁 Salvando em: {SAVE_DIR}", 
            font=("Arial", 11),
            text_color="gray"
        ).pack(pady=15)

        ctk.CTkFrame(self, height=2, width=500, fg_color="gray").pack(pady=10)

        dicas = ctk.CTkLabel(
            self,
            text="💡 Dicas:\n• YouTube: qualquer link de vídeo\n• Instagram: links de reels ou posts\n• O vídeo será salvo na pasta 'videos'",
            font=("Arial", 11),
            text_color="gray",
            justify="left"
        )
        dicas.pack(pady=10)

    # ==============================
    # VALIDAÇÃO URL
    # ==============================

    def validar_url(self, url: str) -> bool:
        padroes = [
            r'^https?://(www\.)?(youtube\.com|youtu\.be)/',
            r'^https?://(www\.)?instagram\.com/',
            r'^https?://(www\.)?(youtu\.be)/',
        ]
        return any(re.match(p, url) for p in padroes)

    # ==============================
    # DOWNLOAD
    # ==============================

    def start_download(self) -> None:
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
        
        self.progress.pack(pady=10)
        self.progress.set(0)
        self.status_label.pack(pady=5)
        self.status_label.configure(text="🔄 Iniciando conexão...")

        threading.Thread(target=self.download_video, args=(url,), daemon=True).start()

    def download_video(self, url: str) -> None:
        try:
            ydl_opts = {
                'outtmpl': os.path.join(SAVE_DIR, '%(title)s.%(ext)s'),
                'progress_hooks': [self.atualizar_progresso],
                'noplaylist': True,
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
                'quiet': True,
                'no_warnings': False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.after(0, partial(self.status_label.configure, text="📥 Obtendo informações do vídeo..."))
                ydl.download([url])

            self.after(0, self.download_sucesso)

        except Exception as e:
            self.after(0, partial(self.download_erro, str(e)))

    def download_sucesso(self) -> None:
        messagebox.showinfo("✅ Sucesso", "Vídeo baixado com sucesso!\n\nVerifique a pasta 'videos'")
        self.reset_ui()

    def download_erro(self, erro: str) -> None:
        if "Unsupported URL" in erro:
            msg = "URL não suportada. Verifique se o link é do YouTube ou Instagram."
        elif "Video unavailable" in erro:
            msg = "Vídeo indisponível. Pode ser privado ou removido."
        else:
            msg = f"Erro no download:\n{erro[:200]}"
        
        messagebox.showerror("❌ Erro", msg)
        self.reset_ui()

    def reset_ui(self) -> None:
        self.downloading = False
        self.download_btn.configure(state="normal", text="Baixar Vídeo")
        self.progress.pack_forget()
        self.status_label.pack_forget()
        self.url_entry.delete(0, "end")

    # ==============================
    # PROGRESSO
    # ==============================

    def atualizar_progresso(self, d: dict) -> None:
        try:
            if d['status'] == 'downloading':
                percentual = d.get('_percent_str', '0%').strip()
                valor_float = float(percentual.replace('%', '')) / 100
                velocidade = d.get('_speed_str', '').strip()
                
                self.after(0, partial(self.atualizar_barra, valor_float, percentual, velocidade))
            
            elif d['status'] == 'finished':
                self.after(0, partial(self.status_label.configure, text="✨ Processando vídeo (convertendo para MP4)..."))
                
        except Exception as e:
            print(f"Erro no progresso: {e}")

    def atualizar_barra(self, valor: float, percentual: str, velocidade: str = "") -> None:
        self.progress.set(valor)
        
        if velocidade:
            texto = f"📥 Baixando... {percentual} ⚡ {velocidade}"
        else:
            texto = f"📥 Baixando... {percentual}"
        
        self.status_label.configure(text=texto)


if __name__ == "__main__":
    app = VideoDownloader()
    app.mainloop()
