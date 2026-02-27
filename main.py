import os
import re
import logging
import threading
import customtkinter as ctk
from tkinter import messagebox
import yt_dlp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "Salvar")
FFMPEG_DIR = os.path.join(BASE_DIR, "ffmpeg-master-latest-win64-gpl-shared", "bin")

ctk.set_appearance_mode("dark")


class VideoDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Universal Video Downloader")
        self.geometry("900x650")
        self.configure(fg_color="#1E1E2E")

        self.downloading = False

        self.create_widgets()
        self.check_ffmpeg()

    # ==============================
    # FFmpeg Check (INALTERADO)
    # ==============================

    def check_ffmpeg(self):
        ffmpeg_path = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
        ffprobe_path = os.path.join(FFMPEG_DIR, "ffprobe.exe")

        if not (os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path)):
            messagebox.showerror("Erro", "FFmpeg não encontrado.")
            self.destroy()

    # ==============================
    # INTERFACE MODERNA (APENAS VISUAL)
    # ==============================

    def create_widgets(self):

        self.card = ctk.CTkFrame(
            self,
            width=650,
            height=420,
            corner_radius=30,
            fg_color="#2A2A3C"
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")

        self.title_label = ctk.CTkLabel(
            self.card,
            text="Universal Video Downloader",
            font=("Segoe UI", 28, "bold"),
            text_color="#F5E0DC"
        )
        self.title_label.pack(pady=(40, 10))

        self.subtitle = ctk.CTkLabel(
            self.card,
            text="YouTube • Instagram • TikTok",
            font=("Segoe UI", 14),
            text_color="#BAC2DE"
        )
        self.subtitle.pack(pady=(0, 25))

        self.url_entry = ctk.CTkEntry(
            self.card,
            width=500,
            height=50,
            corner_radius=20,
            placeholder_text="Cole a URL do vídeo aqui...",
            fg_color="#3A3A4F",
            border_width=0,
            text_color="white"
        )
        self.url_entry.pack(pady=10)

        self.download_btn = ctk.CTkButton(
            self.card,
            text="Baixar Vídeo",
            command=self.start_download,
            width=240,
            height=55,
            corner_radius=25,
            fg_color="#A6E3A1",
            hover_color="#94D88E",
            text_color="#1E1E2E",
            font=("Segoe UI", 15, "bold")
        )
        self.download_btn.pack(pady=25)

        self.progress_bar = ctk.CTkProgressBar(
            self.card,
            width=500,
            height=18,
            corner_radius=10,
            progress_color="#89B4FA"
        )

        self.status_label = ctk.CTkLabel(
            self.card,
            text="",
            font=("Segoe UI", 12),
            text_color="#A6ADC8"
        )

    # ==============================
    # VALIDAÇÃO (INALTERADO)
    # ==============================

    def validate_url(self, url):
        patterns = [
            r'^https?://(www\.)?instagram\.com/',
            r'^https?://(www\.)?(youtube\.com|youtu\.be)/',
            r'^https?://(www\.)?tiktok\.com/',
        ]
        return any(re.match(pattern, url) for pattern in patterns)

    # ==============================
    # DOWNLOAD (EXATAMENTE COMO ESTAVA)
    # ==============================

    def start_download(self):
        url = self.url_entry.get().strip()

        if not self.validate_url(url):
            messagebox.showwarning("URL inválida", "Cole uma URL válida.")
            return

        if self.downloading:
            return

        os.makedirs(SAVE_DIR, exist_ok=True)

        self.downloading = True
        self.download_btn.configure(state="disabled")

        self.progress_bar.pack(pady=15)
        self.status_label.pack()

        threading.Thread(target=self.download_video, args=(url,), daemon=True).start()

    def download_video(self, url):
        try:
            ydl_opts = {
                'outtmpl': os.path.join(SAVE_DIR, '%(title)s.%(ext)s'),
                'progress_hooks': [self.update_progress],
                'noplaylist': True,
                'retries': 10,
                'fragment_retries': 10,

                # 🔒 SUA CONFIGURAÇÃO ORIGINAL
                'format': 'bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best',
                'merge_output_format': 'mp4',
                'ffmpeg_location': FFMPEG_DIR,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)

            messagebox.showinfo("Sucesso", "Download concluído!")

        except Exception as e:
            messagebox.showerror("Erro", str(e)[:300])

        finally:
            self.downloading = False
            self.progress_bar.pack_forget()
            self.status_label.pack_forget()
            self.download_btn.configure(state="normal")

    # ==============================
    # PROGRESSO (INALTERADO)
    # ==============================

    def update_progress(self, d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%').strip()
            try:
                value = float(percent.replace('%', '')) / 100
                self.progress_bar.set(value)
            except:
                pass
            self.status_label.configure(text=f"Baixando... {percent}")


if __name__ == "__main__":
    app = VideoDownloaderApp()
    app.mainloop()
    