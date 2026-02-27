import os
import re
import shutil
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
FFMPEG_DIR = os.path.join(BASE_DIR, "ffmpeg-master-latest-win64-gpl-shared/bin")

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

        self.title("Universal Video Downloader by Misa Andrejezieski")
        self.geometry("800x600")
        self.minsize(800, 600)
        self.downloading = False

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.create_widgets()
        self.check_environment()

    def run_on_ui_thread(self, callback, *args, **kwargs):
        self.after(0, lambda: callback(*args, **kwargs))

    # ==============================
    # INTERFACE
    # ==============================

    def create_widgets(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        ctk.CTkLabel(
            header_frame,
            text="Universal Video Downloader",
            font=("Arial", 28, "bold")
        ).grid(row=0, column=0, pady=5)

        ctk.CTkLabel(
            header_frame,
            text="Cole a URL do Instagram, YouTube ou TikTok",
            font=("Arial", 12),
            text_color="gray"
        ).grid(row=1, column=0)

        self.url_entry = ctk.CTkEntry(self.main_frame, width=400, placeholder_text="Cole a URL aqui...")
        self.url_entry.grid(row=1, column=0, pady=10)

        self.download_btn = ctk.CTkButton(
            self.main_frame,
            text="Baixar Agora",
            command=self.start_download,
            width=200,
            height=45
        )
        self.download_btn.grid(row=2, column=0, pady=10)

        self.progress_bar = ctk.CTkProgressBar(
            self.main_frame,
            mode="determinate",
            width=400
        )

        self.status_label = ctk.CTkLabel(self.main_frame, text="")
        self.loading_label = ctk.CTkLabel(self.main_frame, text="", font=("Arial", 24))

    # ==============================
    # VERIFICAÇÕES
    # ==============================

    def check_environment(self):
        os.makedirs(SAVE_DIR, exist_ok=True)
        self.ffmpeg_location = self.resolve_ffmpeg_location()

        if self.ffmpeg_location is False:
            messagebox.showerror(
                "Erro",
                "FFmpeg não encontrado.\n"
                "Instale FFmpeg no sistema (PATH) ou mantenha os binários na pasta do projeto."
            )
            self.destroy()

    def resolve_ffmpeg_location(self):
        local_ffmpeg = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
        local_ffprobe = os.path.join(FFMPEG_DIR, "ffprobe.exe")
        if os.path.exists(local_ffmpeg) and os.path.exists(local_ffprobe):
            return FFMPEG_DIR

        if shutil.which("ffmpeg") and shutil.which("ffprobe"):
            return "PATH"

        return False

    # ==============================
    # VALIDAÇÃO DE URL
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
            messagebox.showwarning(
                "URL Inválida",
                "Cole uma URL válida do Instagram, YouTube ou TikTok."
            )
            return

        if self.downloading:
            return

        self.downloading = True
        self.show_progress(True)

        threading.Thread(
            target=self.download_video,
            args=(url,),
            daemon=True
        ).start()

    def download_video(self, url):
        try:
            ydl_opts = {
                'outtmpl': os.path.join(SAVE_DIR, '%(title)s.%(ext)s'),
                'progress_hooks': [self.update_progress],
                'noplaylist': True,
                'quiet': True,
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
                'retries': 10,
                'fragment_retries': 10,
                'logger': logging.getLogger(),
            }

            if self.ffmpeg_location not in (False, "PATH"):
                ydl_opts['ffmpeg_location'] = self.ffmpeg_location

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            self.run_on_ui_thread(self.show_success, info)

        except Exception as e:
            logging.error(str(e))
            self.run_on_ui_thread(self.show_error, str(e))
        finally:
            self.downloading = False
            self.run_on_ui_thread(self.show_progress, False)

    # ==============================
    # PROGRESSO
    # ==============================

    def update_progress(self, d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%').strip()
            try:
                progress = float(percent.replace('%', '')) / 100
                self.run_on_ui_thread(self.progress_bar.set, progress)
            except ValueError:
                pass

            self.run_on_ui_thread(self.status_label.configure, text=f"Baixando... {percent}")
            self.run_on_ui_thread(self.animate_loading)

    def show_progress(self, show=True):
        if show:
            self.progress_bar.grid(row=3, column=0, pady=15)
            self.status_label.grid(row=4, column=0)
            self.loading_label.grid(row=5, column=0)
            self.download_btn.configure(state="disabled")
            self.animate_loading()
        else:
            self.progress_bar.grid_forget()
            self.status_label.grid_forget()
            self.loading_label.grid_forget()
            self.download_btn.configure(state="normal")

    def animate_loading(self, frame=0):
        if self.downloading:
            symbols = ['⣾','⣽','⣻','⢿','⡿','⣟','⣯','⣷']
            self.loading_label.configure(text=symbols[frame % 8])
            self.after(100, lambda: self.animate_loading(frame + 1))

    # ==============================
    # MENSAGENS
    # ==============================

    def show_success(self, info):
        try:
            filename = os.path.basename(info['requested_downloads'][0]['filepath'])
        except (KeyError, IndexError, TypeError):
            filename = info.get('title', 'arquivo.mp4')

        messagebox.showinfo(
            "Download Concluído!",
            f"Arquivo salvo em:\n{os.path.join(SAVE_DIR, filename)}"
        )
        self.url_entry.delete(0, 'end')

    def show_error(self, error_msg):
        messagebox.showerror("Erro", error_msg[:300])


if __name__ == "__main__":
    app = VideoDownloaderApp()
    app.mainloop()
