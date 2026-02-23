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
