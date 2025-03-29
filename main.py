import yt_dlp
import tkinter as tk
from tkinter import messagebox, ttk
import os

# Caminho principal
save_folder = r'D:\Programas\BaixarYou\Salvar'
cookie_path = r'D:\Programas\BaixarYou\.venv\cookies.txt'

# Garantir que a pasta de salvamento existe
if not os.path.exists(save_folder):
    os.makedirs(save_folder)
    print(f"Pasta de salvamento criada: {save_folder}")

# Função para baixar vídeos usando yt-dlp
def download_video(url):
    try:
        ydl_opts = {
            'format': 'best',  # Baixa o melhor formato disponível
            'quiet': True,
            'no_warnings': True,
            'cookiefile': cookie_path,  # Caminho para o arquivo de cookies
            'ignoreerrors': True,  # Ignorar erros e continuar
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

            if not os.path.exists(saved_path):
                raise FileNotFoundError(f"O arquivo {saved_path} não foi encontrado após o download.")

            return title, ext, saved_path, None

    except FileNotFoundError as fnf_error:
        return None, None, None, f"Erro ao salvar o arquivo: {fnf_error}"
    except ValueError as value_error:
        return None, None, None, f"Erro nos dados retornados: {value_error}"
    except Exception as e:
        return None, None, None, f"Erro inesperado: {e}"

# Função chamada ao clicar no botão "Iniciar Download"
def start_download(event=None):
    url = url_entry.get().strip()

    if not url:
        messagebox.showwarning("Aviso", "Por favor, insira uma URL válida.")
        return

    progress_label.config(text="Iniciando download...")
    root.update_idletasks()

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

# Função para fechar o programa
def close_program():
    root.quit()

# Configuração da interface gráfica
root = tk.Tk()
root.title("Downloader de Vídeos")

# Configuração de cores e estilos
root.geometry('500x400')
root.configure(bg='#282c34')

style = ttk.Style()
style.theme_use('clam')

style.configure('TButton', background='#4CAF50', foreground='#ffffff', font=('Helvetica', 12, 'bold'))
style.map('TButton', background=[('active', '#56b6c2')])
style.configure('TButton.Red.TButton', background='#f44336', foreground='#ffffff', font=('Helvetica', 12, 'bold'))
style.map('TButton.Red.TButton', background=[('active', '#d32f2f')])
style.configure('TLabel', background='#282c34', foreground='#61afef', font=('Helvetica', 12))
style.configure('TEntry', font=('Helvetica', 12), padding=5)

# Elementos da interface
ttk.Label(root, text="Cole aqui sua URL:", style='TLabel').pack(pady=20)

url_entry = ttk.Entry(root, width=50, style='TEntry')
url_entry.pack(pady=10)
url_entry.focus()

start_button = ttk.Button(root, text="Iniciar Download", command=start_download, style='TButton')
start_button.pack(pady=20)

close_button = ttk.Button(root, text="Fechar Programa", command=close_program, style='TButton.Red.TButton')
close_button.pack(pady=10)

progress_label = ttk.Label(root, text="", style='TLabel')
progress_label.pack(pady=10)

# Rodar a interface
root.mainloop()
