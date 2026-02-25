# Wartung von Berechnungsvorschriften

## Übersicht

Die Wartung von Berechnungsvorschriften erfolgt im Webbrowser in der Anwendung **IAK Farmaxis**. Dieser Abschnitt beschreibt die Abläufe und Prozesse aus Benutzersicht.

## Erzeugung

Berechnungsvorschriften entstehen aus Excel-Zellendaten:

1. **Eingabe:** Tabellenidentifikator, Tabellenblatt, Zellenidentifikator, Beschreibung, Formel
2. **Verarbeitung:** Pseudocode-Umwandlung (Excel-Syntax → menschenlesbar), Variablen-Verlinkung
3. **Ausgabe:** Strukturierte Berechnungsvorschrift mit Name, Formel, Variablen, Metadaten

![Erzeugungsablauf](diagramme/erzeugung_ablauf.png)

## Pflege im Webbrowser (IAK Farmaxis)

In IAK Farmaxis können Berechnungsvorschriften:

- **angezeigt** werden (Details, Abhängigkeiten)
- **bearbeitet** werden (Formel, Metadaten)
- **gesucht** werden (über Metadaten: Name, Kategorie, Symbol, Datentyp, Einheit)

## Workflows

| Workflow | Beschreibung |
|----------|--------------|
| **Neuanlage** | Excel-Zellendaten eingeben → Berechnungsvorschrift wird erzeugt |
| **Bearbeitung** | BV öffnen → Änderungen vornehmen → Speichern (erzeugt neue Version) |
| **Historie anzeigen** | Versionsverlauf einer BV einsehen |
| **Variablen-Verlinkung ändern** | Verlinkung aufheben (Variable wird primitiv) oder manuell verlinken (bei mehreren Treffern) |

## Benutzeraktionen

![Wartungs-Workflow](diagramme/wartung_workflow.png)

*Für die vollständige Darstellung: `./diagramme/render.sh` ausführen (Graphviz erforderlich).*

## Rollen (konzeptionell)

Die Frage „Wer darf was?“ sollte organisationsspezifisch geklärt werden:

- Wer darf neue Berechnungsvorschriften anlegen?
- Wer darf bestehende bearbeiten?
- Wer darf Verlinkungen ändern?
- Wer darf die Historie einsehen?

Diese Rollen sind fachlich zu definieren und in der Anwendung abzubilden.
