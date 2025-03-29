import yt_dlp
import tkinter as tk
from tkinter import messagebox, ttk
import os

# Caminho principal
save_folder = r'D:\Programas\BaixarYou\Salvar'
cookie_path = r'D:\Programas\BaixarYou\.venv\cookies.txt'
icon_path = r'D:\Programas\BaixarYou\Letter-B-icon_34764.ico'

# Garantir que a pasta de salvamento existe
if not os.path.exists(save_folder):
    os.makedirs(save_folder)

# Função para baixar vídeos usando yt-dlp
def download_video(url):
    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',  # Combina melhor vídeo e áudio ou baixa o melhor formato disponível
            'quiet': True,
            'no_warnings': True,
            'cookiefile': cookie_path,
            'outtmpl': os.path.join(save_folder, '%(title)s.%(ext)s'),  # Nome do arquivo com extensão apropriada
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            
            # Verificar se o info_dict foi preenchido corretamente
            if not info_dict:
                raise ValueError("Não foi possível obter informações da URL fornecida.")

            title = info_dict.get('title', 'Desconhecido').replace(" ", "_")
            ext = info_dict.get('ext', 'mp4')  # Usa "mp4" como padrão caso não haja extensão
            saved_path = os.path.join(save_folder, f"{title}.{ext}")

            return title, ext, saved_path, None

    except Exception as e:
        return None, None, None, f"Erro ao realizar o download: {e}"

# Função chamada ao clicar no botão "Iniciar Download"
def start_download(event=None):
    url = url_entry.get().strip()

    if not url:
        messagebox.showwarning("Aviso", "Por favor, insira uma URL válida.")
        return

    progress_label.config(text="Iniciando download...")
    
    try:
        title, ext, saved_path, error = download_video(url)
        if title:
            progress_label.config(text="Download concluído!")
            messagebox.showinfo(
                "Sucesso",
                f"O download foi concluído com sucesso!\n\n"
                f"➡ Título: {title}\n"
                f"➡ Tipo de mídia: {ext}\n"
                f"➡ Caminho do arquivo: {saved_path}"
            )
        else:
            progress_label.config(text="Erro no download.")
            messagebox.showerror(
                "Erro",
                f"Algo deu errado durante o download.\n\nDetalhes do erro:\n{error}"
            )
    finally:
        progress_label.config(text="Pronto para começar!")

# Função para fechar o programa
def close_program():
    root.quit()

# Configuração da interface gráfica
root = tk.Tk()
root.title("Downloader de Vídeos")

if os.path.exists(icon_path):
    root.iconbitmap(icon_path)

root.geometry('600x450')
root.configure(bg='#1f2937')
root.resizable(False, False)

style = ttk.Style()
style.theme_use('clam')

style.configure('TButton', background='#2563eb', foreground='#ffffff', font=('Helvetica', 12, 'bold'))
style.configure('TLabel', background='#1f2937', foreground='#ffffff', font=('Helvetica', 13))
style.configure('TEntry', font=('Helvetica', 12), padding=5)

ttk.Label(root, text="🎥 Downloader de Vídeos 🎥", style='TLabel', font=('Helvetica', 18, 'bold')).pack(pady=20)
ttk.Label(root, text="Cole aqui sua URL:", style='TLabel').pack(pady=10)

url_entry = ttk.Entry(root, width=60, style='TEntry')
url_entry.pack(pady=10)
url_entry.focus()

start_button = ttk.Button(root, text="Iniciar Download", command=start_download, style='TButton')
start_button.pack(pady=20)

progress_label = ttk.Label(root, text="Pronto para começar!", style='TLabel', font=('Helvetica', 12))
progress_label.pack(pady=10)

close_button = ttk.Button(root, text="Fechar Programa", command=close_program, style='TButton')
close_button.pack(pady=20)

footer_label = ttk.Label(root, text="Desenvolvido por Misael © 2025", style='TLabel', font=('Helvetica', 10, 'italic'))
footer_label.pack(side='bottom', pady=10)

root.mainloop()
