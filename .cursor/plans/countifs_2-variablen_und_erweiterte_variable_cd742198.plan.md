---
name: COUNTIFS 2-Variablen und erweiterte Variable
overview: Umstellung der COUNTIFS-Verarbeitung auf den semantisch korrekten 2-Variablen-Ansatz (nur Kriterienzellen D3, E5 als Variablen) sowie Erweiterung des Variable-Modells um Identifikatoren, Referenzen und Vergleichskontext für Auflösung und Auswertung.
todos: []
isProject: false
---

# Plan: COUNTIFS 2-Variablen-Ansatz und erweitertes Variable-Handling

## Ausgangslage

Aktuell werden bei COUNTIFS 8 Variablen erzeugt (2 Zellreferenzen + 6 Tabellenspalten). Semantisch korrekt sind nur **2 Variablen** (Kriterien D3, E5), da die Tabellenspalten Kriterienbereiche sind, keine Wertquellen. Die [Microsoft COUNTIFS-Dokumentation](https://support.microsoft.com/en-us/office/countifs-function-dda3dc6e-f74e-4aee-88bc-aa8c2a866842) bestätigt: `criteria` = Wert zum Vergleichen, `criteria_range` = Bereich zum Prüfen.

## Zielarchitektur

```mermaid
flowchart TB
    subgraph Variable [Erweitertes Variable-Modell]
        Identifikator[name, zellenidentifikator, tabellenblatt_referenz]
        Referenz[quelle_typ: zelle | tabellenspalte | berechnungsvorschrift]
        Vergleich[kriterienbereich, vergleichsoperator]
    end
    subgraph BV [Berechnungsvorschrift]
        formel[formel: Pseudocode]
        operation[operation: ausdruck | index_lookup | count_filter]
    end
    Variable --> BV
```



---

## Konkretes Beispiel: Excel-Formel → Berechnungsvorschrift

### Eingabe (Zelleneingabe)


| Feld                  | Wert                                |
| --------------------- | ----------------------------------- |
| Tabellenidentifikator | Soziales                            |
| Tabellenblatt         | 2. Arbeitszeit AW                   |
| Zellenidentifikator   | B8                                  |
| Beschreibung          | Anzahl MA – Vollzeit festangestellt |
| Formel                | siehe unten                         |


**Excel-Formel (original):**

```
=SUM(COUNTIFS(MAJahr1[Angestelltenverhältnis],'INTERN BEZÜGE'!$D$3,MAJahr1[Wie viele Monate des Jahres im Betrieb angestellt?],'INTERN BEZÜGE'!E5),COUNTIFS(MAJahr2[Angestelltenverhältnis],'INTERN BEZÜGE'!$D$3,MAJahr2[Wie viele Monate des Jahres im Betrieb angestellt?],'INTERN BEZÜGE'!E5),COUNTIFS(MAJahr3[Angestelltenverhältnis],'INTERN BEZÜGE'!$D$3,MAJahr3[Wie viele Monate des Jahres im Betrieb angestellt?],'INTERN BEZÜGE'!E5))
```

### Struktur der Formel (COUNTIFS-Logik)

- **SUM** über 3 Einzelzählungen
- Jede **COUNTIFS** hat 2 Kriterienpaare:
  - `criteria_range1` = MAJahr1[Angestelltenverhältnis], `criteria1` = D3 (INTERN BEZÜGE)
  - `criteria_range2` = MAJahr1[Wie viele Monate...], `criteria2` = E5 (INTERN BEZÜGE)
- Gleiche Kriterien (D3, E5) gelten für MAJahr1, MAJahr2 und MAJahr3

### Ausgabe (Berechnungsvorschrift)

**Pseudocode (formel):**

```
Anzahl(MAJahr1, Angestelltenverhältnis=Kriterium_Angestelltenverhältnis, Monate_im_Betrieb=Kriterium_Monate) + Anzahl(MAJahr2, Angestelltenverhältnis=Kriterium_Angestelltenverhältnis, Monate_im_Betrieb=Kriterium_Monate) + Anzahl(MAJahr3, Angestelltenverhältnis=Kriterium_Angestelltenverhältnis, Monate_im_Betrieb=Kriterium_Monate)
```

**Variablen (2 Stück):**


| name                             | zellenidentifikator | tabellenblatt_referenz | kriterienbereich                                   | quelle_typ |
| -------------------------------- | ------------------- | ---------------------- | -------------------------------------------------- | ---------- |
| Kriterium_Angestelltenverhältnis | D3                  | INTERN BEZÜGE          | Angestelltenverhältnis                             | zelle      |
| Kriterium_Monate                 | E5                  | INTERN BEZÜGE          | Wie viele Monate des Jahres im Betrieb angestellt? | zelle      |


**operation:** `"count_filter"`

**operation_parameter:**

```json
{
  "tabellen": ["MAJahr1", "MAJahr2", "MAJahr3"],
  "aggregation": "summe"
}
```

**Vollständiges JSON (Auszug):**

```json
{
  "name": "Anzahl MA – Vollzeit festangestellt",
  "formel": "Anzahl(MAJahr1, Angestelltenverhältnis=Kriterium_Angestelltenverhältnis, Monate_im_Betrieb=Kriterium_Monate) + Anzahl(MAJahr2, ...) + Anzahl(MAJahr3, ...)",
  "operation": "count_filter",
  "operation_parameter": {
    "tabellen": ["MAJahr1", "MAJahr2", "MAJahr3"],
    "aggregation": "summe"
  },
  "variablen": [
    {
      "name": "Kriterium_Angestelltenverhältnis",
      "ist_primitive": true,
      "zellenidentifikator": "D3",
      "tabellenblatt_referenz": "INTERN BEZÜGE",
      "quelle_typ": "zelle",
      "kriterienbereich": "Angestelltenverhältnis",
      "vergleichsoperator": "="
    },
    {
      "name": "Kriterium_Monate",
      "ist_primitive": true,
      "zellenidentifikator": "E5",
      "tabellenblatt_referenz": "INTERN BEZÜGE",
      "quelle_typ": "zelle",
      "kriterienbereich": "Wie viele Monate des Jahres im Betrieb angestellt?",
      "vergleichsoperator": "="
    }
  ],
  "metadaten": { "kategorie": "Personal", "symbol": "AMV", "datentyp": "integer", "einheit": "Stk" }
}
```

### Auflösung bei der Auswertung

1. **Identifikatoren:** D3 und E5 (INTERN BEZÜGE) → Werte aus Wertequelle laden (z.B. D3 = "Vollzeit festangestellt", E5 = "12").
2. **Referenzen:** Beide Variablen haben `quelle_typ: "zelle"` → Wert kommt aus Zelle, nicht aus BV.
3. **Vergleichswerte:** `kriterienbereich` definiert die Zuordnung:
  - Kriterium_Angestelltenverhältnis filtert Spalte "Angestelltenverhältnis"
  - Kriterium_Monate filtert Spalte "Wie viele Monate des Jahres im Betrieb angestellt?"
4. **Auswertung:** Für jede Tabelle (MAJahr1, MAJahr2, MAJahr3): Zeilen zählen, wo beide Kriterien erfüllt sind. Drei Zähler addieren.

---

## 1. Variable-Modell erweitern

**Datei:** [backend/models/berechnungsvorschrift.py](backend/models/berechnungsvorschrift.py)

Neue optionale Felder in `Variable`:


| Feld                       | Typ             | Beschreibung                                                                                            |
| -------------------------- | --------------- | ------------------------------------------------------------------------------------------------------- |
| `quelle_typ`               | `Optional[str]` | `"zelle"`                                                                                               |
| `kriterienbereich`         | `Optional[str]` | Bei COUNTIFS/SUMIFS: Spaltenname, auf den das Kriterium angewendet wird (z.B. "Angestelltenverhältnis") |
| `vergleichsoperator`       | `Optional[str]` | `"="` (Default), `">"`, `"<"`, etc.                                                                     |
| `tabellenreferenz`         | `Optional[str]` | Bei Tabellenspalten: Tabellenname (z.B. "MAJahr1")                                                      |
| `kriterienbereich_blatt`   | `Optional[str]` | Blatt des Kriterienbereichs – nur wenn aus Excel aufgelöst (Fallback: leer)                             |
| `kriterienbereich_bereich` | `Optional[str]` | Zellbereich der Spalte (z.B. "C6:C20") – nur wenn aus Excel aufgelöst (Fallback: leer)                  |


**Bestehende Felder** bleiben: `name`, `zellenidentifikator`, `tabellenblatt_referenz`, `referenz_berechnungsvorschrift_id`, `ist_primitive`.

**Auflösungslogik:**

- **Identifikator:** `name` + `zellenidentifikator` + `tabellenblatt_referenz` (bereits vorhanden)
- **Referenz:** `quelle_typ` + ggf. `referenz_berechnungsvorschrift_id` – woher kommt der Wert?
- **Vergleichswert:** `kriterienbereich` + `vergleichsoperator` – bei COUNTIFS: „Variable X filtert Spalte Y“

---

## 2. Operation "count_filter" für COUNTIFS

**Datei:** [backend/models/berechnungsvorschrift.py](backend/models/berechnungsvorschrift.py)

`operation` erweitern: `"ausdruck"`  `"index_lookup"`  `"count_filter"`.

**Neues Feld:** `operation_parameter: Optional[dict]` – für `count_filter`:

```python
{
  "tabellen": ["MAJahr1", "MAJahr2", "MAJahr3"],  # Tabellen, die gezählt werden
  "aggregation": "summe"  # summe der Einzelzählungen (SUM(COUNTIFS...))
}
```

Die Zuordnung Variable → Kriterienbereich erfolgt über `Variable.kriterienbereich`.

---

## 3. RDF-Schema erweitern

**Datei:** [backend/services/json_rdf_converter.py](backend/services/json_rdf_converter.py)

Neue Properties (analog zu `referenziertZelle`, `referenziertTabellenblatt`):

- `hatQuelleTyp` (Literal)
- `hatKriterienbereich` (Literal)
- `hatVergleichsoperator` (Literal)
- `hatTabellenreferenz` (Literal)
- `hatKriterienbereichBlatt` (Literal) – optional, nur bei aufgelöster Referenz
- `hatKriterienbereichBereich` (Literal) – optional, nur bei aufgelöster Referenz

Auf BV-Ebene: `hatOperationParameter` (JSON-String oder strukturierte Triples).

**Lesen:** Beim `rdf_to_berechnungsvorschrift` die neuen Properties aus dem Variable-Subgraph auslesen.

---

## 4. Prompt und Beispiel anpassen

**Dateien:**  
[backend/prompts/berechnungsvorschrift_prompt.txt](backend/prompts/berechnungsvorschrift_prompt.txt)  
[backend/prompts/berechnungsvorschrift_beispiel.txt](backend/prompts/berechnungsvorschrift_beispiel.txt)

**Änderungen:**

- **COUNTIFS-Regel:** Nur Kriterienzellen (Zellreferenzen) = Variablen. Tabellenspalten (Kriterienbereiche) sind **keine** Variablen.
- **Pseudocode:** `Anzahl(MAJahr1, Angestelltenverhältnis=Kriterium_Angestelltenverhältnis, Monate_im_Betrieb=Kriterium_Monate) + ...`
- **Beispiel 8:** 2 Variablen mit `kriterienbereich`:
  - `Kriterium_Angestelltenverhältnis`: zellenidentifikator=D3, tabellenblatt_referenz=INTERN BEZÜGE, kriterienbereich="Angestelltenverhältnis"
  - `Kriterium_Monate`: zellenidentifikator=E5, tabellenblatt_referenz=INTERN BEZÜGE, kriterienbereich="Wie viele Monate des Jahres im Betrieb angestellt?"
- **operation:** `"count_filter"` setzen
- **operation_parameter:** `{"tabellen": ["MAJahr1", "MAJahr2", "MAJahr3"], "aggregation": "summe"}`

**JSON-Schema im Prompt** um die neuen Variable-Felder ergänzen.

---

## 5. LLM-Service anpassen

**Datei:** [backend/services/llm_service.py](backend/services/llm_service.py)

- **Tabellenspalten-Hinweis entfernen oder umwidmen:** Nicht mehr „jede Tabellenspalte = Variable“, sondern „Strukturelle Info für COUNTIFS: Tabellen und Kriterienbereiche – diese sind KEINE Variablen, nur die Kriterienzellen (D3, E5) sind Variablen“.
- **Zellreferenzen-Hinweis beibehalten** – zentral für den 2-Variablen-Ansatz.
- **_dict_to_berechnungsvorschrift:** Neue Variable-Felder (`quelle_typ`, `kriterienbereich`, `vergleichsoperator`) aus LLM-JSON übernehmen.
- **Optional:** `tabellenreferenz` und `operation_parameter` aus `tabellenspalten_aus_formel` ableiten und dem LLM als Hinweis mitgeben („Tabellen: MAJahr1, MAJahr2, MAJahr3 – diese werden gezählt, Kriterien kommen aus D3 und E5“).

---

## 6. Excel-Referenz-Index (vorab laden, mit Fallback)

**Ziel:** Alle Tabellen- und Bereichsreferenzen aus der Excel-Datei laden, bevor die erste Berechnungsvorschrift erstellt wird. Bei Auftauchen in einer Formel direkt den aufgelösten Bereich eintragen. **Fallback:** Wenn die Auflösung fehlschlägt, bleibt die bestehende Behandlung (LLM, formel_utils) erhalten – die Felder sind optional.

### 6.1 Neues Modul: excel_referenz_index.py

**Datei:** [backend/utils/excel_referenz_index.py](backend/utils/excel_referenz_index.py) (neu)

**Funktion:** `lade_referenz_index(wb) -> dict`

**Auflösungsreihenfolge:**

1. **ws.tables** (alle Blätter) – ListObjects mit Spaltenstruktur
  - `(tabellenname, spaltenname)` → `{"blatt": str, "bereich": str, "bereich_mit_blatt": str}`
  - Spaltenbereich aus `table.ref` + `tableColumns` berechnen
2. **wb.defined_names** – globale benannte Bereiche
  - `defn.destinations` → `(blatt, bereich)`
  - Bei `[Spalte]`: Header-Zeile des Bereichs lesen, Spaltenindex ermitteln, Spaltenbereich ableiten
3. **ws.defined_names** (pro Blatt) – blattspezifische benannte Bereiche
  - wie 2.

**Index-Struktur:**

```python
{
  ("MAJahr1", "Angestelltenverhältnis"): {"blatt": "2. Arbeitszeit AW", "bereich": "C6:C20", "bereich_mit_blatt": "'2. Arbeitszeit AW'!C6:C20"},
  ("MAJahr1", "Wie viele Monate..."): {"blatt": "2. Arbeitszeit AW", "bereich": "D6:D20", ...},
  ("MAJahr2", "Angestelltenverhältnis"): {...},
  # Einfache benannte Bereiche (ohne Spalte)
  ("UmsatzBereich", None): {"blatt": "Sheet1", "bereich": "A1:A12", ...},
}
```

### 6.2 Integration in Excel-Import

**Datei:** [backend/scripts/excel_import.py](backend/scripts/excel_import.py)

**Ablauf:**

1. Workbook öffnen
2. `referenz_index = lade_referenz_index(wb)` – einmalig vor der Schleife
3. Pro Formelzelle: `tabellenspalten_aus_formel(formel)` aufrufen
4. Für jede `(tabelle, spalte)`: Lookup im Index
5. **Wenn gefunden:** Aufgelöste Bereiche in Zelleneingabe ergänzen (neues optionales Feld `referenz_bereiche`)
6. **Wenn nicht gefunden:** Keine Ergänzung – Fallback auf bestehende Logik (LLM, formel_utils)

**Zelleneingabe erweitern (optional):**

```python
# In zelleneingaben-Dict, nur wenn Auflösung gelang:
"referenz_bereiche": [
  {"tabelle": "MAJahr1", "spalte": "Angestelltenverhältnis", "blatt": "2. Arbeitszeit AW", "bereich": "C6:C20"},
  ...
]
```

### 6.3 Variable-Modell: aufgelöste Bereiche (siehe Abschnitt 1)

Die Felder `kriterienbereich_blatt` und `kriterienbereich_bereich` werden nur bei erfolgreicher Auflösung gesetzt.

**Fallback-Verhalten:**

- Fehlen diese Felder: `kriterienbereich` (Spaltenname) und `operation_parameter.tabellen` reichen – Auswerter muss zur Laufzeit die Tabelle/Spalte auflösen oder Datenstruktur bereitstellen.
- Sind sie gesetzt: Konkreter Bereich kann direkt gelesen werden.

### 6.4 operation_parameter mit Fallback

**Bei aufgelösten Referenzen:**

```json
{
  "tabellen": ["MAJahr1", "MAJahr2", "MAJahr3"],
  "aggregation": "summe",
  "tabellen_bereiche": {
    "MAJahr1": {"blatt": "2. Arbeitszeit AW", "bereich": "B5:G20"},
    "MAJahr2": {"blatt": "2. Arbeitszeit AW", "bereich": "B25:G40"},
    "MAJahr3": {"blatt": "2. Arbeitszeit AW", "bereich": "B45:G60"}
  }
}
```

**Bei nicht aufgelösten Referenzen (Fallback):**

```json
{
  "tabellen": ["MAJahr1", "MAJahr2", "MAJahr3"],
  "aggregation": "summe"
}
```

→ `tabellen_bereiche` fehlt – Auswertung nutzt Tabellennamen und muss Daten extern beziehen.

### 6.5 API/LLM: Nutzung der referenz_bereiche

- **Excel-Import:** Übergibt `referenz_bereiche` an die API (neues optionales Feld in Zelleneingabe).
- **LLM-Service:** Wenn `referenz_bereiche` vorhanden, als Hinweis in den User-Prompt einbauen („Aufgelöste Tabellenspalten: MAJahr1[Angestelltenverhältnis] = '2. Arbeitszeit AW'!C6:C20“).
- **Post-Processing:** Nach LLM-Antwort: Wenn `referenz_bereiche` vorhanden, `kriterienbereich_blatt`, `kriterienbereich_bereich` und `operation_parameter.tabellen_bereiche` aus dem Index befüllen.
- **Fallback:** Fehlt `referenz_bereiche` oder schlägt Auflösung fehl → keine Anreicherung, LLM-Ausgabe bleibt maßgeblich.

---

## 7. formel_utils – Nutzung anpassen

**Datei:** [backend/utils/formel_utils.py](backend/utils/formel_utils.py)

- `zellreferenzen_aus_formel`: Unverändert – weiterhin für Zellreferenz-Hinweis.
- `tabellenspalten_aus_formel`: Nicht mehr für Variable-Erzeugung, sondern für:
  - Ableitung von `operation_parameter.tabellen` (eindeutige Tabellennamen)
  - Ableitung der Kriterienbereichsnamen für den Prompt („D3 filtert Angestelltenverhältnis, E5 filtert Wie viele Monate...“)
  - Lookup im Referenz-Index (wenn vorhanden) für `referenz_bereiche`

---

## 8. Berechnungsvorschrift-Matcher

**Datei:** [backend/services/berechnungsvorschrift_matcher.py](backend/services/berechnungsvorschrift_matcher.py)

- **Keine Änderung** für Zellreferenz-Matching (zellenidentifikator, tabellenblatt_referenz).
- Tabellenspalten-Fallback (Priorität 3) bleibt für andere Formeltypen (z.B. SUMIFS mit Tabellenspalte als Summenbereich).

---

## 9. AUSWERTUNG_UND_OPERATION.md erweitern

**Datei:** [AUSWERTUNG_UND_OPERATION.md](AUSWERTUNG_UND_OPERATION.md)

Neuer Abschnitt für `operation = "count_filter"`:

- **Variablen:** Nur Kriterienzellen (z.B. Kriterium_Angestelltenverhältnis, Kriterium_Monate).
- **Auswertung:** Für jede Tabelle in `operation_parameter.tabellen`: Zähle Zeilen, wo `Spalte[kriterienbereich_i] = Wert(Variable_i)` für alle Kriterien. Summiere die Zähler.
- **Variable.kriterienbereich:** Definiert, welche Spalte pro Variable gefiltert wird.

---

## 10. Rückwärtskompatibilität

- **Bestehende BVs:** Fehlen `quelle_typ`, `kriterienbereich` etc. → Default-Verhalten (Ausdruck, Matching wie bisher).
- **RDF:** Neue Properties optional; fehlende Properties → `None` beim Lesen.
- **Bestehende 8-Variablen-BVs:** Können weiterhin gelesen werden; bei Regenerierung werden sie auf 2 Variablen umgestellt.

---

## 11. Migrations- oder Korrektur-Skript (optional)

Einmal-Skript zum Korrigieren der BV `2c2548ef-8700-4f84-98e8-d87044d749ae` (und ggf. anderer COUNTIFS-BVs) auf den neuen 2-Variablen-Ansatz. Kann manuell oder per API-Update erfolgen.

---

## Abhängigkeiten und Reihenfolge

1. Variable-Modell + operation/operation_parameter erweitern (inkl. `kriterienbereich_blatt`, `kriterienbereich_bereich`)
2. **excel_referenz_index.py** implementieren (lade_referenz_index)
3. Excel-Import: Referenz-Index vorab laden, Zelleneingaben mit `referenz_bereiche` anreichern (Fallback: ohne Anreicherung)
4. Zelleneingabe-Modell: optionales Feld `referenz_bereiche`
5. JSON-RDF-Converter anpassen (neue Variable-Properties, operation_parameter)
6. Prompt + Beispiel anpassen
7. LLM-Service anpassen (referenz_bereiche als Hinweis, Post-Processing für aufgelöste Bereiche, Fallback beibehalten)
8. formel_utils-Nutzung prüfen
9. AUSWERTUNG_UND_OPERATION.md aktualisieren

