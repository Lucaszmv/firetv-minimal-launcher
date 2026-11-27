# 📺 FireTV Minimal Launcher

Launcher minimalista para **Fire TV Stick**, baseado no projeto **[Free My TV](https://github.com/simbasjungles/free-my-tv)** (`simbasjungles`), adaptado para remover bloat da Amazon, exibir recomendações do TMDB, prateleira de apps estilo tvOS e screensaver "Dream".

---

## ✨ Recursos

- **Launcher estilo tvOS:** prateleira de aplicativos com ícones por marca e foco destacado.
- **Recomendações TMDB:** rail de filmes/séries e card principal 16:9 com sinopse.
- **Screensaver "Dream":** fundo com blur suave do card focado, relógio e clima.
- **Debloat & Home Trap:** scripts Python via ADB para desativar pacotes Amazon desnecessários e redirecionar o botão Home para o launcher.
- **Bloqueio de OTA (opcional):** scripts auxiliares para bloquear atualizações automáticas via DNS/NetGuard.

---

## 🗂️ Estrutura do Projeto

```text
├── free-my-tv/               # App Android (launcher + screensaver)
│   ├── app/src/io/freemytv/  # Código-fonte Java
│   ├── tools/                # Scripts Python para geração de assets
│   ├── build.sh              # Build sem Gradle (Linux/macOS)
│   ├── build_windows.py      # Pipeline de build no Windows
│   ├── config.example.properties  # Modelo de configuração (TMDB key, região, cidade)
│   └── LICENSE               # MIT
└── scripts/                  # Utilitários ADB em Python para Fire TV
    ├── common_adb.py         # Wrapper de conexão/serial do ADB
    ├── dev.py                # Descoberta do Fire TV na rede local
    ├── fire_install.py       # Instalação, debloat e Home Trap (+ --revert)
    ├── fire_debloat.py       # Lista de pacotes Amazon para desativar
    └── fire_dns_block.py     # Bloqueio de domínios OTA
```

---

## ⚠️ Aviso importante sobre os `scripts/`

Os scripts em `scripts/` foram escritos para o meu ambiente e modelo de Fire TV Stick. Antes de rodar no seu aparelho, ajuste:

1. **IP / Serial ADB:** defina a variável de ambiente `FMTV_IP` (ou passe o IP do seu Fire TV na rede local) e confira o caminho do `adb` em `scripts/common_adb.py`.
2. **Lista de pacotes (`scripts/fire_debloat.py`):** versões diferentes do Fire OS possuem pacotes diferentes; revise a lista antes de aplicar o debloat (use `--revert` no `fire_install.py` se precisar reverter).

---

## 🚀 Como compilar e configurar

1. Copie `free-my-tv/config.example.properties` para `free-my-tv/config.properties` e preencha sua chave gratuita da API do TMDB, região e cidade.
2. Gere sua keystore (`freemytv.keystore`) e execute o build:

```bash
# Windows
python free-my-tv/build_windows.py

# Linux / macOS
bash free-my-tv/build.sh
```