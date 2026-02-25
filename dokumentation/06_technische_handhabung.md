# Technische Handhabung: Fallstricke, Besonderheiten und fachliche Aspekte

Diese Inhalte sind **generisch und theoretisch** formuliert, damit sie in Anwendungen wie IAK Farmaxis Berücksichtigung finden können – unabhängig von der konkreten Implementierung.

---

## 1. Fallstricke (Pitfalls)

Diese Fallstricke gelten unabhängig von der konkreten Implementierung. Anwendungen sollten sie bei der Handhabung von Berechnungsvorschriften berücksichtigen.

### Variablen und Verlinkung

| Fallstrick | Theoretische Überlegung | Konsequenz für Anwendungen |
|------------|-------------------------|----------------------------|
| **Variablenname exakt** | Der Variablenname im Formel-String muss exakt mit dem Namen in der Variablen-Definition übereinstimmen. Die Frage ist: case-sensitive oder nicht? | Eine einheitliche Konvention (z.B. case-sensitive) muss definiert und dokumentiert werden. Abweichungen führen zu fehlender Verlinkung oder fehlerhafter Auswertung. |
| **Cross-Sheet-Referenzen** | Wenn eine Variable auf eine Zelle in einem anderen Tabellenblatt verweist, reicht die Zellenidentifikator allein nicht. Das Quellblatt muss mitgeführt werden. | Ohne Blatt-Information sucht das Matching nur im aktuellen Blatt – die Referenz bleibt unverlinkt. |
| **Zellenidentifikator-Format** | Excel kennt absolute und relative Referenzen ($A$1 vs. A1). Für Matching muss ein einheitliches Format definiert werden. | Unstimmigkeiten zwischen gespeichertem und gesuchtem Format führen zu Fehlern beim automatischen Verlinken. |
| **Mehrere Treffer beim Matching** | Bei mehr als einer passenden BV kann nicht automatisch entschieden werden. Automatische Verlinkung wäre willkürlich. | Der Benutzer muss explizit wählen. Die Anwendung muss eine Auswahl-Oberfläche bereitstellen. |
| **Zwei Arten von Identifikatoren** | Einerseits die Zellenidentifikator (A1, D7) aus der Quelle, andererseits Excel-Named-Range-Identifikatoren (_1_Wert). Beide können für Matching relevant sein. | Die Priorität der Matching-Strategie muss klar sein – sonst werden falsche BVs verlinkt oder Verlinkungen übersehen. |

### Speicherung und Versionierung

| Fallstrick | Theoretische Überlegung | Konsequenz für Anwendungen |
|------------|-------------------------|----------------------------|
| **Überschreiben vs. Historie** | Beim Speichern einer neuen Version kann die alte Version überschrieben oder zusätzlich erhalten werden. Die Wahl hat Auswirkungen auf Datenmenge und Abrufbarkeit. | Ohne Historie: einfacher, aber keine Wiederherstellung. Mit Historie: Audit-Trail, aber höherer Speicherbedarf und komplexere Abfragen. |
| **Sonderzeichen in Variablennamen** | Variablennamen können Leerzeichen, Sonderzeichen, Umlaute enthalten. Diese können in Speicherformaten Probleme verursachen. | Eine Codierungs- oder Normalisierungsregel muss definiert werden – z.B. Ersetzung für technische IDs bei Beibehaltung des Originalnamens für Anzeige. |
| **Inkonsistente Quelle-Information** | Die Quelle (Tabellenidentifikator, Blatt, Zelle, Beschreibung) kann unvollständig sein. Ohne sie funktioniert Matching nach Zelle nicht. | Die Anwendung sollte prüfen, ob Quelle-Information für Matching erforderlich ist, und ggf. den Benutzer informieren. |
| **Informative vs. bearbeitbare Felder** | Manche Felder (z.B. formel_original) sind nur informativ und werden bei Updates aus der alten Version übernommen. | Klarheit: Welche Felder darf der Benutzer ändern? Welche werden automatisch geführt? |

### Verarbeitung von Excel-Formeln

| Fallstrick | Theoretische Überlegung | Konsequenz für Anwendungen |
|------------|-------------------------|----------------------------|
| **Excel-interne Präfixe** | Excel-Formeln können interne Präfixe enthalten (_xlfn., _xlws. etc.), die keine Named Ranges sind. Diese sollten vor der Verarbeitung entfernt werden. | Ohne Normalisierung werden falsche Identifikatoren für Matching genutzt. |
| **Fehlerbehandlungs-Funktionen** | IFERROR, IFNA etc. wrappen den eigentlichen Ausdruck. Bei der Umwandlung in Pseudocode: Nur der Wert-Teil wird übernommen, die Fehlerbehandlung geht verloren. | Fachliche Entscheidung: Soll die Fehlerbehandlung im Pseudocode abgebildet werden oder nicht? |

---

## 2. Besonderheiten bei der Handhabung

### Matching-Prioritäten (Verlinkung)

