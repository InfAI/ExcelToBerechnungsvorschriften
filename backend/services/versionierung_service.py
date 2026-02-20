"""
Versionierungs-Service für Berechnungsvorschriften
"""
import logging
from datetime import datetime
from typing import Optional, List
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from models.berechnungsvorschrift import Berechnungsvorschrift
from services.rdf_service import RDFService

logger = logging.getLogger(__name__)


class VersionierungService:
    """Service für Versionsverwaltung von Berechnungsvorschriften"""
    
    def __init__(self, rdf_service: RDFService):
        """
        Initialisiert den Versionierungs-Service
        
        Args:
            rdf_service: RDF-Service für Datenbankzugriffe
        """
        self.rdf_service = rdf_service
    
    def erstelle_neue_version(
        self,
        alte_bv: Berechnungsvorschrift,
        aktualisierte_bv: Berechnungsvorschrift
    ) -> Berechnungsvorschrift:
        """
        Erstellt eine neue Version einer Berechnungsvorschrift
        
        Args:
            alte_bv: Alte Version der Berechnungsvorschrift
            aktualisierte_bv: Aktualisierte Berechnungsvorschrift
            
        Returns:
            Neue Version der Berechnungsvorschrift
        """
        logger.info(f"Erstelle neue Version für Berechnungsvorschrift {alte_bv.id}: "
                   f"Version {alte_bv.version} -> {alte_bv.version + 1}")
        # Neue Version-Nummer
        neue_version = alte_bv.version + 1
        logger.debug(f"Erstelle Version {neue_version} für {alte_bv.id} (vorherige Version: {alte_bv.version})")
        
        # Zeitstempel aktualisieren
        aktualisierte_bv.version = neue_version
        aktualisierte_bv.erstellt_am = alte_bv.erstellt_am  # Original-Erstellungszeit beibehalten
        aktualisierte_bv.geaendert_am = datetime.now()
        logger.debug(f"Zeitstempel aktualisiert: erstellt_am={aktualisierte_bv.erstellt_am}, geaendert_am={aktualisierte_bv.geaendert_am}")
        
        # ID bleibt gleich (gleiche Berechnungsvorschrift, neue Version)
        aktualisierte_bv.id = alte_bv.id
        
        # formel_original ist nur informativ und nicht bearbeitbar – bei Update beibehalten, falls nicht mitgesendet
        if not getattr(aktualisierte_bv, "formel_original", None) and getattr(alte_bv, "formel_original", None):
            aktualisierte_bv.formel_original = alte_bv.formel_original
            logger.debug("formel_original aus alter Version übernommen")
        
        logger.info(f"Neue Version erfolgreich erstellt: {aktualisierte_bv.id}, Version {aktualisierte_bv.version}")
        return aktualisierte_bv
    
    def lade_version(
        self,
        bv_id: str,
        version: Optional[int] = None
    ) -> Optional[Berechnungsvorschrift]:
        """
        Lädt eine spezifische Version einer Berechnungsvorschrift
        
        Args:
            bv_id: ID der Berechnungsvorschrift
            version: Versionsnummer (None für neueste Version)
            
        Returns:
            Berechnungsvorschrift oder None
        """
        logger.debug(f"Lade Version für {bv_id}: Version={version if version else 'neueste'}")
        # Aktuell wird nur die neueste Version gespeichert
        # In einer erweiterten Version könnte man alle Versionen speichern
        bv = self.rdf_service.lade_berechnungsvorschrift(bv_id)
        
        if not bv:
            logger.debug(f"Berechnungsvorschrift {bv_id} nicht gefunden")
            return None
        
        if version and bv.version != version:
            logger.warning(f"Angeforderte Version {version} für {bv_id} nicht verfügbar (aktuelle Version: {bv.version})")
            # Spezifische Version angefragt, aber nicht verfügbar
            # In einer erweiterten Version könnte man hier nach der Version suchen
            return None
        
        logger.debug(f"Version geladen: {bv_id}, Version {bv.version}")
        return bv
    
    def lade_alle_versionen(self, bv_id: str) -> List[Berechnungsvorschrift]:
        """
        Lädt alle Versionen einer Berechnungsvorschrift
        
        Args:
            bv_id: ID der Berechnungsvorschrift
            
        Returns:
            Liste aller Versionen (aktuell nur neueste Version)
        """
        logger.debug(f"Lade alle Versionen für {bv_id}")
        bv = self.rdf_service.lade_berechnungsvorschrift(bv_id)
        if bv:
            logger.debug(f"Gefunden: 1 Version für {bv_id} (Version {bv.version})")
            return [bv]
        logger.debug(f"Keine Versionen für {bv_id} gefunden")
        return []
