import os
import re
import logging
import threading
import customtkinter as ctk
from tkinter import messagebox
import yt_dlp

# ==============================
# CONFIGURAÇÃO DE DIRETÓRIOS
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "Salvar")
FFMPEG_DIR = os.path.join(BASE_DIR, "ffmpeg-master-latest-win64-gpl-shared", "bin")

# ==============================
# APARÊNCIA
# ==============================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class VideoDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        logging.basicConfig(
            filename=os.path.join(BASE_DIR, 'download_errors.log'),
            level=logging.ERROR,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        self.title("Universal Video Downloader - MP4 Edition")
        self.geometry("800x600")
        self.minsize(800, 600)
        self.downloading = False

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.create_widgets()
        self.check_ffmpeg()

    # ==============================
    # VERIFICAÇÃO FFmpeg LOCAL
    # ==============================

    def check_ffmpeg(self):
        ffmpeg_path = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
        ffprobe_path = os.path.join(FFMPEG_DIR, "ffprobe.exe")

        if not (os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path)):
            messagebox.showerror(
                "Erro",
                f"FFmpeg não encontrado em:\n{FFMPEG_DIR}\n\n"
                "Coloque ffmpeg.exe e ffprobe.exe dentro da pasta bin."
            )
            self.destroy()

    # ==============================
    # INTERFACE
    # ==============================

    def create_widgets(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(expand=True)

        ctk.CTkLabel(
            self.main_frame,
            text="Universal Video Downloader",
            font=("Arial", 28, "bold")
        ).pack(pady=20)

        self.url_entry = ctk.CTkEntry(
            self.main_frame,
            width=500,
            placeholder_text="Cole a URL do YouTube, Instagram ou TikTok..."
        )
        self.url_entry.pack(pady=10)

        self.download_btn = ctk.CTkButton(
            self.main_frame,
            text="Baixar em MP4",
            command=self.start_download,
            width=200,
            height=45
        )
        self.download_btn.pack(pady=15)

        self.progress_bar = ctk.CTkProgressBar(
            self.main_frame,
            mode="determinate",
            width=500
        )

        self.status_label = ctk.CTkLabel(self.main_frame, text="")

    # ==============================
    # VALIDAÇÃO URL
    # ==============================

    def validate_url(self, url):
        patterns = [
            r'^https?://(www\.)?instagram\.com/',
            r'^https?://(www\.)?(youtube\.com|youtu\.be)/',
            r'^https?://(www\.)?tiktok\.com/',
        ]
        return any(re.match(pattern, url) for pattern in patterns)

    # ==============================
    # DOWNLOAD
    # ==============================

    def start_download(self):
        url = self.url_entry.get().strip()

        if not self.validate_url(url):
            messagebox.showwarning("URL Inválida", "Cole uma URL válida.")
            return

        if self.downloading:
            return

        os.makedirs(SAVE_DIR, exist_ok=True)

        self.downloading = True
        self.progress_bar.pack(pady=10)
        self.status_label.pack()
        self.download_btn.configure(state="disabled")

        threading.Thread(target=self.download_video, args=(url,), daemon=True).start()

    def download_video(self, url):
        try:
            ydl_opts = {
                'outtmpl': os.path.join(SAVE_DIR, '%(title)s.%(ext)s'),
                'progress_hooks': [self.update_progress],
                'noplaylist': True,
                'retries': 10,
                'fragment_retries': 10,
                'logger': logging.getLogger(),

                # 🔥 Força MP4 compatível
                'format': 'bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best',

                # 🔥 Sempre converte para MP4
                'merge_output_format': 'mp4',

                # 🔥 Usa FFmpeg local
                'ffmpeg_location': FFMPEG_DIR,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            self.show_success(info)

        except Exception as e:
            logging.error(str(e))
            messagebox.showerror("Erro", str(e)[:300])

        finally:
            self.downloading = False
            self.progress_bar.pack_forget()
            self.status_label.pack_forget()
            self.download_btn.configure(state="normal")

    # ==============================
    # PROGRESSO
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

    # ==============================
    # SUCESSO
    # ==============================

    def show_success(self, info):
        filename = info.get('title', 'video') + ".mp4"
        messagebox.showinfo(
            "Download Concluído",
            f"Arquivo salvo em:\n{os.path.join(SAVE_DIR, filename)}"
        )
        self.url_entry.delete(0, 'end')


if __name__ == "__main__":
    app = VideoDownloaderApp()
    app.mainloop()
    