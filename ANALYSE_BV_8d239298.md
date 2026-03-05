# Analyse: Berechnungsvorschrift 8d239298 – zu kurzer Pseudocode und fehlende Variablen

## 1. Abruf der Daten aus Fuseki

```bash
docker compose exec middleware python -c "
from services.rdf_service import RDFService
rdf = RDFService()
bv = rdf.lade_berechnungsvorschrift('8d239298-08d2-41a8-9f78-8a69c4141a55')
# ... Ausgabe formel, formel_original, variablen
"
```

## 2. Ist-Zustand (generierte Ausgabe)

| Feld | Wert |
|------|------|
| **Name** | Anzahl MA – Vollzeit festangestellt |
| **Formel (Pseudocode)** | `Summe(Anzahl_MA_Vollzeit_1, Anzahl_MA_Vollzeit_2, Anzahl_MA_Vollzeit_3)` |
| **Formel (Excel, original)** | `=SUM(COUNTIFS(MAJahr1[Angestelltenverhältnis],'INTERN BEZÜGE'!$D$3,MAJahr1[Wie viele Monate des Jahres im Betrieb angestellt?],'INTERN BEZÜGE'!E5),COUNTIFS(MAJahr2[Angestelltenverhältnis],'INTERN BEZÜGE'!$D$3,MAJahr2[Wie viele Monate des Jahres im Betrieb angestellt?],'INTERN BEZÜGE'!E5),COUNTIFS(MAJahr3[Angestelltenverhältnis],'INTERN BEZÜGE'!$D$3,MAJahr3[Wie viele Monate des Jahres im Betrieb angestellt?],'INTERN BEZÜGE'!E5))` |
| **Variablen** | 3× `Anzahl_MA_Vollzeit_1/2/3` mit `zellenidentifikator=C10`, `tabellenblatt_referenz=2. Arbeitszeit AW` |

## 3. Analyse der Probleme

### 3.1 Falsche Variablen und fehlende Zellreferenzen

Die Excel-Formel referenziert **keine** Zelle C10 und kein Blatt „2. Arbeitszeit AW“ als Wertquelle. Tatsächliche Wertquellen:

| Referenz in Formel | Bedeutung | Soll-Variable |
|--------------------|-----------|---------------|
| `'INTERN BEZÜGE'!$D$3` | Kriterium „Angestelltenverhältnis“ (z.B. Vollzeit festangestellt) | `Angestelltenverhältnis` mit `zellenidentifikator=D3`, `tabellenblatt_referenz=INTERN BEZÜGE` |
| `'INTERN BEZÜGE'!E5` | Kriterium „Monate im Betrieb“ | `Monate_im_Betrieb` mit `zellenidentifikator=E5`, `tabellenblatt_referenz=INTERN BEZÜGE` |
| `MAJahr1[Angestelltenverhältnis]`, `MAJahr1[Wie viele Monate...]` | Tabellenspalten (Kriterienbereich) | – (keine eigene Variable, nur Filterlogik) |
| `MAJahr1`, `MAJahr2`, `MAJahr3` | Tabellen (Datenquellen) | Optional: Tabellen als Variablen, wenn gewünscht |

**C10 / 2. Arbeitszeit AW** ist falsch: Die Formel liegt in Zelle **B8** im Blatt „2. Arbeitszeit AW“. C10 gehört zu einem anderen Bereich (A21:G22). Das LLM hat vermutlich Zellen aus der Konfiguration verwechselt oder die Quelle falsch zugeordnet.

### 3.2 Zu kurzer Pseudocode

Der aktuelle Pseudocode `Summe(Anzahl_MA_Vollzeit_1, Anzahl_MA_Vollzeit_2, Anzahl_MA_Vollzeit_3)`:

