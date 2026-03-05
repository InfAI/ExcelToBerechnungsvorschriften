# Auswertung mit echten Werten und Operationstyp

Dieses Dokument beschreibt (1) das Vorgehen beim Rechnen mit echten Werten und (2) die konkrete Einbindung des optionalen Felds **operation** im Modell (JSON/RDF), in der API sowie die Semantik der Variablenrollen (z. B. „Zeile = H9, Spalte = I4“).

---

## Teil 1: Vorgehen beim Rechnen mit echten Werten

### Voraussetzungen

- **BVs in RDF:** Alle Berechnungsvorschriften sind mit `name`, `formel`, `variablen` (und optional `operation`) gespeichert.
- **Wertequelle:** Festlegung, woher die „echten Werte“ kommen:
  - **Primitive Variablen:** z. B. eine Tabelle/JSON pro BV oder global („Variable X = Wert Y“), oder pro Zellreferenz (z. B. H9 = „Facharbeiter“, I4 = „Bruttolohn“).
  - **Variable „Lohn_Tabelle“ (bei index_lookup):** Konkreter Datensatz für die Tabelle Lohn (Matrix/Liste von Zeilen mit Ausbildungsstand + Spaltenköpfen und Werten).
- **Referenzierte BVs:** Variablen mit `referenz_berechnungsvorschrift_id` bekommen ihren Wert aus dem **Ergebnis** der referenzierten BV (siehe unten).

### Ablauf (Schritte)

**Schritt 1 – Abhängigkeiten ermitteln**

- Pro BV: Welche Variablen sind primitiv, welche verweisen auf eine andere BV?
- Daraus einen **Abhängigkeitsgraphen**: „BV A nutzt BV B und BV C“ → A hängt von B und C ab.

**Schritt 2 – Reihenfolge (topologisch sortieren)**

- BVs so sortieren, dass zuerst BVs ohne Abhängigkeiten (nur primitive Variablen) kommen, dann die, die nur von bereits berechneten BVs abhängen, usw.
- So entsteht eine **Reihenfolge**, in der jede BV genau einmal ausgewertet werden kann, sobald alle „Vorgänger“ ein Ergebnis haben.

**Schritt 3 – Werte pro BV besorgen**

- Für jede BV in dieser Reihenfolge:
  - **Primitive Variable:** Wert aus der Wertequelle (z. B. „Ausbildungsstand“ = „Facharbeiter“, „Spaltenkopf“ = „Bruttolohn“, „Lohn_Tabelle“ = die echte Lohn-Matrix).
  - **Variable mit Referenz:** Wert = **bereits berechnetes Ergebnis** der referenzierten BV (wegen der Sortierung bereits vorhanden).
- Pro BV liegen damit für jede Variable konkrete Werte vor (Zahl, Text, Tabelle, …).

**Schritt 4 – BV auswerten (eine Regel pro Operationstyp)**

- **Ohne `operation` bzw. `operation = "ausdruck"`:**  
  Formel als Ausdruck interpretieren (z. B. „Jahresnettogehalt / 12“ → Division). Dafür ein **Ausdrucks-Interpreter**, der die Formel parst und mit den Variablenwerten rechnet (oder festes Format und nur dieses interpretieren).

- **Mit `operation = "index_lookup"`:**  
  **Eine** Funktion aufrufen: z. B. `lookup(Tabelle, Zeilenkriterium, Spaltenkriterium)` – Wert aus der Tabelle an der Zeile, wo die Zeilen-Spalte = Zeilenkriterium ist, und der Spalte, deren Header = Spaltenkriterium ist. Die drei Variablenwerte kommen aus Schritt 3; die **Rolle** jeder Variable (Tabelle vs. Zeilenkey vs. Spaltenkey) ist durch die Reihenfolge bzw. Konvention festgelegt (siehe Teil 3).

- **Mit `operation = "count_filter"`:**  
  COUNTIFS/SUM(COUNTIFS)-Logik: **Variablen** sind nur die Kriterienzellen (z. B. Kriterium_Angestelltenverhältnis, Kriterium_Monate). Für jede Tabelle in `operation_parameter.tabellen` zähle Zeilen, wo für alle Kriterien `Spalte[kriterienbereich_i] = Wert(Variable_i)` gilt. `Variable.kriterienbereich` definiert, welche Spalte pro Variable gefiltert wird. Bei `aggregation = "summe"` werden die Einzelzähler addiert (entspricht SUM(COUNTIFS(...))). Siehe Teil 4.

**Schritt 5 – Ergebnis speichern und weiterverwenden**

- Das Ergebnis dieser BV wird **pro BV-ID** gespeichert (z. B. Dictionary „BV-ID → Wert“).
- Alle BVs, die diese BV referenzieren, lesen in Schritt 3 genau diesen gespeicherten Wert.

**Wiederholung:** Schritte 3–5 für die **nächste** BV in der sortierten Reihenfolge, bis alle BVs ausgewertet sind.

### Beispiel (INDEX/MATCH)

