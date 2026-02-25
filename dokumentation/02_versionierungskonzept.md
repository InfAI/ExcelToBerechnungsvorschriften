# Versionierungskonzept

## Übersicht

Die Versionierung von Berechnungsvorschriften ermöglicht Nachvollziehbarkeit und Rückverfolgbarkeit von Änderungen. Die folgenden Optionen beschreiben unterschiedliche fachliche Strategien – ohne technische Umsetzungsdetails.

## Option A: Vollständige Historie

- **Prinzip:** Alle Versionen bleiben erhalten. Jede Änderung erzeugt eine neue Version.
- **Vorteil:** Vollständige Nachvollziehbarkeit, Wiederherstellung alter Versionen möglich.
- **Nachteil:** Höherer Speicherbedarf, Historie muss gepflegt und abgefragt werden können.

## Option B: Nur aktuelle Version

- **Prinzip:** Versionsnummer zur Nachverfolgung, alte Versionen werden bei Speicherung überschrieben.
- **Vorteil:** Einfach, geringer Speicherbedarf.
- **Nachteil:** Keine Wiederherstellung alter Versionen, nur aktuelle Version verfügbar.

## Option C: Zeitstempel-basierte Versionierung

- **Prinzip:** Zusätzlich zur Versionsnummer wird der Änderungszeitpunkt (`geaendert_am`) als Versionierungs-Key genutzt.
- **Vorteil:** Audit-Trail, zeitliche Zuordnung von Änderungen.
- **Anwendung:** Kann mit Option A oder B kombiniert werden.

## Was wird versioniert?

Die **gesamte Berechnungsvorschrift** wird versioniert – inklusive:

- Name, Formel, Variablen
- Metadaten (Kategorie, Symbol, Datentyp, Einheit)
- Quelle-Information
- Verlinkungen zu anderen Berechnungsvorschriften

## Lebenszyklus

Der typische Lebenszyklus einer Berechnungsvorschrift:

![Versionierungs-Workflow](diagramme/versionierung_workflow.png)

*Für die vollständige Darstellung: `./diagramme/render.sh` ausführen (Graphviz erforderlich).*