- **Verschleiert die Logik**: Es fehlt die COUNTIFS-Filterlogik („gefiltert nach Angestelltenverhältnis und Monate“).
- **Ersetzt Ergebnis durch Platzhalter**: Die drei „Anzahl“-Werte sind die **Ergebnisse** der COUNTIFS, nicht die Eingabefaktoren.
- **Keine Verknüpfung zu Variablen**: Die Formel enthält keine Zellreferenzen (D3, E5) und keine Tabellenreferenzen (MAJahr1–3).

**Sinnvoller Pseudocode** (Beispiel):

```
Anzahl(MAJahr1, gefiltert nach Angestelltenverhältnis und Monate_im_Betrieb) + Anzahl(MAJahr2, gefiltert nach Angestelltenverhältnis und Monate_im_Betrieb) + Anzahl(MAJahr3, gefiltert nach Angestelltenverhältnis und Monate_im_Betrieb)
```

Mit Variablen: `Angestelltenverhältnis` (D3), `Monate_im_Betrieb` (E5) – beide aus `INTERN BEZÜGE`.

### 3.3 Gründe für die Fehler

1. **Komplexe Formelstruktur**: `SUM(COUNTIFS(...), COUNTIFS(...), COUNTIFS(...))` – verschachtelte Aggregationen.
2. **Unzureichende COUNTIFS-Beispiele**: Im Prompt gibt es COUNTIFS, aber nicht mit mehreren Kriterienpaaren und Cross-Sheet-Referenzen.
3. **Keine systematische Extraktion**: Es fehlt eine klare Anweisung, alle Zellreferenzen und Tabellenbezüge systematisch zu extrahieren.
4. **Verwechslung**: Formel-Zelle (B8) vs. referenzierte Zellen (D3, E5) vs. andere Konfigurationsbereiche (C10).

---

## 4. Verbesserungsvorschläge

### 4.1 Prompt-Anpassungen (berechnungsvorschrift_prompt.txt)

**a) Zellreferenz-Extraktion explizit machen**

```
VORHER: Generiere die Berechnungsvorschrift im JSON-Format.

NACHHER: SCHRITT 1 – Extraktion: Zähle alle Zellreferenzen in der Formel (z.B. $D$3, E5, 'INTERN BEZÜGE'!$D$3).
         Für jede Zellreferenz: zellenidentifikator setzen (ohne $), bei fremdem Blatt: tabellenblatt_referenz.
         SCHRITT 2 – Variablen: Jede Zellreferenz = genau eine Variable. Sprechende Namen aus Beschreibung/Kontext.
         SCHRITT 3 – Pseudocode: formel mit exakt diesen Variablennamen schreiben.
```

**b) COUNTIFS mit mehreren Kriterien und Cross-Sheet**

Ergänzung in den REGELN:

```
- COUNTIFS(Kriterienbereich1, Kriterium1, Kriterienbereich2, Kriterium2, ...):
  Jedes Kriterium, das eine Zellreferenz ist (z.B. 'Blatt'!D3, E5) → eigene Variable mit zellenidentifikator und tabellenblatt_referenz.
  Formel: "Anzahl(Tabelle, gefiltert nach Var1, Var2, ...)" – alle Variablennamen in variablen[].
  SUM(COUNTIFS(...), COUNTIFS(...)): "Anzahl(..., gefiltert) + Anzahl(..., gefiltert) + ..." – jede Kriteriumszelle wird Variable.
```

**c) Beispiel für SUM(COUNTIFS(...)) hinzufügen**

Neues Beispiel in `berechnungsvorschrift_beispiel.txt`:

