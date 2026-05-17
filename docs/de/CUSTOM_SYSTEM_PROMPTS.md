# Benutzerdefinierte System-Prompts

[English](../en/CUSTOM_SYSTEM_PROMPTS.md) | [简体中文](../zh-CN/CUSTOM_SYSTEM_PROMPTS.md) | [繁體中文](../zh-TW/CUSTOM_SYSTEM_PROMPTS.md) | [日本語](../ja/CUSTOM_SYSTEM_PROMPTS.md) | [한국어](../ko/CUSTOM_SYSTEM_PROMPTS.md) | [हिन्दी](../hi/CUSTOM_SYSTEM_PROMPTS.md) | [Tiếng Việt](../vi/CUSTOM_SYSTEM_PROMPTS.md) | [Français](../fr/CUSTOM_SYSTEM_PROMPTS.md) | [Рус../](../ru/CUSTOM_SYSTEM_PROMPTS.md) | [Español](../es/CUSTOM_SYSTEM_PROMPTS.md) | [Português](../pt/CUSTOM_SYSTEM_PROMPTS.md) | [Norsk](../no/CUSTOM_SYSTEM_PROMPTS.md) | [Svenska](../sv/CUSTOM_SYSTEM_PROMPTS.md) | **Deutsch** | [Nederlands](../nl/CUSTOM_SYSTEM_PROMPTS.md) | [Italiano](../it/CUSTOM_SYSTEM_PROMPTS.md)

Dieser Leitfaden erklärt, wie Sie den System-Prompt, den GAC zur Generierung von Commit-Nachrichten verwendet, anpassen können, sodass Sie Ihren eigenen Commit-Nachrichten-Stil und Ihre eigenen Konventionen definieren können.

## Inhaltsverzeichnis

