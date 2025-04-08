import os
import threading
import customtkinter as ctk
from tkinter import messagebox
import yt_dlp
import requests
from urllib.parse import urlparse

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
        
        self.title("Video Downloader Misa")
        self.geometry("720x480")
        self.minsize(600, 400)
        
        # Opções de download
        self.format_var = ctk.StringVar(value="video")
        self.quality_var = ctk.StringVar(value="720p")
        self.playlist_var = ctk.BooleanVar(value=False)
        
        self.create_widgets()
        self.check_directories()
        
    def create_widgets(self):
        # Frame principal
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Título
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Baixar Vídeos e Imagens",
            font=("Arial", 24, "bold")
        )
        self.title_label.pack(pady=20)
        
        # Entrada de URL
        self.url_entry = ctk.CTkEntry(
            self.main_frame,
            placeholder_text="Cole a URL do vídeo ou imagem aqui",
            width=500,
            height=40
        )
        self.url_entry.pack(pady=10)
        
        # Frame de opções
        self.options_frame = ctk.CTkFrame(self.main_frame)
        self.options_frame.pack(pady=10, padx=20, fill="x")
        
        # Opções de formato
        self.format_label = ctk.CTkLabel(self.options_frame, text="Formato:")
        self.format_label.pack(side="left", padx=5)
        
        self.format_video = ctk.CTkRadioButton(
            self.options_frame,
            text="Vídeo",
            variable=self.format_var,
            value="video",
            command=self.update_options_visibility
        )
        self.format_video.pack(side="left", padx=5)
        
        self.format_audio = ctk.CTkRadioButton(
            self.options_frame,
            text="MP3",
            variable=self.format_var,
            value="audio",
            command=self.update_options_visibility
        )
        self.format_audio.pack(side="left", padx=5)
        
        self.format_image = ctk.CTkRadioButton(
            self.options_frame,
            text="Imagem",
            variable=self.format_var,
            value="image",
            command=self.update_options_visibility
        )
        self.format_image.pack(side="left", padx=5)
        
        # Seleção de qualidade
        self.quality_label = ctk.CTkLabel(self.options_frame, text="Qualidade:")
        self.quality_label.pack(side="left", padx=5)
        
        self.quality_menu = ctk.CTkOptionMenu(
            self.options_frame,
            variable=self.quality_var,
            values=["720p", "1080p", "1440p", "2160p"],
            width=100
        )
        self.quality_menu.pack(side="left", padx=5)
        
        # Checkbox de playlist
        self.playlist_check = ctk.CTkCheckBox(
            self.options_frame,
            text="Baixar Playlist",
            variable=self.playlist_var
        )
        self.playlist_check.pack(side="left", padx=20)
        
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
        
        # Inicializar visibilidade das opções
        self.update_options_visibility()
        
    def update_options_visibility(self):
        format_type = self.format_var.get()
        if format_type == "image":
            self.quality_label.pack_forget()
            self.quality_menu.pack_forget()
            self.playlist_check.pack_forget()
        else:
            self.quality_label.pack(side="left", padx=5)
            self.quality_menu.pack(side="left", padx=5)
            self.playlist_check.pack(side="left", padx=20)
            
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
        threading.Thread(target=self.download_content, args=(url,), daemon=True).start()
        
    def download_content(self, url):
        try:
            if self.format_var.get() == "image":
                self.download_image(url)
            else:
                self.download_video(url)
        except Exception as e:
            self.show_error(str(e))
        finally:
            self.show_progress(False)
            
    def download_image(self, url):
        try:
            # Verificar se a URL termina com uma extensão de imagem comum
            parsed_url = urlparse(url)
            path = parsed_url.path.lower()
            if not any(path.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                raise ValueError("URL não parece ser uma imagem válida")
            
            # Fazer o download da imagem
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Extrair o nome do arquivo da URL
            filename = os.path.basename(parsed_url.path)
            if not filename:
                filename = "imagem_baixada.jpg"
            
            # Salvar a imagem
            filepath = os.path.join(SAVE_DIR, filename)
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            messagebox.showinfo(
                "Download Concluído",
                f"Imagem salva como:\n{filename}"
            )
            self.url_entry.delete(0, 'end')
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao baixar imagem: {str(e)}")
        except ValueError as e:
            raise Exception(str(e))
            
    def download_video(self, url):
        try:
            # Configurações base
            ydl_opts = {
                'ffmpeg_location': FFMPEG_DIR,
                'progress_hooks': [self.update_progress],
                'quiet': True,
            }
            
            # Configurar formato (vídeo/áudio)
            if self.format_var.get() == "audio":
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'outtmpl': os.path.join(SAVE_DIR, '%(title)s.%(ext)s'),
                })
            else:
                # Configurar qualidade do vídeo
                quality = self.quality_var.get().replace('p', '')
                ydl_opts.update({
                    'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
                    'outtmpl': os.path.join(SAVE_DIR, '%(title)s.%(ext)s'),
                })
            
            # Configurar playlist
            ydl_opts['noplaylist'] = not self.playlist_var.get()
            
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
        elif "URL não parece ser uma imagem válida" in message:
            error_message += "A URL fornecida não parece ser uma imagem válida"
        elif "nsfw" in message.lower() or "requires authentication" in message.lower():
            error_message += "Este conteúdo requer autenticação ou é restrito (NSFW)"
        else:
            error_message += message[:200] + "..."
            
        messagebox.showerror("Erro", error_message)

if __name__ == "__main__":
    app = VideoDownloaderApp()
    app.mainloop()
