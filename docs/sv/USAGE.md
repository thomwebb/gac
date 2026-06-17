# gac Kommandoradsanvändning

[English](../en/USAGE.md) | [简体中文](../zh-CN/USAGE.md) | [繁體中文](../zh-TW/USAGE.md) | [日本語](../ja/USAGE.md) | [한국어](../ko/USAGE.md) | [हिन्दी](../hi/USAGE.md) | [Tiếng Việt](../vi/USAGE.md) | [Français](../fr/USAGE.md) | [Русский](../ru/USAGE.md) | [Español](../es/USAGE.md) | [Português](../pt/USAGE.md) | [Norsk](../no/USAGE.md) | **Svenska** | [Deutsch](../de/USAGE.md) | [Nederlands](../nl/USAGE.md) | [Italiano](../it/USAGE.md)

Det här dokumentet beskriver alla tillgängliga flaggor och alternativ för `uvx gac` CLI-verktyget.

## Innehållsförteckning

- [gac Kommandoradsanvändning](#gac-kommandoradsanvändning)
  - [Innehållsförteckning](#innehållsförteckning)
  - [Grundläggande användning](#grundläggande-användning)
  - [Kärnarbetsflödesflaggor](#kärnarbetsflödesflaggor)
  - [Meddelandeanpassning](#meddelandeanpassning)
  - [Output och detaljnivå](#output-och-detaljnivå)
  - [Hjälp och version](#hjälp-och-version)
  - [Exempelarbetsflöden](#exempelarbetsflöden)
  - [Avancerat](#avancerat)
    - [Hoppa över Pre-commit och Lefthook Hooks](#hoppa-över-pre-commit-och-lefthook-hooks)
    - [Säkerhetsskanning](#säkerhetsskanning)
    - [Binary File Detection](#binary-file-detection)
    - [SSL-certifikatverifiering](#ssl-certifikatverifiering)
  - [Konfigurationsanteckningar](#konfigurationsanteckningar)
    - [Avancerade konfigurationsalternativ](#avancerade-konfigurationsalternativ)
    - [Konfigurationsunderkommandon](#konfigurationsunderkommandon)
  - [Interaktivt Läge](#interaktivt-läge)
    - [Hur det fungerar](#hur-det-fungerar)
    - [När man ska använda interaktivt läge](#när-man-ska-använda-interaktivt-läge)
    - [Användningsexempel](#användningsexempel)
    - [Fråga-Svar Workflow](#fråga-svar-workflow)
    - [Kombination med andra flaggor](#kombination-med-andra-flaggor)
    - [Bästa Praxis](#bästa-praxis)
  - [Användningsstatistik](#användningsstatistik)
  - [Få hjälp](#få-hjälp)

## Grundläggande användning

```sh
uvx gac init
# Följ sedan prompterna för att konfigurera din leverantör, modell och API-nycklar interaktivt
uvx gac
```

Genererar ett LLM-driven commit-meddelande för stageade ändringar och frågar efter bekräftelse. Bekräftelseprompten accepterar:

- `y` eller `yes` - Fortsätt med commiten
- `n` eller `no` - Avbryt commiten
- `r` eller `reroll` - Regenerera commit-meddelandet med samma kontext
- `e` eller `edit` - Redigera commit-meddelandet. Som standard öppnas en inbyggd TUI med vi/emacs-tangentbindningar. Ställ in `GAC_EDITOR` för att öppna din föredragna editor istället (t.ex. `GAC_EDITOR=code gac` för VS Code, `GAC_EDITOR=vim gac` för vim)
- Valfri annan text - Regenerera med den texten som feedback (t.ex. `gör det kortare`, `fokusera på prestanda`)
- Tom input (bara Enter) - Visa prompten igen

---

## Kärnarbetsflödesflaggor

| Flagga / Alternativ  | Kort | Beskrivning                                                                |
| -------------------- | ---- | -------------------------------------------------------------------------- |
| `--add-all`          | `-a` | Stagea alla ändringar innan commit                                         |
| `--stage`            | `-S` | Välj interaktivt filer att stagea med en träd-baserad TUI                  |
| `--group`            | `-g` | Gruppera stageade ändringar i flera logiska commits                        |
| `--push`             | `-p` | Pusha ändringar till remote efter commit                                   |
| `--yes`              | `-y` | Automatiskt bekräfta commit utan prompt                                    |
| `--dry-run`          |      | Visa vad som skulle hända utan att göra några ändringar                    |
| `--message-only`     |      | Skriv bara ut det genererade commit-meddelandet utan att faktiskt committa |
| `--no-verify`        |      | Hoppa över pre-commit och lefthook hooks vid commit                        |
| `--skip-secret-scan` |      | Hoppa över säkerhetsskanning för hemligheter i stageade ändringar          |
| `--no-verify-ssl`    |      | Hoppa över SSL-certifikatverifiering (användbart för företagsproxyer)      |
| `--signoff`          |      | Lägg till Signed-off-by-rad i commit-meddelandet (DCO-efterlevnad)         |
| `--interactive`      | `-i` | Ställ frågor om ändringar för bättre commits                               |

**Obs:** `--stage` och `--add-all` är ömsesidigt uteslutande. Använd `--stage` för att interaktivt välja vilka filer du vill stagea, och `--add-all` för att stagea alla ändringar på en gång.

**Obs:** Kombinera `-a` och `-g` (dvs. `-ag`) för att stagea ALLA ändringar först, sedan gruppera dem i commits.

**Obs:** När du använder `--group`, skalas max output tokens-gränsen automatiskt baserat på antalet filer som committas (2x för 1-9 filer, 3x för 10-19 filer, 4x för 20-29 filer, 5x för 30+ filer). Detta säkerställer att LLM:n har tillräckligt med tokens för att generera alla grupperade commits utan trunkering, även för stora ändringsuppsättningar.

**Obs:** `--message-only` och `--group` är ömsesidigt uteslutande. Använd `--message-only` när du vill hämta commit-meddelandet för extern bearbetning, och `--group` när du vill organisera flera commits inom det aktuella git‑arbetsflödet.

**Obs:** `--interactive`-flagget ger extra kontext till LLM genom att ställa frågor om dina ändringar, vilket leder till mer exakta och detaljerade commit-meddelanden. Detta är särskilt användbart för komplexa ändringar eller när du vill säkerställa att commit-meddelandet fångar hela kontexten av ditt arbete.

## Meddelandeanpassning

| Flagga / Alternativ  | Kort | Beskrivning                                                                   |
| -------------------- | ---- | ----------------------------------------------------------------------------- |
| `--one-liner`        | `-o` | Generera ett enrads commit-meddelande                                         |
| `--verbose`          | `-v` | Generera detaljerade commit-meddelanden med motivation, arkitektur & påverkan |
| `--hint <text>`      | `-h` | Lägg till en ledtråd för att guida LLM:n                                      |
| `--model <modell>`   | `-m` | Specificera modellen att använda för denna commit                             |
| `--language <språk>` | `-l` | Åsidosätt språket (namn eller kod: 'Spanish', 'es', 'sv', 'ja')               |
| `--scope`            | `-s` | Härled ett lämpligt scope för commiten                                        |
| `--50-72`            |      | Använd 50/72-regeln för formatering av commit-meddelanden                     |

**Obs:** Flaggan `--50-72` tillämpar [50/72-regeln](https://www.conventionalcommits.org/en/v1.0.0/#summary) där:

- Ämnesrad: maximalt 50 tecken
- Brödtextlinjer: maximalt 72 tecken per rad
- Detta håller commit-meddelanden läsbara i `git log --oneline` och GitHub:s UI

Du kan också ställa in `GAC_USE_50_72_RULE=true` i din `.gac.env` fil för att alltid tillämpa denna regel.

**Obs:** Du kan ge feedback interaktivt genom att helt enkelt skriva den vid bekräftelseprompten - inget behov att prefixa med 'r'. Skriv `r` för en enkel regenerering, `e` för att redigera meddelandet (inbyggd TUI som standard, eller din `$GAC_EDITOR` om angiven), eller skriv din feedback direkt som `gör det kortare`.

## Output och detaljnivå

| Flagga / Alternativ  | Kort | Beskrivning                                                       |
| -------------------- | ---- | ----------------------------------------------------------------- |
| `--quiet`            | `-q` | Dämpa all output utom fel                                         |
| `--log-level <nivå>` |      | Ställ in loggnivå (debug, info, warning, error)                   |
| `--show-prompt`      |      | Skriv ut LLM-prompten som används för commit-meddelandegenerering |

## Hjälp och version

| Flagga / Alternativ | Kort | Beskrivning                      |
| ------------------- | ---- | -------------------------------- |
| `--version`         |      | Visa gac version och avsluta     |
| `--help`            |      | Visa hjälpmeddelande och avsluta |

---

## Exempelarbetsflöden

- **Stagea alla ändringar och commit:**

  ```sh
  uvx gac -a
  ```

- **Commit och push i ett steg:**

  ```sh
  uvx gac -ap
  ```

- **Generera ett enrads commit-meddelande:**

  ```sh
  uvx gac -o
  ```

- **Generera ett detaljerat commit-meddelande med strukturerade sektioner:**

  ```sh
  uvx gac -v
  ```

- **Lägg till en ledtråd för LLM:n:**

  ```sh
  uvx gac -h "Refaktorisera autentiseringslogik"
  ```

- **Härled scope för commiten:**

  ```sh
  uvx gac -s
  ```

- **Gruppera stageade ändringar i logiska commits:**

  ```sh
  uvx gac -g
  # Grupperar endast de filer du redan har stageade
  ```

- **Gruppera alla ändringar (stageade + unstageda) och auto-bekräfta:**

  ```sh
  uvx gac -agy
  # Stagear allt, grupperar det och auto-bekräftar
  ```

- **Använd en specifik modell för denna commit:**

  ```sh
  uvx gac -m anthropic:claude-haiku-4-5
  ```

- **Generera commit-meddelande på ett specifikt språk:**

  ```sh
  # Använda språkkoder (kortare)
  uvx gac -l sv
  uvx gac -l ja
  uvx gac -l es

  # Använda fullständiga namn
  uvx gac -l "Svenska"
  uvx gac -l Japanese
  uvx gac -l Spanish
  ```

- **Testkörning (se vad som skulle hända):**

  ```sh
  uvx gac --dry-run
  ```

- **Hämta endast commit-meddelandet (för skriptintegration):**

  ```sh
  uvx gac --message-only
  # Exempelutdata: feat: add user authentication system
  ```

- **Hämta commit-meddelandet i enradsformat:**

  ```sh
  uvx gac --message-only --one-liner
  # Exempelutdata: feat: add user authentication system
  ```

- **Använd interaktivt läge för att ge kontext:**

  ```sh
  uvx gac -i
  # Vad är huvudsyftet med dessa ändringar?
  # Vilket problem löser du?
  # Finns det implementeringsdetaljer att nämna?
  ```

- **Interaktivt läge med detaljerad output:**

  ```sh
  uvx gac -i -v
  # Ställ frågor och generera detaljerade commit-meddelanden
  ```

## Avancerat

- Kombinera flaggor för mer kraftfulla arbetsflöden (t.ex. `uvx gac -ayp` för att stagea, auto-bekräfta och pusha)
- Använd `--show-prompt` för att felsöka eller granska prompten som skickas till LLM:n
- Justera detaljnivån med `--log-level` eller `--quiet`

### Hoppa över Pre-commit och Lefthook Hooks

Flaggan `--no-verify` gör att du kan hoppa över alla pre-commit eller lefthook hooks som är konfigurerade i ditt projekt:

```sh
uvx gac --no-verify  # Hoppa över alla pre-commit och lefthook hooks
```

**Använd `--no-verify` när:**

- Pre-commit eller lefthook hooks misslyckas tillfälligt
- Arbeta med tidskrävande hooks
- Committa pågående arbete som inte klarar alla kontroller ännu

**Obs:** Använd med försiktighet eftersom dessa hooks upprätthåller kodkvalitetsstandarder.

### Säkerhetsskanning

uvx gac inkluderar inbyggd säkerhetsskanning som automatiskt upptäcker potentiella hemligheter och API-nycklar i dina stageade ändringar **innan något AI API-anrop görs**. Om en hemlighet upptäcks avbryts arbetsflödet omedelbart — inget API-anrop utförs. Detta säkerställer att din känsliga data aldrig skickas till någon AI-modell. Scannern använder **regex-baserad mönstermatching**, inte LLM:er, så skanning är snabb och körs helt lokalt.

**Hoppa över säkerhetsskanningar:**

```sh
uvx gac --skip-secret-scan  # Hoppa över säkerhetsskanning för denna commit
```

**För att inaktivera permanent:** Ställ in `GAC_SKIP_SECRET_SCAN=true` i din `.gac.env` fil.

**När man ska hoppa över:**

- Committa exempelkod med platshållarnycklar
- Arbeta med testfixtures som innehåller dummy-inloggningsuppgifter
- När du har verifierat att ändringarna är säkra

**Obs:** Scannern använder regex-baserad mönstermatching (inte LLM:er) för att upptäcka vanliga hemlighetsformat. Den körs innan något AI API-anrop görs — om en hemlighet hittas utförs inget API-anrop. Granska alltid dina stageade ändringar innan du committar.

### Binary File Detection

uvx gac includes automatic detection of binary files in staged changes, preventing accidental commits of compiled files, images, and other binary assets that typically should not be in version control. The detector uses multiple strategies:

- **Extension-based detection** - Fast recognition of 60+ binary file types
- **Null byte detection** - Reliable indicator of binary content
- **UTF-8 validity checking** - Text files should be valid UTF-8 or ASCII
- **Magic byte identification** - Detects file types from file signatures

**Supported binary types:**

- **Executables:** .exe, .dll, .so, .dylib, .bin, .o, .obj, .lib, .a
- **Archives:** .zip, .tar, .gz, .bz2, .7z, .rar, .xz, .zst
- **Images:** .png, .jpg, .jpeg, .gif, .bmp, .ico, .svg, .tiff, .webp
- **Media:** .mp3, .wav, .ogg, .flac, .m4a, .aac, .mp4, .avi, .mkv, .mov, .wmv
- **Fonts:** .ttf, .otf, .woff, .woff2, .eot
- **Documents:** .pdf, .doc, .docx, .xls, .xlsx, .ppt, .pptx
- **Databases:** .db, .sqlite, .sqlite3, .mdb, .accdb
- **Compiled code:** .class, .jar, .war, .ear, .pyc, .pyd, .pyo, .beam, .hi

**When binary files are detected:**

```sh
uvx gac
# Output:
# BINARY FILE WARNING: Binary files detected!
#
#   • image.png
#     Type: Image file
#     Size: 2.3 MB
#
# Binary files should typically be excluded from version control.
# Use .gitignore to prevent accidental commits of binary files.
#
# Options:
#   [a] Abort commit (recommended)
#   [c] Continue anyway (you know what you are doing)
#   [r] Unstage binary file(s) and continue
#
# Choose an option [a]:
```

**Best practices:**

1. **Add binary patterns to .gitignore:**

   ```gitignore
   # Compiled files
   *.exe
   *.dll
   *.so
   *.dylib
   *.o
   *.a

   # Images
   *.png
   *.jpg
   *.jpeg
   *.gif

   # Archives
   *.zip
   *.tar.gz

   # Python
   *.pyc
   __pycache__/
   ```

2. **Use Git LFS** for large binary files that must be tracked:

   ```sh
   git lfs track "*.psd"
   git lfs track "*.zip"
   ```

3. **Commit binary files only when necessary:**
   - Icons and assets that are part of the codebase
   - Test fixtures that need to be versioned
   - Documentation images

**Note:** Binary detection runs automatically during the commit workflow (similar to secret scanning). There is no flag to disable it, as binary files generally should not be committed unless there is a specific reason. If you need to commit a binary file, choose the "Continue anyway" option or ensure it is properly documented in your project guidelines.

### SSL-certifikatverifiering

Flaggan `--no-verify-ssl` gör att du kan hoppa över SSL-certifikatverifiering för API-anrop:

```sh
uvx gac --no-verify-ssl  # Hoppa över SSL-verifiering för denna commit
```

**För att konfigurera permanent:** Ställ in `GAC_NO_VERIFY_SSL=true` i din `.gac.env`-fil.

**Använd `--no-verify-ssl` när:**

- Företagsproxyer fångar SSL-trafik (MITM-proxyer)
- Utvecklingsmiljöer använder självsignerade certifikat
- Du stöter på SSL-certifikatfel på grund av nätverkssäkerhetsinställningar

**Obs:** Använd endast detta alternativ i betrodda nätverksmiljöer. Att inaktivera SSL-verifiering minskar säkerheten och kan göra dina API-förfrågningar sårbara för man-in-the-middle-attacker.

### Signed-off-by-rad (DCO-efterlevnad)

uvx gac stödjer att lägga till en `Signed-off-by`-rad i commit-meddelanden, vilket krävs för [Developer Certificate of Origin (DCO)](https://developercertificate.org/)-efterlevnad i många open source-projekt.

**Lägg till signoff :**

```sh
uvx gac --signoff  # Lägg till Signed-off-by-rad i commit-meddelandet (DCO-efterlevnad)
```

**För att aktivera permanent :** Ställ in `GAC_SIGNOFF=true` i din `.gac.env`-fil, eller lägg till `signoff=true` i din konfiguration.

**Vad den gör :**

- Lägger till `Signed-off-by: Ditt Namn <din.email@example.com>` i commit-meddelandet
- Använder din git-konfiguration (`user.name` och `user.email`) för raden
- Krävs för projekt som Cherry Studio, Linux-kärnan och andra som använder DCO

**Git-identitetsinställningar :**

Se till att din git-konfiguration har rätt namn och e-post :

```sh
git config --global user.name "Your Full Name"
git config --global user.email "your.email@example.com"
```

**Obs :** Signed-off-by-raden läggs till av git under commit, inte av AI under meddelandegenerering. Du ser den inte i förhandsgranskningen, men den kommer att finnas i den slutliga commiten (kontrollera med `git log -1`).

## Konfigurationsanteckningar

- Det rekommenderade sättet att konfigurera gac är att köra `uvx gac init` och följa de interaktiva prompterna.
- Redan konfigurerat språk och bara behöver byta leverantör eller modell? Kör `uvx gac model` för att upprepa installationen utan språkfrågor.
- **Använder Claude Code?** Se [Claude Code installationsguide](CLAUDE_CODE.md) för OAuth-autentiseringsinstruktioner.
- **Använder ChatGPT OAuth?** Se [ChatGPT OAuth installationsguide](CHATGPT_OAUTH.md) för webbläsarbaserade autentiseringsinstruktioner.
- **Använder du GitHub Copilot?** Se [GitHub Copilot-installationsguiden](GITHUB_COPILOT.md) för Device Flow-autentiseringsinstruktioner.
- gac laddar konfigurationen i följande prioritetsordning:
  1. CLI-flaggor
  2. Projekt-nivå `.gac.env`
  3. Användar-nivå `~/.gac.env`
  4. Miljövariabler

### Avancerade konfigurationsalternativ

Du kan anpassa gacs beteende med dessa valfria miljövariabler:

- `GAC_EDITOR=code --wait` - Åsidosätt editorn som används när du trycker `e` vid bekräftelseprompten. Som standard öppnar `e` en inbyggd TUI; att ställa in `GAC_EDITOR` byter till en extern editor. Stöder alla editor-kommandon med argument. Vänteflaggor (`--wait`/`-w`) infogas automatiskt för kända GUI-editorer (VS Code, Cursor, Zed, Sublime Text) så att processen blockeras tills du stänger filen
- `GAC_ALWAYS_INCLUDE_SCOPE=true` - Härled automatiskt och inkludera scope i commit-meddelanden (t.ex. `feat(auth):` vs `feat:)
- `GAC_ALWAYS_GROUPED=true` - Använd alltid grupperat commit-läge (motsvarar att alltid ange flaggan `-g` eller `--group`)
- `GAC_VERBOSE=true` - Generera detaljerade commit-meddelanden med motivation, arkitektur och påverkanssektioner
- `GAC_USE_50_72_RULE=true` - Tillämpa alltid 50/72-regeln för commit-meddelanden (ämne ≤50 tecken, brödtextlinjer ≤72 tecken)
- `GAC_SIGNOFF=true` - Lägg alltid till Signed-off-by-rad i commits (för DCO-efterlevnad)
- `GAC_TEMPERATURE=0.7` - Kontrollera LLM:s kreativitet (0.0-1.0, lägre = mer fokuserad)
- `GAC_REASONING_EFFORT=medium` - Kontrollera resonemangs-/tankedjup för modeller som stöder utökat tänkande (low, medium, high). Lämna oinställt för att använda varje modells standard. Skickas endast till kompatibla leverantörer (OpenAI-stil; inte Anthropic).
- `GAC_MAX_OUTPUT_TOKENS=4096` - Maximalt antal tokens för genererade meddelanden (automatiskt skalat 2-5x vid användning av `--group` baserat på filantal; åsidosätt för att gå högre eller lägre)
- `GAC_WARNING_LIMIT_TOKENS=4096` - Varna när prompter överskrider denna tokenräkning
- `GAC_SYSTEM_PROMPT_PATH=/path/to/custom_prompt.txt` - Använd en anpassad systemprompt för commit-meddelande generation
- `GAC_LANGUAGE=Swedish` - Generera commit-meddelanden på ett specifikt språk (t.ex. Spanish, French, Japanese, German). Stöder fullständiga namn eller ISO-koder (es, fr, ja, de, sv, zh-CN). Använd `uvx gac language` för interaktivt val
- `GAC_TRANSLATE_PREFIXES=true` - Översätt konventionella commit-prefix (feat, fix, etc.) till målspråket (standard: false, behåller prefix på engelska)
- `GAC_SKIP_SECRET_SCAN=true` - Inaktivera automatisk säkerhetsskanning för hemligheter i stageade ändringar (använd med försiktighet)
- `GAC_NO_VERIFY_SSL=true` - Hoppa över SSL-certifikatverifiering för API-anrop (användbart för företagsproxyer som fångar SSL-trafik)
- `GAC_DISABLE_STATS=true` - Inaktivera spårning av användningsstatistik (ingen läsning eller skrivning av statistikfil; befintlig data bevaras). Endast truthy-värden inaktiverar statistik; att ställa in på `false`/`0`/`no`/`off` håller statistik aktiverad, samma som att lämna variabeln odefinierad

Se `.gac.env.example` för en komplett konfigurationsmall.

För detaljerad vägledning om hur man skapar anpassade systemprompter, se [docs/CUSTOM_SYSTEM_PROMPTS.md](docs/CUSTOM_SYSTEM_PROMPTS.md).

### Konfigurationsunderkommandon

Följande underkommandon är tillgängliga:

- `uvx gac init` — Interaktiv installationsguide för leverantör, modell och språk
- `uvx gac model` — Leverantör/modell/API-nyckel konfiguration utan språkprompter (idealiskt för snabba byten)
- `uvx gac auth` — Visa OAuth-autentiseringsstatus för alla leverantörer
- `uvx gac auth claude-code login` — Logga in på Claude Code med OAuth (öppnar webbläsare)
- `uvx gac auth claude-code logout` — Logga ut från Claude Code och ta bort sparat token
- `uvx gac auth claude-code status` — Kontrollera Claude Code-autentiseringsstatus
- `uvx gac auth chatgpt login` — Logga in på ChatGPT med OAuth (öppnar webbläsare)
- `uvx gac auth chatgpt logout` — Logga ut från ChatGPT och ta bort sparat token
- `uvx gac auth chatgpt status` — Kontrollera ChatGPT-autentiseringsstatus
- `uvx gac auth copilot login` — Logga in på GitHub Copilot med Device Flow
- `uvx gac auth copilot login --host ghe.mycompany.com` — Logga in på Copilot på en GitHub Enterprise-instans
- `uvx gac auth copilot logout` — Logga ut från Copilot och ta bort lagrade tokens
- `uvx gac auth copilot status` — Kontrollera Copilot-autentiseringsstatus
- `uvx gac config show` — Visa nuvarande konfiguration
- `uvx gac config set KEY VALUE` — Ställ in konfigurationsnyckel i `$HOME/.gac.env`
- `uvx gac config get KEY` — Hämta konfigurationsvärde
- `uvx gac config unset KEY` — Ta bort konfigurationsnyckel från `$HOME/.gac.env`
- `uvx gac language` (eller `uvx gac lang`) — Interaktiv språkväljare för commit-meddelanden (ställer in GAC_LANGUAGE)
- `uvx gac editor` (eller `uvx gac edit`) — Interaktiv editorväljare för `e`-knappen vid bekäftelsesprompten (ställer in GAC_EDITOR)
- `uvx gac diff` — Visa filtrerad git diff med alternativ för staged/unstaged ändringar, färg och trunkering
- `uvx gac serve` — Starta GAC som [MCP-server](MCP.md) för AI-agent integration (stdio transport)
- `uvx gac stats show` — Visa din gac-användningsstatistik (totaler, streaks, daglig & veckovis aktivitet, tokenanvändning, topprojekt med snitt filer, toppmodeller med fart och latens)
- `uvx gac stats models` — Detaljerad statistik för alla modeller med token-uppdelning, hastighet, latens och latens-per-commit-diagram
- `uvx gac stats projects` — Statistik för alla projekt med token-uppdelning och snitt filer per gac
- `uvx gac stats recent` — Senaste 10 gacs med tokens, hastighet, latens och filer per gac (`-n 20` för fler)
- `uvx gac stats reset` — Återställ all statistik till noll (ber om bekräftelse)
- `uvx gac stats reset model <model-id>` — Återställ statistik för en specifik modell (skiftlägesokänslig)

## Interaktivt Läge

`--interactive` (`-i`) flagget förbättrar gac's commit-meddelandegenerering genom att ställa riktade frågor om dina ändringar. Denna extra kontext hjälper LLM att skapa mer exakta, detaljerade och kontextanpassade commit-meddelanden.

### Hur det fungerar

När du använder `--interactive` kommer gac att ställa frågor som:

- **Vad är huvudsyftet med dessa ändringar?** - Hjälper till att förstå övergripande mål
- **Vilket problem löser du?** - Ger kontext om motivationen
- **Finns det implementeringsdetaljer att nämna?** - Fångar tekniska specifikationer
- **Finns det breaking changes?** - Identifierar potentiella påverkningsproblem
- **Är detta relaterat till en issue eller ticket?** - Kopplar till projekthantering

### När man ska använda interaktivt läge

Interaktivt läge är särskilt användbart för:

- **Komplexa ändringar** där kontexten inte är klar från diff-en ensam
- **Refactoring-arbete** som sträcker sig över flera filer och koncept
- **Nya funktioner** som kräver förklaring av övergripande syfte
- **Bug fixes** där rotorsaken inte är omedelbart synlig
- **Prestandaoptimering** där logiken inte är uppenbar
- **Code review-förberedelse** - frågor hjälper dig att tänka på dina ändringar

### Användningsexempel

**Grundläggande interaktivt läge:**

```sh
uvx gac -i
```

Detta kommer att:

1. Visa en sammanfattning av stageade ändringar
2. Ställa frågor om ändringarna
3. Generera ett commit-meddelande med dina svar
4. Be om bekräftelse (eller automatiskt bekräfta när kombinerat med `-y`)

**Interaktivt läge med stageade ändringar:**

```sh
uvx gac -ai
# Stage alla ändringar, ställ sedan frågor för bättre kontext
```

**Interaktivt läge med specifika hints:**

```sh
uvx gac -i -h "Databasmigrering för användarprofiler"
# Ställ frågor medan du ger ett specifikt hint för att fokusera LLM
```

**Interaktivt läge med detaljerad output:**

```sh
uvx gac -i -v
# Ställ frågor och generera ett detaljerat, strukturerat commit-meddelande
```

**Automatiskt bekräftat interaktivt läge:**

```sh
uvx gac -i -y
# Ställ frågor men bekräfta det resulterande committet automatiskt
```

### Fråga-Svar Workflow

Den interaktiva workflown följer detta mönster:

1. **Ändringsgranskning** - gac visar en sammanfattning av vad du committar
2. **Svara på frågor** - svara på varje prompt med relevanta detaljer
3. **Kontextförbättring** - dina svar läggs till i LLM-prompten
4. **Meddelandegenerering** - LLM skapar ett commit-meddelande med full kontext
5. **Bekräftelse** - granska och bekräfta committet (eller automatiskt med `-y`)

**Tips för användbara svar:**

- **Kortfattat men komplett** - ge viktiga detaljer utan att vara överdrivet verbose
- **Fokusera på "varför"** - förklara resonemanget bakom dina ändringar
- **Nämna begränsningar** - notera begränsningar eller särskilda överväganden
- **Länka till extern kontext** - referera till issues, dokumentation eller designdokument
- **Tomma svar är ok** - om en fråga inte är tillämplig, tryck bara på Enter

### Kombination med andra flaggor

Interaktivt läge fungerar bra med de flesta andra flaggor:

```sh
# Stage alla ändringar och ställ frågor
uvx gac -ai

# Ställ frågor med detaljerad output
uvx gac -i -v
```

### Bästa Praxis

- **Använd för komplexa PR:er** - särskilt användbart för pull requests som behöver detaljerade förklaringar
- **Team-samarbete** - frågor hjälper dig att tänka på ändringar som andra kommer att granska
- **Dokumentationsförberedelse** - dina svar kan hjälpa till att bilda grunden för release notes
- **Lärverktyg** - frågor förstärker bra praxis för commit-meddelanden
- **Hoppa över för enkla ändringar** - för triviala fixes kan grundläggande läge vara snabbare

## Användningsstatistik

uvx gac spårar lättviktig användningsstatistik så att du kan se din commit-aktivitet, streaks, tokenanvändning och mest aktiva projekt och modeller. Statistik lagras lokalt i `~/.gac_stats.json` och skickas aldrig någonstans — det finns ingen telemetri.

**Vad spåras:** totalt antal gac-körningar, totalt antal commits, totalt antal prompt-, output- och reasoning-tokens, första/senaste användningsdatum, dagliga och veckovisa antal (gacs, commits, tokens), nuvarande och längsta streak, aktivitet per projekt (gacs, commits, tokens) och aktivitet per modell (gacs, tokens).

**Vad INTE spåras:** commit-meddelanden, kodinnehåll, filsökvägar, personlig information eller något utöver antal, datum, projektnamn (härledda från git remote eller katalognamn) och modellnamn.

### Opt-in eller Opt-out

`uvx gac init` frågar om du vill aktivera statistik och förklarar exakt vad som sparas. Du kan ändra dig när som helst:

- **Aktivera statistik:** ta bort `GAC_DISABLE_STATS` eller ställ in på `false`/`0`/`no`/`off`/tom.
- **Inaktivera statistik:** ställ in `GAC_DISABLE_STATS` på ett truthy-värde (`true`, `1`, `yes`, `on`).

När du avböjer statistik under `uvx gac init` och en befintlig `~/.gac_stats.json` upptäcks, erbjuds du möjligheten att ta bort den.

### Statistikunderkommandon

| Kommando                               | Beskrivning                                                                                                              |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `uvx gac stats`                        | Visa din statistik (samma som `uvx gac stats show`)                                                                      |
| `uvx gac stats show`                   | Visa fullständig statistik: totaler, streaks, daglig & veckovis aktivitet, tokenanvändning, topprojekt, toppmodeller     |
| `uvx gac stats models`                 | Detaljerad statistik för **alla** använda modeller med token-uppdelning, hastighet, latens och latens-per-commit-diagram |
| `uvx gac stats projects`               | Statistik för **alla** projekt med token-uppdelning och snitt filer per gac                                              |
| `uvx gac stats recent`                 | Senaste 10 gacs (`-n 20` för fler), med tokens, hastighet, latens och filer per gac                                      |
| `uvx gac stats reset`                  | Återställ all statistik till noll (ber om bekräftelse)                                                                   |
| `uvx gac stats reset model <model-id>` | Återställ statistik för en specifik modell (skiftlägesokänslig)                                                          |

### Exempel

```sh
# Visa din övergripande statistik
uvx gac stats

# Detaljerad fördelning av alla använda modeller
uvx gac stats models

# Statistik för alla projekt
uvx gac stats projects

# Senaste gac-historik
uvx gac stats recent -n 20

# Återställ all statistik (med bekräftelseprompt)
uvx gac stats reset

# Återställ statistik för en specifik modell
uvx gac stats reset model wafer:deepseek-v4-pro
```

### Vad du kommer att se

Att köra `uvx gac stats` visar:

- **Totalt antal gacs och commits** — hur många gånger du har använt gac och hur många commits det skapat
- **Nuvarande och längsta streak** — på varandra följande dagar med gac-aktivitet (🔥 vid 5+ dagar)
- **Aktivitetssammanfattning** — dagens och denna veckas gacs, commits och tokens jämfört med din toppdag och toppvecka
- **Toppprojekt** — dina 5 mest aktiva repos efter gac- + commit-antal, med snitt filer per gac och tokenanvändning
- **Toppmodeller** — dina 5 mest använda modeller med total fart, latens och tokenanvändning

Att köra `uvx gac stats projects` visar **alla** projekt (inte bara topp 5) med:

- **Alla projekt-tabell** — varje projekt sorterat efter aktivitet, med gac-antal, commit-antal, commits-per-gac-ratio, snitt filer per gac, prompt-tokens, output-tokens, reasoning-tokens, totala tokens och andel av totala gacs
- **Aktivitetsstapeldiagram** — horisontella staplar som visar relativt gac-antal per projekt
- **Tokenanvändningsstapeldiagram** — horisontella staplar som visar relativ tokenförbrukning per projekt

Att köra `uvx gac stats models` visar **alla** modeller (inte bara topp 5) med:

- **Alla modeller-tabell** — varje använd modell sorterad efter aktivitet, med gac-antal, commit-antal, total fart (tokens/sek), total latens, prompt-tokens, output-tokens, reasoning-tokens och totala tokens
- **Hastighetsjämförelse (30d)-diagram** — ett horisontellt stapeldiagram av nyliga (senaste 30 dagarna) modellhastigheter, sorterade från snabbast till långsammast, färgkodade efter hastighetspercentil (🟡 blixtsnabbt, 🟢 snabbt, 🔵 måttligt, 🔘 långsamt)
- **Latensjämförelse (30d)-diagram** — ett horisontellt stapeldiagram av nylig latens per anrop, sorterat från kortast till längst
- **Latens-per-commit (30d)-diagram** — ett horisontellt stapeldiagram av nylig latens delat med commit-antal, visar verklig väntetid per commit (en modell som gör 5 commits i en 10s gac kostar 2s/commit vs en som gör 1 commit i en 25s gac till 25s/commit)
- **Highscore-firanden** — 🏆 troféer när du sätter nya dagliga, veckovisa, token- eller streak-rekord; 🥈 för att matcha dem
- **Uppmuntransmeddelanden** — kontextuella uppmuntringar baserade på din aktivitet

Att köra `uvx gac stats recent` visar dina senaste 10 gacs (konfigurerbart med `-n`):

- **Nyliga gacs-tabell** — varje gac med relativ tid, projekt, modell, commit-antal, filer, fart, latens och token-uppdelning per gac

### Inaktivera statistik

Ställ in miljövariabeln `GAC_DISABLE_STATS` till ett truthy-värde:

```sh
# Inaktivera statistikspårning
export GAC_DISABLE_STATS=true

# Eller i .gac.env
GAC_DISABLE_STATS=true
```

Falsy-värden (`false`, `0`, `no`, `off`, tom) håller statistik aktiverad — samma som att lämna variabeln odefinierad.

När inaktiverat hoppar gac över all statistikinspelning — ingen filläsning eller skrivning sker. Befintlig data bevaras men uppdateras inte förrän du återaktiverar den.

---

## Discord Webhook-notifikationer

gac kan pinga en Discord-kanal varje gång du gör en commit, med hjälp av en webhook-URL från kanalens integrationsinställningar. Integrationen är **opt-in**: den gör ingenting förrän du uttryckligen konfigurerar en webhook-URL.

### Konfigurering

Använd den dedikerade `discord` underkommandogruppen:

```bash
uvx gac discord setup     # konfigurera en webhook-URL interaktivt
uvx gac discord show      # visa om en webhook är konfigurerad (URL maskerad)
uvx gac discord test      # skicka ett testmeddelande till den konfigurerade webhooken
uvx gac discord remove    # ta bort den konfigurerade webhook-URL:en
```

Alternativt, ställ in variabeln direkt i `$HOME/.gac.env`（eller`./.gac.env`):

```bash
GAC_DISCORD_WEBHOOK_URL='https://discord.com/api/webhooks/XXXX/YYYY'
```

### Beteende

- Avfyras efter varje lyckad commit (enskilda och grupperade arbetsflöden). Hoppas över vid `--dry-run` och `--message-only`.
- Postar ett GitHub-stil **embed** med en grön rand, repo + gren som författarrad, commit-ämnet som titel, commit-kroppen som beskrivning och det korta SHA i fotnoten.
- Använder gac-avatar och användarnamnet `gac`.
- Webhook-fel loggas som WARNING och **blokerar aldrig** din commit.
- Lämna `GAC_DISCORD_WEBHOOK_URL` oinställt（eller tomt）för att inaktivera. `gac init` påverkas inte — Discord-konfiguration lever endast under `gac discord`.

---

## Få Hjälp

- För MCP-server setup (AI-agent integration), se [docs/MCP.md](MCP.md)
- För anpassade systemprompter, se [docs/CUSTOM_SYSTEM_PROMPTS.md](docs/CUSTOM_SYSTEM_PROMPTS.md)
- För Claude Code OAuth-installation, se [CLAUDE_CODE.md](CLAUDE_CODE.md)
- För ChatGPT OAuth-installation, se [CHATGPT_OAUTH.md](CHATGPT_OAUTH.md)
- För GitHub Copilot-installation, se [GITHUB_COPILOT.md](GITHUB_COPILOT.md)
- För felsökning och avancerade tips, se [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- För installation och konfiguration, se [README.md#installation-and-configuration](README.md#installation-and-configuration)
- För att bidra, se [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- Licensinformation: [LICENSE](LICENSE)
