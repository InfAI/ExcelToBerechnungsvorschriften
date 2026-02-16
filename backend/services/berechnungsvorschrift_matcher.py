"""
Berechnungsvorschrift-Matcher
Programmatische Prüfung auf bestehende Berechnungsvorschriften und Verlinkung von Variablen
"""
import logging
from typing import List, Optional, Tuple
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from models.berechnungsvorschrift import Berechnungsvorschrift, Variable
from services.rdf_service import RDFService

logger = logging.getLogger(__name__)


class BerechnungsvorschriftMatcher:
    """Matcher für bestehende Berechnungsvorschriften"""
    
    def __init__(self, rdf_service: RDFService):
        """
        Initialisiert den Matcher
        
        Args:
            rdf_service: RDF-Service für Datenbankzugriffe
        """
        self.rdf_service = rdf_service
    
    def finde_passende_berechnungsvorschriften(
        self,
        tabellenidentifikator: Optional[str],
        tabellenblatt: Optional[str],
        zellenidentifikator: Optional[str],
        beschreibung: Optional[str]
    ) -> List[Berechnungsvorschrift]:
        """
        Findet passende Berechnungsvorschriften basierend auf Matching-Kriterien
        
        Kriterien:
        - Tabellenidentifikator + Tabellenblatt + Zellenidentifikator müssen identisch sein
        - ODER Beschreibung ist identisch
        
        Args:
            tabellenidentifikator: Tabellenidentifikator
            tabellenblatt: Tabellenblatt
            zellenidentifikator: Zellenidentifikator
            beschreibung: Beschreibung
            
        Returns:
            Liste der passenden Berechnungsvorschriften
        """
        alle_bvs = self.rdf_service.lade_alle_berechnungsvorschriften()
        passende = []
        
        for bv in alle_bvs:
            # Kriterium 1: Tabellenidentifikator + Tabellenblatt + Zellenidentifikator identisch
            if (bv.quelle and
                bv.quelle.tabellenidentifikator == tabellenidentifikator and
                bv.quelle.tabellenblatt == tabellenblatt and
                bv.quelle.zellenidentifikator == zellenidentifikator):
                passende.append(bv)
                continue
            
            # Kriterium 2: Beschreibung identisch
            if (bv.quelle and
                bv.quelle.beschreibung and
                beschreibung and
                bv.quelle.beschreibung.strip().lower() == beschreibung.strip().lower()):
                passende.append(bv)
        
        logger.info(f"Gefunden: {len(passende)} passende Berechnungsvorschrift(en)")
        return passende
    
    def finde_bvs_mit_passender_variable(
        self,
        neue_bv: Berechnungsvorschrift
    ) -> List[Tuple[Berechnungsvorschrift, str]]:
        """
        Findet Berechnungsvorschriften, die eine primitive Variable haben, die auf die
        neu angelegte BV verlinkt werden kann (Rückwärts-Verlinkung).
        
        Matching (Priorität):
        1. Variable.zellenidentifikator == neue_bv.quelle.zellenidentifikator (und gleiches Blatt)
        2. Variable-Name stimmt mit neuer BV (Name oder Quelle-Beschreibung) überein.
        
        Returns:
            Liste von (Berechnungsvorschrift, Variablenname) die verlinkt werden können
        """
        if not neue_bv.id or not neue_bv.quelle:
            logger.debug("Rückwärts-Verlinkung: neue BV hat keine ID oder Quelle - überspringe")
            return []
        
        alle_bvs = self.rdf_service.lade_alle_berechnungsvorschriften()
        neue_name_lower = (neue_bv.name or "").strip().lower()
        neue_beschreibung_lower = (neue_bv.quelle.beschreibung or "").strip().lower() if neue_bv.quelle else ""
        neue_zelle = (neue_bv.quelle.zellenidentifikator or "").strip() if neue_bv.quelle else ""
        neue_tabelle = (neue_bv.quelle.tabellenidentifikator or "").strip() if neue_bv.quelle else ""
        neue_blatt = (neue_bv.quelle.tabellenblatt or "").strip() if neue_bv.quelle else ""
        ergebnis = []
        verlinkt_ids = set()  # Verhindert Dopplungen (BV, var.name)
        
        for bv in alle_bvs:
            if bv.id == neue_bv.id:
                continue
            for var in bv.variablen:
                if not var.ist_primitive and var.referenz_berechnungsvorschrift_id:
                    continue
                # 1. Priorität: Zellenidentifikator-Match (D7 in Variable ↔ D7 in neuer BV.quelle)
                # Zusätzlich: Tabellenidentifikator, Tabellenblatt (hatQuelleTabellenblatt)
                if neue_zelle and getattr(var, "zellenidentifikator", None):
                    var_zelle = (var.zellenidentifikator or "").strip()
                    if var_zelle and var_zelle.upper() == neue_zelle.upper():
                        bv_tabelle = (bv.quelle.tabellenidentifikator or "").strip() if bv.quelle else ""
                        bv_blatt = (bv.quelle.tabellenblatt or "").strip() if bv.quelle else ""
                        if (not neue_tabelle or bv_tabelle == neue_tabelle) and \
                           (not neue_blatt or bv_blatt == neue_blatt):
                            key = (bv.id, var.name)
                            if key not in verlinkt_ids:
                                verlinkt_ids.add(key)
                                ergebnis.append((bv, var.name))
                                logger.debug(f"Rückwärts-Match (Zelle+Blatt): BV {bv.id} Variable '{var.name}' ({var_zelle}) -> neue BV {neue_bv.id} ({neue_zelle})")
                            continue
                
                # 2. Fallback: Name/Symbol/Beschreibung-Match
                var_name_lower = (var.name or "").strip().lower()
                if not var_name_lower:
                    continue
                if (var_name_lower == neue_name_lower or
                    (neue_beschreibung_lower and var_name_lower in neue_beschreibung_lower) or
                    (neue_name_lower and neue_name_lower in var_name_lower)):
                    key = (bv.id, var.name)
                    if key not in verlinkt_ids:
                        verlinkt_ids.add(key)
                        ergebnis.append((bv, var.name))
                        logger.debug(f"Rückwärts-Match (Name): BV {bv.id} Variable '{var.name}' -> neue BV {neue_bv.id}")
        
        logger.info(f"Rückwärts-Verlinkung: {len(ergebnis)} Variable(n) in anderen BVs können zu {neue_bv.id} verlinkt werden")
        return ergebnis
    
    def verlinke_variablen(
        self,
        berechnungsvorschrift: Berechnungsvorschrift
    ) -> Tuple[Berechnungsvorschrift, List[Tuple[str, List[Berechnungsvorschrift]]]]:
        """
        Verlinkt Variablen zu bestehenden Berechnungsvorschriften.
        
        Matching-Strategie (Priorität):
        1. Variable mit zellenidentifikator (z.B. D7): Suche BV, deren Quelle die Zelle D7 ist
           (quelle.tabellenidentifikator + tabellenblatt + zellenidentifikator = D7). D7 und D8
           liegen im gleichen Blatt wie die Ausgabezelle (E8).
        2. Variable ohne zellenidentifikator (Tabellenspalte): Fallback auf Name/Symbol in Metadaten.
        
        Args:
            berechnungsvorschrift: Berechnungsvorschrift mit unverlinkten Variablen
            
        Returns:
            Tuple von (aktualisierte Berechnungsvorschrift, Liste von (Variablenname, [mehrere Treffer]))
            Die Liste enthält Variablen, für die mehrere Treffer gefunden wurden (Benutzer muss wählen)
        """
        aktualisierte_variablen = []
        mehrere_treffer = []
        
        # Kontext der Ausgabezelle (z.B. E8) – D7, D8 liegen im gleichen Blatt
        tabellenidentifikator = berechnungsvorschrift.quelle.tabellenidentifikator if berechnungsvorschrift.quelle else None
        tabellenblatt = berechnungsvorschrift.quelle.tabellenblatt if berechnungsvorschrift.quelle else None
        
        for var in berechnungsvorschrift.variablen:
            logger.debug(f"Suche passende Berechnungsvorschrift für Variable: {var.name}")
            passende = []
            
            # 1. Priorität: Zellenidentifikator + Tabellenidentifikator + Tabellenblatt
            if getattr(var, "zellenidentifikator", None) and var.zellenidentifikator.strip():
                passende = self.rdf_service.suche_nach_quelle(
                    tabellenidentifikator=tabellenidentifikator,
                    tabellenblatt=tabellenblatt,
                    zellenidentifikator=var.zellenidentifikator.strip()
                )
                if passende:
                    logger.debug(f"Variable '{var.name}' (Zelle {var.zellenidentifikator}): {len(passende)} Treffer via Zellenidentifikator")
            
            # 2. Fallback: Name/Symbol in Metadaten (Tabellenspalten, keine Zellreferenz)
            if not passende:
                passende = self.rdf_service.suche_nach_metadaten(
                    name=var.name,
                    symbol=var.name  # Symbol könnte auch passen
                )
                if passende:
                    logger.debug(f"Variable '{var.name}': {len(passende)} Treffer via Metadaten (Name/Symbol)")
            
            # Wenn genau eine Übereinstimmung gefunden wurde
            if len(passende) == 1:
                logger.debug(f"Variable '{var.name}' automatisch verlinkt zu {passende[0].id}")
                var.referenz_berechnungsvorschrift_id = passende[0].id
                var.ist_primitive = False
                aktualisierte_variablen.append(var)
            
            # Wenn mehrere Übereinstimmungen gefunden wurden
            elif len(passende) > 1:
                logger.info(f"Variable '{var.name}': {len(passende)} Treffer gefunden - Benutzer muss wählen")
                mehrere_treffer.append((var.name, passende))
                aktualisierte_variablen.append(var)
            
            # Wenn keine Übereinstimmung gefunden wurde
            else:
                logger.debug(f"Variable '{var.name}': Keine Treffer - bleibt primitiv")
                var.ist_primitive = True
                aktualisierte_variablen.append(var)
        
        # Aktualisierte Berechnungsvorschrift erstellen
        berechnungsvorschrift.variablen = aktualisierte_variablen
        
        logger.info(f"Variablen-Verlinkung abgeschlossen für {berechnungsvorschrift.id}: "
                   f"{len([v for v in aktualisierte_variablen if v.referenz_berechnungsvorschrift_id])} verlinkt, "
                   f"{len(mehrere_treffer)} mit mehreren Treffern")
        return berechnungsvorschrift, mehrere_treffer
    
    def verlinkung_aufheben(
        self,
        berechnungsvorschrift: Berechnungsvorschrift,
        variablenname: str
    ) -> Berechnungsvorschrift:
        """
        Hebt die Verlinkung einer Variable auf (Variable wird wieder primitiv).
        
        Args:
            berechnungsvorschrift: Berechnungsvorschrift
            variablenname: Name der Variable
            
        Returns:
            Aktualisierte Berechnungsvorschrift
        """
        logger.info(f"Verlinkung aufheben: Variable '{variablenname}' in {berechnungsvorschrift.id}")
        for var in berechnungsvorschrift.variablen:
            if var.name == variablenname:
                var.referenz_berechnungsvorschrift_id = None
                var.ist_primitive = True
                logger.debug(f"Variable '{variablenname}' ist wieder primitiv")
                break
        else:
            logger.warning(f"Variable '{variablenname}' nicht in Berechnungsvorschrift {berechnungsvorschrift.id} gefunden")
        
        return berechnungsvorschrift
    
    def verlinke_variable_manuell(
        self,
        berechnungsvorschrift: Berechnungsvorschrift,
        variablenname: str,
        referenz_id: str
    ) -> Berechnungsvorschrift:
        """
        Verlinkt eine Variable manuell zu einer spezifischen Berechnungsvorschrift
        
        Args:
            berechnungsvorschrift: Berechnungsvorschrift
            variablenname: Name der Variable
            referenz_id: ID der referenzierten Berechnungsvorschrift
            
        Returns:
            Aktualisierte Berechnungsvorschrift
        """
        logger.info(f"Manuelle Verlinkung: Variable '{variablenname}' in {berechnungsvorschrift.id} -> {referenz_id}")
        for var in berechnungsvorschrift.variablen:
            if var.name == variablenname:
                var.referenz_berechnungsvorschrift_id = referenz_id
                var.ist_primitive = False
                logger.debug(f"Variable '{variablenname}' erfolgreich verlinkt")
                break
        else:
            logger.warning(f"Variable '{variablenname}' nicht in Berechnungsvorschrift {berechnungsvorschrift.id} gefunden")
        
        return berechnungsvorschrift
    
    def pruefe_zirkulaere_abhaengigkeiten(
        self,
        berechnungsvorschrift: Berechnungsvorschrift,
        referenz_id: str
    ) -> bool:
        """
        Prüft, ob eine Verlinkung zu einer zirkulären Abhängigkeit führt
        
        Args:
            berechnungsvorschrift: Die Berechnungsvorschrift, die verlinkt werden soll
            referenz_id: ID der Berechnungsvorschrift, zu der verlinkt werden soll
            
        Returns:
            True wenn zirkuläre Abhängigkeit erkannt wird, sonst False
        """
        # Prüfe, ob die referenzierte Berechnungsvorschrift diese Berechnungsvorschrift referenziert
        if not berechnungsvorschrift.id:
            logger.debug(f"Neue Berechnungsvorschrift ohne ID - keine Zirkularitätsprüfung möglich")
            return False  # Neue Berechnungsvorschrift, noch keine ID
        
        logger.debug(f"Lade referenzierte Berechnungsvorschrift {referenz_id} für Zirkularitätsprüfung...")
        # Lade die referenzierte Berechnungsvorschrift
        referenz_bv = self.rdf_service.lade_berechnungsvorschrift(referenz_id)
        if not referenz_bv:
            logger.debug(f"Referenzierte Berechnungsvorschrift {referenz_id} nicht gefunden - keine Zirkularität")
            return False
        
        # Prüfe rekursiv, ob die referenzierte Berechnungsvorschrift diese referenziert
        logger.debug(f"Starte rekursive Zirkularitätsprüfung: {referenz_bv.id} -> {berechnungsvorschrift.id}")
        result = self._pruefe_rekursiv_zirkulaer(referenz_bv, berechnungsvorschrift.id, set())
        if result:
            logger.warning(f"Zirkuläre Abhängigkeit erkannt: {berechnungsvorschrift.id} <-> {referenz_id}")
        return result
    
    def _pruefe_rekursiv_zirkulaer(
        self,
        bv: Berechnungsvorschrift,
        ziel_id: str,
        besucht: set
    ) -> bool:
        """
        Rekursive Prüfung auf zirkuläre Abhängigkeiten
        
        Args:
            bv: Aktuelle Berechnungsvorschrift
            ziel_id: ID der Berechnungsvorschrift, die vermieden werden soll
            besucht: Set von bereits besuchten IDs (verhindert Endlosschleifen)
            
        Returns:
            True wenn zirkuläre Abhängigkeit gefunden wird
        """
        if bv.id == ziel_id:
            logger.debug(f"Zirkuläre Abhängigkeit gefunden: {bv.id} == {ziel_id}")
            return True  # Zirkuläre Abhängigkeit gefunden
        
        if bv.id in besucht:
            logger.debug(f"Bereits besucht: {bv.id} - keine Zirkularität in diesem Pfad")
            return False  # Bereits besucht, keine Zirkularität hier
        
        besucht.add(bv.id)
        logger.debug(f"Prüfe Berechnungsvorschrift {bv.id} (Ziel: {ziel_id}, Besucht: {len(besucht)} Knoten)")
        
        # Prüfe alle Variablen
        for var in bv.variablen:
            if var.referenz_berechnungsvorschrift_id and not var.ist_primitive:
                logger.debug(f"Prüfe Variable '{var.name}' -> {var.referenz_berechnungsvorschrift_id}")
                ref_bv = self.rdf_service.lade_berechnungsvorschrift(var.referenz_berechnungsvorschrift_id)
                if ref_bv:
                    if self._pruefe_rekursiv_zirkulaer(ref_bv, ziel_id, besucht):
                        return True
        
        logger.debug(f"Keine Zirkularität gefunden für {bv.id} -> {ziel_id}")
        return False
