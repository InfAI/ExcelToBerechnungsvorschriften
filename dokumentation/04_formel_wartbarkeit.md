# Formel-Wartbarkeit für Nichtinformatiker

## Ziel

Berechnungsvorschriften sollen von Fachverantwortlichen ohne Programmierkenntnisse verstanden und gepflegt werden können. Dafür sind klare Pseudocode-Regeln und geeignete UI-Unterstützung erforderlich.

## Pseudocode-Regeln

Die Formel (Pseudocode) folgt folgenden Regeln:

| Regel | Beschreibung |
|-------|--------------|
| **Sprechende Variablennamen** | Statt „A1“ oder „B5“ werden lesbare Namen verwendet (z.B. „Jahresnettogehalt“) |
| **Keine Excel-Syntax** | Kein „=“, keine Zellreferenzen, keine Bereichsnotation |
| **Keine Kommentare** | Der Pseudocode enthält keine Kommentare – die Lesbarkeit kommt aus den Variablennamen |
| **Excel-Funktionen vereinfacht** | SUMME → Addition, WENN → „Wenn … dann … sonst …“, MITTELWERT → Division |

**Beispiele:**

- `=A1/12` → `Jahresnettogehalt/12`
- `=SUMME(B1:B10)` → `Wert1 + Wert2 + … + Wert10` (mit sprechenden Variablennamen)
- `=WENN(C1>0;D1;0)` → `Wenn Bedingung dann Wert1 sonst 0`

## Unterstützung für Nichtinformatiker

Die Anwendung (IAK Farmaxis) sollte folgende Hilfen bieten:

1. **Variablen erkennbar und anklickbar**  
   Variablen im Formel-Text sind hervorgehoben und führen per Klick zur referenzierten Berechnungsvorschrift.

2. **Metadaten sichtbar**  
   Beim Hover oder in einer Sidebar: Kategorie, Symbol, Einheit der Variablen und der aktuellen BV.

3. **Abhängigkeiten visualisieren**  
   Listen „Verwendet folgende Berechnungsvorschriften“ und „Wird verwendet in“ mit anklickbarer Navigation.

4. **Validierung**  
   Variablen im Formel-String müssen in der Variablen-Liste existieren – Fehlermeldung bei Abweichung.

## Optionen für den Formel-Editor

| Option | Beschreibung | Vor-/Nachteile |
|--------|--------------|----------------|
| **Freitext mit Validierung** | Benutzer tippt Formel, System prüft Variablennamen | Flexibel, erfordert Kenntnis der exakten Variablennamen |
| **Strukturierter Editor** | Variablen als Chips/Badges einfügbar | Weniger Tippfehler, evtl. weniger flexibel |

Die Wahl hängt von der Zielgruppe und den typischen Bearbeitungsszenarien ab.
