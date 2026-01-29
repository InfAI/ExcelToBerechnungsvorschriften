"""
JSON-zu-RDF Konverter (Middleware)
Konvertiert Berechnungsvorschriften von JSON zu RDF-Triples
"""
import logging
from datetime import datetime
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD
from typing import List
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from models.berechnungsvorschrift import Berechnungsvorschrift
from utils.rdf_helper import BV, berechnungsvorschrift_uri, variable_uri, get_namespace_iri, property_uri

logger = logging.getLogger(__name__)


class JSONRDFConverter:
    """Konvertiert JSON-Berechnungsvorschriften zu RDF-Triples"""
    
    def __init__(self):
        """Initialisiert den Converter"""
        self.graph = Graph()
        self.graph.bind("bv", BV)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("xsd", XSD)
    
    def berechnungsvorschrift_to_rdf(self, bv: Berechnungsvorschrift) -> Graph:
        """
        Konvertiert eine Berechnungsvorschrift zu RDF-Triples
        
        Args:
            bv: Berechnungsvorschrift
            
        Returns:
            RDF-Graph mit den Triples
        """
        if not bv.id:
            raise ValueError("Berechnungsvorschrift muss eine ID haben")
        
        logger.debug(f"Erstelle RDF-Graph für {bv.id}")
        graph = Graph()
        graph.bind("bv", BV)
        graph.bind("rdf", RDF)
        graph.bind("rdfs", RDFS)
        graph.bind("xsd", XSD)
        
        bv_uri = berechnungsvorschrift_uri(bv.id)
        namespace_iri = get_namespace_iri()
        
        # Typ
        bv_type = URIRef(f"{namespace_iri}Berechnungsvorschrift")
        graph.add((bv_uri, RDF.type, bv_type))
        
        # Grunddaten
        graph.add((bv_uri, property_uri("hatName"), Literal(bv.name)))
        graph.add((bv_uri, property_uri("hatFormel"), Literal(bv.formel)))
        graph.add((bv_uri, property_uri("hatVersion"), Literal(bv.version, datatype=XSD.integer)))
        
        # Metadaten
        graph.add((bv_uri, property_uri("hatKategorie"), Literal(bv.metadaten.kategorie)))
        graph.add((bv_uri, property_uri("hatSymbol"), Literal(bv.metadaten.symbol)))
        graph.add((bv_uri, property_uri("hatDatentyp"), Literal(bv.metadaten.datentyp)))
        graph.add((bv_uri, property_uri("hatEinheit"), Literal(bv.metadaten.einheit)))
        
        # Zeitstempel
        if bv.erstellt_am:
            graph.add((bv_uri, property_uri("hatErstelltAm"), 
                      Literal(bv.erstellt_am.isoformat(), datatype=XSD.dateTime)))
        if bv.geaendert_am:
            graph.add((bv_uri, property_uri("hatGeaendertAm"), 
                      Literal(bv.geaendert_am.isoformat(), datatype=XSD.dateTime)))
        
        # Quelle-Information (optional)
        if bv.quelle:
            if bv.quelle.tabellenidentifikator:
                graph.add((bv_uri, property_uri("hatQuelleTabellenidentifikator"), 
                          Literal(bv.quelle.tabellenidentifikator)))
            if bv.quelle.tabellenblatt:
                graph.add((bv_uri, property_uri("hatQuelleTabellenblatt"), 
                          Literal(bv.quelle.tabellenblatt)))
            if bv.quelle.zellenidentifikator:
                graph.add((bv_uri, property_uri("hatQuelleZellenidentifikator"), 
                          Literal(bv.quelle.zellenidentifikator)))
            if bv.quelle.beschreibung:
                graph.add((bv_uri, property_uri("hatQuelleBeschreibung"), 
                          Literal(bv.quelle.beschreibung)))
        
        # Variablen: Jede Variable wird als RDF-Objekt angelegt; Verlinkung über
        # referenz_berechnungsvorschrift_id. Variablennamen im formel-String müssen zu
        # Variable.name passen, damit die Anzeige/Verlinkung im Frontend funktioniert.
        logger.debug(f"Füge {len(bv.variablen)} Variablen zum RDF-Graph hinzu...")
        var_type = URIRef(f"{namespace_iri}Variable")
        for var in bv.variablen:
            var_uri = variable_uri(bv.id, var.name)
            graph.add((var_uri, RDF.type, var_type))
            graph.add((var_uri, property_uri("hatName"), Literal(var.name)))
            graph.add((var_uri, property_uri("istPrimitive"), 
                      Literal(var.ist_primitive, datatype=XSD.boolean)))
            graph.add((bv_uri, property_uri("hatVariable"), var_uri))
            
            # Referenz zu anderer Berechnungsvorschrift (falls vorhanden)
            if var.referenz_berechnungsvorschrift_id and not var.ist_primitive:
                logger.debug(f"Variable '{var.name}' referenziert Berechnungsvorschrift {var.referenz_berechnungsvorschrift_id}")
                ref_uri = berechnungsvorschrift_uri(var.referenz_berechnungsvorschrift_id)
                graph.add((var_uri, property_uri("referenziertBerechnungsvorschrift"), ref_uri))
        
        logger.debug(f"RDF-Konvertierung abgeschlossen: {len(graph)} Triples erstellt für {bv.id}")
        return graph
    
    def rdf_to_berechnungsvorschrift(self, graph: Graph, bv_id: str) -> Berechnungsvorschrift:
        """
        Konvertiert RDF-Triples zurück zu einer Berechnungsvorschrift
        
        Args:
            graph: RDF-Graph
            bv_id: ID der Berechnungsvorschrift
            
        Returns:
            Berechnungsvorschrift
        """
        from models.berechnungsvorschrift import Variable, Metadaten, Quelle
        
        bv_uri = berechnungsvorschrift_uri(bv_id)
        
        # Grunddaten extrahieren
        name_val = graph.value(bv_uri, property_uri("hatName"))
        name = str(name_val) if name_val else ""
        
        formel_val = graph.value(bv_uri, property_uri("hatFormel"))
        formel = str(formel_val) if formel_val else ""
        
        version_val = graph.value(bv_uri, property_uri("hatVersion"))
        version = int(version_val) if version_val else 1
        
        # Metadaten extrahieren
        kategorie_val = graph.value(bv_uri, property_uri("hatKategorie"))
        symbol_val = graph.value(bv_uri, property_uri("hatSymbol"))
        datentyp_val = graph.value(bv_uri, property_uri("hatDatentyp"))
        einheit_val = graph.value(bv_uri, property_uri("hatEinheit"))
        
        metadaten = Metadaten(
            kategorie=str(kategorie_val) if kategorie_val else "",
            symbol=str(symbol_val) if symbol_val else "",
            datentyp=str(datentyp_val) if datentyp_val else "decimal",
            einheit=str(einheit_val) if einheit_val else ""
        )
        
        # Zeitstempel extrahieren
        erstellt_am_str = graph.value(bv_uri, property_uri("hatErstelltAm"))
        erstellt_am = None
        if erstellt_am_str:
            try:
                erstellt_am = datetime.fromisoformat(str(erstellt_am_str).replace('Z', '+00:00'))
            except:
                pass
        
        geaendert_am_str = graph.value(bv_uri, property_uri("hatGeaendertAm"))
        geaendert_am = None
        if geaendert_am_str:
            try:
                geaendert_am = datetime.fromisoformat(str(geaendert_am_str).replace('Z', '+00:00'))
            except:
                pass
        
        # Quelle extrahieren
        quelle = None
        tabellenidentifikator_val = graph.value(bv_uri, property_uri("hatQuelleTabellenidentifikator"))
        beschreibung_val = graph.value(bv_uri, property_uri("hatQuelleBeschreibung"))
        if tabellenidentifikator_val or beschreibung_val:
            quelle = Quelle(
                tabellenidentifikator=str(tabellenidentifikator_val) if tabellenidentifikator_val else None,
                tabellenblatt=str(graph.value(bv_uri, property_uri("hatQuelleTabellenblatt")) or "") if graph.value(bv_uri, property_uri("hatQuelleTabellenblatt")) else None,
                zellenidentifikator=str(graph.value(bv_uri, property_uri("hatQuelleZellenidentifikator")) or "") if graph.value(bv_uri, property_uri("hatQuelleZellenidentifikator")) else None,
                beschreibung=str(beschreibung_val) if beschreibung_val else None
            )
        
        # Variablen extrahieren
        logger.debug(f"Extrahiere Variablen aus RDF-Graph für {bv_id}...")
        variablen = []
        hat_variable_uri = property_uri("hatVariable")
        var_uris = list(graph.objects(bv_uri, hat_variable_uri))
        logger.debug(f"Gefunden: {len(var_uris)} Variable(n) in RDF-Graph")
        for var_uri in var_uris:
            var_name_val = graph.value(var_uri, property_uri("hatName"))
            if not var_name_val:
                continue
                
            var_name = str(var_name_val)
            
            ist_primitive_val = graph.value(var_uri, property_uri("istPrimitive"))
            ist_primitive = True
            if ist_primitive_val:
                ist_primitive = str(ist_primitive_val).lower() == "true"
            
            # Referenz extrahieren
            ref_uri = graph.value(var_uri, property_uri("referenziertBerechnungsvorschrift"))
            ref_id = None
            if ref_uri:
                # ID aus URI extrahieren
                ref_id = str(ref_uri).split("/")[-1]
                ist_primitive = False
            
            variablen.append(Variable(
                name=var_name,
                referenz_berechnungsvorschrift_id=ref_id,
                ist_primitive=ist_primitive
            ))
            if ref_id:
                logger.debug(f"Variable '{var_name}' extrahiert mit Referenz zu {ref_id}")
            else:
                logger.debug(f"Variable '{var_name}' extrahiert (primitiv: {ist_primitive})")
        
        logger.debug(f"Erstelle Berechnungsvorschrift-Objekt aus RDF-Daten: {bv_id}")
        # Berechnungsvorschrift erstellen
        bv = Berechnungsvorschrift(
            id=bv_id,
            name=name,
            formel=formel,
            variablen=variablen,
            metadaten=metadaten,
            quelle=quelle,
            version=version,
            erstellt_am=erstellt_am,
            geaendert_am=geaendert_am
        )
        logger.debug(f"RDF-zu-JSON Konvertierung abgeschlossen: ID={bv.id}, Name={bv.name}, Variablen={len(bv.variablen)}")
        return bv
