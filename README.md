# FireStickMod

> **Free My TV** customizado para Fire TV Stick — Launcher minimalista, sem bloat Amazon, com recomendações TMDB, apps em shelf estilo tvOS e screensaver "Dream".

Baseado no projeto **[Free My TV](https://github.com/marin-m/FreeMyTV)** (marin-m) — inspiração direta, código adaptado e simplificado para Fire TV.

---

## 🎯 O que é

Um **launcher** (home screen) para Fire TV Stick que:

- **Remove bloat Amazon** (anúncios, telemetria, OTA forçado, screensaver padrão)
- **Shelf de apps estilo tvOS** — ícones coloridos por marca, foco com grow + shadow + anel cinza-claro
- **Rail de recomendações TMDB** — 3 cards/hora (manhã/tarde/noite), card principal 16:9 "billboard" com sinopse
- **Screensaver "Dream"** — foto do card focado, blur suave, relógio + clima
- **Debloat automático** — desativa pacotes Amazon desnecessários no install
- **Home Trap** — botão Home sempre volta pra cá (acessibilidade service)
- **DNS block OTA** — opcional, impede atualizações Amazon automáticas

---

## 📁 Estrutura

```
FireStickMod/
├── free-my-tv/              # App Android (launcher + screensaver)
│   ├── app/
│   │   ├── src/io/freemytv/  # 31 arquivos Java
│   │   ├── assets/           # fonts, i18n, logos, symbols (pré-gerados)
│   │   └── AndroidManifest.xml
│   ├── tools/                # Python: geração de assets (logos, symbols, zones)
│   ├── build.sh              # Build sem Gradle (aapt2 + javac + d8)
│   ├── build_windows.py      # Mesmo pipeline, com o SDK/JDK descobertos no Windows
│   ├── config.properties     # SUA config (TMDB key, região, cidade) — não versionado
│   ├── freemytv.keystore     # Chave de assinatura — não versionada
│   ├── LICENSE               # MIT
│   └── out/                  # Artefatos do build (gerado, não versionado)
│
├── scripts/                  # Utilitários Fire TV (Python)
│   ├── common_adb.py         # Caminho/serial/timeout do adb, num lugar só
│   ├── dev.py                # Descoberta do Fire TV na LAN (mDNS + scan)
│   ├── fire_install.py       # Install + debloat + home trap (+ --revert)
│   ├── fire_debloat.py       # Lista de pacotes para desativar (biblioteca)
│   ├── fire_dns_block.py     # PersonalDNSFilter + blocklist OTA
│   ├── fire_ota.py           # Baseline do device antes de uma OTA
│   └── fire_trap.py          # Home trap (accessibility service)
│
├── tools/                    # platform-tools local (adb), ignorado pelo git
├── .gitignore
└── README.md
```

---

## ⚙️ Pré-requisitos

| Ferramenta | Versão | Como instalar |
|------------|--------|---------------|
| **JDK** | 17+ | `winget install EclipseAdoptium.Temurin.17.JDK` |
| **Android SDK** | build-tools 34+, platform android-34 | `sdkmanager "build-tools;34.0.0" "platforms;android-34"` |
| **Python** | 3.10+ | `winget install Python.Python.3.12` |
| **adb** | Incluído no SDK | `%LOCALAPPDATA%\android-sdk\platform-tools\adb.exe` |

**Variáveis de ambiente** (adicione ao `.bashrc` / `.zshrc` / PowerShell profile):

```bash
export ANDROID_HOME="$LOCALAPPDATA/android-sdk"
export JAVA_HOME="/c/Program Files/Eclipse Adoptium/jdk-17.0.x.x-hotspot"
export PATH="$ANDROID_HOME/platform-tools:$PATH"
```

---

## 🔑 Configuração

```bash
cd free-my-tv
cp config.example.properties config.properties
```

Edite `config.properties`:

```properties
# Obrigatório: TMDB Read Access Token (themoviedb.org → Settings → API)
tmdb_key=eyJhbGciOiJIUzI1NiJ9...

# Região para "onde passa" (BR, US, GB, etc.)
tmdb_region=BR

# Opcional: cidade para clima (Open-Meteo)
latitude=-23.5505
longitude=-46.6333
city=São Paulo

# Moeda para crypto (BRL, USD, EUR...)
currency=BRL

# Ocultar animação (gênero 16 no TMDB)
hide_animation=false

# Desativar Assistant (microfone no remote)
disable_assistant=false
```

---

## 🏗️ Build

```bash
cd free-my-tv
./build.sh
# ou no Windows Git Bash:
bash build.sh
```

**Output:** `FreeMyTV.apk` (1.4 MB) — pronto para instalar.

**Dois Fire TVs em casa, configurações diferentes** (outra cidade, outro app de "assistir"): o `config.properties` é embutido no APK em tempo de build, então gere um APK por aparelho — sem tocar no seu:

```bash
cp config.properties config.sala.properties   # ajuste city/latitude/longitude/watch_app_pkg
FMTV_CONFIG=config.sala.properties FMTV_APK=FreeMyTV-sala.apk bash build.sh
```

`config.*.properties` e `*.apk` já estão no `.gitignore`.

> **Sem Gradle!** Build direto: `aapt2 → javac → d8 → zipalign → apksigner`. Rápido, sem daemon, sem cache sujo.

---

## 📱 Deploy no Fire TV

### 1. Ative ADB no Fire TV
- Settings → My Fire TV → Developer Options → **ADB Debugging ON**
- Settings → My Fire TV → About → Network → anote o **IP** (ex: `192.168.1.50`)

### 2. Instale (automático: debloat + home trap + launcher padrão)

```bash
cd scripts
python fire_install.py --ip 192.168.1.50
```

**O que faz:**
1. Instala APK
2. Snapshot do estado original (`fmtv_backup.json`)
3. **Debloat** — desativa ~60 pacotes Amazon (anúncios, telemetria, OTA, bloat)
4. Define como **launcher padrão** (`cmd package set-home-activity`)
5. Ativa **Home Trap** (botão Home → Free My TV)

### 3. Reverter (se algo der errado)

```bash
python fire_install.py --ip 192.168.1.50 --revert
```
Restaura launcher Amazon original + reativa pacotes do snapshot.

---

## 🛠️ Scripts Úteis

| Script | Função |
|--------|--------|
| `fire_install.py --ip <IP>` | Install completo + debloat + home trap |
| `fire_install.py --ip <IP> --revert` | Rollback total (usa `fmtv_backup.json`) |
| `fire_install.py --ip <IP> --trap on\|off` | Só o Home Trap |
| `fire_debloat.py` | Biblioteca de listas (importada por `fire_install.py`) |
| `fire_dns_block.py [install\|block\|start\|verify\|all]` | PersonalDNSFilter + blocklist OTA Amazon |
| `fire_ota.py` | Baseline do device (`fmtv_ota_baseline.json`) antes de uma OTA |
| `fire_trap.py --trap on\|off [--ip <IP>]` | Liga/desliga Home Trap |
| `dev.py` | Descobre Fire TV na LAN (mDNS + scan 10.20.20.x/24) |

> Todos usam `common_adb.py` (adb do `ANDROID_HOME`, senão do PATH) e, sem `--ip`, o device descoberto por `dev.py`.

---

## 🎨 Personalização Visual (já aplicado)

| Ajuste | Antes | Depois |
|--------|-------|--------|
| **Gap entre cards rail** | 24dp | **48dp** |
| **Raio de canto (cards, shelf, sheet, drawer, ajustes)** | 18 / 20 / 22 / 30dp misturados | **20dp unificado (`Ui.RADIUS`)** |
| **Anel do card focado** | 85% opacidade, gradiente, 4dp, branco puro | **cinza claro `#7E8487`, 2dp, por cima de tudo** |
| **Card de apps** | 40..1880 (padding para fora) | **80..1840, mesma margem dos cards de clima** |
| **Fontes billboard** | 48/26/26 | **32/20/20** |
| **Cache TMDB** | Só disk | **ETag/304 + request dedup** |

---

## 🧪 Desenvolvimento

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

## 📦 O que NÃO está aqui (removido intencionalmente)

- ❌ **webOS** (LG TV) — pasta `webos/`
- ❌ **Tizen** (Samsung TV) — pasta `tizen/`
- ❌ **Web/browser** — pasta `web/`
- ❌ **Docs web** — pasta `docs/`, `CLAUDE.md`, `AGENTS.md`, `README.md` original
- ❌ **GitHub Actions** — `.github/`

> Mantido **apenas Fire TV**. Menos superfície, menos bugs, build mais rápido.

---

## 🔐 Segurança

- `config.properties` — **NUNCA commit** (tem TMDB key). Está no `.gitignore`.
- `freemytv.keystore` — **NUNCA commit** (chave de assinatura). Está no `.gitignore`.
- `scripts/.device_addr` — cache local de IP do device. No `.gitignore`.

---

## 📄 Licença

**MIT** — veja `free-my-tv/LICENSE`.

Código original: **Free My TV** (c) marin-m — licença MIT.  
Este fork: modificações para Fire TV Stick, mantida licença original.

---

## 🙏 Créditos

- **[Free My TV](https://github.com/marin-m/FreeMyTV)** — marin-m — base completa, arquitetura, assets, shaders, TMDB integration, Watchmode, etc.
- **TMDB** — dados de filmes/séries + "onde passa"
- **Watchmode** — deep links para apps de streaming
- **Open-Meteo** — clima + sunrise/sunset (sem key)
- **Binance** — crypto prices (sem key)
- **Material Symbols** — ícones (Apache 2.0)
- **Inter font** — SIL OFL

---

## 🤝 Contribuindo

1. Fork
2. Branch: `feature/nome` ou `fix/nome`
3. Commit convencional: `feat:`, `fix:`, `chore:`, `refactor:`
4. PR com descrição clara

---

## ⚠️ Disclaimer

**Use por sua conta e risco.** Modifica configurações do sistema (launcher padrão, pacotes desativados, DNS).  
Testado em Fire TV Stick 4K Max (2023), Fire OS 7/8. Pode variar em outros modelos.  
Sempre faça backup (`fire_install.py` cria `fmtv_backup.json` automático).

---

**Feito com ☕ para Fire TV Stick — sem anúncios, sem telemetria, só conteúdo.**