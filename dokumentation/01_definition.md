# Definition: Berechnungsvorschriften

## Was ist eine Berechnungsvorschrift?

Eine **Berechnungsvorschrift** ist ein strukturiertes Objekt, das die Berechnung eines Wertes beschreibt. Sie besteht aus:

| Bestandteil | Beschreibung |
|-------------|--------------|
| **Name** | Bezeichnung der Berechnungsvorschrift (z.B. „monatliches Nettogehalt“) |
| **Formel** | Menschenlesbarer Pseudocode (keine Excel-Syntax) |
| **Variablen** | Liste der Wertquellen, die in die Formel einfließen |
| **Metadaten** | Kategorie, Symbol, Datentyp, Einheit |
| **Quelle** | Optionale Referenz zur ursprünglichen Excel-Zelle (für Matching) |
| **Version** | Versionsnummer (wird bei Änderung erhöht) |

## Variablen

Jede Wertquelle in der Formel wird als **Variable** abgebildet:

- **Primitive Variable** (`ist_primitive = true`): Einfacher Eingabewert (z.B. Zelle, Spalte). Keine Referenz auf eine andere Berechnungsvorschrift.
- **Verlinkte Variable** (`ist_primitive = false`): Verweist auf eine andere Berechnungsvorschrift. Der Wert wird aus der referenzierten Berechnungsvorschrift ermittelt.

Der Variablenname muss exakt mit dem Namen im Formel-String übereinstimmen (Verlinkbarkeit, Auswertung).

## Abhängigkeiten

Für jede Berechnungsvorschrift werden zwei Listen geführt:

- **„Verwendet folgende Berechnungsvorschriften“**: Alle BVs, die im Pseudocode dieser Berechnungsvorschrift vorkommen (anklickbar zur Navigation).
- **„Wird verwendet in“**: Alle BVs, die diese Berechnungsvorschrift referenzieren.

## Pseudocode

Die Formel wird als **Pseudocode** statt als Excel-Syntax dargestellt:

- Sprechende Variablennamen (z.B. „Jahresnettogehalt“ statt „B1“)
- Keine Zellreferenzen, kein „=“, keine Bereichsnotation
- Keine Kommentare im Pseudocode
- Excel-Funktionen werden in lesbare Form umgewandelt (z.B. SUMME → Addition)

**Beispiel:**  
Excel: `=B1/12` → Pseudocode: `Jahresnettogehalt/12`

## Abhängigkeitsgraph

Die Abhängigkeiten zwischen Berechnungsvorschriften lassen sich als Graph darstellen:

![Abhängigkeitsgraph](diagramme/abhaendigkeiten.png)

*Für die vollständige Darstellung: `./diagramme/render.sh` ausführen (Graphviz erforderlich).*
