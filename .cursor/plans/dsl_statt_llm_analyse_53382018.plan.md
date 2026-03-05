---
name: DSL statt LLM Analyse
overview: Analyse der LLM-Nutzung und Plan zur partiellen oder vollständigen Ersetzung durch eine Domain-Specific Language (DSL) mit Excel-Formel-Parser. Der LLM erfüllt heute sowohl deterministische (Formel-Struktur, Zellreferenzen) als auch semantische Aufgaben (Variablennamen, Metadaten). Eine DSL kann den Großteil übernehmen; für Variablennamen und Metadaten bleiben Hybrid-Optionen.
todos: []
isProject: false
---

# Plan: DSL statt LLM für Berechnungsvorschriften

## 1. Analyse: Was macht der LLM heute?

Der [LLMService](backend/services/llm_service.py) transformiert eine [Zelleneingabe](backend/models/zelleneingabe.py) (Tabellenidentifikator, Tabellenblatt, Zellenidentifikator, Beschreibung, Formel) in eine [Berechnungsvorschrift](backend/models/berechnungsvorschrift.py) (formel, variablen, metadaten, operation).

### 1.1 Deterministische Aufgaben (gut durch DSL ersetzbar)


| Aufgabe                               | Beispiel                                                           | Ersetzbarkeit             |
| ------------------------------------- | ------------------------------------------------------------------ | ------------------------- |
| Zellreferenzen extrahieren            | `=A1+B1` → variablen mit zellenidentifikator A1, B1                | 100% – Parser-basiert     |
| Cross-Sheet erkennen                  | `='1. Lohn AW'.G19` → tabellenblatt_referenz setzen                | 100% – Token-Typ prüfen   |
| Tabellenspalten erkennen              | `MAJahr1[Arbeitsstunden/Jahr]` → Variable ohne zellenidentifikator | 100% – Regex/Tokenizer    |
| Bereichsnotation auflösen             | `A1:A4` → 4 Variablen (B1, B2, B3, B4)                             | 100% – Parser             |
| IFERROR/IFNA weglassen                | Nur ersten Parameter nehmen                                        | 100% – AST-Transformation |
| operation="index_lookup" setzen       | Bei INDEX/MATCH-Pattern                                            | 100% – Funktionserkennung |
| Variablenreihenfolge bei index_lookup | [Tabelle, Zeilenkey, Spaltenkey]                                   | 100% – Konvention         |


### 1.2 Semantische Aufgaben (LLM-spezifisch)


| Aufgabe                                              | Beispiel                                                              | Ersetzbarkeit                  |
| ---------------------------------------------------- | --------------------------------------------------------------------- | ------------------------------ |
| **Variablennamen** aus Beschreibung                  | B1 bei "Monatliches Nettogehalt" → "Jahresnettogehalt"                | Schwierig – Kontextverständnis |
| **Metadaten** (kategorie, symbol, datentyp, einheit) | "Monatliches Nettogehalt" → kategorie=Gehalt, symbol=MNG, einheit=EUR | Schwierig – Domänenwissen      |


Die [Beispiele](backend/prompts/berechnungsvorschrift_beispiel.txt) zeigen: Der LLM leitet z.B. "Jahresnettogehalt" aus der Beschreibung "Monatliches Nettogehalt berechnen" und der Formel `=B1/12` ab – B1 ist der Divisor, also das Jahresgehalt. Das erfordert semantisches Verständnis.

---

## 2. Architektur-Überblick

```mermaid
flowchart TB
    subgraph heute [Aktuell: LLM-only]
        ZE[Zelleneingabe] --> LLM[LLM Service]
        LLM --> BV[Berechnungsvorschrift]
    end

    subgraph dsl [Mit DSL]
        ZE2[Zelleneingabe] --> Parser[Excel-Formel Parser]
        Parser --> AST[AST]
        AST --> DSL[DSL Transformer]
        DSL --> BVStruktur[BV-Struktur]
        BVStruktur --> NamenGen[Variablennamen-Generator]
        NamenGen --> BV2[Berechnungsvorschrift]
    end
```



---

## 3. DSL-Konzept

### 3.1 Zwei Ebenen

