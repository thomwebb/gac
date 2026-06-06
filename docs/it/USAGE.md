# Utilizzo della Linea di Comando di gac

[English](../en/USAGE.md) | [简体中文](../zh-CN/USAGE.md) | [繁體中文](../zh-TW/USAGE.md) | [日本語](../ja/USAGE.md) | [한국어](../ko/USAGE.md) | [हिन्दी](../hi/USAGE.md) | [Tiếng Việt](../vi/USAGE.md) | [Français](../fr/USAGE.md) | [Русский](../ru/USAGE.md) | [Español](../es/USAGE.md) | [Português](../pt/USAGE.md) | [Norsk](../no/USAGE.md) | [Svenska](../sv/USAGE.md) | [Deutsch](../de/USAGE.md) | [Nederlands](../nl/USAGE.md) | **Italiano**

Questo documento descrive tutte le flag e opzioni disponibili per lo strumento CLI `uvx gac`.

## Indice

- [Utilizzo della Linea di Comando di gac](#utilizzo-della-linea-di-comando-di-gac)
  - [Indice](#indice)
  - [Utilizzo Base](#utilizzo-base)
  - [Flag del Workflow Principale](#flag-del-workflow-principale)
  - [Personalizzazione Messaggio](#personalizzazione-messaggio)
  - [Output e Verbosità](#output-e-verbosità)
  - [Aiuto e Versione](#aiuto-e-versione)
  - [Workflow di Esempio](#workflow-di-esempio)
  - [Avanzate](#avanzate)
    - [Integrazione Script e Elaborazione Esterna](#integrazione-script-e-elaborazione-esterna)
    - [Saltare Hook Pre-commit e Lefthook](#saltare-hook-pre-commit-e-lefthook)
    - [Scansione Sicurezza](#scansione-sicurezza)
    - [Verifica Certificato SSL](#verifica-certificato-ssl)
  - [Note di Configurazione](#note-di-configurazione)
    - [Opzioni di Configurazione Avanzate](#opzioni-di-configurazione-avanzate)
    - [Sottocomandi di Configurazione](#sottocomandi-di-configurazione)
  - [Modalità Interattiva](#modalità-interattiva)
    - [Come Funziona](#come-funziona)
    - [Quando Usare la Modalità Interattiva](#quando-usare-la-modalità-interattiva)
    - [Esempi di Utilizzo](#esempi-di-utilizzo)
    - [Workflow Domanda-Risposta](#workflow-domanda-risposta)
    - [Combinazione con Altre Flag](#combinazione-con-altre-flag)
    - [Best Practice](#best-practice)
  - [Statistiche di Utilizzo](#statistiche-di-utilizzo)
  - [Ottenere Aiuto](#ottenere-aiuto)

## Utilizzo Base

```sh
uvx gac init
# Segui le istruzioni per configurare il tuo provider, modello e chiavi API in modo interattivo
uvx gac
```

Genera un messaggio di commit basato su LLM per le modifiche in staging e richiede conferma. Il prompt di conferma accetta:

- `y` o `yes` - Procedi con il commit
- `n` o `no` - Annulla il commit
- `r` o `reroll` - Rigenera il messaggio di commit con lo stesso contesto
- `e` o `edit` - Modifica il messaggio di commit. Per impostazione predefinita, apre una TUI in-place con binding vi/emacs. Imposta `GAC_EDITOR` per aprire il tuo editor preferito (es., `GAC_EDITOR=code gac` per VS Code, `GAC_EDITOR=vim gac` per vim)
- Qualsiasi altro testo - Rigenera con quel testo come feedback (es. `rendilo più breve`, `concentrati sulle performance`)
- Input vuoto (solo Enter) - Mostra di nuovo il prompt

---

## Flag del Workflow Principale

| Flag / Opzione       | Breve | Descrizione                                                               |
| -------------------- | ----- | ------------------------------------------------------------------------- |
| `--add-all`          | `-a`  | Metti in staging tutte le modifiche prima del commit                      |
| `--stage`            | `-S`  | Seleziona interattivamente i file da mettere in staging con TUI ad albero |
| `--group`            | `-g`  | Raggruppa le modifiche in staging in più commit logici                    |
| `--push`             | `-p`  | Push delle modifiche al remote dopo il commit                             |
| `--yes`              | `-y`  | Conferma automaticamente il commit senza richiedere                       |
| `--dry-run`          |       | Mostra cosa accadrebbe senza fare modifiche                               |
| `--message-only`     |       | Output solo del messaggio di commit generato senza commit                 |
| `--no-verify`        |       | Salta hook pre-commit e lefthook durante il commit                        |
| `--skip-secret-scan` |       | Salta scansione sicurezza per segreti nelle modifiche                     |
| `--no-verify-ssl`    |       | Salta verifica certificato SSL (utile per proxy aziendali)                |
| `--signoff`          |       | Aggiungi riga Signed-off-by al messaggio di commit (conformità DCO)       |
| `--interactive`      | `-i`  | Fai domande sulle modifiche per generare commit migliori                  |

**Nota:** `--stage` e `--add-all` si escludono a vicenda. Usa `--stage` per selezionare interattivamente quali file mettere in staging, e `--add-all` per mettere in staging tutte le modifiche in una volta.

**Nota:** Combina `-a` e `-g` (cioè `-ag`) per mettere in staging TUTTE le modifiche prima, poi raggrupparle in commit.

**Nota:** Quando usi `--group`, il limite massimo di token di output viene scalato automaticamente in base al numero di file in commit (2x per 1-9 file, 3x per 10-19 file, 4x per 20-29 file, 5x per 30+ file). Questo assicura che l'LLM abbia abbastanza token per generare tutti i commit raggruppati senza troncamento, anche per changeset grandi.

**Nota:** `--message-only` e `--group` si escludono a vicenda. Usa `--message-only` quando vuoi ottenere il messaggio di commit per elaborazione esterna, e `--group` quando vuoi organizzare più commit nel workflow git corrente.

**Nota:** La flag `--interactive` fa domande sulle tue modifiche per fornire contesto aggiuntivo all'LLM, risultando in messaggi di commit più accurati e dettagliati. Questo è particolarmente utile per modifiche complesse o quando vuoi assicurarti che il messaggio di commit catturi il contesto completo del tuo lavoro.

## Personalizzazione Messaggio

| Flag / Opzione      | Breve | Descrizione                                                                   |
| ------------------- | ----- | ----------------------------------------------------------------------------- |
| `--one-liner`       | `-o`  | Genera un messaggio di commit su una riga                                     |
| `--verbose`         | `-v`  | Genera messaggi di commit dettagliati con motivazione, architettura e impatto |
| `--hint <text>`     | `-h`  | Aggiungi un suggerimento per guidare l'LLM                                    |
| `--model <model>`   | `-m`  | Specifica il modello da usare per questo commit                               |
| `--language <lang>` | `-l`  | Sovrascrivi la lingua (nome o codice: 'Italian', 'it', 'zh-CN', 'ja')         |
| `--scope`           | `-s`  | Deduci uno scope appropriato per il commit                                    |
| `--50-72`           |       | Applica la regola 50/72 per la formattazione dei messaggi di commit           |

**Nota:** Il flag `--50-72` applica la [regola 50/72](https://www.conventionalcommits.org/en/v1.0.0/#summary) dove:

- Linea oggetto: massimo 50 caratteri
- Linee del corpo: massimo 72 caratteri per riga
- Questo mantiene i messaggi di commit leggibili in `git log --oneline` e nell'interfaccia di GitHub

Puoi anche impostare `GAC_USE_50_72_RULE=true` nel tuo file `.gac.env` per applicare sempre questa regola.

**Nota:** Puoi fornire feedback in modo interattivo digitandolo semplicemente al prompt di conferma - non è necessario prefissare con 'r'. Digita `r` per un semplice reroll, `e` per modificare il messaggio (TUI in-place per impostazione predefinita, o il tuo `$GAC_EDITOR` se impostato), o digita il tuo feedback direttamente come `rendilo più breve`.

## Output e Verbosità

| Flag / Opzione        | Breve | Descrizione                                                 |
| --------------------- | ----- | ----------------------------------------------------------- |
| `--quiet`             | `-q`  | Sopprimi tutto l'output tranne gli errori                   |
| `--log-level <level>` |       | Imposta livello di log (debug, info, warning, error)        |
| `--show-prompt`       |       | Stampa il prompt LLM usato per la generazione del messaggio |

## Aiuto e Versione

| Flag / Opzione | Breve | Descrizione                       |
| -------------- | ----- | --------------------------------- |
| `--version`    |       | Mostra versione gac ed esce       |
| `--help`       |       | Mostra messaggio di aiuto ed esce |

---

## Workflow di Esempio

- **Metti in staging tutte le modifiche e fai commit:**

  ```sh
  uvx gac -a
  ```

- **Fai commit e push in un passo:**

  ```sh
  uvx gac -ap
  ```

- **Genera un messaggio di commit su una riga:**

  ```sh
  uvx gac -o
  ```

- **Genera un messaggio di commit dettagliato con sezioni strutturate:**

  ```sh
  uvx gac -v
  ```

- **Aggiungi un suggerimento per l'LLM:**

  ```sh
  uvx gac -h "Rifattorizza logica di autenticazione"
  ```

- **Deduci scope per il commit:**

  ```sh
  uvx gac -s
  ```

- **Raggruppa modifiche in staging in commit logici:**

  ```sh
  uvx gac -g
  # Raggruppa solo i file che hai già messo in staging
  ```

- **Raggruppa tutte le modifiche (staging + non-staging) e conferma automaticamente:**

  ```sh
  uvx gac -agy
  # Mette in staging tutto, raggruppa e conferma automaticamente
  ```

- **Usa un modello specifico solo per questo commit:**

  ```sh
  uvx gac -m anthropic:claude-haiku-4-5
  ```

- **Genera messaggio di commit in una lingua specifica:**

  ```sh
  # Usando codici lingua (più brevi)
  uvx gac -l zh-CN
  uvx gac -l ja
  uvx gac -l es

  # Usando nomi completi
  uvx gac -l "Cinese Semplificato"
  uvx gac -l Giapponese
  uvx gac -l Spagnolo
  ```

- **Dry run (vedi cosa accadrebbe):**

  ```sh
  uvx gac --dry-run
  ```

- **Ottieni solo il messaggio di commit (per integrazione script):**

  ```sh
  uvx gac --message-only
  # Output: feat: aggiungi sistema di autenticazione utente
  ```

- **Ottieni messaggio di commit in formato una riga:**

  ```sh
  uvx gac --message-only --one-liner
  # Output: feat: aggiungi sistema di autenticazione utente
  ```

- **Usa modalità interattiva per fornire contesto:**

  ```sh
  uvx gac -i
  # Qual è lo scopo principale di queste modifiche?
  # Quale problema stai risolvendo?
  # Ci sono dettagli implementativi da menzionare?
  ```

- **Modalità interattiva con output dettagliato:**

  ```sh
  uvx gac -i -v
  # Fai domande e genera messaggio di commit dettagliato
  ```

## Avanzate

- Combina flag per workflow più potenti (es. `uvx gac -ayp` per mettere in staging, confermare automaticamente e pushare)
- Usa `--show-prompt` per debuggare o rivedere il prompt inviato all'LLM
- Regola verbosità con `--log-level` o `--quiet`
- Usa `--message-only` per integrazione script e workflow automatizzati

### Integrazione Script e Elaborazione Esterna

La flag `--message-only` è progettata per integrazione script e workflow strumenti esterni. Output solo il messaggio di commit grezzo senza formattazione, spinner o elementi UI aggiuntivi.

**Casi d'uso:**

- **Integrazione agenti:** Permetti agli agenti AI di ottenere messaggi di commit e gestire i commit stessi
- **VCS alternativi:** Usa messaggi generati con altri sistemi di controllo versione (Mercurial, Jujutsu, ecc.)
- **Workflow commit personalizzati:** Elabora o modifica il messaggio prima del commit
- **Pipeline CI/CD:** Estrai messaggi di commit per processi automatizzati

**Esempio uso script:**

```sh
#!/bin/bash
# Ottieni messaggio di commit e usa con funzione commit personalizzata
MESSAGE=20 20 12 61 79 80 81 98 701 33 100 204 250 395 398 399 400uvx gac --message-only --add-all --yes)
git commit -m "$MESSAGE"
```

```python
# Esempio integrazione Python
import subprocess

def get_commit_message():
    result = subprocess.run(
        ["gac", "--message-only", "--yes"],
        capture_output=True, text=True
    )
    return result.stdout.strip()

message = get_commit_message()
print(f"Messaggio generato: {message}")
```

**Caratteristiche chiave per uso script:**

- Output pulito senza formattazione Rich o spinner
- Bypassa automaticamente i prompt di conferma
- Nessun commit effettivo viene fatto su git
- Funziona con `--one-liner` per output semplificato
- Può essere combinato con altre flag come `--hint`, `--model`, ecc.

### Saltare Hook Pre-commit e Lefthook

La flag `--no-verify` ti permette di saltare qualsiasi hook pre-commit o lefthook configurato nel tuo progetto:

```sh
uvx gac --no-verify  # Salta tutti gli hook pre-commit e lefthook
```

**Usa `--no-verify` quando:**

- Gli hook pre-commit o lefthook falliscono temporaneamente
- Stai lavorando con hook che richiedono molto tempo
- Stai facendo commit di codice work-in-progress che non passa ancora tutti i controlli

**Nota:** Usa con cautela poiché questi hook mantengono standard di qualità del codice.

### Scansione Sicurezza

uvx gac include scansione sicurezza integrata che rileva automaticamente potenziali segreti e chiavi API nelle tue modifiche in staging **prima di qualsiasi chiamata API di IA**. Se viene rilevato un segreto, il workflow viene interrotto immediatamente — nessuna chiamata API viene effettuata. Questo garantisce che i tuoi dati sensibili non vengano mai inviati a nessun modello di IA. Lo scanner usa **pattern matching basato su regex**, non LLM, quindi la scansione è veloce e viene eseguita interamente in locale.

**Saltare scansioni sicurezza:**

```sh
uvx gac --skip-secret-scan  # Salta scansione sicurezza per questo commit
```

**Per disabilitare permanentemente:** Imposta `GAC_SKIP_SECRET_SCAN=true` nel tuo file `.gac.env`.

**Quando saltare:**

- Commit di codice esempio con chiavi segnaposto
- Lavoro con test fixture che contengono credenziali fittizie
- Quando hai verificato che le modifiche sono sicure

**Nota:** Lo scanner usa pattern matching basato su regex (non LLM) per rilevare formati segreti comuni. Viene eseguito prima di qualsiasi chiamata API di IA — se viene trovato un segreto, nessuna chiamata API viene effettuata. Rivedi sempre le tue modifiche in staging prima del commit.

### Verifica Certificato SSL

Il flag `--no-verify-ssl` ti permette di saltare la verifica del certificato SSL per le chiamate API:

```sh
uvx gac --no-verify-ssl  # Salta verifica SSL per questo commit
```

**Per impostare permanentemente:** Imposta `GAC_NO_VERIFY_SSL=true` nel tuo file `.gac.env`.

**Usa `--no-verify-ssl` quando:**

- Proxy aziendali intercettano traffico SSL (proxy MITM)
- Ambienti di sviluppo usano certificati auto-firmati
- Riscontri errori di certificato SSL a causa di impostazioni di sicurezza di rete

**Nota:** Usa questa opzione solo in ambienti di rete affidabili. Disabilitare la verifica SSL riduce la sicurezza e può rendere le tue richieste API vulnerabili ad attacchi man-in-the-middle.

### Riga Signed-off-by (Conformità DCO)

uvx gac supporta l'aggiunta di una riga `Signed-off-by` ai messaggi di commit, che è richiesta per la conformità al [Developer Certificate of Origin (DCO)](https://developercertificate.org/) in molti progetti open source.

**Aggiungi signoff :**

```sh
uvx gac --signoff  # Aggiungi riga Signed-off-by al messaggio di commit (conformità DCO)
```

**Per abilitare permanentemente :** Imposta `GAC_SIGNOFF=true` nel tuo file `.gac.env`, o aggiungi `signoff=true` alla tua configurazione.

**Cosa fa :**

- Aggiunge `Signed-off-by: Il Tuo Nome <tua.email@example.com>` al messaggio di commit
- Usa la tua configurazione git (`user.name` e `user.email`) per la riga
- Richiesto per progetti come Cherry Studio, kernel Linux e altri che usano DCO

**Configurazione identità git :**

Assicurati che la tua configurazione git abbia il nome e l'email corretti :

```sh
git config --global user.name "Your Full Name"
git config --global user.email "your.email@example.com"
```

**Nota :** La riga Signed-off-by è aggiunta da git durante il commit, non dall'IA durante la generazione del messaggio. Non la vedrai nell'anteprima, ma sarà nel commit finale (verifica con `git log -1`).

## Note di Configurazione

- Il modo raccomandato per configurare gac è eseguire `uvx gac init` e seguire i prompt interattivi.
- Già configurata la lingua e devi solo cambiare provider o modelli? Esegui `uvx gac model` per ripetere la configurazione senza domande sulla lingua.
- **Usi Claude Code?** Vedi la [guida setup Claude Code](CLAUDE_CODE.md) per istruzioni autenticazione OAuth.
- **Usi ChatGPT OAuth?** Vedi la [guida setup ChatGPT OAuth](CHATGPT_OAUTH.md) per istruzioni autenticazione basata su browser.
- **Usi GitHub Copilot?** Vedi la [guida setup GitHub Copilot](GITHUB_COPILOT.md) per istruzioni autenticazione Device Flow.
- gac carica la configurazione nel seguente ordine di precedenza:
  1. Flag CLI
  2. `.gac.env` a livello di progetto
  3. `~/.gac.env` a livello utente
  4. Variabili ambiente

### Opzioni di Configurazione Avanzate

Puoi personalizzare il comportamento di gac con queste variabili ambiente opzionali:

- `GAC_EDITOR=code --wait` - Sovrascrive l'editor usato quando premi `e` al prompt di conferma. Per impostazione predefinita, `e` apre una TUI in-place; impostando `GAC_EDITOR` si passa a un editor esterno. Supporta qualsiasi comando di editor con argomenti. I flag di attesa (`--wait`/`-w`) vengono inseriti automaticamente per gli editor GUI noti (VS Code, Cursor, Zed, Sublime Text) in modo che il processo si blocchi fino alla chiusura del file
- `GAC_ALWAYS_INCLUDE_SCOPE=true` - Deduci automaticamente e includi scope nei messaggi di commit (es. `feat(auth):` vs `feat:)
- `GAC_VERBOSE=true` - Genera messaggi di commit dettagliati con sezioni motivazione, architettura e impatto
- `GAC_USE_50_72_RULE=true` - Applica sempre la regola 50/72 per i messaggi di commit (oggetto ≤50 caratteri, righe corpo ≤72 caratteri)
- `GAC_SIGNOFF=true` - Aggiungi sempre la riga Signed-off-by ai commit (per conformità DCO)
- `GAC_TEMPERATURE=0.7` - Controlla creatività LLM (0.0-1.0, più basso = più focalizzato)
- `GAC_REASONING_EFFORT=medium` - Controllare la profondità di ragionamento/pensiero per modelli che supportano il pensiero esteso (low, medium, high). Lasciare non impostato per usare il predefinito di ciascun modello. Inviato solo a provider compatibili (stile OpenAI; non Anthropic).
- `GAC_MAX_OUTPUT_TOKENS=4096` - Token massimi per messaggi generati (scalato automaticamente 2-5x quando usi `--group` in base al numero di file; sovrascrivi per andare più alto o più basso)
- `GAC_WARNING_LIMIT_TOKENS=4096` - Avvisa quando i prompt superano questo numero di token
- `GAC_SYSTEM_PROMPT_PATH=/path/to/custom_prompt.txt` - Usa un prompt di sistema personalizzato per la generazione messaggi di commit
- `GAC_LANGUAGE=Italian` - Genera messaggi di commit in una lingua specifica (es. Italian, French, Japanese, German). Supporta nomi completi o codici ISO (it, fr, ja, de, zh-CN). Usa `uvx gac language` per selezione interattiva
- `GAC_TRANSLATE_PREFIXES=true` - Traduci prefissi commit convenzionali (feat, fix, ecc.) nella lingua target (default: false, mantiene prefissi in inglese)
- `GAC_SKIP_SECRET_SCAN=true` - Disabilita scansione sicurezza automatica per segreti nelle modifiche in staging (usa con cautela)
- `GAC_NO_VERIFY_SSL=true` - Salta verifica certificato SSL per chiamate API (utile per proxy aziendali che intercettano traffico SSL)
- `GAC_DISABLE_STATS=true` - Disabilita il tracciamento delle statistiche di utilizzo (nessuna lettura o scrittura di file di statistiche; i dati esistenti sono preservati). Solo i valori truthy disabilitano le statistiche; impostare a `false`/`0`/`no`/`off` le mantiene abilitate, come se la variabile non fosse impostata

Vedi `.gac.env.example` per un template di configurazione completo.

Per guida dettagliata sulla creazione di prompt di sistema personalizzati, vedi [docs/CUSTOM_SYSTEM_PROMPTS.md](docs/CUSTOM_SYSTEM_PROMPTS.md).

### Sottocomandi di Configurazione

I seguenti sottocomandi sono disponibili:

- `uvx gac init` — Setup guidato interattivo per configurazione provider, modello e lingua
- `uvx gac model` — Setup provider/modello/chiave API senza prompt lingua (ideale per cambi rapidi)
- `uvx gac auth` — Mostra stato autenticazione OAuth per tutti i provider
- `uvx gac auth claude-code login` — Accedi a Claude Code usando OAuth (apre browser)
- `uvx gac auth claude-code logout` — Esci da Claude Code e rimuovi token memorizzato
- `uvx gac auth claude-code status` — Controlla stato autenticazione Claude Code
- `uvx gac auth chatgpt login` — Accedi a ChatGPT usando OAuth (apre browser)
- `uvx gac auth chatgpt logout` — Esci da ChatGPT e rimuovi token memorizzati
- `uvx gac auth chatgpt status` — Controlla stato autenticazione ChatGPT
- `uvx gac auth copilot login` — Accedi a GitHub Copilot usando Device Flow
- `uvx gac auth copilot login --host ghe.mycompany.com` — Accedi a Copilot su un'istanza GitHub Enterprise
- `uvx gac auth copilot logout` — Esci da Copilot e rimuovi token memorizzati
- `uvx gac auth copilot status` — Controlla stato autenticazione Copilot
- `uvx gac config show` — Mostra configurazione corrente
- `uvx gac config set KEY VALUE` — Imposta una chiave di configurazione in `$HOME/.gac.env`
- `uvx gac config get KEY` — Ottieni un valore di configurazione
- `uvx gac config unset KEY` — Rimuovi una chiave di configurazione da `$HOME/.gac.env`
- `uvx gac language` (o `uvx gac lang`) — Selettore lingua interattivo per messaggi di commit (imposta GAC_LANGUAGE)
- `uvx gac editor` (o `uvx gac edit`) — Selettore editor interattivo per il tasto `e` al prompt di conferma (imposta GAC_EDITOR)
- `uvx gac diff` — Mostra git diff filtrato con opzioni per modifiche staging/non-staging, colore e troncamento
- `uvx gac serve` — Avvia GAC come [server MCP](MCP.md) per l'integrazione con agenti AI (trasporto stdio)
- `uvx gac stats show` — Vedi le tue statistiche di utilizzo di gac (totali, serie, attività giornaliera e settimanale, utilizzo dei token, progetti principali con file medi, modelli principali con velocità e latenza)
- `uvx gac stats models` — Statistiche dettagliate per tutti i modelli con ripartizione token, velocità, latenza e grafici latenza per commit
- `uvx gac stats projects` — Statistiche per tutti i progetti con ripartizione token e file medi per gac
- `uvx gac stats recent` — Ultimi 10 gac con token, velocità, latenza e file per gac (`-n 20` per più)
- `uvx gac stats reset` — Ripristina tutte le statistiche a zero (richiede conferma)
- `uvx gac stats reset model <model-id>` — Ripristina le statistiche di un modello specifico (insensibile a maiuscole e minuscole)

## Modalità Interattiva

La flag `--interactive` (`-i`) migliora la generazione messaggi di commit di gac facendoti domande mirate sulle tue modifiche. Questo contesto aggiuntivo aiuta l'LLM a creare messaggi di commit più accurati, dettagliati e contestualmente appropriati.

### Come Funziona

Quando usi `--interactive`, gac ti farà domande come:

- **Qual è lo scopo principale di queste modifiche?** - Aiuta a capire l'obiettivo di alto livello
- **Quale problema stai risolvendo?** - Fornisce contesto sulla motivazione
- **Ci sono dettagli implementativi da menzionare?** - Cattura specifiche tecniche
- **Ci sono breaking changes?** - Identifica potenziali problemi di impatto
- **Questo è correlato a qualche issue o ticket?** - Collega al project management

### Quando Usare la Modalità Interattiva

La modalità interattiva è particolarmente utile per:

- **Modifiche complesse** dove il contesto non è ovvio solo dal diff
- **Lavoro di refactoring** che si estende su più file e concetti
- **Nuove funzionalità** che richiedono spiegazione dello scopo generale
- **Bug fix** dove la causa radice non è immediatamente visibile
- **Ottimizzazioni performance** dove il ragionamento non è ovvio
- **Preparazione code review** - le domande aiutano a pensare alle tue modifiche

### Esempi di Utilizzo

**Modalità interattiva base:**

```sh
uvx gac -i
```

Questo:

1. Mostra un riepilogo delle modifiche in staging
2. Fa domande sulle modifiche
3. Genera un messaggio di commit incorporando le tue risposte
4. Richiede conferma (o conferma automatica se combinato con `-y`)

**Modalità interattiva con modifiche in staging:**

```sh
uvx gac -ai
# Metti in staging tutte le modifiche, poi fai domande per migliore contesto
```

**Modalità interattiva con suggerimenti specifici:**

```sh
uvx gac -i -h "Migrazione database per profili utente"
# Fai domande fornendo un suggerimento specifico per focalizzare l'LLM
```

**Modalità interattiva con output dettagliato:**

```sh
uvx gac -i -v
# Fai domande e genera un messaggio di commit dettagliato e strutturato
```

**Modalità interattiva con conferma automatica:**

```sh
uvx gac -i -y
# Fai domande ma conferma automaticamente il commit risultante
```

### Workflow Domanda-Risposta

Il workflow interattivo segue questo schema:

1. **Rivedi modifiche** - gac mostra un riepilogo di ciò che stai committando
2. **Rispondi alle domande** - rispondi a ogni prompt con dettagli rilevanti
3. **Miglioramento contesto** - le tue risposte vengono aggiunte al prompt LLM
4. **Generazione messaggio** - l'LLM crea un messaggio di commit con contesto completo
5. **Conferma** - rivedi e conferma il commit (o conferma automatica con `-y`)

**Suggerimenti per fornire risposte utili:**

- **Sii conciso ma completo** - fornisci dettagli chiave senza essere eccessivamente verboso
- **Concentrati sul "perché"** - spiega il ragionamento dietro le tue modifiche
- **Menziona vincoli** - nota limitazioni o considerazioni speciali
- **Collega a contesto esterno** - riferisci a issues, documentazione o documenti di design
- **Risposte vuote vanno bene** - se una domanda non si applica, premi solo Enter

### Combinazione con Altre Flag

La modalità interattiva funziona bene con la maggior parte delle altre flag:

```sh
# Metti in staging tutte le modifiche e fai domande
uvx gac -ai

# Fai domande con output dettagliato
uvx gac -i -v
```

### Best Practice

- **Usa per PR complessi** - particolarmente utile per pull request che necessitano descrizioni dettagliate
- **Collaborazione team** - le domande aiutano a pensare a modifiche che altri revisioneranno
- **Preparazione documentazione** - le tue risposte possono aiutare a formare la base per le release notes
- **Strumento di apprendimento** - le domande rafforzano buone pratiche di messaggi di commit
- **Salta per modifiche semplici** - per fix banali, la modalità base potrebbe essere più veloce

## Statistiche di Utilizzo

uvx gac traccia statistiche di utilizzo leggere per permetterti di vedere la tua attività di commit, serie, utilizzo dei token e progetti e modelli più attivi. Le statistiche sono memorizzate localmente in `~/.gac_stats.json` e non vengono mai inviate da nessuna parte — non c'è telemetria.

**Cosa viene tracciato:** esecuzioni totali di gac, commit totali, token totali di prompt, output e ragionamento, date primo/ultimo utilizzo, conteggi giornalieri e settimanali (gac, commit, token), serie attuale e più lunga, attività per progetto (gac, commit, token) e attività per modello (gac, token).

**Cosa NON viene tracciato:** messaggi di commit, contenuto del codice, percorsi dei file, informazioni personali o qualsiasi cosa oltre conteggi, date, nomi di progetti (derivati dal remote o dalla directory git) e nomi di modelli.

### Opt-in o Opt-out

`uvx gac init` chiede se abilitare le statistiche e spiega esattamente cosa viene memorizzato. Puoi cambiare idea in qualsiasi momento:

- **Abilitare le statistiche:** rimuovi `GAC_DISABLE_STATS` o impostalo a `false`/`0`/`no`/`off`/vuoto.
- **Disabilitare le statistiche:** imposta `GAC_DISABLE_STATS` a un valore truthy (`true`, `1`, `yes`, `on`).

Quando rifiuti le statistiche durante `uvx gac init` e viene rilevato un file `~/.gac_stats.json` esistente, ti verrà offerta l'opzione di eliminarlo.

### Sottocomandi delle Statistiche

| Comando                                | Descrizione                                                                                                                                 |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `uvx gac stats`                        | Mostra le tue statistiche (come `uvx gac stats show`)                                                                                       |
| `uvx gac stats show`                   | Mostra statistiche complete: totali, serie, attività giornaliera e settimanale, utilizzo dei token, progetti principali, modelli principali |
| `uvx gac stats models`                 | Statistiche dettagliate per **tutti** i modelli con ripartizione token, velocità, latenza e grafici latenza per commit                      |
| `uvx gac stats projects`               | Statistiche per **tutti** i progetti con ripartizione token e file medi per gac                                                             |
| `uvx gac stats recent`                 | Ultimi 10 gac (`-n 20` per più), con token, velocità, latenza e file per gac                                                                |
| `uvx gac stats reset`                  | Ripristina tutte le statistiche a zero (richiede conferma)                                                                                  |
| `uvx gac stats reset model <model-id>` | Ripristina le statistiche di un modello specifico (insensibile a maiuscole e minuscole)                                                     |

### Esempi

```sh
# Visualizza le tue statistiche generali
uvx gac stats

# Ripartizione dettagliata di tutti i modelli utilizzati
uvx gac stats models

# Statistiche di tutti i progetti
uvx gac stats projects

# Cronologia gac recenti
uvx gac stats recent -n 20

# Ripristina tutte le statistiche (con conferma)
uvx gac stats reset

# Ripristina le statistiche di un modello specifico
uvx gac stats reset model wafer:deepseek-v4-pro
```

### Cosa vedrai

Eseguire `uvx gac stats` mostra:

- **Gac e commit totali** — quante volte hai usato gac e quanti commit ha creato
- **Serie attuale e più lunga** — giorni consecutivi con attività gac (🔥 a 5+ giorni)
- **Riepilogo attività** — gac, commit e token di oggi e di questa settimana vs il tuo picco giornaliero e settimanale
- **Progetti principali** — i tuoi 5 repository più attivi per conteggio gac + commit, con file medi per gac e utilizzo dei token
- **Modelli principali** — i tuoi 5 modelli più usati con velocità storica, latenza e utilizzo dei token

Eseguire `uvx gac stats projects` mostra **tutti** i progetti (non solo i primi 5) con:

- **Tabella di tutti i progetti** — ogni progetto ordinato per attività, con conteggio gac, conteggio commit, rapporto commit-per-gac, file medi per gac, token di prompt, token di output, token di ragionamento, token totali e quota di gac totali
- **Grafico a barre dell'attività** — barre orizzontali che mostrano il conteggio relativo di gac per progetto
- **Grafico a barre dell'utilizzo dei token** — barre orizzontali che mostrano il consumo relativo di token per progetto

Eseguire `uvx gac stats models` mostra **tutti** i modelli (non solo i primi 5) con:

- **Tabella di tutti i modelli** — ogni modello utilizzato ordinato per attività, con conteggio gac, conteggio commit, velocità storica (token/sec), latenza storica, token di prompt, token di output, token di ragionamento e token totali
- **Grafico comparativo della velocità (30g)** — un grafico a barre orizzontali delle velocità recenti (ultimi 30 giorni) dei modelli, ordinati dal più veloce al più lento, colorati per percentile di velocità (🟡 fulmineo, 🟢 veloce, 🔵 moderato, 🔘 lento)
- **Grafico comparativo della latenza (30g)** — un grafico a barre orizzontali della latenza recente per chiamata, ordinata dalla più breve alla più lunga
- **Grafico latenza per commit (30g)** — un grafico a barre orizzontali della latenza recente divisa per numero di commit, mostra il tempo reale di attesa per commit (un modello che fa 5 commit in un gac di 10s costa 2s/commit vs uno che fa 1 commit in un gac di 25s a 25s/commit)
- **Celebrazioni dei record** — 🏆 trofei quando stabilisci nuovi record giornalieri, settimanali, di token o di serie; 🥈 per pareggiarli
- **Messaggi di incoraggiamento** — suggerimenti contestuali basati sulla tua attività

Eseguire `uvx gac stats recent` mostra i tuoi ultimi 10 gac (configurabile con `-n`):

- **Tabella gac recenti** — ogni gac con tempo relativo, progetto, modello, conteggio commit, file, velocità, latenza e ripartizione token per gac

### Disabilitare le statistiche

Imposta la variabile d'ambiente `GAC_DISABLE_STATS` a un valore truthy:

```sh
# Disabilita tracciamento statistiche
export GAC_DISABLE_STATS=true

# Oppure in .gac.env
GAC_DISABLE_STATS=true
```

I valori falsy (`false`, `0`, `no`, `off`, vuoto) mantengono le statistiche abilitate — come se la variabile non fosse impostata.

Quando disabilitato, gac salta tutta la registrazione delle statistiche — nessuna lettura o scrittura di file avviene. I dati esistenti sono preservati ma non verranno aggiornati finché non le riabiliti.

---

## Notifiche Webhook Discord

gac può notificare un canale Discord ogni volta che effettui un commit, utilizzando un URL webhook dalle impostazioni di integrazione del tuo canale. L'integrazione è **opt-in**: non fa nulla finché non configuri esplicitamente un URL webhook.

### Configurazione

Utilizza il gruppo di sottocomandi `discord` dedicato:

```bash
uvx gac discord setup     # configura interattivamente un URL webhook
uvx gac discord show      # mostra se è configurato un webhook (URL mascherato)
uvx gac discord test      # invia una notifica di prova al webhook configurato
uvx gac discord remove    # rimuove l'URL webhook configurato
```

In alternativa, imposta la variabile direttamente in `$HOME/.gac.env` (o `./.gac.env`):

```bash
GAC_DISCORD_WEBHOOK_URL='https://discord.com/api/webhooks/XXXX/YYYY'
```

### Comportamento

- Si attiva dopo ogni commit riuscito (flussi di lavoro singoli e raggruppati). Saltato con `--dry-run` e `--message-only`.
- Pubblica un **embed** in stile GitHub con una striscia verde, repo + branch come riga autore, l'oggetto del commit come titolo, il corpo del commit come descrizione e l'SHA breve nel footer.
- Usa l'avatar gac e il nome utente `gac`.
- I fallimenti del webhook sono registrati a WARNING e **non bloccano mai** il tuo commit.
- Lascia `GAC_DISCORD_WEBHOOK_URL` non impostato (o vuoto) per disabilitare. `gac init` non è interessato — la configurazione Discord vive solo sotto `gac discord`.

---

## Ottenere Aiuto

- Per la configurazione del server MCP (integrazione agenti AI), vedi [docs/MCP.md](MCP.md)
- Per prompt di sistema personalizzati, vedi [docs/CUSTOM_SYSTEM_PROMPTS.md](docs/CUSTOM_SYSTEM_PROMPTS.md)
- Per configurazione OAuth di Claude Code, vedi [CLAUDE_CODE.md](CLAUDE_CODE.md)
- Per configurazione OAuth di ChatGPT, vedi [CHATGPT_OAUTH.md](CHATGPT_OAUTH.md)
- Per configurazione GitHub Copilot, vedi [GITHUB_COPILOT.md](GITHUB_COPILOT.md)
- Per troubleshooting e suggerimenti avanzati, vedi [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- Per installazione e configurazione, vedi [README.md#installation-and-configuration](README.md#installation-and-configuration)
- Per contribuire, vedi [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- Informazioni licenza: [LICENSE](LICENSE)