Die Reihenfolge der Matching-Strategien entscheidet, welche BV verlinkt wird, wenn mehrere Kandidaten existieren. Dies entspricht dem Konzept der [Entity Resolution](https://en.wikipedia.org/wiki/Record_linkage) (Record Linkage) – der Zuordnung von Referenzen zu Entitäten bei Ambiguität. Siehe [07 Konzeptioneller Rahmen](07_konzeptioneller_rahmen.md).

Theoretisch sinnvolle Priorität:

1. **Zelle + Blatt** (exakt): Zellenidentifikator und Tabellenblatt der Variable stimmen mit der Quelle einer BV überein. Höchste Zuverlässigkeit.
2. **Excel-Identifikator**: Wenn die Variable einem Excel-Named-Range-Identifikator entspricht, Suche nach BV mit diesem Identifikator. Relevant bei Import aus Excel.
3. **Metadaten** (Name, Symbol): Fallback für Tabellenspalten ohne Zellreferenz. Weniger eindeutig – mehrere Treffer wahrscheinlich.

### Rückwärts-Verlinkung

Nach Anlegen einer neuen BV können andere BVs eine Variable haben, die nun auf diese BV verlinkt werden kann. Theoretische Überlegungen:

- **Wann auslösen?** Nach jedem Speichern einer neuen BV prüfen oder nur bei expliziter Aktion?
- **Zirkularitätsprüfung:** Vor jeder Verlinkung muss geprüft werden, ob eine zirkuläre Abhängigkeit entstünde (A→B→C→A).
- **Priorität:** Auch bei Rückwärts-Verlinkung sollte eine Priorität (Zelle, Excel-ID, Name) definiert sein.

### Zirkuläre Abhängigkeiten

- **Definition:** Eine zirkuläre Abhängigkeit liegt vor, wenn A→B→C→…→A (A referenziert B, B referenziert C, … C referenziert A). Der Abhängigkeitsgraph soll ein [DAG](https://en.wikipedia.org/wiki/Directed_acyclic_graph) (Directed Acyclic Graph) sein – azyklisch, ohne Zyklen. Siehe [07 Konzeptioneller Rahmen](07_konzeptioneller_rahmen.md).
- **Prüfung:** Bei jeder Verlinkung oder Rückwärts-Verlinkung muss rekursiv geprüft werden, ob die Ziel-BV (direkt oder indirekt) die Ausgangs-BV referenziert.
- **Endlosschleifen:** Bei fehlerhaften oder unvollständigen Daten kann die Prüfung in eine Schleife geraten – ein Besucht-Set verhindert das.

### Löschen

- **Referenzprüfung:** Eine BV, die von anderen referenziert wird, sollte nicht gelöscht werden können – oder nur mit expliziter Bestätigung und Kaskadierung (z.B. Referenzen aufheben). Dies entspricht dem Konzept der [referentiellen Integrität](https://en.wikipedia.org/wiki/Referential_integrity) – Referenzen müssen konsistent behandelt werden.
- **Konsequenz:** Die Anwendung muss vor dem Löschen prüfen, ob Referenzen existieren, und den Benutzer entsprechend informieren.

### Auswertungstyp (operation)

- Bei INDEX/MATCH-artigen Formeln ist ein spezieller Auswertungstyp (z.B. `index_lookup`) sinnvoll – die Formel ist kein einfacher arithmetischer Ausdruck.
- Die Variablenreihenfolge hat Bedeutung: (1) Tabelle, (2) Zeilenkriterium, (3) Spaltenkriterium.
- Die Anwendung muss diese Semantik bei der Auswertung mit echten Werten berücksichtigen.

---

## 3. Fachliche Aspekte

### Drei Identifikatoren

| Begriff | Bedeutung | Verwendung |
|---------|-----------|------------|
| **BV-ID** | Eindeutige Identität der Berechnungsvorschrift (z.B. UUID) | Referenz zwischen BVs (referenz_berechnungsvorschrift_id), Speicherung, Abruf |
| **Zellenidentifikator** | Excel-Zelle (A1, D7) aus der Quelle | Matching: Variable mit Zellreferenz sucht BV, deren Quelle diese Zelle ist |
| **Excel-Identifikator** | Excel-Named-Range oder ähnlicher Identifikator (_1_Wert) | Matching: Wenn Formeln auf Named Ranges verweisen, sucht man nach BV mit diesem Identifikator |

### Formel vs. formel_original

- **formel:** Pseudocode, menschenlesbar, bearbeitbar. Dies ist die „aktive“ Formel.
- **formel_original:** Originale Excel-Formel, nur informativ. Dient der Nachvollziehbarkeit und ggf. dem Matching (Excel-Identifikatoren).

### Account-Referenz (erstellt_von, geaendert_von)

- Für Audit und Nachvollziehbarkeit sollte jede Version wissen, welcher Benutzer/Account die Änderung vorgenommen hat.
- Die Dokumentation empfiehlt `erstellt_von` und `geaendert_von`. Bei Anwendungen wie IAK Farmaxis sollten diese Felder von Anfang an unterstützt werden.

### Vollständigkeit der Quelle

- Für zuverlässiges Matching nach Zelle: Tabellenidentifikator, Tabellenblatt und Zellenidentifikator sollten vollständig sein. Dies unterstützt [Data Lineage](https://en.wikipedia.org/wiki/Data_lineage) – die Nachverfolgbarkeit der Datenherkunft für Compliance und Audit. Siehe [07 Konzeptioneller Rahmen](07_konzeptioneller_rahmen.md).
- Bei Cross-Sheet-Referenzen: Die Variable muss das Tabellenblatt der referenzierten Zelle kennen (tabellenblatt_referenz).

### Performance bei vielen Daten

- Das Laden aller BVs und das Abrufen von „verwendet in“ / „verwendet“ kann bei vielen BVs aufwändig werden.
- Theoretische Überlegung: Batch-Loading, Caching oder indizierte Abfragen statt N+1-Ladevorgänge.
