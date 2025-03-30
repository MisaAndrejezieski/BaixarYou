import os
import threading
import customtkinter as ctk
from tkinter import messagebox
import yt_dlp

# Configuração de diretórios
BASE_DIR = "D:/Programas/BaixarYou/"
SAVE_DIR = os.path.join(BASE_DIR, "Salvar")
FFMPEG_DIR = os.path.join(BASE_DIR, "ffmpeg-master-latest-win64-gpl-shared/bin")

# Configurar aparência
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class VideoDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Video Downloader Pro")
        self.geometry("720x480")
        self.minsize(600, 400)
        
        self.create_widgets()
        self.check_directories()
        
    def create_widgets(self):
        # Frame principal
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Título
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Baixar Vídeos",
            font=("Arial", 24, "bold")
        )
        self.title_label.pack(pady=20)
        
        # Entrada de URL
        self.url_entry = ctk.CTkEntry(
            self.main_frame,
            placeholder_text="Cole a URL do vídeo aqui",
            width=500,
            height=40
        )
        self.url_entry.pack(pady=10)
        
        # Botão de download
        self.download_btn = ctk.CTkButton(
            self.main_frame,
            text="Iniciar Download",
            command=self.start_download_thread,
            height=40,
            font=("Arial", 14)
        )
        self.download_btn.pack(pady=20)
        
        # Barra de progresso
        self.progress_bar = ctk.CTkProgressBar(
            self.main_frame,
            orientation="horizontal",
            mode="indeterminate",
            width=400
        )
        
        # Status
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            text_color="gray70"
        )
        
    def check_directories(self):
        required_dirs = [SAVE_DIR, FFMPEG_DIR]
        for directory in required_dirs:
            if not os.path.exists(directory):
                messagebox.showerror(
                    "Erro de Configuração",
                    f"Diretório não encontrado: {directory}"
                )
                self.destroy()
                
    def start_download_thread(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Aviso", "Por favor, insira uma URL válida")
            return
            
        self.show_progress(True)
        threading.Thread(target=self.download_video, args=(url,), daemon=True).start()
        
    def download_video(self, url):
        try:
            ydl_opts = {
                'outtmpl': os.path.join(SAVE_DIR, '%(title)s.%(ext)s'),
                'ffmpeg_location': FFMPEG_DIR,
                'progress_hooks': [self.update_progress],
                'noplaylist': True,
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
            self.show_success_message(info)
            
        except Exception as e:
            self.show_error(str(e))
        finally:
            self.show_progress(False)
            
    def update_progress(self, d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', "0%")
            speed = d.get('_speed_str', "N/A")
            self.status_label.configure(
                text=f"Baixando: {percent} | Velocidade: {speed}"
            )
            
    def show_progress(self, show=True):
        if show:
            self.progress_bar.pack(pady=10)
            self.status_label.pack(pady=5)
            self.progress_bar.start()
            self.download_btn.configure(state="disabled")
        else:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.status_label.pack_forget()
            self.download_btn.configure(state="normal")
            
    def show_success_message(self, info):
        filename = os.path.basename(info['requested_downloads'][0]['filepath'])
        messagebox.showinfo(
            "Download Concluído",
            f"Vídeo salvo em:\n{filename}"
        )
        self.url_entry.delete(0, 'end')
        
    def show_error(self, message):
        error_message = "Erro durante o download:\n"
        if "Private content" in message:
            error_message += "Conteúdo privado - Faça login primeiro"
        elif "unable to open for writing" in message:
            error_message += "Erro de permissão - Feche o arquivo se estiver aberto"
        else:
            error_message += message[:200] + "..."
            
        messagebox.showerror("Erro", error_message)

if __name__ == "__main__":
    app = VideoDownloaderApp()
    app.mainloop()