```
BEISPIEL 8 – SUM(COUNTIFS(...)) mit Cross-Sheet-Kriterien

EINGABE:
Formel: =SUM(COUNTIFS(MAJahr1[Angestelltenverhältnis],'INTERN BEZÜGE'!$D$3,MAJahr1[Monate],'INTERN BEZÜGE'!E5), ...)

JSON:
{
  "formel": "Anzahl(MAJahr1, gefiltert nach Angestelltenverhältnis und Monate_im_Betrieb) + Anzahl(MAJahr2, gefiltert nach Angestelltenverhältnis und Monate_im_Betrieb) + Anzahl(MAJahr3, gefiltert nach Angestelltenverhältnis und Monate_im_Betrieb)",
  "variablen": [
    {"name": "Angestelltenverhältnis", "ist_primitive": true, "zellenidentifikator": "D3", "tabellenblatt_referenz": "INTERN BEZÜGE"},
    {"name": "Monate_im_Betrieb", "ist_primitive": true, "zellenidentifikator": "E5", "tabellenblatt_referenz": "INTERN BEZÜGE"}
  ]
}
```

### 4.2 Code-Erweiterungen

**a) Vorab-Extraktion der Zellreferenzen (formel_utils.py)**

```python
def zellreferenzen_aus_formel(formel: str) -> list[dict]:
    """
    Extrahiert alle Zellreferenzen aus einer Excel-Formel (z.B. D3, $D$3, 'Blatt'!E5).
    Returns: [{"zelle": "D3", "blatt": "INTERN BEZÜGE"}, ...]
    """
    # Regex für 'Blatt'!$A$1 oder 'Blatt'!A1
    # Regex für A1, $A$1 (ohne Blatt = gleiches Blatt)
    ...
```

**b) Validierung im LLM-Service**

Nach der LLM-Antwort: Zellreferenzen aus `formel_original` extrahieren und prüfen, ob jede Referenz in `variablen` eine passende Variable hat. Bei Abweichung: Log-Warnung oder optionale Nachbearbeitung.

**c) Optional: Zellreferenz-Hinweis im User-Prompt**

```python
# In llm_service.py: Vor dem User-Prompt
zellrefs = zellreferenzen_aus_formel(zelleneingabe.formel)
if zellrefs:
    hinweis = "\nHinweis: Die Formel enthält folgende Zellreferenzen (müssen alle als Variable mit zellenidentifikator/tabellenblatt_referenz abgebildet werden):\n"
    for r in zellrefs:
        hinweis += f"  - {r.get('zelle')} (Blatt: {r.get('blatt', 'gleiches Blatt')})\n"
    user_prompt += hinweis
```

### 4.3 Empfehlung zur Modellwahl

- **gpt-4.1-nano** ist für einfache Formeln geeignet, bei komplexen Strukturen (COUNTIFS, Cross-Sheet, verschachtelte Aggregationen) kann ein stärkeres Modell (z.B. gpt-4o-mini) bessere Ergebnisse liefern.
- **Temperatur**: Falls möglich, niedrigere Temperatur (z.B. 0.3) für konsistentere Extraktion.

---

## 5. Zusammenfassung

| Problem | Ursache | Vorschlag |
|--------|---------|-----------|
| Falsche Variablen (C10 statt D3, E5) | Verwechslung / Halluzination | Explizite Extraktionsschritte im Prompt; optional Vorab-Extraktion + Hinweis |
| Fehlende Zellreferenzen (D3, E5) | Cross-Sheet / COUNTIFS nicht abgedeckt | Beispiel + Regel für COUNTIFS mit mehreren Kriterien und Cross-Sheet |
| Zu kurzer Pseudocode | Fokus auf „Summe“ statt auf Filterlogik | Regel: COUNTIFS → „Anzahl(..., gefiltert nach Var1, Var2)“; Beispiel ergänzen |
| Tabellenblatt falsch (2. Arbeitszeit AW) | Zelle der Formel vs. referenzierte Zellen | Klarstellung: „Formel liegt in Zelle X – die referenzierten Zellen sind Y, Z“ |

Die vorgeschlagenen Änderungen sollten vor allem die **systematische Extraktion** aller Wertquellen und die **Abbildung von COUNTIFS** mit Cross-Sheet-Kriterien verbessern.
