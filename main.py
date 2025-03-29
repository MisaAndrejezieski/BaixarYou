import yt_dlp
import tkinter as tk
from tkinter import messagebox, ttk
import os

# Caminhos principais
save_folder = r'D:\Programas\BaixarYou\Salvar'
cookie_path = r'D:\Programas\BaixarYou\.venv\cookies.txt'

# Garantir que a pasta de salvamento existe
if not os.path.exists(save_folder):
    os.makedirs(save_folder)
    print(f"Pasta de salvamento criada: {save_folder}")

# Função para gerar um número sequencial para os arquivos
def generate_filename(title, extension):
    # Verificar arquivos existentes na pasta de salvamento
    existing_files = [f for f in os.listdir(save_folder) if f.startswith(title) and f.endswith(f".{extension}")]
    next_number = len(existing_files) + 1  # Próximo número com base nos arquivos existentes
    return f"{title}_{next_number:03d}.{extension}"  # Formato 001, 002, etc.

def download_media(url):
    # Verifica se o arquivo cookies.txt existe e é acessível
    if not os.path.exists(cookie_path):
        return None, None, None, f"Erro: O arquivo cookies.txt não foi encontrado no caminho: {cookie_path}"

    try:
        with open(cookie_path, 'r') as file:
            print("O arquivo cookies.txt foi lido com sucesso!")
    except Exception as e:
        return None, None, None, f"Erro ao acessar o arquivo cookies.txt: {e}"

    ydl_opts = {
        'format': 'best',  # Baixa o melhor formato disponível (vídeo ou imagem)
        'quiet': True,
        'no_warnings': True,
        'cookiefile': cookie_path,  # Caminho para o arquivo de cookies
        'ignoreerrors': True,  # Ignora erros e continua com outros downloads
        'extract_flat': True,  # Tenta extrair mídia mesmo em casos complexos
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            # Verifica se info_dict é um dicionário válido
            if not isinstance(info_dict, dict):
                return None, None, None, "Erro: Não foi possível extrair informações da URL."

            title = info_dict.get('title', 'Desconhecido').replace(" ", "_")  # Substituir espaços no título
            media_type = info_dict.get('ext', 'Desconhecido')  # Tipo de mídia (mp4, jpg, etc.)

            # Gerar o nome do arquivo com numeração sequencial
            filename = generate_filename(title, media_type)
            ydl_opts['outtmpl'] = os.path.join(save_folder, filename)  # Atualizar nome de saída
            ydl.download([url])  # Fazer o download usando o yt_dlp

        return title, media_type, os.path.join(save_folder, filename), None

    except Exception as e:
        return None, None, None, str(e)

def start_download(event=None):  # Adicionado event=None para suportar pressionar Enter
    url = url_entry.get().strip()
    if not url:
        messagebox.showwarning("Aviso", "Por favor, insira uma URL válida.")
        return

    progress_label.config(text="Iniciando download...")
    root.update_idletasks()

    title, media_type, saved_path, result = download_media(url)
    if title:
        progress_label.config(text="Download concluído!")
        messagebox.showinfo("Sucesso", f"Título: {title}\nTipo de mídia: {media_type}\nSalvo em:\n{saved_path}")
    else:
        progress_label.config(text="Erro no download.")
        messagebox.showerror("Erro", f"Ocorreu um erro: {result}")

def close_program():
    root.quit()

# Configuração da interface gráfica
root = tk.Tk()
root.title("Downloader de Vídeos e Imagens")

# Verificar se o ícone existe antes de aplicar
icon_path = r'D:\Programas\BaixarYou\Letter-B-icon_34764.ico'
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)
else:
    print(f"Ícone não encontrado no caminho: {icon_path}")

# Configuração de cores e estilos
root.geometry('500x350')
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
url_entry.focus()  # Foca no campo de entrada ao iniciar o programa

# Vincular o evento de pressionar Enter ao início do download
url_entry.bind('<Return>', start_download)

start_button = ttk.Button(root, text="Iniciar Download", command=start_download, style='TButton')
start_button.pack(pady=20)

close_button = ttk.Button(root, text="Fechar Programa", command=close_program, style='TButton.Red.TButton')
close_button.pack(pady=10)

progress_label = ttk.Label(root, text="", style='TLabel')
progress_label.pack(pady=10)

root.mainloop()
