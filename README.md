📥 BaixarYou - Downloader Universal de Vídeos
https://img.shields.io/badge/Python-3.8%252B-blue
https://img.shields.io/badge/License-MIT-green
https://img.shields.io/badge/Status-Est%C3%A1vel-brightgreen
https://img.shields.io/badge/Plataformas-9%252B-orange

Baixe vídeos e áudios de YouTube, Instagram, TikTok, Twitter/X, Facebook, Vimeo, SoundCloud, Twitch e Reddit com interface gráfica moderna e intuitiva.

https://screenshot.png

📋 Índice
Funcionalidades

Plataformas Suportadas

Requisitos

Instalação

Como Usar

Configuração de Cookies (Instagram)

Estrutura do Projeto

Compilando para Executável

Histórico de Downloads

Resolução de Problemas

Aviso Legal

Tecnologias Utilizadas

Contribuição

Licença

✨ Funcionalidades
Funcionalidade	Descrição
🎬 Download de Vídeos	Baixa vídeos em diversas qualidades (best, 1080p, 720p, 480p)
🎵 Extração de Áudio	Converte vídeos para MP3 (192kbps) automaticamente
📋 Suporte a Playlists	Baixa playlists inteiras do YouTube de uma só vez
🍪 Autenticação por Cookies	Suporte a cookies.txt para plataformas que exigem login (Instagram)
📊 Barra de Progresso	Acompanhe o progresso em tempo real com velocidade de download
📜 Histórico de Downloads	Registro completo de todos os downloads realizados (JSON)
📝 Sistema de Logs	Logs detalhados em arquivo para depuração
🖥️ Interface Moderna	GUI construída com CustomTkinter (modo escuro por padrão)
📂 Pasta Personalizável	Escolha onde salvar seus arquivos
🌐 Detecção Automática	Identifica automaticamente a plataforma pela URL
⚡ Multi-threading	Downloads executados em thread separada (interface não trava)
🌍 Plataformas Suportadas
Plataforma	Status	Requer Cookies?
YouTube	✅ Total	Não
Instagram	⚠️ Parcial	Sim (recomendado)
TikTok	✅ Total	Não
Twitter/X	✅ Total	Não
Facebook	✅ Total	Não
Vimeo	✅ Total	Não
SoundCloud	✅ Total	Não
Twitch	✅ Total	Não
Reddit	✅ Total	Não
📦 Requisitos
Dependências Python
text
Python 3.8 ou superior
yt-dlp >= 2024.12.13
customtkinter >= 5.2.0
Dependências do Sistema
FFmpeg (necessário para extração de áudio MP3 e merge de formatos)

Instalação do FFmpeg:

Windows: Baixe de ffmpeg.org e adicione ao PATH

macOS: brew install ffmpeg

Linux: sudo apt install ffmpeg (Ubuntu/Debian) ou sudo pacman -S ffmpeg (Arch)

🚀 Instalação
Método 1: Clonar e Executar (Recomendado para Desenvolvedores)
bash
# Clone o repositório
git clone https://github.com/MisaAndrejezieski/BaixarYou.git
cd BaixarYou

# Crie um ambiente virtual (opcional, mas recomendado)
python -m venv venv

# Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Execute o programa
python main.py
Método 2: Executável (Usuários Finais)
Baixe o arquivo BaixarYou.exe da seção de Releases e execute diretamente (não requer Python instalado).

📖 Como Usar
Download Básico
Copie a URL do vídeo desejado (YouTube, Instagram, TikTok, etc.)

Cole a URL no campo de texto do programa

Selecione a qualidade desejada no menu suspenso:

best (recomendado) — Melhor qualidade disponível

1080p — Full HD

720p — HD

480p — SD

Apenas Áudio (MP3) — Extrai apenas o áudio

Clique em "BAIXAR VÍDEO"

Aguarde a conclusão — o arquivo estará na pasta Downloads/

Download de Playlist (YouTube)
Cole a URL da playlist do YouTube

Marque a caixa de seleção "📋 Playlist (baixar todos)"

Clique em "BAIXAR VÍDEO"

Todos os vídeos da playlist serão baixados sequencialmente

Gerenciamento de Arquivos
📂 Abrir Pasta: Abre o diretório onde os arquivos são salvos

🗂️ Mudar Pasta: Altera o local de destino dos downloads

📜 Histórico: Exibe os últimos 20 downloads realizados com status, data e URL

🍪 Configuração de Cookies (Instagram)
O Instagram frequentemente exige autenticação para download. Siga estes passos:

Passo 1: Instalar a Extensão
Instale a extensão "Get cookies.txt LOCALLY" no seu navegador:

Chrome/Edge/Brave

Firefox

Passo 2: Exportar Cookies
Faça login no Instagram no seu navegador

Clique no ícone da extensão

Selecione "Export" (exportar)

Salve o arquivo como cookies.txt

Passo 3: Posicionar o Arquivo
Copie o arquivo cookies.txt para a pasta raiz do programa (ao lado do main.py ou do executável).

Verificação
Ao iniciar o programa, você verá a mensagem:

text
✅ cookies.txt carregado (XX cookies)
🍪 XX cookies - Instagram OK
Nota: O programa funciona perfeitamente sem cookies para YouTube, TikTok, Twitter e outras plataformas. Os cookies são necessários apenas para o Instagram e situações específicas.

