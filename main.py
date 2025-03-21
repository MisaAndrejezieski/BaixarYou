import yt_dlp
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
import os
import threading
from PIL import Image, ImageTk
import requests
from io import BytesIO

def download_video(url, output_dir):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            title = info_dict.get('title', 'Unknown')
            thumbnail_url = info_dict.get('thumbnail', 'No thumbnail available')

        return title, thumbnail_url

    except Exception as e:
        return None, str(e)

def start_download_thread():
    url = url_entry.get().strip()
    if not url:
        messagebox.showwarning("Aviso", "Por favor, insira uma URL válida.")
        return

    output_dir = filedialog.askdirectory(title="Selecione o diretório para salvar o vídeo")
    if not output_dir:
        messagebox.showwarning("Aviso", "Nenhum diretório selecionado.")
        return

    progress_label.config(text="Iniciando download...")
    root.update_idletasks()

    # Iniciar o download em uma thread separada
    threading.Thread(target=download_video_task, args=(url, output_dir)).start()

def download_video_task(url, output_dir):
    try:
        title, result = download_video(url, output_dir)
        if title:
            progress_label.config(text="Download concluído!")
            messagebox.showinfo("Sucesso", f"Título: {title}")
            # Exibir miniatura
            if result.startswith("http"):
                response = requests.get(result)
                img_data = BytesIO(response.content)
                img = Image.open(img_data)
                img.thumbnail((200, 200))
                thumbnail = ImageTk.PhotoImage(img)
                thumbnail_label.config(image=thumbnail)
                thumbnail_label.image = thumbnail
        else:
            progress_label.config(text="Erro no download.")
            messagebox.showerror("Erro", f"Ocorreu um erro: {result}")
    except Exception as e:
        progress_label.config(text="Erro no download.")
        messagebox.showerror("Erro", f"Ocorreu um erro inesperado: {str(e)}")

def close_program():
    root.quit()

# Configuração da interface gráfica
root = tk.Tk()
root.title("Downloader de Vídeos")

# Verificar se o ícone existe antes de aplicar
icon_path = 'D:\\BaixarYou\\Letter-B-icon_34764.ico'
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)
else:
    print(f"Ícone não encontrado no caminho: {icon_path}")

# Configuração de cores e estilos
root.geometry('600x400')
root.configure(bg='#282c34')

style = ttk.Style()
style.theme_use('clam')

style.configure('TButton', background='#4CAF50', foreground='#ffffff', font=('Helvetica', 12, 'bold'))
style.map('TButton', background=[('active', '#56b6c2')])
style.configure('TButton.Red.TButton', background='#f44336', foreground='#ffffff', font=('Helvetica', 12, 'bold'))
style.map('TButton.Red.TButton', background=[('active', '#d32f2f')])
style.configure('TLabel', background='#282c34', foreground='#61afef', font=('Helvetica', 10))
style.configure('TEntry', font=('Helvetica', 10))

# Elementos da interface
ttk.Label(root, text="Cole aqui sua URL:", style='TLabel').pack(pady=20)
url_entry = ttk.Entry(root, width=50)
url_entry.pack(pady=5)

start_button = ttk.Button(root, text="Iniciar Download", command=start_download_thread, style='TButton')
start_button.pack(pady=20)

close_button = ttk.Button(root, text="Fechar Programa", command=close_program, style='TButton.Red.TButton')
close_button.pack(pady=10)

progress_label = ttk.Label(root, text="", style='TLabel')
progress_label.pack(pady=5)

thumbnail_label = ttk.Label(root, style='TLabel')
thumbnail_label.pack(pady=10)

root.mainloop()