- **BV „Lohnwert …“:** variablen = [Lohn_Tabelle, Ausbildungsstand, Spaltenkopf], `operation = "index_lookup"`.
- **Werte:** Lohn_Tabelle = echte Lohn-Tabelle, Ausbildungsstand = „Facharbeiter“, Spaltenkopf = „Bruttolohn“.
- **Auswertung:** Aufruf `lookup(Lohn_Tabelle, "Facharbeiter", "Bruttolohn")` → z. B. 3500. Diese Zahl ist das Ergebnis dieser BV.
- Jede andere BV, die auf diese BV verweist, bekommt in Schritt 3 den Wert 3500.

---

## Teil 2: Platzierung von `operation` im bestehenden Modell

### 2.1 JSON / Pydantic (Berechnungsvorschrift)

**Datei:** `backend/models/berechnungsvorschrift.py`

**Änderung:** Optionales Feld auf **Berechnungsvorschrift** (nicht auf Variable).

```python
# In class Berechnungsvorschrift:
operation: Optional[str] = Field(
    None,
    description="Auswertungstyp: 'ausdruck' (Default) = Formel als Ausdruck; 'index_lookup' = 2D-Tabellenlookup (Tabelle, Zeilenkey, Spaltenkey)"
)
```

- **Werte:** `"ausdruck"` | `"index_lookup"` | `"count_filter"` (COUNTIFS/SUM(COUNTIFS)).
- **Default:** `None` oder `"ausdruck"` – wenn fehlend, gilt Ausdruck-Auswertung.
- **Stellung:** Gleichrangig mit `name`, `formel`, `variablen`, `metadaten`; die BV beschreibt weiterhin *was* berechnet wird, `operation` sagt *wie* ausgewertet wird.

### 2.2 RDF

**Datei:** `backend/services/json_rdf_converter.py`

**Schreiben (`berechnungsvorschrift_to_rdf`):** Nach den Grunddaten (z. B. nach `hatVersion`) ein optionales Triple:

```python
# Operation (optional) – bestimmt die Auswertungsregel
if getattr(bv, 'operation', None):
    graph.add((bv_uri, property_uri("hatOperation"), Literal(bv.operation)))
```

**Lesen (`rdf_to_berechnungsvorschrift`):** Beim Extrahieren der BV-Attribute:

```python
operation_val = graph.value(bv_uri, property_uri("hatOperation"))
operation = str(operation_val) if operation_val else None
# ...
bv = Berechnungsvorschrift(
    ...
    operation=operation,
    ...
)
```

**Property-Name:** `hatOperation` (oder in der bestehenden Namenskonvention, z. B. `bv:hatOperation` über `property_uri("hatOperation")`).

**Rückwärtskompatibilität:** Fehlt `hatOperation` im Graph, bleibt `operation` im Modell `None` → Auswertung wie bisher als Ausdruck.

### 2.3 API

**Datei:** `backend/api/routes/berechnungsvorschriften.py`

- **GET** (einzelne BV, Liste): Response-Modell ist `Berechnungsvorschrift` – sobald das Pydantic-Modell `operation` enthält, erscheint das Feld automatisch in der JSON-Response. **Keine Route-Anpassung nötig.**
- **PUT** (Update): Body ist `Berechnungsvorschrift` – wenn der Client `operation` mitschickt, wird es mitgespeichert. **Keine Route-Anpassung nötig.**
- **POST** (Erstellen): Die BV kommt aus dem LLM und wird per `model_dump()` in die Response gepackt; gespeichert wird dieselbe BV. Sobald das **Modell** `operation` hat und das LLM (oder ein Post-Processing) es setzt, wird es persistiert. **Keine Route-Anpassung nötig**, sofern das Modell erweitert wird.

**Zusammenfassung API:** Einmal `operation` im Pydantic-Modell ergänzen – dann wird es über alle bestehenden Endpoints (GET/PUT/POST-Response) automatisch gelesen und geschrieben. Keine zusätzlichen Query-Parameter oder eigenen Endpoints nötig.

---

## Teil 3: Semantik „Zeile = H9, Spalte = I4“ – Anbindung an die Variablen

Für `operation = "index_lookup"` muss die Auswertung wissen: Welche Variable ist die **Tabelle**, welche das **Zeilenkriterium** (entspricht H9), welche das **Spaltenkriterium** (entspricht I4)?

### 3.1 Konvention: Reihenfolge der Variablen

**Festlegung:** Die **Reihenfolge** der Einträge in `variablen[]` definiert die Rolle:

| Position (0-basiert) | Rolle              | Bedeutung                          | Excel-Entsprechung      |
|----------------------|--------------------|------------------------------------|-------------------------|
| 0                    | Tabelle            | Datentabelle (Matrix/Reihe)        | INDEX(***Lohn[]***, …)  |
| 1                    | Zeilenkriterium    | Wert, nach dem die **Zeile** gesucht wird | ***H9*** (z. B. Ausbildungsstand) |
| 2                    | Spaltenkriterium   | Wert, nach dem die **Spalte** gesucht wird | ***I4*** (z. B. Spaltenkopf)      |

**Beispiel:**  
variablen = [  
  { "name": "Lohn_Tabelle", "ist_primitive": true },   ← Tabelle  
  { "name": "Ausbildungsstand", "ist_primitive": true }, ← Zeile = H9  
  { "name": "Spaltenkopf", "ist_primitive": true }    ← Spalte = I4  
]

