# Warum nicht alle Excel-Formeln in Berechnungsvorschriften überführen?

## Einleitung und Kontext

**ExcelToBerechnungsvorschriften** erzeugt aus Excel-Zellen strukturierte Berechnungsvorschriften (BVs). Technisch wäre es möglich, jede Formel-Zelle 1:1 in eine Berechnungsvorschrift zu überführen – doch eine vollständige Überführung ist **nicht sinnvoll**.

Die 1:1-Abbildung (eine Zelle = eine BV) führt zu vielen, stark verlinkten Berechnungsvorschriften. Siehe [01 Definition](01_definition.md) und [05 Zusammenführung](05_zusammenfuehrung.md). Die folgende Argumentation begründet, warum eine **selektive Überführung** fachlich relevanter Berechnungen der bessere Ansatz ist.

---

## Argument a) Komplexität des Baums

### Kern

Der entstehende Baum an Berechnungsvorschriften ist **zu komplex**, um ihn manuell zu warten oder zu verstehen.

### Ausarbeitung


| Aspekt                     | Beschreibung                                                                                                                                                                             |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Skalierung**             | Excel-Dateien mit hunderten Zellen erzeugen hunderte BVs. Beispiel: 200 Zellen → 200 Berechnungsvorschriften (vgl. [05 Zusammenführung](05_zusammenfuehrung.md)).                        |
| **Abhängigkeitsgraph**     | Der Graph wird unübersichtlich. Die Navigation über „verwendet folgende Berechnungsvorschriften“ und „wird verwendet in“ skaliert schlecht bei vielen BVs.                               |
| **Zielgruppe**             | Fachverantwortliche ohne Programmierkenntnisse sollen BVs pflegen – mit Fokus auf Wartbarkeit für Nichtinformatiker (vgl. [04 Formel-Wartbarkeit](04_formel_wartbarkeit.md)).            |
| **Technische Hilfsmittel** | Topologische Sortierung und das DAG-Konzept ([07 Konzeptioneller Rahmen](07_konzeptioneller_rahmen.md)) helfen bei der Auswertung, lösen aber nicht das Verständnisproblem für Menschen. |


### Fazit

Nur **fachlich zentrale** Berechnungen als BVs zu führen, ergibt ein wartbares und verständliches Modell. Ein Baum mit hunderten BVs überfordert die Pflege und das Nachvollziehen der Logik.

---

## Argument b) Historische Daten vs. Stammdaten

### Kern

Die Excel-Dateien enthalten Berechnungsergebnisse aus **Jahren, die nicht Teil der Betrachtungen** sind – z.B. um Veränderungen über längere Zeiträume aufzuzeigen. In der späteren Anwendung fließen aber **nur Stammdaten** in die Berechnungen ein.

### Ausarbeitung


| Aspekt                           | Beschreibung                                                                                                                                                              |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Excel als Analysewerkzeug**    | Excel dient als Berichts- und Analysewerkzeug. Spalten/Zeilen für mehrere Jahre (MAJahr1, MAJahr2, MAJahr3 etc.) visualisieren Zeitreihen und Vergleiche.                 |
| **Zielanwendung (IAK Farmaxis)** | Die PHP-Anwendung führt Berechnungen auf **aktuellen Stammdaten** aus. Historische Zeitreihen sind nicht Teil der Laufzeit-Berechnung.                                    |
| **Excel-spezifische Strukturen** | Formeln, die explizit auf MAJahr1, MAJahr2, MAJahr3 verweisen, modellieren Excel-Layouts. In einer relationalen Anwendung werden diese durch Abfragen und Filter ersetzt. |
| **MDM-Kontext**                  | BVs beschreiben Regeln für Stammdaten, nicht für historische Excel-Snapshots. Siehe [07 Konzeptioneller Rahmen](07_konzeptioneller_rahmen.md) (Master Data Management).   |


### Fazit

Viele Excel-Formeln sind an das **Excel-Layout** (Jahresspalten, Zeitreihen) gebunden und haben in der Zielanwendung keine direkte Entsprechung. Ihre Überführung würde BVs erzeugen, die in der Anwendung nicht sinnvoll ausgewertet werden können.

