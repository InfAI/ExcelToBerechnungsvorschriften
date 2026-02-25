# Dokumentation: Versionierung und Wartung von Berechnungsvorschriften

## Übersicht

Diese Dokumentation beschreibt **fachlich und konzeptionell**, wie Berechnungsvorschriften versioniert und gewartet werden können. Sie ist eigenständig und verzichtet bewusst auf technische Aspekte wie Datenhaltung oder Implementierungsdetails.

**Zielgruppe:** Fachverantwortliche, die Berechnungsvorschriften in der Anwendung IAK Farmaxis im Webbrowser pflegen – mit Fokus auf Wartbarkeit für Nichtinformatiker.

## Inhaltsverzeichnis

| Kapitel | Inhalt |
|---------|--------|
| [01 Definition](01_definition.md) | Was ist eine Berechnungsvorschrift? Struktur, Variablen, Abhängigkeiten |
| [02 Versionierungskonzept](02_versionierungskonzept.md) | Versionierungsstrategien und Optionen (fachlich) |
| [03 Wartung](03_wartung.md) | Wartungsabläufe, Workflows, Pflege im Webbrowser |
| [04 Formel-Wartbarkeit](04_formel_wartbarkeit.md) | Pseudocode-Regeln, Unterstützung für Nichtinformatiker |
| [05 Zusammenführung](05_zusammenfuehrung.md) | Konzept zum Zusammenführen mehrerer BVs, potenzielle Probleme |

## Diagramme

Die Flussdiagramme liegen als Graphviz-DOT-Dateien in `diagramme/` vor und können bei Bedarf neu gerendert werden:

```bash
./diagramme/render.sh
```

Oder manuell:

```bash
cd diagramme && for f in *.dot; do dot -Tpng "$f" -o "${f%.dot}.png"; done
```

Voraussetzung: [Graphviz](https://graphviz.org/) muss installiert sein.
