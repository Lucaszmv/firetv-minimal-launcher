# FireStickMod

> **Free My TV** customizado para Fire TV Stick â€” Launcher minimalista, sem bloat Amazon, com recomendaÃ§Ãµes TMDB, apps em shelf estilo tvOS e screensaver "Dream".

Baseado no projeto **[Free My TV](https://github.com/simbasjungles/free-my-tv)** (simbasjungles) â€” inspiraÃ§Ã£o direta, cÃ³digo adaptado e simplificado para Fire TV.

---

## ðŸŽ¯ O que Ã©

Um **launcher** (home screen) para Fire TV Stick que:

- **Remove bloat Amazon** (anÃºncios, telemetria, OTA forÃ§ado, screensaver padrÃ£o)
- **Shelf de apps estilo tvOS** â€” Ã­cones coloridos por marca, foco com grow + shadow + anel cinza-claro
- **Rail de recomendaÃ§Ãµes TMDB** â€” 3 cards/hora (manhÃ£/tarde/noite), card principal 16:9 "billboard" com sinopse
- **Screensaver "Dream"** â€” foto do card focado, blur suave, relÃ³gio + clima
- **Debloat automÃ¡tico** â€” desativa pacotes Amazon desnecessÃ¡rios no install
- **Home Trap** â€” botÃ£o Home sempre volta pra cÃ¡ (acessibilidade service)
- **DNS block OTA** â€” opcional, impede atualizaÃ§Ãµes Amazon automÃ¡ticas

---

## ðŸ“ Estrutura

```
FireStickMod/
â”œâ”€â”€ free-my-tv/              # App Android (launcher + screensaver)
â”‚   â”œâ”€â”€ app/
â”‚   â”‚   â”œâ”€â”€ src/io/freemytv/  # 31 arquivos Java
â”‚   â”‚   â”œâ”€â”€ assets/           # fonts, i18n, logos, symbols (prÃ©-gerados)
â”‚   â”‚   â””â”€â”€ AndroidManifest.xml
â”‚   â”œâ”€â”€ tools/                # Python: geraÃ§Ã£o de assets (logos, symbols, zones)
â”‚   â”œâ”€â”€ build.sh              # Build sem Gradle (aapt2 + javac + d8)
â”‚   â”œâ”€â”€ build_windows.py      # Mesmo pipeline, com o SDK/JDK descobertos no Windows
â”‚   â”œâ”€â”€ config.properties     # SUA config (TMDB key, regiÃ£o, cidade) â€” nÃ£o versionado
â”‚   â”œâ”€â”€ freemytv.keystore     # Chave de assinatura â€” nÃ£o versionada
â”‚   â”œâ”€â”€ LICENSE               # MIT
â”‚   â””â”€â”€ out/                  # Artefatos do build (gerado, nÃ£o versionado)
â”‚
â”œâ”€â”€ scripts/                  # UtilitÃ¡rios Fire TV (Python)
â”‚   â”œâ”€â”€ common_adb.py         # Caminho/serial/timeout do adb, num lugar sÃ³
â”‚   â”œâ”€â”€ dev.py                # Descoberta do Fire TV na LAN (mDNS + scan)
â”‚   â”œâ”€â”€ fire_install.py       # Install + debloat + home trap (+ --revert)
â”‚   â”œâ”€â”€ fire_debloat.py       # Lista de pacotes para desativar (biblioteca)
â”‚   â”œâ”€â”€ fire_dns_block.py     # PersonalDNSFilter + blocklist OTA
â”‚   â”œâ”€â”€ fire_ota.py           # Baseline do device antes de uma OTA
â”‚   â””â”€â”€ fire_trap.py          # Home trap (accessibility service)
â”‚
â”œâ”€â”€ tools/                    # platform-tools local (adb), ignorado pelo git
â”œâ”€â”€ .gitignore
â””â”€â”€ README.md
```

---

## âš™ï¸ PrÃ©-requisitos

| Ferramenta | VersÃ£o | Como instalar |
|------------|--------|---------------|
| **JDK** | 17+ | `winget install EclipseAdoptium.Temurin.17.JDK` |
| **Android SDK** | build-tools 34+, platform android-34 | `sdkmanager "build-tools;34.0.0" "platforms;android-34"` |
| **Python** | 3.10+ | `winget install Python.Python.3.12` |
| **adb** | IncluÃ­do no SDK | `%LOCALAPPDATA%\android-sdk\platform-tools\adb.exe` |

**VariÃ¡veis de ambiente** (adicione ao `.bashrc` / `.zshrc` / PowerShell profile):

```bash
export ANDROID_HOME="$LOCALAPPDATA/android-sdk"
export JAVA_HOME="/c/Program Files/Eclipse Adoptium/jdk-17.0.x.x-hotspot"
export PATH="$ANDROID_HOME/platform-tools:$PATH"
```

---

## ðŸ”‘ ConfiguraÃ§Ã£o

```bash
cd free-my-tv
cp config.example.properties config.properties
```

Edite `config.properties`:

```properties
# ObrigatÃ³rio: TMDB Read Access Token (themoviedb.org â†’ Settings â†’ API)
tmdb_key=eyJhbGciOiJIUzI1NiJ9...

# RegiÃ£o para "onde passa" (BR, US, GB, etc.)
tmdb_region=BR

# Opcional: cidade para clima (Open-Meteo)
latitude=-23.5505
longitude=-46.6333
city=SÃ£o Paulo

# Moeda para crypto (BRL, USD, EUR...)
currency=BRL

# Ocultar animaÃ§Ã£o (gÃªnero 16 no TMDB)
hide_animation=false

# Desativar Assistant (microfone no remote)
disable_assistant=false
```

---

## ðŸ—ï¸ Build

```bash
cd free-my-tv
./build.sh
# ou no Windows Git Bash:
bash build.sh
```

**Output:** `FreeMyTV.apk` (1.4 MB) â€” pronto para instalar.

**Dois Fire TVs em casa, configuraÃ§Ãµes diferentes** (outra cidade, outro app de "assistir"): o `config.properties` Ã© embutido no APK em tempo de build, entÃ£o gere um APK por aparelho â€” sem tocar no seu:

```bash
cp config.properties config.sala.properties   # ajuste city/latitude/longitude/watch_app_pkg
FMTV_CONFIG=config.sala.properties FMTV_APK=FreeMyTV-sala.apk bash build.sh
```

`config.*.properties` e `*.apk` jÃ¡ estÃ£o no `.gitignore`.

> **Sem Gradle!** Build direto: `aapt2 â†’ javac â†’ d8 â†’ zipalign â†’ apksigner`. RÃ¡pido, sem daemon, sem cache sujo.

---

## ðŸ“± Deploy no Fire TV

### 1. Ative ADB no Fire TV
- Settings â†’ My Fire TV â†’ Developer Options â†’ **ADB Debugging ON**
- Settings â†’ My Fire TV â†’ About â†’ Network â†’ anote o **IP** (ex: `192.168.1.50`)

### 2. Instale (automÃ¡tico: debloat + home trap + launcher padrÃ£o)

```bash
cd scripts
python fire_install.py --ip 192.168.1.50
```

**O que faz:**
1. Instala APK
2. Snapshot do estado original (`fmtv_backup.json`)
3. **Debloat** â€” desativa ~60 pacotes Amazon (anÃºncios, telemetria, OTA, bloat)
4. Define como **launcher padrÃ£o** (`cmd package set-home-activity`)
5. Ativa **Home Trap** (botÃ£o Home â†’ Free My TV)

### 3. Reverter (se algo der errado)

```bash
python fire_install.py --ip 192.168.1.50 --revert
```
Restaura launcher Amazon original + reativa pacotes do snapshot.

---

## ðŸ› ï¸ Scripts Ãšteis

| Script | FunÃ§Ã£o |
|--------|--------|
| `fire_install.py --ip <IP>` | Install completo + debloat + home trap |
| `fire_install.py --ip <IP> --revert` | Rollback total (usa `fmtv_backup.json`) |
| `fire_install.py --ip <IP> --trap on\|off` | SÃ³ o Home Trap |
| `fire_debloat.py` | Biblioteca de listas (importada por `fire_install.py`) |
| `fire_dns_block.py [install\|block\|start\|verify\|all]` | PersonalDNSFilter + blocklist OTA Amazon |
| `fire_ota.py` | Baseline do device (`fmtv_ota_baseline.json`) antes de uma OTA |
| `fire_trap.py --trap on\|off [--ip <IP>]` | Liga/desliga Home Trap |
| `dev.py` | Descobre Fire TV na LAN (mDNS + scan 10.20.20.x/24) |

> Todos usam `common_adb.py` (adb do `ANDROID_HOME`, senÃ£o do PATH) e, sem `--ip`, o device descoberto por `dev.py`.

---

## ðŸŽ¨ PersonalizaÃ§Ã£o Visual (jÃ¡ aplicado)

| Ajuste | Antes | Depois |
|--------|-------|--------|
| **Gap entre cards rail** | 24dp | **48dp** |
| **Raio de canto (cards, shelf, sheet, drawer, ajustes)** | 18 / 20 / 22 / 30dp misturados | **20dp unificado (`Ui.RADIUS`)** |
| **Anel do card focado** | 85% opacidade, gradiente, 4dp, branco puro | **cinza claro `#7E8487`, 2dp, por cima de tudo** |
| **Card de apps** | 40..1880 (padding para fora) | **80..1840, mesma margem dos cards de clima** |
| **Fontes billboard** | 48/26/26 | **32/20/20** |
| **Cache TMDB** | SÃ³ disk | **ETag/304 + request dedup** |

---

## ðŸ§ª Desenvolvimento

### Logs no device
```bash
adb -s 192.168.1.50:5555 logcat -s "FreeMyTV:*" "HomeView:*" "Recs:*"
```

### Screenshot
```bash
adb -s 192.168.1.50:5555 exec-out screencap -p > screen.png
```

### Force-restart app
```bash
adb -s 192.168.1.50:5555 shell am force-stop io.freemytv
adb -s 192.168.1.50:5555 shell am start -n io.freemytv/.HomeActivity
```

### Regenerar assets (logos, symbols, zones)
```bash
cd free-my-tv/tools
python make_symbols.py
python logos.py
python make_zones.py
python make_art.py
```

---

## ðŸ“¦ O que NÃƒO estÃ¡ aqui (removido intencionalmente)

- âŒ **webOS** (LG TV) â€” pasta `webos/`
- âŒ **Tizen** (Samsung TV) â€” pasta `tizen/`
- âŒ **Web/browser** â€” pasta `web/`
- âŒ **Docs web** â€” pasta `docs/`, `CLAUDE.md`, `AGENTS.md`, `README.md` original
- âŒ **GitHub Actions** â€” `.github/`

> Mantido **apenas Fire TV**. Menos superfÃ­cie, menos bugs, build mais rÃ¡pido.

---

## ðŸ” SeguranÃ§a

- `config.properties` â€” **NUNCA commit** (tem TMDB key). EstÃ¡ no `.gitignore`.
- `freemytv.keystore` â€” **NUNCA commit** (chave de assinatura). EstÃ¡ no `.gitignore`.
- `scripts/.device_addr` â€” cache local de IP do device. No `.gitignore`.

---

## ðŸ“„ LicenÃ§a

**MIT** â€” veja `free-my-tv/LICENSE`.

CÃ³digo original: **Free My TV** (c) marin-m â€” licenÃ§a MIT.  
Este fork: modificaÃ§Ãµes para Fire TV Stick, mantida licenÃ§a original.

---

## ðŸ™ CrÃ©ditos

- **[Free My TV](https://github.com/simbasjungles/free-my-tv)** â€” marin-m â€” base completa, arquitetura, assets, shaders, TMDB integration, Watchmode, etc.
- **TMDB** â€” dados de filmes/sÃ©ries + "onde passa"
- **Watchmode** â€” deep links para apps de streaming
- **Open-Meteo** â€” clima + sunrise/sunset (sem key)
- **Binance** â€” crypto prices (sem key)
- **Material Symbols** â€” Ã­cones (Apache 2.0)
- **Inter font** â€” SIL OFL

---

## ðŸ¤ Contribuindo

1. Fork
2. Branch: `feature/nome` ou `fix/nome`
3. Commit convencional: `feat:`, `fix:`, `chore:`, `refactor:`
4. PR com descriÃ§Ã£o clara

---

## âš ï¸ Disclaimer

**Use por sua conta e risco.** Modifica configuraÃ§Ãµes do sistema (launcher padrÃ£o, pacotes desativados, DNS).  
Testado em Fire TV Stick 4K Max (2023), Fire OS 7/8. Pode variar em outros modelos.  
Sempre faÃ§a backup (`fire_install.py` cria `fmtv_backup.json` automÃ¡tico).

---

**Feito com â˜• para Fire TV Stick â€” sem anÃºncios, sem telemetria, sÃ³ conteÃºdo.**