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
        
        self.title("Instagram Downloader by Misa Andrejezieski")
        self.geometry("800x600")  # Janela um pouco maior
        self.minsize(800, 600)
        
        # Configurar grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.create_widgets()
        self.check_directories()
        
    def create_widgets(self):
        # Container principal
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        # Frame do cabeçalho
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        self.header_frame.grid_columnconfigure(0, weight=1)
        
        # Título principal
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Instagram Downloader",
            font=("Arial", 32, "bold"),
            text_color=("gray10", "gray90")
        )
        self.title_label.grid(row=0, column=0, pady=10)
        
        # Subtítulo
        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Baixe seus conteúdos favoritos do Instagram",
            font=("Arial", 14),
            text_color=("gray40", "gray60")
        )
        self.subtitle_label.grid(row=1, column=0)
        
        # Frame principal de conteúdo
        self.content_frame = ctk.CTkFrame(self.main_container)
        self.content_frame.grid(row=1, column=0, sticky="nsew", pady=20)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # Frame da URL
        self.url_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.url_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=20)
        self.url_frame.grid_columnconfigure(1, weight=1)
        
        # Label URL
        self.url_label = ctk.CTkLabel(
            self.url_frame,
            text="URL do Post ou Reels:",
            font=("Arial", 14, "bold")
        )
        self.url_label.grid(row=0, column=0, padx=(0, 10))
        
        # Entrada de URL com novo estilo
        self.url_entry = ctk.CTkEntry(
            self.url_frame,
            placeholder_text="Cole a URL do post ou reels do Instagram aqui",
            height=40,
            font=("Arial", 12)
        )
        self.url_entry.grid(row=0, column=1, sticky="ew")
        
        # Frame de ações
        self.action_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.action_frame.grid(row=1, column=0, sticky="ew", padx=30, pady=20)
        self.action_frame.grid_columnconfigure(0, weight=1)
        
        # Botão de download com novo estilo
        self.download_btn = ctk.CTkButton(
            self.action_frame,
            text="Iniciar Download",
            command=self.start_download_thread,
            height=45,
            font=("Arial", 14, "bold"),
            fg_color=("blue", "blue"),
            hover_color=("darkblue", "darkblue"),
            corner_radius=10
        )
        self.download_btn.grid(row=0, column=0, pady=10)
        
        # Frame de progresso
        self.progress_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.progress_frame.grid(row=2, column=0, sticky="ew", padx=30, pady=10)
        self.progress_frame.grid_columnconfigure(0, weight=1)
        
        # Barra de progresso com novo estilo
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            orientation="horizontal",
            mode="indeterminate",
            height=10,
            corner_radius=5
        )
        
        # Status com novo estilo
        self.status_label = ctk.CTkLabel(
            self.progress_frame,
            text="",
            font=("Arial", 12),
            text_color=("gray40", "gray60")
        )
        
        # Frame de informações
        self.info_frame = ctk.CTkFrame(self.content_frame)
        self.info_frame.grid(row=3, column=0, sticky="ew", padx=30, pady=20)
        self.info_frame.grid_columnconfigure(0, weight=1)
        
        # Texto informativo
        self.info_label = ctk.CTkLabel(
            self.info_frame,
            text="Os conteúdos serão salvos na pasta 'Salvar'",
            font=("Arial", 12),
            text_color=("gray40", "gray60")
        )
        self.info_label.grid(row=0, column=0, pady=10)
        
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
                'format': 'best',  # Seleciona a melhor qualidade disponível
                'concurrent_fragments': 3,  # Download paralelo de fragmentos
                'retries': 10,  # Aumenta o número de tentativas em caso de erro
                'fragment_retries': 10,  # Aumenta as tentativas para fragmentos
                'buffersize': 1024 * 16,  # Aumenta o buffer de download
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
            self.progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, 5))
            self.status_label.grid(row=1, column=0, pady=(0, 5))
            self.progress_bar.start()
            self.download_btn.configure(state="disabled")
        else:
            self.progress_bar.stop()
            self.progress_bar.grid_forget()
            self.status_label.grid_forget()
            self.download_btn.configure(state="normal")
            
    def show_success_message(self, info):
        filename = os.path.basename(info['requested_downloads'][0]['filepath'])
        messagebox.showinfo(
            "Download Concluído",
            f"Conteúdo salvo em:\n{filename}"
        )
        self.url_entry.delete(0, 'end')
        
    def show_error(self, message):
        error_message = "Erro durante o download:\n"
        if "Private content" in message:
            error_message += "Conteúdo privado - Esta conta do Instagram é privada"
        elif "unable to open for writing" in message:
            error_message += "Erro de permissão - Feche o arquivo se estiver aberto"
        elif "HTTP Error 403" in message:
            error_message += "Erro de acesso - Instagram bloqueou o download.\nTente novamente em alguns minutos."
        elif "Cloudflare" in message:
            error_message += "Site protegido.\nTente novamente em alguns minutos."
        elif "Unsupported URL" in message:
            error_message += "URL inválida. Certifique-se de que é uma URL válida do Instagram"
        else:
            error_message += message[:200] + "..."
            
        messagebox.showerror("Erro", error_message)

if __name__ == "__main__":
    app = VideoDownloaderApp()
    app.mainloop()