- [Benutzerdefinierte System-Prompts](#benutzerdefinierte-system-prompts)
  - [Inhaltsverzeichnis](#inhaltsverzeichnis)
  - [Was sind System-Prompts?](#was-sind-system-prompts)
  - [Warum benutzerdefinierte System-Prompts verwenden?](#warum-benutzerdefinierte-system-prompts-verwenden)
  - [Schnellstart](#schnellstart)
  - [Ihren benutzerdefinierten System-Prompt schreiben](#ihren-benutzerdefinierten-system-prompt-schreiben)
  - [Beispiele](#beispiele)
    - [Emoji-basierter Commit-Stil](#emoji-basierter-commit-stil)
    - [Team-spezifische Konventionen](#team-spezifische-konventionen)
    - [Detaillierter technischer Stil](#detaillierter-technischer-stil)
  - [Best Practices](#best-practices)
    - [Do:](#do)
    - [Don't:](#dont)
    - [Tips:](#tips)
  - [Fehlerbehebung](#fehlerbehebung)
    - [Nachrichten haben immer noch "chore:"-Präfix](#nachrichten-haben-immer-noch-chore-präfix)
    - [KI ignoriert meine Anweisungen](#ki-ignoriert-meine-anweisungen)
    - [Nachrichten sind zu lang/kurz](#nachrichten-sind-zu-langkurz)
    - [Benutzerdefinierter Prompt wird nicht verwendet](#benutzerdefinierter-prompt-wird-nicht-verwendet)
    - [Zurück zum Standard wechseln möchten](#zurück-zum-standard-wechseln-möchten)
  - [Verwandte Dokumentation](#verwandte-dokumentation)
  - [Hilfe benötigt?](#hilfe-benötigt)

## Was sind System-Prompts?

GAC verwendet zwei Prompts bei der Generierung von Commit-Nachrichten:

1. **System-Prompt** (anpassbar): Anweisungen, die die Rolle, den Stil und die Konventionen für Commit-Nachrichten definieren
2. **Benutzer-Prompt** (automatisch): Die Git-Diff-Daten, die zeigen, was geändert wurde

Der System-Prompt sagt der KI, _wie_ Commit-Nachrichten geschrieben werden sollen, während der Benutzer-Prompt das _was_ liefert (die tatsächlichen Code-Änderungen).

## Warum benutzerdefinierte System-Prompts verwenden?

Sie möchten möglicherweise einen benutzerdefinierten System-Prompt, wenn:

- Ihr Team einen anderen Commit-Nachrichten-Stil als konventionelle Commits verwendet
- Sie Emojis, Präfixe oder andere benutzerdefinierte Formate bevorzugen
- Sie mehr oder weniger Details in Commit-Nachrichten möchten
- Sie unternehmensspezifische Richtlinien oder Vorlagen haben
- Sie die Stimme und den Ton Ihres Teams angleichen möchten
- Sie Commit-Nachrichten in einer anderen Sprache möchten (siehe Sprachkonfiguration unten)

## Schnellstart

1. **Erstellen Sie Ihre benutzerdefinierte System-Prompt-Datei:**

   ```bash
   # Kopieren Sie das Beispiel als Ausgangspunkt
   cp custom_system_prompt.example.txt ~/.config/gac/my_system_prompt.txt

   # Oder erstellen Sie Ihre eigene von Grund auf
   vim ~/.config/gac/my_system_prompt.txt
   ```

2. **Fügen Sie zu Ihrer `.gac.env`-Datei hinzu:**

   ```bash
   # In ~/.gac.env oder projekt-weitem .gac.env
   GAC_SYSTEM_PROMPT_PATH=/path/to/your/custom_system_prompt.txt
   ```

3. **Testen Sie es:**

   ```bash
   uvx gac --dry-run
   ```

Das ist alles! GAC wird jetzt Ihre benutzerdefinierten Anweisungen anstelle des Standards verwenden.

## Ihren benutzerdefinierten System-Prompt schreiben

Ihr benutzerdefinierter System-Prompt kann Klartext sein - keine speziellen Formate oder XML-Tags erforderlich. Schreiben Sie einfach klare Anweisungen, wie die KI Commit-Nachrichten generieren sollte.

**Wichtige Dinge, die einbezogen werden sollten:**

1. **Rollendefinition** - Was die KI sein sollte
2. **Formatanforderungen** - Struktur, Länge, Stil
3. **Beispiele** - Zeigen, wie gute Commit-Nachrichten aussehen
4. **Einschränkungen** - Was vermieden werden soll oder Anforderungen, die erfüllt werden müssen

**Beispielstruktur:**

```text
Sie sind ein Commit-Nachrichten-Schreiber für [Ihr Projekt/Team].

Bei der Analyse von Code-Änderungen erstellen Sie eine Commit-Nachricht, die:

1. [Erste Anforderung]
2. [Zweite Anforderung]
3. [Dritte Anforderung]

Beispielformat:
[Zeigen Sie eine Beispiel-Commit-Nachricht]

Ihre gesamte Antwort wird direkt als Commit-Nachricht verwendet.
```

## Beispiele

### Emoji-basierter Commit-Stil

Siehe [`custom_system_prompt.example.txt`](../../examples/custom_system_prompt.example.txt) für ein vollständiges Emoji-basiertes Beispiel.

**Schneller Ausschnitt:**

```text
Sie sind ein Commit-Nachrichten-Schreiber, der Emojis und einen freundlichen Ton verwendet.

Beginnen Sie jede Nachricht mit einem Emoji:
- 🎉 für neue Funktionen
- 🐛 für Fehlerbehebungen
- 📝 für Dokumentation
- ♻️ für Refactoring

Halten Sie die erste Zeile unter 72 Zeichen und erklären Sie, WARUM die Änderung wichtig ist.
```

### Team-spezifische Konventionen

```text
Sie schreiben Commit-Nachrichten für eine Unternehmens-Banking-Anwendung.

Anforderungen:
1. Beginnen Sie mit einer JIRA-Ticket-Nummer in Klammern (z.B. [BANK-1234])
2. Verwenden Sie einen formalen, professionellen Ton
3. Fügen Sie Sicherheitsauswirkungen hinzu, falls relevant
4. Verweisen Sie auf Compliance-Anforderungen (PCI-DSS, SOC2, etc.)
5. Halten Sie Nachrichten prägnant aber vollständig

Format:
[TICKET-123] Kurze Zusammenfassung der Änderung

Detaillierte Erklärung dessen, was geändert wurde und warum. Fügen Sie hinzu:
- Geschäftliche Begründung
- Technischer Ansatz
- Risikobewertung (falls zutreffend)

Beispiel:
[BANK-1234] Rate Limiting für Login-Endpunkte implementieren

Redis-basiertes Rate Limiting hinzugefügt, um Brute-Force-Angriffe zu verhindern.
Begrenzt Login-Versuche auf 5 pro IP pro 15 Minuten.
Erfüllt SOC2-Sicherheitsanforderungen für Zugriffskontrolle.
```

### Detaillierter technischer Stil

```text
Sie sind ein technischer Commit-Nachrichten-Schreiber, der umfassende Dokumentation erstellt.

Für jeden Commit liefern Sie:

1. Einen klaren, beschreibenden Titel (unter 72 Zeichen)
2. Eine leere Zeile
3. WAS: Was geändert wurde (2-3 Sätze)
4. WARUM: Warum die Änderung notwendig war (2-3 Sätze)
5. WIE: Technischer Ansatz oder wichtige Implementierungsdetails
6. AUSWIRKUNG: Betroffene Dateien/Komponenten und mögliche Nebenwirkungen

Verwenden Sie technische Präzision. Verweisen Sie auf spezifische Funktionen, Klassen und Module.
Verwenden Sie Präsens und aktive Stimme.

Beispiel:
Authentifizierungs-Middleware zu Verwendung von Dependency Injection refaktorisiert

WAS: Globalen Auth-Zustand durch injizierbaren AuthService ersetzt. Alle
Route-Handler aktualisiert, um authService durch Konstruktor-Injection zu akzeptieren.

WARUM: Globaler Zustand erschwerte Tests und schuf versteckte Abhängigkeiten.
Dependency Injection verbessert Testbarkeit und macht Abhängigkeiten explizit.

WIE: AuthService-Schnittstelle erstellt, JWTAuthService und
MockAuthService implementiert. Route-Handler-Konstruktoren geändert, um AuthService zu erfordern.
Dependency-Injection-Container-Konfiguration aktualisiert.

AUSWIRKUNG: Betrifft alle authentifizierten Routen. Keine Verhaltensänderungen für Benutzer.
Tests laufen jetzt 3x schneller mit MockAuthService. Migration erforderlich für
routes/auth.ts, routes/api.ts und routes/admin.ts.
```

## Best Practices

### Do

- ✅ **Seien Sie spezifisch** - Klare Anweisungen erzeugen bessere Ergebnisse
- ✅ **Fügen Sie Beispiele hinzu** - Zeigen Sie der KI, wie gut aussieht
- ✅ **Testen Sie iterativ** - Probieren Sie Ihren Prompt, verfeinern Sie basierend auf Ergebnissen
- ✅ **Halten Sie ihn fokussiert** - Zu viele Regeln können die KI verwirren
- ✅ **Verwenden Sie konsistente Terminologie** - Bleiben Sie bei denselben Begriffen im gesamten Text
- ✅ **Beenden Sie mit einer Erinnerung** - Verstärken Sie, dass die Antwort wie verwendet wird

### Don't

- ❌ **Verwenden Sie XML-Tags** - Klartext funktioniert am besten (es sei denn, Sie wollen speziell diese Struktur)
- ❌ **Machen Sie ihn zu lang** - Zielen Sie auf 200-500 Wörter an Anweisungen
- ❌ **Widersprechen Sie sich selbst** - Seien Sie konsistent in Ihren Anforderungen
- ❌ **Vergessen Sie das Ende** - Erinnern Sie immer: "Ihre gesamte Antwort wird direkt als Commit-Nachricht verwendet"

### Tips

- **Beginnen Sie mit dem Beispiel** - Kopieren Sie `../../examples/custom_system_prompt.example.txt` und modifizieren Sie es
- **Testen Sie mit `--dry-run`** - Sehen Sie das Ergebnis, ohne einen Commit zu machen
- **Verwenden Sie `--show-prompt`** - Sehen Sie, was an die KI gesendet wird
- **Iterieren Sie basierend auf Ergebnissen** - Wenn Nachrichten nicht ganz richtig sind, passen Sie Ihre Anweisungen an
- **Versionskontrolle Ihres Prompts** - Behalten Sie Ihren benutzerdefinierten Prompt im Repository Ihres Teams
- **Projekt-spezifische Prompts** - Verwenden Sie projekt-weites `.gac.env` für projekt-spezifische Stile

## Fehlerbehebung

### Nachrichten haben immer noch "chore:"-Präfix

**Problem:** Ihre benutzerdefinierten Emoji-Nachrichten erhalten "chore:" hinzu.

**Lösung:** Das sollte nicht passieren - GAC deaktiviert automatisch die Durchsetzung konventioneller Commits bei Verwendung benutzerdefinierter System-Prompts. Wenn Sie dies sehen, please [file an issue](https://github.com/cellwebb/gac/issues).

### KI ignoriert meine Anweisungen

**Problem:** Generierte Nachrichten folgen nicht Ihrem benutzerdefinierten Format.

**Lösung:**

1. Machen Sie Ihre Anweisungen expliziter und spezifischer
2. Fügen Sie klare Beispiele des gewünschten Formats hinzu
3. Beenden Sie mit: "Ihre gesamte Antwort wird direkt als Commit-Nachricht verwendet"
4. Reduzieren Sie die Anzahl der Anforderungen - zu viele können die KI verwirren
5. Versuchen Sie, ein anderes Modell zu verwenden (einige folgen Anweisungen besser als andere)

### Nachrichten sind zu lang/kurz

**Problem:** Generierte Nachrichten entsprechen nicht Ihren Längenanforderungen.

**Lösung:**

- Seien Sie explizit über die Länge (z.B. "Halten Sie Nachrichten unter 50 Zeichen")
- Zeigen Sie Beispiele der exakten Länge, die Sie möchten
- Erwägen Sie die Verwendung des `--one-liner`-Flags ebenfalls für kurze Nachrichten

### Benutzerdefinierter Prompt wird nicht verwendet

**Problem:** GAC verwendet weiterhin das Standard-Commit-Format.

**Lösung:**

1. Überprüfen Sie, dass `GAC_SYSTEM_PROMPT_PATH` korrekt gesetzt ist:

   ```bash
   uvx gac config get GAC_SYSTEM_PROMPT_PATH
   ```

2. Überprüfen Sie, dass der Dateipfad existiert und lesbar ist:

   ```bash
   cat "$GAC_SYSTEM_PROMPT_PATH"
   ```

3. Überprüfen Sie `.gac.env`-Dateien in dieser Reihenfolge:
   - Projekt-Ebene: `./.gac.env`
   - Benutzerebene: `~/.gac.env`
4. Versuchen Sie einen absoluten Pfad anstelle eines relativen Pfads

### Sprachkonfiguration

**Hinweis:** Sie benötigen keinen benutzerdefinierten System-Prompt, um die Sprache der Commit-Nachrichten zu ändern!

Wenn Sie nur die Sprache Ihrer Commit-Nachrichten ändern möchten (während Sie das Standard-konventionelle Commit-Format beibehalten), verwenden Sie den interaktiven Sprachwähler:

```bash
uvx gac language
```

Dies präsentiert ein interaktives Menü mit 25+ Sprachen in ihren nativen Schriften (Español, Français, 日本語, etc.). Wählen Sie Ihre bevorzugte Sprache, und sie wird automatisch `GAC_LANGUAGE` in Ihrer `~/.gac.env`-Datei setzen.

Alternativ können Sie die Sprache manuell setzen:

```bash
# In ~/.gac.env oder projekt-weitem .gac.env
GAC_LANGUAGE=Spanish
```

Standardmäßig bleiben konventionelle Commit-Präfixe (feat:, fix:, etc.) aus Kompatibilität mit Changelog-Tools und CI/CD-Pipelines auf Englisch, während aller andere Text in Ihrer angegebenen Sprache ist.

**Präfixe auchübersetzen möchten?** Setzen Sie `GAC_TRANSLATE_PREFIXES=true` in Ihrer `.gac.env` für vollständige Lokalisierung:

```bash
GAC_LANGUAGE=Spanish
GAC_TRANSLATE_PREFIXES=true
```

Dies wird alles übersetzen, einschließlich Präfixe (z.B. `corrección:` anstelle von `fix:`).

Dies ist einfacher als das Erstellen eines benutzerdefinierten System-Prompts, wenn Sprache Ihr einziger Anpassungsbedarf ist.

### Zurück zum Standard wechseln möchten

**Problem:** Möchten vorübergehend Standard-Prompts verwenden.

**Lösung:**

```bash
# Option 1: Die Umgebungsvariable aufheben
uvx gac config unset GAC_SYSTEM_PROMPT_PATH

# Option 2: In .gac.env auskommentieren
# GAC_SYSTEM_PROMPT_PATH=/path/to/custom_prompt.txt

# Option 3: Verwenden Sie ein anderes .gac.env für spezifische Projekte
```

---

## Verwandte Dokumentation

- [USAGE.md](USAGE.md) - Kommandozeilen-Flags und Optionen
- [README.md](../../README.md) - Installation und grundlegende Einrichtung
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Allgemeine Fehlerbehebung

## Hilfe benötigt?

- Probleme melden: [GitHub Issues](https://github.com/cellwebb/gac/issues)
- Ihre benutzerdefinierten Prompts teilen: Beiträge willkommen!