Auswertung: `lookup(werte[Lohn_Tabelle], werte[Ausbildungsstand], werte[Spaltenkopf])`.

### 3.2 Alternative: Explizite Rollen auf der Variable (optional, später)

Falls die Reihenfolge nicht stabil ist (z. B. LLM liefert Variablen in wechselnder Reihenfolge), könnte man pro Variable optional eine **Rolle** speichern, z. B.:

- `variable.rolle`: `"tabelle"` | `"zeilenkriterium"` | `"spaltenkriterium"` (nur bei `operation = "index_lookup"` relevant).

Dann würde die Auswertung die Rolle statt der Position nutzen. Das würde das Variable-Modell und RDF erweitern (z. B. `hatVariableRolle`). **Empfehlung zunächst:** Reihenfolge-Konvention nutzen und im Prompt/Beispiel festhalten, dass bei INDEX/MATCH die Variablen in der Reihenfolge [Tabelle, Zeilenkriterium, Spaltenkriterium] stehen; bei Bedarf später Rollen ergänzen.

### 3.3 Prompt / LLM

In `backend/prompts/berechnungsvorschrift_prompt.txt` (und ggf. in `berechnungsvorschrift_beispiel.txt` bei INDEX/MATCH-Beispiel) explizit festhalten:

- Bei **index_lookup** (INDEX/MATCH) die Variablen **in dieser Reihenfolge** ausgeben:  
  1. Tabelle (z. B. Lohn_Tabelle),  
  2. Zeilenkriterium (z. B. Ausbildungsstand, entspricht H9),  
  3. Spaltenkriterium (z. B. Spaltenkopf, entspricht I4).

So ist die Semantik „Zeile = H9, Spalte = I4“ eindeutig an die Variablen geknüpft: H9 → zweite Variable (Zeilenkriterium), I4 → dritte Variable (Spaltenkriterium).

---

## Teil 4: operation = "count_filter" (COUNTIFS / SUM(COUNTIFS))

### 4.1 Variablen

Nur die **Kriterienzellen** (Zellreferenzen) sind Variablen – z. B. D3, E5 aus `'INTERN BEZÜGE'!D3` und `'INTERN BEZÜGE'!E5`. Tabellenspalten (Kriterienbereiche wie MAJahr1[Angestelltenverhältnis]) sind **keine** Variablen; sie dienen nur der Filterlogik.

Jede Variable hat optional:
- `kriterienbereich`: Spaltenname, auf den das Kriterium angewendet wird (z. B. "Angestelltenverhältnis")
- `vergleichsoperator`: "=" (Default), ">", "<", etc.
- `kriterienbereich_blatt`, `kriterienbereich_bereich`: Aufgelöste Excel-Bereiche (falls aus Referenz-Index verfügbar)

### 4.2 operation_parameter

```json
{
  "tabellen": ["MAJahr1", "MAJahr2", "MAJahr3"],
  "aggregation": "summe",
  "tabellen_bereiche": {
    "MAJahr1": {"blatt": "2. Arbeitszeit AW", "bereich": "B5:G20"},
    "MAJahr2": {"blatt": "2. Arbeitszeit AW", "bereich": "B25:G40"}
  }
}
```

- `tabellen`: Liste der Tabellen, die gezählt werden
- `aggregation`: "summe" (SUM der Einzelzählungen)
- `tabellen_bereiche`: Optional – aufgelöste Blatt+Bereich pro Tabelle (aus Excel-Referenz-Index)

### 4.3 Auswertung

Für jede Tabelle in `operation_parameter.tabellen`:
1. Lade die Tabellendaten (aus `tabellen_bereiche` oder externer Wertequelle)
2. Filtere Zeilen: Für jede Variable muss `Spalte[kriterienbereich] = Wert(Variable)` gelten (bzw. vergleichsoperator)
3. Zähle die gefilterten Zeilen

Summiere die Zähler aller Tabellen (bei `aggregation = "summe"`).

---

## Kurzfassung

| Bereich        | Platzierung von `operation` |
|----------------|-----------------------------|
| **JSON-Modell**| `Berechnungsvorschrift.operation: Optional[str]` (z. B. `"ausdruck"` \| `"index_lookup"` \| `"count_filter"`). |
| **RDF**        | Optionales Triple `bv_uri bv:hatOperation "..."`; `hatOperationParameter` (JSON) für count_filter. |
| **API**        | Keine Änderung der Routen nötig; Feld wird mit dem bestehenden Response/Body-Modell mitgeführt. |
| **Semantik**   | Bei `index_lookup`: Variable[0] = Tabelle, [1] = Zeilenkriterium, [2] = Spaltenkriterium. Bei `count_filter`: Nur Kriterienzellen = Variablen; `Variable.kriterienbereich` = gefilterte Spalte. |

Damit ist das Vorgehen für die Auswertung mit echten Werten dokumentiert und die Einbindung von `operation` sowie die Anbindung von „Zeile = H9, Spalte = I4“ an die Variablen konkret beschrieben.
