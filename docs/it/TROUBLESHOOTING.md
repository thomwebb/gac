# Risoluzione problemi gac

[English](../en/TROUBLESHOOTING.md) | [简体中文](../zh-CN/TROUBLESHOOTING.md) | [繁體中文](../zh-TW/TROUBLESHOOTING.md) | [日本語](../ja/TROUBLESHOOTING.md) | [한국어](../ko/TROUBLESHOOTING.md) | [हिन्दी](../hi/TROUBLESHOOTING.md) | [Tiếng Việt](../vi/TROUBLESHOOTING.md) | [Français](../fr/TROUBLESHOOTING.md) | [Русский](../ru/TROUBLESHOOTING.md) | [Español](../es/TROUBLESHOOTING.md) | [Português](../pt/TROUBLESHOOTING.md) | [Norsk](../no/TROUBLESHOOTING.md) | [Svenska](../sv/TROUBLESHOOTING.md) | [Deutsch](../de/TROUBLESHOOTING.md) | [Nederlands](../nl/TROUBLESHOOTING.md) | **Italiano**

Questa guida illustra i problemi comuni e le soluzioni per l'installazione, la configurazione e l'esecuzione di gac.

## Indice

- [Risoluzione problemi gac](#risoluzione-problemi-gac)
  - [Indice](#indice)
  - [1. Problemi di installazione](#1-problemi-di-installazione)
  - [2. Problemi di configurazione](#2-problemi-di-configurazione)
  - [3. Errori provider/API](#3-errori-providerapi)
  - [4. Problemi di raggruppamento commit](#4-problemi-di-raggruppamento-commit)
  - [5. Sicurezza e rilevamento segreti](#5-sicurezza-e-rilevamento-segreti)
  - [6. Problemi con hook pre-commit e lefthook](#6-problemi-con-hook-pre-commit-e-lefthook)
  - [7. Problemi comuni di flusso di lavoro](#7-problemi-comuni-di-flusso-di-lavoro)
  - [8. Debug generale](#8-debug-generale)
  - [Ancora bloccato?](#ancora-bloccato)
  - [Dove ottenere ulteriore aiuto](#dove-ottenere-ulteriore-aiuto)

## 1. Problemi di installazione

**Problema:** Comando `gac` non trovato dopo l'installazione

- Assicurati di aver installato con `uvx gac`
- Assicurati che `uv` sia installato e nel tuo `$PATH`
- Riavvia il terminale dopo l'installazione

**Problema:** Permesso negato o impossibile scrivere file

- Controlla i permessi della directory
- Prova a eseguire con privilegi appropriati o cambia la proprietà della directory

## 2. Problemi di configurazione

**Problema:** gac non trova la tua chiave API o il modello

- Se sei nuovo, esegui `gac init` per configurare interattivamente il tuo provider, modello e chiavi API
- Assicurati che `.gac.env` o le variabili d'ambiente siano impostate correttamente
- Esegui `gac --log-level=debug` per vedere quali file di configurazione vengono caricati e risolvere i problemi
- Controlla eventuali errori di battitura nei nomi delle variabili (es. `GAC_GROQ_API_KEY`)

**Problema:** Le modifiche a `$HOME/.gac.env` a livello utente non vengono rilevate

- Assicurati di modificare il file corretto per il tuo sistema operativo:
  - Su macOS/Linux: `$HOME/.gac.env` (di solito `/Users/<tuo-username>/.gac.env` o `/home/<tuo-username>/.gac.env`)
  - Su Windows: `$HOME/.gac.env` (tipicamente `C:\\Users\\<tuo-username>\\.gac.env` o usa `%USERPROFILE%`)
- Esegui `gac --log-level=debug` per confermare che la configurazione a livello utente venga caricata
- Riavvia il terminale o ri-esegui la shell per ricaricare le variabili d'ambiente
- Se ancora non funziona, controlla errori di battitura e permessi dei file

**Problema:** Le modifiche a `.gac.env` a livello di progetto non vengono rilevate

- Assicurati che il progetto contenga un file `.gac.env` nella directory radice (accanto alla cartella `.git`)
- Esegui `gac --log-level=debug` per confermare che la configurazione a livello di progetto venga caricata
- Se modifichi `.gac.env`, riavvia il terminale o ri-esegui la shell per ricaricare le variabili d'ambiente
- Se ancora non funziona, controlla errori di battitura e permessi dei file

**Problema:** Impossibile impostare o cambiare la lingua per i messaggi di commit

- Esegui `gac language` (o `gac lang`) per selezionare interattivamente tra 25+ lingue supportate
- Usa il flag `-l <lingua>` per sovrascrivere la lingua per un singolo commit (es. `gac -l zh-CN`, `gac -l Italian`)
- Controlla la configurazione con `gac config show` per vedere l'impostazione della lingua corrente
- L'impostazione della lingua è memorizzata in `GAC_LANGUAGE` nel tuo file `.gac.env`

## 3. Errori provider/API

**Problema:** Errori di autenticazione o API

- Assicurati di aver impostato le chiavi API corrette per il modello scelto (es. `ANTHROPIC_API_KEY`, `GROQ_API_KEY`)
- Ricontrolla la tua chiave API e lo stato dell'account del provider
- Per Ollama e LM Studio, conferma che l'URL API corrisponda alla tua istanza locale. Le chiavi API sono necessarie solo se hai abilitato l'autenticazione.
- **Per scadenza token di Claude Code**: Esegui `gac auth` per ri-autenticarti rapidamente e aggiornare il tuo token. Il browser si aprirà automaticamente per OAuth.
- **Per scadenza token di ChatGPT OAuth**: Esegui `gac auth chatgpt login` per ri-autenticarti. Il browser si aprirà automaticamente per OAuth.
- **Per problemi di sessione GitHub Copilot**: Esegui `gac auth copilot login` per ri-autenticarti tramite Device Flow. I token di sessione vengono rinnovati automaticamente dal token OAuth memorizzato nella cache.
- **Per altri problemi OAuth di Claude Code**, consulta la [guida alla configurazione di Claude Code](CLAUDE_CODE.md) per la risoluzione completa dei problemi.
- **Per altri problemi OAuth di ChatGPT**, consulta la [guida alla configurazione di ChatGPT OAuth](CHATGPT_OAUTH.md) per la risoluzione completa dei problemi.
- **Per altri problemi di Copilot**, consulta la [guida alla configurazione di GitHub Copilot](GITHUB_COPILOT.md) per la risoluzione completa dei problemi.

**Problema:** Modello non disponibile o non supportato

- Streamlake utilizza ID degli endpoint di inferenza anziché nomi di modello. Assicurati di fornire l'ID endpoint dalla loro console.
- Verifica che il nome del modello sia corretto e supportato dal tuo provider
- Consulta la documentazione del provider per i modelli disponibili

## 4. Problemi di raggruppamento commit

**Problema:** Flag `--group` non funziona come previsto

- Il flag `--group` analizza automaticamente le modifiche staged e può creare commit logici multipli
- L'LLM potrebbe decidere che un singolo commit ha senso per il tuo insieme di modifiche staged, anche con `--group`
- Questo è un comportamento intenzionale - l'LLM raggruppa le modifiche in base alle relazioni logiche, non solo alla quantità
- Assicurati di avere più modifiche non correlate in staging (es. correzione bug + aggiunta funzionalità) per ottenere i migliori risultati
- Usa `gac --show-prompt` per vedere cosa sta elaborando l'LLM

**Problema:** Commit raggruppati in modo errato o non raggruppati quando previsto

- Il raggruppamento è determinato dall'analisi dell'LLM delle tue modifiche
- L'LLM potrebbe creare un singolo commit se determina che le modifiche sono logicamente correlate
- Prova ad aggiungere suggerimenti con `-h "hint"` per guidare la logica di raggruppamento (es. `-h "separa la correzione bug dal refactoring"`)
- Rivedi i gruppi generati prima di confermare
- Se il raggruppamento non funziona bene per il tuo caso d'uso, fai commit delle modifiche separatamente

## 5. Sicurezza e rilevamento segreti

**Problema:** Falso positivo: la scansione dei segreti rileva non-segreti

- Lo scanner di sicurezza cerca pattern che assomigliano a chiavi API, token e password
- Se stai facendo commit di codice di esempio, fixture di test o documentazione con chiavi segnaposto, potresti vedere falsi positivi
- Usa `--skip-secret-scan` per ignorare la scansione se sei certo che le modifiche siano sicure
- Considera di escludere file di test/esempio dai commit, o usa segnaposto chiaramente contrassegnati

**Problema:** La scansione dei segreti non rileva segreti effettivi

- Lo scanner utilizza il pattern matching e potrebbe non individuare tutti i tipi di segreti
- Rivedi sempre le tue modifiche staged con `git diff --staged` prima di fare commit
- Considera l'uso di strumenti di sicurezza aggiuntivi come `git-secrets` o `gitleaks` per una protezione completa
- Segnala eventuali pattern mancati come issue per aiutare a migliorare il rilevamento

**Problema:** Necessità di disabilitare permanentemente la scansione dei segreti

- Imposta `GAC_SKIP_SECRET_SCAN=true` nel tuo file `.gac.env`
- Usa `gac config set GAC_SKIP_SECRET_SCAN true`
- Nota: disabilita solo se hai altre misure di sicurezza in atto

## 6. Problemi con hook pre-commit e lefthook

**Problema:** Gli hook pre-commit o lefthook falliscono e bloccano i commit

- Usa `gac --no-verify` per saltare temporaneamente tutti gli hook pre-commit e lefthook
- Risolvi i problemi sottostanti che causano il fallimento degli hook
- Considera di modificare la configurazione pre-commit o lefthook se gli hook sono troppo restrittivi

**Problema:** Gli hook pre-commit o lefthook richiedono troppo tempo o interferiscono con il flusso di lavoro

- Usa `gac --no-verify` per saltare temporaneamente tutti gli hook pre-commit e lefthook
- Considera di configurare gli hook pre-commit in `.pre-commit-config.yaml` o gli hook lefthook in `.lefthook.yml` per renderli meno aggressivi per il tuo flusso di lavoro
- Rivedi la configurazione degli hook per ottimizzare le prestazioni

## 7. Problemi comuni di flusso di lavoro

**Problema:** Nessuna modifica da sottoporre a commit / nulla in staging

- gac richiede modifiche staged per generare un messaggio di commit
- Usa `git add <file>` per mettere in staging le modifiche, o usa `gac -a` per mettere in staging tutte le modifiche automaticamente
- Controlla `git status` per vedere quali file sono stati modificati
- Usa `gac diff` per vedere una vista filtrata delle tue modifiche

**Problema:** Messaggio di commit non come previsto

- Usa il sistema di feedback interattivo: digita `r` per rigenerare, `e` per modificare (TUI in-place, o editor esterno tramite `GAC_EDITOR`), o fornisci feedback in linguaggio naturale
- Aggiungi contesto con `-h "il tuo suggerimento"` per guidare l'LLM
- Usa `-o` per messaggi più semplici su una riga o `-v` per messaggi più dettagliati
- Usa `--show-prompt` per vedere quali informazioni sta ricevendo l'LLM

**Problema:** gac è troppo lento

- Usa `gac -y` per saltare il prompt di conferma
- Usa `gac -q` per la modalità silenziosa con meno output
- Considera l'uso di modelli più veloci/economici per commit di routine
- Usa `gac --no-verify` per saltare gli hook se ti stanno rallentando

**Problema:** Impossibile modificare o fornire feedback dopo la generazione del messaggio

- Al prompt, digita `e` per entrare in modalità modifica (TUI in-place con keybindings vi/emacs; imposta `GAC_EDITOR` per usare il tuo editor preferito invece)
- Digita `r` per rigenerare senza feedback
- O semplicemente digita il tuo feedback direttamente (es. "rendilo più breve", "concentrati sulla correzione del bug")
- Premi Invio su input vuoto per vedere nuovamente il prompt

## 8. Debug generale

- Usa `gac init` per ripristinare o aggiornare la tua configurazione interattivamente
- Usa `gac --log-level=debug` per output di debug dettagliato e logging
- Usa `gac --show-prompt` per vedere quale prompt viene inviato all'LLM
- Usa `gac --help` per vedere tutti i flag della riga di comando disponibili
- Usa `gac config show` per vedere tutti i valori di configurazione correnti
- Controlla i log per messaggi di errore e tracce dello stack
- Consulta il [README.md](../README.md) principale per funzionalità, esempi e istruzioni di avvio rapido

## Ancora bloccato?

- Cerca tra le issue esistenti o aprine una nuova sul [repository GitHub](https://github.com/cellwebb/gac)
- Includi dettagli sul tuo sistema operativo, versione di Python, versione di gac, provider e output degli errori
- Più dettagli fornisci, più velocemente il tuo problema potrà essere risolto

## Dove ottenere ulteriore aiuto

- Per funzionalità ed esempi di utilizzo, consulta il [README.md](../README.md) principale
- Per prompt di sistema personalizzati, consulta [CUSTOM_SYSTEM_PROMPTS.md](CUSTOM_SYSTEM_PROMPTS.md)
- Per le linee guida di contribuzione, consulta [CONTRIBUTING.md](CONTRIBUTING.md)
- Per informazioni sulla licenza, consulta [../LICENSE](../LICENSE)