1. **Excel-Formel-DSL (Parsing)**: Excel-Formel → strukturierter AST
  - Nutzung: [formulas](https://formulas.readthedocs.io/) oder [openpyxl.formula.tokenizer](https://openpyxl.readthedocs.io/en/stable/formula.html)
  - Output: Liste von Referenzen (Zelle, Bereich, Tabelle, Cross-Sheet), Funktionsbaum (SUMME, AVERAGE, INDEX, MATCH, IFERROR, …)
2. **Transformations-DSL (Regeln)**: AST → Berechnungsvorschrift-Struktur
  - Regeln pro Excel-Funktion: z.B. `AVERAGE(a,b,c,d) → (a+b+c+d)/4`
  - Regeln für operation: `INDEX(..., MATCH(...), MATCH(...)) → index_lookup`
  - Zellreferenz → Variable mit zellenidentifikator; Tabellenspalte → Variable ohne zellenidentifikator

### 3.2 Variablennamen-Strategien (ohne LLM)


| Strategie                       | Beschreibung                                                                              | Vor-/Nachteile                                                              |
| ------------------------------- | ----------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| **A: Platzhalter**              | Namen = "Var_A1", "Var_B1" oder zellenidentifikator "A1", "B1"                            | Einfach, deterministisch; Matcher nutzt zellenidentifikator; weniger lesbar |
| **B: Beschreibung + Heuristik** | Beschreibung tokenisieren, z.B. "Material und Lohn" → A1="Material", B1="Lohn" bei =A1+B1 | Mittlerer Aufwand; funktioniert nur bei passender Beschreibung              |
| **C: Nutzer-Eingabe**           | UI: Pro Variable Namen eingeben oder aus Dropdown wählen                                  | Volle Kontrolle; mehr Aufwand pro Zelle                                     |
| **D: Hybrid**                   | DSL für Struktur, kleines LLM nur für Variablennamen (1–2 Sätze)                          | Geringerer Token-Verbrauch, LLM nur für semantische Teile                   |


### 3.3 Metadaten-Strategien (ohne LLM)


| Strategie            | Beschreibung                                                                                                         |
| -------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **Defaults**         | kategorie="Sonstiges", symbol="N/A", datentyp="decimal", einheit=""                                                  |
| **Nutzer-Kategorie** | Bereits unterstützt in [Zelleneingabe](backend/models/zelleneingabe.py); Lookup-Tabelle: Kategorie → symbol, einheit |
| **Konfiguration**    | Pro Tabellenblatt/Spalte Default-Metadaten in Excel-Import-Config                                                    |


---

## 4. Implementierungsplan

### Phase 1: Excel-Formel-Parser einbinden

- **formulas**-Bibliothek evaluieren (AST, unterstützte Funktionen) oder openpyxl Tokenizer
- Neues Modul: `backend/services/excel_formula_parser.py`
  - `parse_formula(formel: str) -> FormulaAST` (oder Token-Liste)
  - Extraktion: Zellreferenzen, Bereiche, Tabellenspalten, Cross-Sheet, Funktionsnamen + Argumente

### Phase 2: DSL-Transformer (Struktur ohne LLM)

- Neues Modul: `backend/services/dsl_transformer.py`
  - `transform_to_berechnungsvorschrift(ast, zelleneingabe) -> Berechnungsvorschrift`
  - Regeln für: SUMME, AVERAGE, IFERROR, SUMIFS, COUNTIFS, INDEX/MATCH
  - Variablen: zellenidentifikator, tabellenblatt_referenz aus AST
  - operation="index_lookup" bei INDEX/MATCH
  - Variablennamen: Strategie A (Platzhalter) initial

### Phase 3: Service-Strategie (LLM vs. DSL)

- Neues Interface: `BerechnungsvorschriftGenerator` (Protocol/ABC)
- Implementierungen: `LLMGenerator`, `DSLGenerator`
- Konfiguration (z.B. Umgebungsvariable `USE_DSL=true`) wählt Generator
- [API-Route](backend/api/routes/berechnungsvorschriften.py) nutzt den konfigurierten Generator

### Phase 4: Variablennamen verbessern (optional)

- Heuristik: Beschreibung parsen, Wörter mit Zellreihenfolge zuordnen (Strategie B)
- Oder: Hybrid – DSL für Struktur, reduzierter LLM-Call nur für Variablennamen + Metadaten

### Phase 5: Metadaten-Lookup (optional)

- Konfigurationsdatei: Kategorie → symbol, datentyp, einheit
- Nutzer-Kategorie (bereits vorhanden) als Key

---

## 5. Betroffene Dateien


| Datei                                                                                                      | Änderung                                                                 |
| ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| [backend/services/llm_service.py](backend/services/llm_service.py)                                         | Beibehalten als `LLMGenerator`; optional aus Konfiguration deaktivierbar |
| [backend/services/excel_formula_parser.py](backend/services/excel_formula_parser.py)                       | **Neu** – Excel-Formel → AST                                             |
| [backend/services/dsl_transformer.py](backend/services/dsl_transformer.py)                                 | **Neu** – AST → Berechnungsvorschrift                                    |
| [backend/services/berechnungsvorschrift_generator.py](backend/services/berechnungsvorschrift_generator.py) | **Neu** – Interface + Factory                                            |
| [backend/api/routes/berechnungsvorschriften.py](backend/api/routes/berechnungsvorschriften.py)             | Generator injizieren statt festem LLMService                             |
| [backend/requirements.txt](backend/requirements.txt)                                                       | `formulas` hinzufügen (falls gewählt)                                    |


---

## 6. Risiken und Einschränkungen

1. **Excel-Funktionen**: Die `formulas`-Bibliothek deckt nicht alle Excel-Funktionen ab. Unbekannte Funktionen → Fallback auf LLM oder Fehler.
2. **Variablennamen**: Ohne LLM weniger lesbar (Platzhalter). Akzeptanz prüfen.
3. **Metadaten**: Defaults können fachlich ungenau sein (z.B. falsche Einheit).
4. **Wartung**: Neue Excel-Funktionen erfordern neue DSL-Regeln.

---

## 7. Empfehlung

**Hybrid-Ansatz (Phase 1–3):**

- DSL für die gesamte **Struktur** (formel, variablen mit Referenzen, operation)
- Variablennamen zunächst als Platzhalter (`Var_A1` oder `zellenidentifikator`)
- Metadaten: Nutzer-Kategorie + Defaults für symbol/datentyp/einheit
- LLM als **Fallback**, wenn Parser/DSL scheitert (unbekannte Funktion, komplexe Formel)

Damit wird der LLM-Aufruf für den Großteil der Formeln vermieden; nur Randfälle und optionale Verbesserungen (sprechende Namen) nutzen weiterhin das LLM.