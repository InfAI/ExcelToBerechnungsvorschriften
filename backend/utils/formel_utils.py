"""
Hilfsfunktionen für Excel-Formeln
"""
import re

# Excel-interne Präfixe, die keine Named Ranges sind (z.B. _xlfn.IFS, _xlws.FILTER)
_EXCEL_PREFIX_PATTERN = re.compile(r"_xl(?:fn|ws|pm|op)\.")


def formel_excel_normalisieren(formel: str) -> str:
    """
    Entfernt Excel-interne Präfixe aus Formeln (z.B. _xlfn.IFS -> IFS).

    openpyxl/Excel liefert bei neueren Funktionen Formeln mit Präfixen wie
    _xlfn., _xlws., _xlpm., _xlop. für Abwärtskompatibilität. Diese sind keine
    Named Ranges und stören LLM-Auswertung sowie Matcher (Variable-Verlinkung).
    """
    if not formel:
        return ""
    return _EXCEL_PREFIX_PATTERN.sub("", formel)


def excel_identifikatoren_aus_formel(formel: str) -> set:
    """
    Extrahiert Excel-Named-Range-Identifikatoren aus formel_original (z.B. _1_Wert, _2_Wert).

    Schließt Excel-interne Präfixe aus (_xlfn, _xlws, _xlpm, _xlop), da diese
    keine Named Ranges sind.
    """
    if not formel:
        return set()
    gefunden = set(re.findall(r"_[\w]+", formel))
    # Excel-Funktionspräfixe ausschließen (keine Named Ranges)
    ausgeschlossen = {"_xlfn", "_xlws", "_xlpm", "_xlop"}
    return gefunden - ausgeschlossen


def zellreferenzen_aus_formel(formel: str) -> list[dict]:
    """
    Extrahiert alle Zellreferenzen aus einer Excel-Formel.

    Unterstützt:
    - Cross-Sheet: 'Blattname'!$A$1, 'Blattname'!A1
    - Same-Sheet: A1, $A$1, $A1, A$1

    Returns:
        Liste von {"zelle": "D3", "blatt": "INTERN BEZÜGE"} oder {"zelle": "A1", "blatt": None}
        (blatt=None bedeutet gleiches Blatt wie die Formel).
    """
    if not formel or not isinstance(formel, str):
        return []

    result = []
    seen = set()

    # Cross-Sheet: 'Blatt'!$A$1 oder 'Blatt'!A1 (Blattname in einfachen Anführungszeichen)
    # Pattern: '...'! optional $ Col $ Row
    cross_sheet_pattern = re.compile(
        r"'([^']+)'!\$?([A-Z]+)\$?(\d+)",
        re.IGNORECASE
    )
    for m in cross_sheet_pattern.finditer(formel):
        blatt = m.group(1).strip()
        col = m.group(2).upper()
        row = m.group(3)
        zelle = f"{col}{row}"
        key = (zelle, blatt)
        if key not in seen:
            seen.add(key)
            result.append({"zelle": zelle, "blatt": blatt})

    # Same-Sheet: A1, $A$1, $A1, A$1 (ohne Blatt-Präfix)
    # Vorsicht: Nicht in String-Literalen oder innerhalb von 'Blatt'!... matchen
    # Einfaches Pattern für Zellreferenz (Buchstaben + Zahlen)
    # Wir müssen Bereiche wie A1:A10 vermeiden – nur einzelne Zellen
    # Pattern für isolierte Zellref: (?:^|[\s,;\(\)\+\-\*\/=]) dann $?Col$?Row
    same_sheet_pattern = re.compile(
        r"(?:^|[\s,;\(\)\+\-\*\/=])(\$?[A-Z]+\$?\d+)(?=[\s,;\(\)\+\-\*\/\]\}]|$)",
        re.IGNORECASE
    )
    for m in same_sheet_pattern.finditer(formel):
        raw = m.group(1)
        # $ entfernen für normalisierte Form
        zelle = re.sub(r"\$", "", raw)
        # Prüfen, ob wir in einem Cross-Sheet-Kontext sind (nach '...'!)
        # Vereinfacht: Wenn die Formel ' enthält und wir kurz danach sind, könnte es Cross-Sheet sein
        # Unser cross_sheet_pattern hat bereits Cross-Sheet erfasst. Hier nur Same-Sheet.
        # Same-Sheet: Zelle ohne vorheriges '...'!
        start = m.start()
        # Prüfen ob vor uns ein '...'! kommt (ohne dazwischen)
        prefix = formel[:start]
        if re.search(r"'[^']*'!\s*$", prefix):
            # Wir sind direkt nach 'Blatt'! – also Cross-Sheet, schon erfasst
            continue
        key = (zelle, None)
        if key not in seen:
            seen.add(key)
            result.append({"zelle": zelle, "blatt": None})

    return result


def tabellenspalten_aus_formel(formel: str) -> list[dict]:
    """
    Extrahiert Tabellenspalten-Referenzen aus einer Excel-Formel (z.B. MAJahr1[Angestelltenverhältnis]).

    Returns:
        Liste von {"tabelle": "MAJahr1", "spalte": "Angestelltenverhältnis"}
        (#headers und leere Spalten werden ausgeschlossen)
    """
    if not formel or not isinstance(formel, str):
        return []

    result = []
    seen = set()

    # Pattern: TableName[ColumnName] – Tabelle und Spalte können Sonderzeichen enthalten
    # z.B. MAJahr1[Angestelltenverhältnis], MAJahr1[Wie viele Monate des Jahres im Betrieb angestellt?]
    tabellen_pattern = re.compile(
        r"\b([A-Za-z_][\w]*)\[([^\]#]+)\]",
        re.IGNORECASE
    )
    for m in tabellen_pattern.finditer(formel):
        tabelle = m.group(1).strip()
        spalte = m.group(2).strip()
        # #headers und ähnliche Excel-Sonderbereiche ausschließen
        if spalte.startswith("#") or not spalte:
            continue
        key = (tabelle, spalte)
        if key not in seen:
            seen.add(key)
            result.append({"tabelle": tabelle, "spalte": spalte})

    return result