---

## Argument c) Hilfskonstrukte und -tabellen

### Kern

So wie Excel funktioniert, sind **Hilfskonstrukte und -tabellen** im Einsatz. Bei relationaler Datenhaltung und einer PHP-Anwendung sind diese **nicht notwendig**.

### Ausarbeitung


| Excel-Hilfsmittel             | Beschreibung                                                      | In relationaler Anwendung                                         |
| ----------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------- |
| **Zwischenergebnisse**        | Versteckte Zeilen/Spalten für Teilsummen, Zwischenwerte           | Direkte Berechnung auf DB-Ergebnissen; keine Zwischenzellen nötig |
| **Lookup-Tabellen**           | Tabellen für Übersetzungen, Zuordnungen (z.B. Code → Bezeichnung) | Joins, Views und Abfragen ersetzen Lookups                        |
| **Pivot-ähnliche Strukturen** | Aggregationen über Zeilen/Spalten                                 | SQL-Gruppierungen, Aggregationsfunktionen                         |
| **Named Ranges**              | Benannte Bereiche für komplexe Referenzen                         | Keine Entsprechung; Abfragen definieren die Datenmenge            |


**Beispiel:** Eine COUNTIFS-Formel über MAJahr1, MAJahr2 und MAJahr3 zählt in Excel drei separate Tabellen. In der Anwendung wird stattdessen **eine** Abfrage mit Filterkriterien ausgeführt – nicht drei separate Zählungen.

### Fazit

Hilfskonstrukte in BVs zu überführen würde **unnötige Komplexität und Redundanz** erzeugen. Die Zielarchitektur (relationale DB, PHP) bietet bessere Abstraktionen.

---

## Argument d) Komplexe Anweisungen und Filter – DSL und programmierte Methoden

### Kern

