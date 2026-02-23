/**
 * API-Client für die Kommunikation mit dem Backend
 */
const api = {
    baseUrl: '/api',
    
    /**
     * Führt einen API-Request aus
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: response.statusText }));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }
            
            // 204 No Content hat keinen Body
            if (response.status === 204) {
                return null;
            }
            
            return await response.json();
        } catch (error) {
            throw error;
        }
    },
    
    /**
     * Erstellt eine neue Berechnungsvorschrift
     */
    async erstelleBerechnungsvorschrift(zelleneingabe) {
        return this.request('/berechnungsvorschriften', {
            method: 'POST',
            body: JSON.stringify({ zelleneingabe }),
        });
    },
    
    /**
     * Lädt alle Berechnungsvorschriften
     */
    async ladeAlleBerechnungsvorschriften() {
        return this.request('/berechnungsvorschriften');
    },
    
    /**
     * Lädt eine spezifische Berechnungsvorschrift
     */
    async ladeBerechnungsvorschrift(id) {
        return this.request(`/berechnungsvorschriften/${id}`);
    },
    
    /**
     * Aktualisiert eine Berechnungsvorschrift
     */
    async aktualisiereBerechnungsvorschrift(id, berechnungsvorschrift) {
        return this.request(`/berechnungsvorschriften/${id}`, {
            method: 'PUT',
            body: JSON.stringify(berechnungsvorschrift),
        });
    },
    
    /**
     * Löscht eine Berechnungsvorschrift
     */
    async loescheBerechnungsvorschrift(id) {
        return this.request(`/berechnungsvorschriften/${id}`, {
            method: 'DELETE',
        });
    },

    /**
     * Löscht alle Berechnungsvorschriften für ein Tabellenblatt
     * (Kombination aus Tabellenidentifikator + Tabellenblatt)
     */
    async loescheBerechnungsvorschriftenNachBlatt(tabellenidentifikator, tabellenblatt) {
        const params = new URLSearchParams({
            tabellenidentifikator,
            tabellenblatt,
        });
        return this.request(`/berechnungsvorschriften/blatt?${params.toString()}`, {
            method: 'DELETE',
        });
    },
    
    /**
     * Lädt Berechnungsvorschriften, die diese referenzieren
     */
    async ladeVerwendetIn(id) {
        return this.request(`/berechnungsvorschriften/${id}/verwendet-in`);
    },
    
    /**
     * Lädt Berechnungsvorschriften, die diese verwendet
     */
    async ladeVerwendet(id) {
        return this.request(`/berechnungsvorschriften/${id}/verwendet`);
    },
    
    /**
     * Sucht Berechnungsvorschriften nach Metadaten
     */
    async sucheBerechnungsvorschriften(filter) {
        const params = new URLSearchParams();
        if (filter.name) params.append('name', filter.name);
        if (filter.kategorie) params.append('kategorie', filter.kategorie);
        if (filter.symbol) params.append('symbol', filter.symbol);
        if (filter.datentyp) params.append('datentyp', filter.datentyp);
        if (filter.einheit) params.append('einheit', filter.einheit);
        if (filter.wichtig === true) params.append('wichtig', 'true');
        
        return this.request(`/berechnungsvorschriften/suche?${params.toString()}`);
    },
    
    /**
     * Verlinkt eine Variable manuell
     */
    async verlinkeVariable(bvId, variablenname, referenzId) {
        return this.request(`/berechnungsvorschriften/${bvId}/variablen/${encodeURIComponent(variablenname)}/verlinken?referenz_id=${encodeURIComponent(referenzId)}`, {
            method: 'POST',
        });
    },
    
    /**
     * Hebt die Verlinkung einer Variable auf (Variable wird wieder primitiv)
     */
    async verlinkungAufheben(bvId, variablenname) {
        return this.request(`/berechnungsvorschriften/${bvId}/variablen/${encodeURIComponent(variablenname)}/verlinkung-aufheben`, {
            method: 'POST',
        });
    },
};
