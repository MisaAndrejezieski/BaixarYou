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

# Função para fazer download de vídeos e imagens
def download_media(url, manual_filename=None):
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
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            
            # Verifica se info_dict é válido e está no formato esperado
            if not isinstance(info_dict, dict):
                raise ValueError("As informações da URL não estão no formato esperado.")

            # Usar nome manual caso fornecido; caso contrário, título original
            title = manual_filename if manual_filename else info_dict.get('title', 'Desconhecido').replace(" ", "_")
            media_type = info_dict.get('ext', 'Desconhecido')  # Tipo de mídia (mp4, jpg, etc.)
            
            # Caminho completo com nome escolhido
            filename = f"{title}.{media_type}"
            ydl_opts['outtmpl'] = os.path.join(save_folder, filename)  # Nome de saída atualizado
            ydl.download([url])  # Fazer o download usando o yt_dlp

        return title, media_type, os.path.join(save_folder, filename), None

    except KeyError as key_error:
        return None, None, None, f"Erro ao acessar uma chave inexistente: {key_error}"
    except ValueError as value_error:
        return None, None, None, f"Erro nos dados retornados: {value_error}"
    except Exception as e:
        return None, None, None, f"Erro inesperado: {e}"

# Função chamada ao clicar no botão "Iniciar Download"
def start_download(event=None):
    url = url_entry.get().strip()
    manual_filename = manual_name_entry.get().strip()  # Nome fornecido pelo usuário

    if not url:
        messagebox.showwarning("Aviso", "Por favor, insira uma URL válida.")
        return

    progress_label.config(text="Iniciando download...")
    root.update_idletasks()

    title, media_type, saved_path, result = download_media(url, manual_filename)
    if title:
        progress_label.config(text="Download concluído!")
        messagebox.showinfo(
            "Sucesso",
            f"O download foi concluído com sucesso!\n\n"
            f"➡ Título: {title}\n"
            f"➡ Tipo de mídia: {media_type}\n"
            f"➡ Caminho do arquivo: {saved_path}"
        )
    else:
        progress_label.config(text="Erro no download.")
        messagebox.showerror(
            "Erro",
            f"Algo deu errado durante o download.\n\nDetalhes do erro:\n{result}"
        )

# Função para fechar o programa
def close_program():
    root.quit()

# Configuração da interface gráfica
root = tk.Tk()
root.title("Downloader de Mídias - Vídeos e Imagens")

# Verificar se o ícone existe antes de aplicar
icon_path = r'D:\Programas\BaixarYou\Letter-B-icon_34764.ico'
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)
else:
    print(f"Ícone não encontrado no caminho: {icon_path}")

# Configuração de cores e estilos
root.geometry('500x450')  # Ajuste para uma interface mais espaçosa
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

ttk.Label(root, text="Digite um nome para o arquivo (opcional):", style='TLabel').pack(pady=20)
manual_name_entry = ttk.Entry(root, width=50, style='TEntry')
manual_name_entry.pack(pady=10)

# Vincular o evento de pressionar Enter ao início do download
url_entry.bind('<Return>', start_download)
manual_name_entry.bind('<Return>', start_download)

start_button = ttk.Button(root, text="Iniciar Download", command=start_download, style='TButton')
start_button.pack(pady=20)

close_button = ttk.Button(root, text="Fechar Programa", command=close_program, style='TButton.Red.TButton')
close_button.pack(pady=10)

progress_label = ttk.Label(root, text="", style='TLabel')
progress_label.pack(pady=10)

# Rodar a interface
root.mainloop()
