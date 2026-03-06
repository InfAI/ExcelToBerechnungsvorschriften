# Konzeptioneller Rahmen: Etablierte Konzepte

Dieses Kapitel bündelt **etablierte Konzepte** aus Softwareentwicklung, Semantic Web und Informatik, die für die Berechnungsvorschriften relevant sind. Sie dienen als Referenz für technische Leser und erleichtern die Kommunikation mit Stakeholdern.

---

## Übersicht

| Konzept | Kurzbeschreibung | Relevanz für BVs | Kapitel |
|---------|------------------|------------------|---------|
| **DAG** | Gerichteter azyklischer Graph | Abhängigkeiten zwischen BVs, Zirkularitätsprüfung | [01](01_definition.md), [06](06_technische_handhabung.md) |
| **Topologische Sortierung** | Reihenfolge entlang Abhängigkeiten | Auswertung, Zusammenführung | [05](05_zusammenfuehrung.md), [06](06_technische_handhabung.md) |
| **Referentielle Integrität** | Konsistenz von Referenzen | Löschen, Verlinkung, `referenz_berechnungsvorschrift_id` | [01](01_definition.md), [06](06_technische_handhabung.md) |
| **Entity Resolution** | Zuordnung Referenz → Entität | Matching bei mehreren Treffern (Zelle, Excel-ID, Name) | [06](06_technische_handhabung.md) |
| **Immutability** | Unveränderliche Versionen | Option B (Vollständige Historie) | [02](02_versionierungskonzept.md) |
| **Provenance** | Herkunft, Wer/Wann/Was | Account-Referenz, Audit | [02](02_versionierungskonzept.md) |
| **DSL** | Domänenspezifische Sprache | Pseudocode-Formel (menschen- und maschinenlesbar) | [01](01_definition.md), [04](04_formel_wartbarkeit.md) |
| **MDM** | Zentrale Pflege von Stammdaten | IAK Farmaxis als Pflegeort für BVs | [03](03_wartung.md) |
| **Business Rules Engine** | Definition und Ausführung von Regeln | BVs als Geschäftsregeln | [01](01_definition.md) |
| **Data Lineage** | Nachverfolgbarkeit der Datenherkunft | Quelle, Versionierung, Audit | [02](02_versionierungskonzept.md), [06](06_technische_handhabung.md) |
| **Regionale Ausprägungen** | Mehrere Manifestationen pro logischer BV | Version + Region, Verlinkung Basis/Schwester | [01](01_definition.md), [02](02_versionierungskonzept.md) |

---

## Kurzbeschreibungen

### DAG (Directed Acyclic Graph)

Die Abhängigkeiten zwischen Berechnungsvorschriften („verwendet“ / „wird verwendet in“) bilden einen gerichteten Graphen. Zirkuläre Abhängigkeiten sind verboten – der Graph soll **azyklisch** sein. Dies entspricht dem Konzept eines [DAG](https://en.wikipedia.org/wiki/Directed_acyclic_graph) aus der Graphentheorie.

### Topologische Sortierung

Für Auswertung und Zusammenführung muss die Reihenfolge der BVs entlang der Abhängigkeiten bestimmt werden. Die [topologische Sortierung](https://en.wikipedia.org/wiki/Topological_sorting) ist das Standardverfahren für DAGs, um eine lineare Reihenfolge zu ermitteln (BV A vor BV B, wenn B von A abhängt).

### Referentielle Integrität

`referenz_berechnungsvorschrift_id` verweist auf eine andere BV. Wenn die referenzierte BV gelöscht wird, entstehen „tote“ Referenzen. Das Konzept der [referentiellen Integrität](https://en.wikipedia.org/wiki/Referential_integrity) fordert: Fremdschlüssel verweisen auf existierende Einträge; Löschen/Ändern muss konsistent behandelt werden.

### Entity Resolution

Das Matching (Variable → BV anhand Zelle, Excel-ID, Name) entspricht dem Zuordnen von Referenzen zu Entitäten. Bei mehreren Kandidaten ist [Entity Resolution](https://en.wikipedia.org/wiki/Record_linkage) (Record Linkage) der konzeptionelle Rahmen – der Benutzer muss explizit wählen.

### Immutability

Bei Option B (Vollständige Historie) ist jede Version **unveränderlich** (immutable). Änderungen erzeugen neue Versionen; alte werden nicht überschrieben. Dies entspricht dem Konzept der [Immutability](https://en.wikipedia.org/wiki/Immutable_object) aus funktionaler Programmierung und Event Sourcing.

### Provenance

`erstellt_von`, `geaendert_von`, `quelle` – wer hat was wann geändert, woher stammt die BV? Das Konzept der [Provenance](https://www.w3.org/TR/prov-overview/) (W3C PROV) beschreibt die Nachvollziehbarkeit von Herkunft und Änderungen.

### DSL (Domain-Specific Language)

Der Pseudocode ist eine kleine, fachlich definierte Sprache für Formeln – eine [Domain-Specific Language](https://en.wikipedia.org/wiki/Domain-specific_language). Sie ist menschen- und maschinenlesbar und auf den Anwendungsbereich beschränkt.

### MDM (Master Data Management)

Berechnungsvorschriften sind fachlich relevante Stammdaten. **IAK Farmaxis** soll künftig der Ort sein, an dem diese Stammdaten gepflegt werden. Das Konzept des [Master Data Management](https://en.wikipedia.org/wiki/Master_data_management) beschreibt die zentrale Pflege und Verteilung von Stammdaten.

### Business Rules Engine

BVs beschreiben Berechnungsregeln – wenn-dann-Logik, Formeln; sie sind ausführbare Geschäftslogik. Im Sinne einer [Business Rules Engine](https://en.wikipedia.org/wiki/Business_rules_engine) sind Berechnungsvorschriften Geschäftsregeln, die definiert und ausgewertet werden können.

### Data Lineage

Nachvollziehen, woher eine BV stammt (Excel-Zelle), wer sie geändert hat, welche BVs sie verwendet – das ist [Data Lineage](https://en.wikipedia.org/wiki/Data_lineage) (Datenherkunft). Wichtig für Compliance und Audit.

### Regionale Ausprägungen

Berechnungsvorschriften können in **verschiedenen Versionen** (zeitlich) und **verschiedenen Regionen** (räumlich) existieren. Eine logische Berechnungsvorschrift (z.B. „Anteil regionaler Rohstoffe") hat eine überregionale **Basis-BV** und optional **regionale Ausprägungen** (z.B. für Bayern, Baden-Württemberg). Alle Ausprägungen sind untereinander verlinkt (`referenz_basis_berechnungsvorschrift_id`, `referenz_schwester_auspraegung_id`). Dies ermöglicht regionalspezifische Anpassungen bei gleichzeitiger Nachvollziehbarkeit der Verwandtschaft. Siehe [01 Definition](01_definition.md), Abschnitt „Regionale Ausprägungen".

---

## Benutzerentscheidung bei Konflikten

Bei der **Zusammenführung** mehrerer BVs können Metadaten-Konflikte auftreten (unterschiedliche Kategorien, Einheiten, Datentypen). Das vereinfachte Konzept: **Benutzerentscheidung** – bei Konflikten muss der Anwender explizit die Metadaten der resultierenden BV festlegen. Das System warnt und schlägt einen Default vor (z.B. aus der „Haupt-BV“). Siehe [05 Zusammenführung](05_zusammenfuehrung.md), Abschnitt „Metadaten-Konflikt“.
