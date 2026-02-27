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
# APARÊNCIA MODERNA
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

        self.title("Universal Video Downloader")
        self.geometry("900x650")
        self.minsize(900, 650)
        self.configure(fg_color="#1E1E2E")  # fundo dark pastel

        self.downloading = False

        self.create_widgets()
        self.check_ffmpeg()

    # ==============================
    # VERIFICAÇÃO FFmpeg
    # ==============================

    def check_ffmpeg(self):
        ffmpeg_path = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
        ffprobe_path = os.path.join(FFMPEG_DIR, "ffprobe.exe")

        if not (os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path)):
            messagebox.showerror(
                "Erro",
                f"FFmpeg não encontrado em:\n{FFMPEG_DIR}"
            )
            self.destroy()

    # ==============================
    # INTERFACE MODERNA
    # ==============================

    def create_widgets(self):

        # Card central
        self.card = ctk.CTkFrame(
            self,
            width=600,
            height=400,
            corner_radius=25,
            fg_color="#2A2A3C"
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")

        # Título
        self.title_label = ctk.CTkLabel(
            self.card,
            text="Universal Downloader",
            font=("Segoe UI", 30, "bold"),
            text_color="#F8F8F2"
        )
        self.title_label.pack(pady=(40, 10))

        self.subtitle = ctk.CTkLabel(
            self.card,
            text="YouTube • Instagram • TikTok",
            font=("Segoe UI", 14),
            text_color="#B4B4C8"
        )
        self.subtitle.pack(pady=(0, 30))

        # Campo URL
        self.url_entry = ctk.CTkEntry(
            self.card,
            width=450,
            height=45,
            corner_radius=15,
            placeholder_text="Cole a URL aqui...",
            fg_color="#3A3A4F",
            border_width=0,
            text_color="white"
        )
        self.url_entry.pack(pady=10)

        # Botão moderno pastel
        self.download_btn = ctk.CTkButton(
            self.card,
            text="Baixar em MP4",
            command=self.start_download,
            width=220,
            height=50,
            corner_radius=20,
            fg_color="#CBA6F7",  # lavanda pastel
            hover_color="#B48EED",
            text_color="#1E1E2E",
            font=("Segoe UI", 15, "bold")
        )
        self.download_btn.pack(pady=25)

        # Barra progresso
        self.progress_bar = ctk.CTkProgressBar(
            self.card,
            width=450,
            height=15,
            corner_radius=10,
            progress_color="#89B4FA"  # azul pastel
        )

        self.status_label = ctk.CTkLabel(
            self.card,
            text="",
            text_color="#A6ADC8",
            font=("Segoe UI", 12)
        )

    # ==============================
    # VALIDAÇÃO
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
                'format': 'bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best',
                'merge_output_format': 'mp4',
                'ffmpeg_location': FFMPEG_DIR,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            self.show_success(info)

        except Exception as e:
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
        messagebox.showinfo(
            "Download Concluído",
            "Seu vídeo foi salvo com sucesso em MP4!"
        )
        self.url_entry.delete(0, 'end')


if __name__ == "__main__":
    app = VideoDownloaderApp()
    app.mainloop()
    