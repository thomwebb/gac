<!-- markdownlint-disable MD013 -->
<!-- markdownlint-disable MD033 MD036 -->

<div align="center">

# 🚀 Git Auto Commit (`gac`)

[![PyPI version](https://img.shields.io/pypi/v/gac.svg)](https://pypi.org/project/gac/)
[![Changelog](https://img.shields.io/badge/changelog-kittylog-10b981)](https://kittylog.app/c/thomwebb/gac)
[![Python](https://img.shields.io/badge/python-3.10--3.14-blue.svg)](https://www.python.org/downloads/)
[![Build Status](https://github.com/cellwebb/gac/actions/workflows/ci.yml/badge.svg)](https://github.com/cellwebb/gac/actions)
[![codecov](https://codecov.io/gh/cellwebb/gac/branch/main/graph/badge.svg)](https://app.codecov.io/gh/cellwebb/gac)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![mypy](https://img.shields.io/badge/mypy-checked-blue.svg)](https://mypy-lang.org/)
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](docs/nl/CONTRIBUTING.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[English](../../README.md) | [简体中文](../zh-CN/README.md) | [繁體中文](../zh-TW/README.md) | [日本語](../ja/README.md) | [한국어](../ko/README.md) | [हिन्दी](../hi/README.md) | [Tiếng Việt](../vi/README.md) | [Français](../fr/README.md) | [Русский](../ru/README.md) | [Español](../es/README.md) | [Português](../pt/README.md) | [Norsk](../no/README.md) | [Svenska](../sv/README.md) | [Deutsch](../de/README.md) | **Nederlands** | [Italiano](../it/README.md)

**Met LLM-gedreven commitberichten die uw code begrijpen!**

**Automatiseer uw commits!** Vervang `git commit -m "..."` door `uvx gac` voor contextuele, goed geformateerde commitberichten die zijn gegenereerd door grote taalmodellen!

---

## Wat U Krijgt

Intelligente, contextuele berichten die het **waarom** achter uw wijzigingen uitleggen:

![GAC generating a contextual commit message](../../assets/gac-simple-usage.nl.png)

---

</div>

<!-- markdownlint-enable MD033 MD036 -->

## Snel Starten

```bash
uvx gac init   # Configureer uw provider, model en taal
uvx gac        # Genereer en commit met LLM
```

Dat is alles! Beoordeel het gegenereerde bericht en bevestig met `y`.

---

## Belangrijkste Functies

### 🌐 **29+ Ondersteunde Providers**

- **Anthropic** • **Azure OpenAI** • **Cerebras** • **ChatGPT (OAuth)** • **Chutes.ai**
- **Claude Code (OAuth)** • **Crof.ai** • **DeepSeek** • **Fireworks** • **Gemini** • **GitHub Copilot (OAuth)**
- **Groq** • **Kimi for Coding** • **LM Studio** • **MiniMax.io** • **Mistral AI** • **Moonshot AI**
- **Neuralwatt** • **Ollama** • **OpenAI** • **OpenCode Go** • **OpenRouter** • **Qwen Cloud (CN & INTL)**
- **Replicate** • **Streamlake/Vanchin** • **Synthetic.new** • **Together AI** • **Wafer.ai**
- **Z.AI (API & Coding Plans)** • **Custom Endpoints (Anthropic/OpenAI)**

### 🧠 **Slimme LLM-analyse**

- **Begrijpt intentie**: Analyseert codestructuur, logica en patronen om het "waarom" achter uw wijzigingen te begrijpen, niet alleen wat er is veranderd
- **Semantisch bewustzijn**: Herkent refactoring, bugfixes, features en breaking changes om contextueel passende berichten te genereren
- **Intelligente filtering**: Prioriteert betekenisvolle wijzigingen en negeert gegenereerde bestanden, dependencies en artefacten
- **Intelligente commit-groepering** - Groepeer automatisch gerelateerde wijzigingen in meerdere logische commits met `--group`

### 📝 **Meerdere Berichtformaten**

- **One-liner** (-o vlag): Eénregelig commitbericht in conventioneel commitformaat
- **Standaard** (standaard): Samenvatting met bullet points die implementatiedetails uitleggen
- **Uitgebreid** (-v vlag): Uitgebreide uitleg inclusief motivatie, technische aanpak en impactanalyse
- **50/72 regel** (--50-72 vlag): Forceer het klassieke commit-berichtformaat voor optimale leesbaarheid in git log en GitHub UI
- **DCO/Signoff** (--signoff vlag): Voeg Signed-off-by regel toe voor Developer Certificate of Origin naleving (vereist door Cherry Studio, Linux kernel en andere projecten)

### 🌍 **Meertalige Ondersteuning**

- **25+ talen**: Genereer commitberichten in Engels, Chinees, Japans, Koreaans, Spaans, Frans, Duits en 18+ andere talen
- **Flexibele vertaling**: Kies ervoor om conventionele commit-prefixen in het Engels te houden voor tool-compatibiliteit, of vertaal ze volledig
- **Meerdere workflows**: Stel een standaardtaal in met `uvx gac language`, of gebruik de `-l <taal>` vlag voor eenmalige overschrijvingen
- **Ondersteuning voor native scripts**: Volledige ondersteuning voor niet-Latijnse scripts inclusief CJK, Cyrillisch, Thai en meer

### 💻 **Ontwikkelervaring**

- **Interactieve feedback**: Typ `r` om opnieuw te rollen, `e` om te bewerken (standaard in-place TUI, of `$GAC_EDITOR` indien ingesteld), of typ direct uw feedback zoals `maak het korter` of `focus op de bugfix`
- **Interactieve ondervraging**: Gebruik `--interactive` (`-i`) om gerichte vragen over uw wijzigingen te beantwoorden voor meer contextuele commitberichten
- **Één-commando workflows**: Volledige workflows met vlaggen zoals `uvx gac -ayp` (stage alles, auto-bevestig, push)
- **Git-integratie**: Respecteert pre-commit en lefthook hooks en voert ze uit vóór dure LLM-operaties
- **MCP-server**: Voer `uvx gac serve` uit om commit-tools beschikbaar te stellen aan AI-agents via het [Model Context Protocol](https://modelcontextprotocol.io/)

### 📊 **Gebruiksstatistieken**

```bash
uvx gac stats               # Overzicht: totale gacs, streaks, dagelijkse/wekelijkse pieken, topprojecten & -modellen
uvx gac stats models        # Per model: gacs, tokens, latentie, snelheid
uvx gac stats projects      # Per project: gacs, commits, tokens over alle repo's
uvx gac stats reset         # Alle statistieken resetten (vraagt om bevestiging)
uvx gac stats reset model <model-id>  # Alleen statistieken van een specifiek model resetten
```

- **Volg uw gacs**: Zie hoeveel commits u met gac heeft gedaan, uw huidige streak, piekdagelijkse/wekelijkse activiteit en topprojecten
- **Token-tracking**: Totaal aan prompt-, output- en reasoning-tokens per dag, week, project en model — met highscore-trofeeën voor tokengebruik
- **Topmodellen**: Zie welke modellen u het meest gebruikt en hoeveel tokens elk model verbruikt
- **Highscore-vieringen**: 🏆 trofeeën wanneer u nieuwe dagelijkse, wekelijkse, token- of streak-records vestigt; 🥈 voor het evenaren ervan
- **Opt-in tijdens setup**: `uvx gac init` vraagt of u statistieken wilt inschakelen en legt uit wat er wordt opgeslagen
- **Altijd opt-out**: Stel `GAC_DISABLE_STATS=true` (of `1`/`yes`/`on`) in om uit te schakelen. Instellen op `false`/`0`/`no` (of verwijderen) houdt statistieken ingeschakeld
- **Privacy eerst**: Lokaal opgeslagen in `~/.gac_stats.json`. Alleen tellingen, datums, projectnamen en modelnamen — geen commitberichten, code of persoonlijke gegevens. Geen telemetrie

### 🛡️ **Ingebouwde Beveiliging**

- **Automatische secret-detectie**: Scant op API-sleutels, wachtwoorden en tokens voor het committen
- **Interactieve bescherming**: Vraagt voor het committen van mogelijk gevoelige gegevens met duidelijke herstelopties
- **Slimme filtering**: Negeert voorbeeldbestanden, sjabloonbestanden en plaatshoudertekst om false positives te verminderen

---

## Gebruiksvoorbeelden

### Basisworkflow

```bash
# Stage uw wijzigingen
git add .

# Genereer en commit met LLM
uvx gac

# Beoordeel → y (commit) | n (annuleer) | r (opnieuw rollen) | e (bewerken) | of typ feedback
```

### Veelgebruikte Commando's

| Commando            | Beschrijving                                                         |
| ------------------- | -------------------------------------------------------------------- |
| `uvx gac`           | Genereer commitbericht                                               |
| `uvx gac -y`        | Auto-bevestig (geen beoordeling nodig)                               |
| `uvx gac -a`        | Stage alles voordat u commitbericht genereert                        |
| `uvx gac -S`        | Interactief bestanden selecteren om te stagen                        |
| `uvx gac -o`        | Eénregelig bericht voor triviale wijzigingen                         |
| `uvx gac -v`        | Uitgebreid formaat met Motivatie, Technische Aanpak en Impactanalyse |
| `uvx gac -h "hint"` | Voeg context toe voor LLM (bv., `uvx gac -h "bug fix"`)              |
| `uvx gac -s`        | Inclusief scope (bv., feat(auth):)                                   |
| `uvx gac -i`        | Stel vragen over wijzigingen voor betere context                     |
| `uvx gac -g`        | Wijzigingen groeperen in meerdere logische commits                   |
| `uvx gac -p`        | Commit en push                                                       |
| `uvx gac stats`     | Uw gac-gebruiksstatistieken bekijken                                 |

### Power User Voorbeelden

```bash
# Volledige workflow in één commando
# Uw commitstatistieken bekijken
uvx gac stats

# Statistieken van alle projecten
uvx gac stats projects

uvx gac -ayp -h "release preparation"

# Gedetailleerde uitleg met scope
uvx gac -v -s

# Snelle one-liner voor kleine wijzigingen
uvx gac -o

# Genereer commitbericht in een specifieke taal
uvx gac -l nl

# Groepeer wijzigingen in logisch gerelateerde commits
uvx gac -ag

# Interactieve modus met gedetailleerde output voor gedetailleerde uitleg
uvx gac -iv

# Debug wat de LLM ziet
uvx gac --show-prompt

# Sla security scan over (gebruik voorzichtig)
uvx gac --skip-secret-scan

# Signoff toevoegen voor DCO naleving (Cherry Studio, Linux kernel, etc.)
uvx gac --signoff
```

### Interactief Feedbacksysteem

Niet tevreden met het resultaat? U heeft mehrere opties:

```bash
# Eenvoudige reroll (geen feedback)
r

# Bewerk het commitbericht
e
# Standaard: in-place TUI met vi/emacs-keybindings
# Druk op Esc+Enter of Ctrl+S om in te dienen, Ctrl+C om te annuleren

# Stel GAC_EDITOR in om uw voorkeurseditor te openen:
# GAC_EDITOR=code gac → opent VS Code (--wait automatisch toegepast)
# GAC_EDITOR=vim gac → opent vim
# GAC_EDITOR=nano gac → opent nano

# Of typ gewoon uw feedback direct!
maak het korter en focus op de prestatieverbetering
gebruik conventioneel commitformaat met scope
leg de security-implicaties uit

# Druk op Enter op lege invoer om de prompt opnieuw te zien
```

De bewerkfunctie (`e`) laat u het commitbericht verfijnen:

- **Standaard (in-place TUI)**: Meerregelige bewerking met vi/emacs-keybindings — typefouten corrigeren, formulering aanpassen, herstructureren
- **Met `GAC_EDITOR`**: Opent uw voorkeurseditor (`code`, `vim`, `nano`, enz.) — volledige editorfuncties inclusief zoeken/vervangen, macro's, enz.

GUI-editors zoals VS Code worden automatisch afgehandeld: gac voegt `--wait` in zodat het proces blokkeert tot u het editortabblad sluit. Geen extra configuratie nodig.

---

## Configuratie

Voer `uvx gac init` uit om uw provider interactief te configureren, of stel omgevingsvariabelen in:

Wilt u later providers of modellen wijzigen zonder taalinstellingen aan te passen? Gebruik `uvx gac model` voor een gestroomlijnde workflow die de taalprompts overslaat.

```bash
# Voorbeeldconfiguratie
GAC_MODEL=anthropic:your-model-name
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

Zie `.gac.env.example` voor alle beschikbare opties.

**Wilt u commitberichten in een andere taal?** Voer `uvx gac language` uit om te kiezen uit 25+ talen inclusief Español, Français, 日本語 en meer.

**Wilt u de stijl van commitberichten aanpassen?** Zie [docs/CUSTOM_SYSTEM_PROMPTS.md](docs/nl/CUSTOM_SYSTEM_PROMPTS.md) voor begeleiding bij het schrijven van aangepaste systeemprompts.

---

## Hulp Krijgen

- **Volledige documentatie**: [docs/USAGE.md](docs/nl/USAGE.md) - Volledige CLI-referentie
- **MCP-server**: [docs/MCP.md](MCP.md) - Gebruik GAC als MCP-server voor AI-agents
- **Claude Code OAuth**: [docs/CLAUDE_CODE.md](docs/nl/CLAUDE_CODE.md) - Claude Code installatie en authenticatie
- **ChatGPT OAuth**: [docs/CHATGPT_OAUTH.md](docs/nl/CHATGPT_OAUTH.md) - ChatGPT OAuth installatie en authenticatie
- **Aangepaste prompts**: [docs/CUSTOM_SYSTEM_PROMPTS.md](docs/nl/CUSTOM_SYSTEM_PROMPTS.md) - Pas stijl van commitberichten aan
- **Gebruiksstatistieken**: Zie `uvx gac stats --help` of de [volledige docs](docs/nl/USAGE.md#gebruiksstatistieken)
- **Probleemoplossing**: [docs/TROUBLESHOOTING.md](docs/nl/TROUBLESHOOTING.md) - Veelvoorkomende problemen en oplossingen
- **Bijdragen**: [docs/CONTRIBUTING.md](docs/nl/CONTRIBUTING.md) - Ontwikkelsetup en richtlijnen

---

<!-- markdownlint-disable MD033 MD036 -->

<div align="center">

[⭐ Star ons op GitHub](https://github.com/cellwebb/gac) • [🐛 Rapporteer problemen](https://github.com/cellwebb/gac/issues) • [📖 Volledige docs](docs/nl/USAGE.md)

</div>

<!-- markdownlint-enable MD033 MD036 -->