Die Anweisungen und Filter in Excel sind **sehr komplex** und nicht direkt in Pseudocode abbildbar. Sie müssen in eine [Domain-Specific Language](https://en.wikipedia.org/wiki/Domain-specific_language) (DSL) überführt werden bzw. auf **programmierte Methoden** zurückgreifen.

### Ausarbeitung


| Aspekt                 | Beschreibung                                                                                                                                                                                                      |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Excel-Funktionen**   | INDEX/MATCH, COUNTIFS, SUMIFS, verschachtelte WENN, Array-Formeln – semantisch reich, syntaktisch Excel-spezifisch.                                                                                               |
| **Pseudocode-Grenzen** | Der Pseudocode ([01 Definition](01_definition.md)) ist eine kleine DSL für arithmetische Ausdrücke und einfache Bedingungen. Er bildet COUNTIFS, INDEX/MATCH etc. nicht direkt ab.                                |
| **Auswertungstypen**   | Komplexe Formeln erfordern spezielle Auswertungstypen: `operation="index_lookup"` für INDEX/MATCH, `operation="count_filter"` für COUNTIFS/SUMIFS. Siehe [06 Technische Handhabung](06_technische_handhabung.md). |
| **Zwei Wege**          | Entweder (1) DSL/Transformer mit Regeln pro Excel-Funktion oder (2) programmierte Methoden in der Anwendung. Eine 1:1-Überführung „wie in Excel“ ist nicht möglich.                                               |
| **Logik im Code**      | Viele Excel-Formeln würden zu BVs mit `operation="count_filter"` oder `operation="index_lookup"` – die eigentliche Logik steckt dann im Programmcode, nicht im lesbaren Pseudocode.                               |


### Fazit

Komplexe Excel-Logik lässt sich nicht sinnvoll als „lesbare“ Berechnungsvorschrift abbilden. Eine **selektive Überführung** kombiniert mit **programmierten Methoden** für die Auswertung ist der pragmatischere Ansatz.

---

## Empfehlung: Selektive Überführung

### Strategie

Nur **fachlich zentrale**, für die Anwendung relevante Berechnungen als BVs überführen.

### Kriterien (Beispiele)


| Überführen                           | Nicht überführen                |
| ------------------------------------ | ------------------------------- |
| Wichtige Kennzahlen                  | Hilfszellen                     |
| Stammdaten-abhängige Regeln          | Zwischenergebnisse              |
| Von Nutzern pflegbare Geschäftslogik | Jahresspezifische Aggregationen |
|                                      | Reine Excel-Layout-Logik        |


### Technische Unterstützung

Das Projekt kennt bereits ein Konzept für „wichtige“ Zellen: Das Flag `wichtig` in der Berechnungsvorschrift und die Konfiguration in der Excel-Import-Config ermöglichen, bestimmte Zellen hervorzuheben. Dies unterstützt die selektive Überführung – z.B. nur Zellen mit `wichtig=true` als BVs zu persistieren oder priorisiert anzuzeigen.

---

## Todos: Codeänderungen aus der Empfehlung

Die folgenden Codeänderungen leiten sich aus der Empfehlung zur selektiven Überführung ab:

| # | Todo | Priorität | Beschreibung |
|---|------|-----------|--------------|
| 1 | **Excel-Import: Option „nur wichtige“** | Hoch | CLI-Parameter oder Config-Option `nur_wichtige: true` einführen. Wenn aktiv: Nur Zellen mit `wichtig=true` (aus `wichtige_zellen`) werden als BVs erzeugt und persistiert; alle anderen Formelzellen werden übersprungen. Ermöglicht strikte selektive Überführung. |
| 2 | **Auswertung: operation count_filter** | Hoch | Programmierte Methode für `operation="count_filter"` (COUNTIFS/SUMIFS) implementieren. Die BV enthält Variablen und Parameter; die eigentliche Zählung/Aggregation erfolgt im Code (z.B. SQL oder PHP), nicht als Pseudocode-Auswertung. |
| 3 | **Auswertung: operation index_lookup** | Hoch | Programmierte Methode für `operation="index_lookup"` (INDEX/MATCH) implementieren. Lookup-Logik in der Anwendung ausführen statt Pseudocode zu interpretieren. |
| 4 | **Suche/Filter: Default „nur wichtige“** | Mittel | Optional: Bei der Suche `wichtig=true` als Default setzen oder „nur wichtige“ als empfohlene Ansicht anbieten, um die Komplexität für Nutzer zu reduzieren. |
| 5 | **Listen: Sortierung nach wichtig** | Mittel | In Listen (z.B. Berechnungsvorschriften-Übersicht) BVs mit `wichtig=true` zuerst anzeigen oder als Standard-Sortierung anbieten. |
| 6 | **DSL/Transformer für komplexe Formeln** | Mittel (langfristig) | Excel-Formel-Parser und Transformationsregeln pro Funktion (COUNTIFS, INDEX/MATCH etc.) implementieren, um deterministisch BVs mit korrektem `operation` und `operation_parameter` zu erzeugen. Siehe Plan „DSL statt LLM“. |
| 7 | **Config: Kriterien dokumentieren** | Niedrig | In `excel_import_config.yaml` oder als Kommentar die Kriterien „Überführen vs. Nicht überführen“ dokumentieren, damit Konfigurierende wissen, welche Zellen in `wichtige_zellen` aufgenommen werden sollen. |

---

## Verweise


| Kapitel                                                   | Inhalt                                                    |
| --------------------------------------------------------- | --------------------------------------------------------- |
| [01 Definition](01_definition.md)                         | Was ist eine Berechnungsvorschrift? Pseudocode, Variablen |
| [04 Formel-Wartbarkeit](04_formel_wartbarkeit.md)         | Pseudocode-Regeln, Unterstützung für Nichtinformatiker    |
| [05 Zusammenführung](05_zusammenfuehrung.md)              | Viele BVs, Abhängigkeiten, Zusammenführungsoptionen       |
| [06 Technische Handhabung](06_technische_handhabung.md)   | operation, Auswertungstypen, Matching                     |
| [07 Konzeptioneller Rahmen](07_konzeptioneller_rahmen.md) | DAG, DSL, MDM, etablierte Konzepte                        |


