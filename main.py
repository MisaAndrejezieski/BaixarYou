import os
import re
import subprocess
import threading
from tkinter import messagebox

import customtkinter as ctk
import yt_dlp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "videos")
os.makedirs(SAVE_DIR, exist_ok=True)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class VideoDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("📥 BaixarYou - Downloader")
        self.geometry("650x500")
        self.resizable(False, False)

        self.downloading = False
        self.last_file = None

        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Baixar Vídeos e Áudios", font=("Arial", 26, "bold")).pack(pady=20)

        self.url_entry = ctk.CTkEntry(
            self, width=550, height=45,
            placeholder_text="Cole a URL do YouTube ou Instagram",
            font=("Arial", 14)
        )
        self.url_entry.pack(pady=10)

        # Botões principais
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=15)

        self.download_btn = ctk.CTkButton(
            btn_frame, text="⬇️ Baixar Vídeo",
            command=self.start_download_video,
            width=250, height=45, font=("Arial", 14, "bold")
        )
        self.download_btn.grid(row=0, column=0, padx=10)

        self.audio_btn = ctk.CTkButton(
            btn_frame, text="🎵 Baixar Áudio (MP3)",
            command=self.start_download_audio,
            width=250, height=45, font=("Arial", 14, "bold")
        )
        self.audio_btn.grid(row=0, column=1, padx=10)

        # Botões extras
        extra_frame = ctk.CTkFrame(self)
        extra_frame.pack(pady=15)

        self.exibir_btn = ctk.CTkButton(
            extra_frame, text="▶️ Exibir Último Vídeo",
            command=self.exibir_video,
            width=250, height=45, font=("Arial", 14, "bold"),
            state="disabled"
        )
        self.exibir_btn.grid(row=0, column=0, padx=10)

        self.abrir_pasta_btn = ctk.CTkButton(
            extra_frame, text="📂 Abrir Pasta de Vídeos",
            command=self.abrir_pasta,
            width=250, height=45, font=("Arial", 14, "bold")
        )
        self.abrir_pasta_btn.grid(row=0, column=1, padx=10)

        ctk.CTkLabel(
            self, text=f"📁 Salvando em: {SAVE_DIR}",
            font=("Arial", 11), text_color="gray"
        ).pack(pady=15)

    def validar_url(self, url):
        padroes = [
            r'^https?://(www\.)?(youtube\.com|youtu\.be)/',
            r'^https?://(www\.)?instagram\.com/',
        ]
        return any(re.match(p, url) for p in padroes)

    def start_download_video(self):
        self._start_download("video")

    def start_download_audio(self):
        self._start_download("audio")

    def _start_download(self, tipo):
        url = self.url_entry.get().strip()

        if not self.validar_url(url):
            messagebox.showwarning("URL inválida",
                "Cole um link válido do YouTube ou Instagram.\n\nExemplos:\n• https://youtube.com/watch?v=...\n• https://instagram.com/p/...")
            return

        if self.downloading:
            messagebox.showinfo("Aviso", "Já existe um download em andamento!")
            return

        self.downloading = True
        self.download_btn.configure(state="disabled", text="⏬ Baixando...")
        self.audio_btn.configure(state="disabled", text="⏬ Baixando...")

        threading.Thread(target=self.download_video, args=(url, tipo), daemon=True).start()

    def download_video(self, url, tipo):
        try:
            if tipo == "video":
                ydl_opts = {
                    'outtmpl': os.path.join(SAVE_DIR, '%(title)s.%(ext)s'),
                    'noplaylist': True,
                    'format': 'bestvideo+bestaudio/best',
                    'merge_output_format': 'mp4',
                    'quiet': True,
                }
            else:  # áudio
                ydl_opts = {
                    'outtmpl': os.path.join(SAVE_DIR, '%(title)s.%(ext)s'),
                    'noplaylist': True,
                    'format': 'bestaudio/best',
                    'quiet': True,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                self.last_file = filename

            self.download_sucesso(tipo)

        except Exception as e:
            self.download_erro(str(e))

    def download_sucesso(self, tipo):
        if tipo == "video":
            msg = f"🎬 Vídeo baixado com sucesso!\n\nVerifique a pasta:\n{SAVE_DIR}"
        else:
            msg = f"🎵 Áudio (MP3) baixado com sucesso!\n\nVerifique a pasta:\n{SAVE_DIR}"

        messagebox.showinfo("✅ Sucesso", msg)
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
        self.download_btn.configure(state="normal", text="⬇️ Baixar Vídeo")
        self.audio_btn.configure(state="normal", text="🎵 Baixar Áudio (MP3)")
        self.url_entry.delete(0, "end")

    def exibir_video(self):
        if self.last_file and os.path.exists(self.last_file):
            try:
                if os.name == "nt":  # Windows
                    os.startfile(self.last_file)
                elif os.name == "posix":  # Linux/Mac
                    subprocess.run(["xdg-open", self.last_file])
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível abrir o arquivo:\n{e}")
        else:
            messagebox.showwarning("Aviso", "Nenhum arquivo disponível para exibir.")

    def abrir_pasta(self):
        try:
            if os.name == "nt":  # Windows
                os.startfile(SAVE_DIR)
            elif os.name == "posix":  # Linux/Mac
                subprocess.run(["xdg-open", SAVE_DIR])
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")


if __name__ == "__main__":
    app = VideoDownloader()
    app.mainloop()
