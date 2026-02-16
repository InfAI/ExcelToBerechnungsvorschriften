"""
RDF-Service für Jena Fuseki SPARQL-Operationen
"""
import os
import logging
from typing import List, Optional, Dict, Any
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from models.berechnungsvorschrift import Berechnungsvorschrift
from services.json_rdf_converter import JSONRDFConverter
from utils.rdf_helper import BV, berechnungsvorschrift_uri, get_namespace_iri

# Logger konfigurieren
logger = logging.getLogger(__name__)


class RDFService:
    """Service für RDF-Operationen mit Jena Fuseki"""
    
    def __init__(self):
        """Initialisiert den RDF-Service"""
        fuseki_url = os.getenv("FUSEKI_URL", "http://fuseki:3030")
        dataset = os.getenv("FUSEKI_DATASET", "berechnungsvorschriften")
        
        self.sparql_endpoint = f"{fuseki_url}/{dataset}/sparql"
        self.update_endpoint = f"{fuseki_url}/{dataset}/update"
        self.converter = JSONRDFConverter()
        
        # Credentials aus Environment-Variablen laden
        self.fuseki_user = os.getenv("FUSEKI_USER", "admin")
        self.fuseki_password = os.getenv("FUSEKI_PASSWORD", "")
        
        # Debug: Prüfe ob Credentials geladen wurden (ohne Passwort zu loggen)
        if self.fuseki_user and self.fuseki_password:
            logger.info(f"RDFService initialisiert - SPARQL: {self.sparql_endpoint}, Update: {self.update_endpoint}, User: {self.fuseki_user}, Password gesetzt: {'Ja' if self.fuseki_password else 'Nein'}")
        else:
            logger.warning(f"RDFService initialisiert ohne vollständige Credentials - User: '{self.fuseki_user}', Password gesetzt: {'Ja' if self.fuseki_password else 'Nein'}")
    
    def _get_sparql_client(self) -> SPARQLWrapper:
        """Erstellt einen SPARQL-Client mit Authentifizierung"""
        client = SPARQLWrapper(self.sparql_endpoint)
        client.setReturnFormat(JSON)
        # Credentials setzen, falls vorhanden
        if self.fuseki_user and self.fuseki_password:
            client.setCredentials(self.fuseki_user, self.fuseki_password)
            logger.debug(f"SPARQL-Client erstellt mit Credentials für User: {self.fuseki_user}")
        else:
            logger.warning("SPARQL-Client erstellt OHNE Credentials - Authentifizierung wird fehlschlagen")
        return client
    
    def _get_update_client(self) -> SPARQLWrapper:
        """Erstellt einen SPARQL-Update-Client mit Authentifizierung"""
        client = SPARQLWrapper(self.update_endpoint)
        client.setMethod("POST")
        client.setRequestMethod("urlencoded")
        # Credentials setzen, falls vorhanden
        if self.fuseki_user and self.fuseki_password:
            client.setCredentials(self.fuseki_user, self.fuseki_password)
            logger.debug(f"Update-Client erstellt mit Credentials für User: {self.fuseki_user}")
        else:
            logger.warning("Update-Client erstellt OHNE Credentials - Authentifizierung wird fehlschlagen")
        return client
    
    def speichere_berechnungsvorschrift(self, bv: Berechnungsvorschrift) -> None:
        """
        Speichert eine Berechnungsvorschrift in Fuseki
        
        Args:
            bv: Berechnungsvorschrift
        """
        if not bv.id:
            raise ValueError("Berechnungsvorschrift muss eine ID haben")
        
        logger.info(f"Speichere Berechnungsvorschrift: ID={bv.id}, Name={bv.name}, Version={bv.version}")
        
        # Zuerst alte Version löschen (falls vorhanden) - nur wenn ID existiert
        try:
            logger.debug(f"Lösche alte Version der Berechnungsvorschrift {bv.id} (falls vorhanden)")
            self.loesche_berechnungsvorschrift(bv.id)
            logger.debug(f"Alte Version von {bv.id} erfolgreich gelöscht")
        except Exception as e:
            logger.debug(f"Keine alte Version von {bv.id} gefunden oder Fehler beim Löschen (wird ignoriert): {type(e).__name__}: {e}")
        
        # Zu RDF konvertieren
        logger.debug(f"Konvertiere Berechnungsvorschrift {bv.id} zu RDF")
        graph = self.converter.berechnungsvorschrift_to_rdf(bv)
        logger.debug(f"RDF-Graph erstellt: {len(graph)} Triples")
        
        # Verwende RDF-Graph Serialisierung für zuverlässigere Einfügung
        # RDF-Graph zu N-Triples serialisieren
        rdf_nt = graph.serialize(format="nt")
        
        # SPARQL INSERT-Query mit N-Triples
        insert_query = f"""
        INSERT DATA {{
            {rdf_nt}
        }}
        """
        
        # Update ausführen
        logger.debug(f"Führe SPARQL INSERT für {bv.id} aus (N-Triples Format)")
        client = self._get_update_client()
        client.setQuery(insert_query)
        try:
            client.query()
            logger.info(f"Berechnungsvorschrift {bv.id} erfolgreich gespeichert (N-Triples)")
        except Exception as e:
            logger.warning(f"N-Triples INSERT fehlgeschlagen für {bv.id}: {type(e).__name__}: {e}. Versuche Turtle-Format...")
            # Wenn N-Triples nicht funktioniert, versuche Turtle
            rdf_turtle = graph.serialize(format="turtle")
            namespace_iri = get_namespace_iri()
            insert_query = f"""
            PREFIX bv: <{namespace_iri}>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            
            INSERT DATA {{
                {rdf_turtle}
            }}
            """
            client.setQuery(insert_query)
            try:
                client.query()
                logger.info(f"Berechnungsvorschrift {bv.id} erfolgreich gespeichert (Turtle Format)")
            except Exception as e2:
                logger.error(f"SPARQL INSERT fehlgeschlagen für {bv.id} (beide Formate): {type(e2).__name__}: {e2}")
                raise
    
    def lade_berechnungsvorschrift(self, bv_id: str) -> Optional[Berechnungsvorschrift]:
        """
        Lädt eine Berechnungsvorschrift aus Fuseki
        
        Args:
            bv_id: ID der Berechnungsvorschrift
            
        Returns:
            Berechnungsvorschrift oder None
        """
        logger.debug(f"Lade Berechnungsvorschrift: ID={bv_id}")
        namespace_iri = get_namespace_iri()
        bv_uri_full = berechnungsvorschrift_uri(bv_id)
        query = f"""
        PREFIX bv: <{namespace_iri}>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        CONSTRUCT {{
            ?bv ?p ?o .
            ?var ?vp ?vo .
        }}
        WHERE {{
            BIND(<{bv_uri_full}> AS ?bv)
            ?bv rdf:type bv:Berechnungsvorschrift .
            OPTIONAL {{
                ?bv bv:hatVariable ?var .
                ?var ?vp ?vo .
            }}
            ?bv ?p ?o .
        }}
        """
        
        client = self._get_sparql_client()
        client.setQuery(query)
        client.setReturnFormat("turtle")
        
        try:
            result = client.queryAndConvert()
            if not result or len(str(result).strip()) == 0:
                return None
            
            # RDF-Graph erstellen
            graph = Graph()
            graph.parse(data=result, format="turtle")
            
            # Prüfe ob Graph leer ist
            if len(graph) == 0:
                logger.debug(f"Keine Daten für Berechnungsvorschrift {bv_id} gefunden")
                return None
            
            # Zu Berechnungsvorschrift konvertieren
            logger.debug(f"Konvertiere RDF-Graph zu Berechnungsvorschrift für {bv_id}")
            bv = self.converter.rdf_to_berechnungsvorschrift(graph, bv_id)
            logger.info(f"Berechnungsvorschrift {bv_id} erfolgreich geladen: Name={bv.name}")
            return bv
        except Exception as e:
            logger.error(f"Fehler beim Laden der Berechnungsvorschrift {bv_id}: {type(e).__name__}: {e}", exc_info=True)
            return None
    
    def lade_alle_berechnungsvorschriften(self) -> List[Berechnungsvorschrift]:
        """
        Lädt alle Berechnungsvorschriften aus Fuseki
        
        Returns:
            Liste aller Berechnungsvorschriften
        """
        namespace_iri = get_namespace_iri()
        # Escape für Regex: Namespace muss escaped werden für REPLACE
        # Extrahiere die ID aus der URI (alles nach dem letzten /)
        query = f"""
        PREFIX bv: <{namespace_iri}>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT DISTINCT ?bv_id
        WHERE {{
            ?bv rdf:type bv:Berechnungsvorschrift .
            BIND(REPLACE(STR(?bv), ".*berechnungsvorschrift/", "") AS ?bv_id)
        }}
        """
        
        client = self._get_sparql_client()
        client.setQuery(query)
        
        try:
            results = client.queryAndConvert()
            
            berechnungsvorschriften = []
            if "results" in results and "bindings" in results["results"]:
                for result in results["results"]["bindings"]:
                    bv_id = result["bv_id"]["value"]
                    bv = self.lade_berechnungsvorschrift(bv_id)
                    if bv:
                        berechnungsvorschriften.append(bv)
            
            return berechnungsvorschriften
        except Exception as e:
            logger.error(f"Fehler beim Laden aller Berechnungsvorschriften: {type(e).__name__}: {e}", exc_info=True)
            return []
    
    def suche_nach_metadaten(
        self,
        name: Optional[str] = None,
        kategorie: Optional[str] = None,
        symbol: Optional[str] = None,
        datentyp: Optional[str] = None,
        einheit: Optional[str] = None
    ) -> List[Berechnungsvorschrift]:
        """
        Sucht Berechnungsvorschriften nach Metadaten
        
        Args:
            name: Name (optional)
            kategorie: Kategorie (optional)
            symbol: Symbol (optional)
            datentyp: Datentyp (optional)
            einheit: Einheit (optional)
            
        Returns:
            Liste der gefundenen Berechnungsvorschriften
        """
        conditions = []
        
        # Helper-Funktion zum Escapen von SPARQL-Strings
        def escape_sparql_string(s):
            return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        
        if name:
            conditions.append(f'?bv bv:hatName "{escape_sparql_string(name)}"')
        if kategorie:
            conditions.append(f'?bv bv:hatKategorie "{escape_sparql_string(kategorie)}"')
        if symbol:
            conditions.append(f'?bv bv:hatSymbol "{escape_sparql_string(symbol)}"')
        if datentyp:
            conditions.append(f'?bv bv:hatDatentyp "{escape_sparql_string(datentyp)}"')
        if einheit:
            conditions.append(f'?bv bv:hatEinheit "{escape_sparql_string(einheit)}"')
        
        if not conditions:
            return self.lade_alle_berechnungsvorschriften()
        
        where_clause = " . ".join(conditions)
        namespace_iri = get_namespace_iri()
        
        query = f"""
        PREFIX bv: <{namespace_iri}>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT DISTINCT ?bv_id
        WHERE {{
            ?bv rdf:type bv:Berechnungsvorschrift .
            {where_clause} .
            BIND(REPLACE(STR(?bv), ".*berechnungsvorschrift/", "") AS ?bv_id)
        }}
        """
        
        client = self._get_sparql_client()
        client.setQuery(query)
        
        try:
            results = client.queryAndConvert()
            
            berechnungsvorschriften = []
            if "results" in results and "bindings" in results["results"]:
                for result in results["results"]["bindings"]:
                    bv_id = result["bv_id"]["value"]
                    bv = self.lade_berechnungsvorschrift(bv_id)
                    if bv:
                        berechnungsvorschriften.append(bv)
            
            return berechnungsvorschriften
        except Exception as e:
            logger.error(f"Fehler bei Suche nach Metadaten: {type(e).__name__}: {e}", exc_info=True)
            return []
    
    def suche_nach_quelle(
        self,
        tabellenidentifikator: Optional[str] = None,
        tabellenblatt: Optional[str] = None,
        zellenidentifikator: Optional[str] = None
    ) -> List[Berechnungsvorschrift]:
        """
        Sucht Berechnungsvorschriften nach Quelle (Quellzelle).
        Matching über hatQuelleTabellenidentifikator, hatQuelleTabellenblatt, hatQuelleZellenidentifikator.
        
        Args:
            tabellenidentifikator: Tabellenidentifikator (optional)
            tabellenblatt: Tabellenblatt (optional)
            zellenidentifikator: Zellenidentifikator (z.B. D7, A9) – erforderlich
            
        Returns:
            Liste der gefundenen Berechnungsvorschriften
        """
        if not zellenidentifikator:
            return []
        
        def escape_sparql_string(s):
            return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        
        conditions = [
            f'?bv bv:hatQuelleZellenidentifikator "{escape_sparql_string(zellenidentifikator.strip())}"'
        ]
        if tabellenidentifikator:
            conditions.append(f'?bv bv:hatQuelleTabellenidentifikator "{escape_sparql_string(tabellenidentifikator)}"')
        if tabellenblatt:
            conditions.append(f'?bv bv:hatQuelleTabellenblatt "{escape_sparql_string(tabellenblatt)}"')
        
        where_clause = " . ".join(conditions)
        namespace_iri = get_namespace_iri()
        
        query = f"""
        PREFIX bv: <{namespace_iri}>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT DISTINCT ?bv_id
        WHERE {{
            ?bv rdf:type bv:Berechnungsvorschrift .
            {where_clause} .
            BIND(REPLACE(STR(?bv), ".*berechnungsvorschrift/", "") AS ?bv_id)
        }}
        """
        
        client = self._get_sparql_client()
        client.setQuery(query)
        
        try:
            results = client.queryAndConvert()
            berechnungsvorschriften = []
            if "results" in results and "bindings" in results["results"]:
                for result in results["results"]["bindings"]:
                    bv_id = result["bv_id"]["value"]
                    bv = self.lade_berechnungsvorschrift(bv_id)
                    if bv:
                        berechnungsvorschriften.append(bv)
            logger.debug(f"Suche nach Quelle {zellenidentifikator} (Blatt={tabellenblatt}): {len(berechnungsvorschriften)} Treffer")
            return berechnungsvorschriften
        except Exception as e:
            logger.error(f"Fehler bei Suche nach Quelle: {type(e).__name__}: {e}", exc_info=True)
            return []
    
    def finde_verwendet_in(self, bv_id: str) -> List[Berechnungsvorschrift]:
        """
        Findet alle Berechnungsvorschriften, die diese Berechnungsvorschrift referenzieren
        
        Args:
            bv_id: ID der Berechnungsvorschrift
            
        Returns:
            Liste der referenzierenden Berechnungsvorschriften
        """
        namespace_iri = get_namespace_iri()
        bv_uri_full = berechnungsvorschrift_uri(bv_id)
        query = f"""
        PREFIX bv: <{namespace_iri}>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT DISTINCT ?ref_bv_id
        WHERE {{
            ?ref_bv rdf:type bv:Berechnungsvorschrift .
            ?ref_bv bv:hatVariable ?var .
            ?var bv:referenziertBerechnungsvorschrift <{bv_uri_full}> .
            BIND(REPLACE(STR(?ref_bv), ".*berechnungsvorschrift/", "") AS ?ref_bv_id)
        }}
        """
        
        client = self._get_sparql_client()
        client.setQuery(query)
        
        try:
            results = client.queryAndConvert()
            
            berechnungsvorschriften = []
            if "results" in results and "bindings" in results["results"]:
                for result in results["results"]["bindings"]:
                    ref_bv_id = result["ref_bv_id"]["value"]
                    bv = self.lade_berechnungsvorschrift(ref_bv_id)
                    if bv:
                        berechnungsvorschriften.append(bv)
            
            return berechnungsvorschriften
        except Exception as e:
            logger.error(f"Fehler beim Finden von 'verwendet in' für {bv_id}: {type(e).__name__}: {e}", exc_info=True)
            return []
    
    def finde_verwendet(self, bv_id: str) -> List[Berechnungsvorschrift]:
        """
        Findet alle Berechnungsvorschriften, die im Pseudocode dieser Berechnungsvorschrift vorkommen
        
        Args:
            bv_id: ID der Berechnungsvorschrift
            
        Returns:
            Liste der referenzierten Berechnungsvorschriften
        """
        bv = self.lade_berechnungsvorschrift(bv_id)
        if not bv:
            return []
        
        referenzierte = []
        for var in bv.variablen:
            if var.referenz_berechnungsvorschrift_id and not var.ist_primitive:
                ref_bv = self.lade_berechnungsvorschrift(var.referenz_berechnungsvorschrift_id)
                if ref_bv:
                    referenzierte.append(ref_bv)
        
        return referenzierte
    
    def loesche_berechnungsvorschrift(self, bv_id: str) -> None:
        """
        Löscht eine Berechnungsvorschrift aus Fuseki
        
        Args:
            bv_id: ID der Berechnungsvorschrift
        """
        logger.info(f"Lösche Berechnungsvorschrift: ID={bv_id}")
        logger.debug(f"Update-Endpoint: {self.update_endpoint}")
        
        namespace_iri = get_namespace_iri()
        bv_uri_full = berechnungsvorschrift_uri(bv_id)
        query = f"""
        PREFIX bv: <{namespace_iri}>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        DELETE {{
            ?bv ?p ?o .
            ?var ?vp ?vo .
        }}
        WHERE {{
            BIND(<{bv_uri_full}> AS ?bv)
            ?bv rdf:type bv:Berechnungsvorschrift .
            OPTIONAL {{
                ?bv bv:hatVariable ?var .
                ?var ?vp ?vo .
            }}
            ?bv ?p ?o .
        }}
        """
        
        logger.debug(f"SPARQL DELETE Query für {bv_id} erstellt")
        client = self._get_update_client()
        logger.debug(f"SPARQL Update-Client erstellt, Methode: POST, Request-Methode: urlencoded")
        client.setQuery(query)
        
        try:
            logger.debug(f"Führe SPARQL DELETE für {bv_id} aus...")
            client.query()
            logger.info(f"Berechnungsvorschrift {bv_id} erfolgreich gelöscht")
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            logger.error(
                f"Fehler beim Löschen der Berechnungsvorschrift {bv_id}: "
                f"{error_type}: {error_msg}. "
                f"Update-Endpoint: {self.update_endpoint}"
            )
            # Zusätzliche Debug-Informationen
            logger.debug(f"Vollständige Exception-Details für {bv_id}:", exc_info=True)
            raise
    
    def hat_referenzen(self, bv_id: str) -> bool:
        """
        Prüft, ob eine Berechnungsvorschrift von anderen referenziert wird
        
        Args:
            bv_id: ID der Berechnungsvorschrift
            
        Returns:
            True wenn Referenzen existieren, sonst False
        """
        logger.debug(f"Prüfe ob {bv_id} Referenzen hat...")
        referenzen = self.finde_verwendet_in(bv_id)
        hat_refs = len(referenzen) > 0
        logger.debug(f"{bv_id} hat {'Referenzen' if hat_refs else 'keine Referenzen'}")
        return hat_refs