📁 Estrutura do Projeto
text
BaixarYou/
├── main.py                  # Código principal da aplicação
├── requirements.txt         # Dependências Python
├── cookies.txt              # Cookies para autenticação (criado pelo usuário)
├── download_history.json    # Histórico de downloads (gerado automaticamente)
├── Downloads/               # Pasta padrão de downloads (gerada automaticamente)
├── logs/
│   └── downloader.log       # Logs de execução (gerado automaticamente)
├── README.md                # Esta documentação
└── screenshot.png           # Captura de tela da interface
Arquivos Gerados Automaticamente
Arquivo	Função
download_history.json	Armazena o histórico completo de downloads
logs/downloader.log	Registro detalhado de todas as operações e erros
Downloads/	Pasta padrão onde os vídeos são salvos
🔧 Compilando para Executável
Para gerar um arquivo .exe standalone (Windows):

Passo 1: Instalar PyInstaller
bash
pip install pyinstaller
Passo 2: Gerar o Executável
bash
pyinstaller --onefile --windowed --name "BaixarYou" --add-data "requirements.txt;." main.py
Opções Adicionais
bash
# Com ícone personalizado
pyinstaller --onefile --windowed --icon=icon.ico --name "BaixarYou" main.py

# Sem console (modo silencioso)
pyinstaller --onefile --windowed --noconsole --name "BaixarYou" main.py
O executável será gerado na pasta dist/.

📜 Histórico de Downloads
O programa mantém um registro automático de todos os downloads no arquivo download_history.json:

json
[
  {
    "url": "https://www.youtube.com/watch?v=...",
    "title": "Nome do Vídeo",
    "platform": "YouTube",
    "status": "SUCCESS",
    "error": "",
    "save_dir": "C:\\...\\Downloads",
    "timestamp": "2026-01-15T14:30:00.000000"
  }
]
Para visualizar, clique em "📜 Histórico" na interface ou abra o arquivo JSON diretamente.

🛠️ Resolução de Problemas
Erro 429 (Instagram)
Problema: "Instagram bloqueou temporariamente (429)"

Solução:

Aguarde 5-10 minutos antes de tentar novamente

Utilize o arquivo cookies.txt com uma conta logada

Evite múltiplos downloads em sequência rápida

Vídeo não encontrado / URL inválida
Verifique:

Se a URL está correta e completa (incluindo https://)

Se o vídeo não foi removido ou está privado

Se a plataforma é suportada

Erro de FFmpeg
Problema: Downloads de alta qualidade ou extração de áudio falham

Solução:

Instale o FFmpeg (veja Requisitos)

Verifique se o FFmpeg está no PATH do sistema

Teste com ffmpeg -version no terminal

Interface não abre
Possíveis causas:

Python < 3.8 → Atualize para 3.8+

CustomTkinter não instalado → pip install customtkinter

yt-dlp desatualizado → pip install --upgrade yt-dlp

⚠️ Aviso Legal
Este software é fornecido apenas para fins educacionais e uso pessoal legítimo.

Respeite os direitos autorais: Baixe apenas conteúdo que você tem permissão para baixar

Verifique os Termos de Serviço: Cada plataforma possui suas próprias regras sobre download de conteúdo

Uso pessoal: Este programa destina-se ao download de conteúdo próprio ou de domínio público

Responsabilidade: O autor não se responsabiliza pelo uso indevido desta ferramenta

💡 Dica: Use esta ferramenta para baixar seus próprios vídeos, conteúdos Creative Commons ou materiais com permissão explícita do criador.

🔬 Tecnologias Utilizadas
Tecnologia	Uso
Python 3.8+	Linguagem principal
yt-dlp	Engine de download (fork ativo do youtube-dl)
CustomTkinter	Interface gráfica moderna
Tkinter	Base da GUI
FFmpeg	Processamento de áudio/vídeo
JSON	Persistência de dados
Threading	Execução assíncrona
🤝 Contribuição
Contribuições são bem-vindas! Para contribuir:

Faça um Fork do projeto

Crie uma Branch para sua feature (git checkout -b feature/nova-funcionalidade)

Faça o Commit das alterações (git commit -m 'Adiciona nova funcionalidade')

Faça o Push para a Branch (git push origin feature/nova-funcionalidade)

Abra um Pull Request

Áreas que precisam de contribuição:
Testes automatizados

Suporte a mais plataformas

Interface em outros idiomas

Versão para Linux/macOS (empacotamento)

Fila de downloads múltiplos

Agendamento de downloads

📄 Licença
Este projeto está licenciado sob a Licença MIT — veja o arquivo LICENSE para detalhes.

text
MIT License

Copyright (c) 2026 Misa Andrejezieski

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
...
🌟 Agradecimentos
Equipe yt-dlp pelo excelente trabalho mantendo a biblioteca

Tom Schimansky pelo CustomTkinter

Comunidade Python open-source

📞 Contato
GitHub: @MisaAndrejezieski

Issues: Abrir um problema

⭐ Se este projeto foi útil, considere deixar uma estrela no repositório!

Arquivos complementares para criar:

requirements.txt
text
yt-dlp>=2024.12.13
customtkinter>=5.2.0
.gitignore
text
# Diretórios gerados
Downloads/
logs/
__pycache__/
*.pyc
*.pyo
build/
dist/
*.spec

# Arquivos de ambiente
venv/
env/
.env

# Arquivos do sistema
.DS_Store
Thumbs.db

# Arquivos sensíveis
cookies.txt
download_history.json

# IDE
.vscode/
.idea/