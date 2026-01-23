/**
 * Funktionen für die Verwaltung von Berechnungsvorschriften
 */

/**
 * Formatiert eine Berechnungsvorschrift-Formel mit anklickbaren Variablen
 */
function formatiereFormelMitVariablen(formel, variablen, bvId) {
    let formatierteFormel = formel;
    
    // Ersetze Variablen durch anklickbare Links
    variablen.forEach(variable => {
        if (!variable.ist_primitive && variable.referenz_berechnungsvorschrift_id) {
            const regex = new RegExp(`\\b${variable.name}\\b`, 'g');
            formatierteFormel = formatierteFormel.replace(
                regex,
                `<a href="berechnungsvorschrift.html?id=${variable.referenz_berechnungsvorschrift_id}" class="variable-link badge bg-primary">${variable.name}</a>`
            );
        } else {
            const regex = new RegExp(`\\b${variable.name}\\b`, 'g');
            formatierteFormel = formatierteFormel.replace(
                regex,
                `<span class="badge bg-secondary">${variable.name}</span>`
            );
        }
    });
    
    return formatierteFormel;
}

/**
 * Erstellt eine Bootstrap Card für eine Berechnungsvorschrift
 */
function erstelleBerechnungsvorschriftCard(bv) {
    const formelHtml = formatiereFormelMitVariablen(bv.formel, bv.variablen || [], bv.id);
    
    return `
        <div class="card mb-3" data-bv-id="${bv.id}">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0">${bv.name}</h5>
                <span class="badge bg-info">Version ${bv.version}</span>
            </div>
            <div class="card-body">
                <p class="mb-2"><strong>Formel:</strong> ${formelHtml}</p>
                <div class="row mt-3">
                    <div class="col-md-6">
                        <h6>Metadaten</h6>
                        <ul class="list-unstyled">
                            <li><strong>Kategorie:</strong> ${bv.metadaten.kategorie}</li>
                            <li><strong>Symbol:</strong> ${bv.metadaten.symbol}</li>
                            <li><strong>Datentyp:</strong> ${bv.metadaten.datentyp}</li>
                            <li><strong>Einheit:</strong> ${bv.metadaten.einheit}</li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h6>Variablen</h6>
                        <ul class="list-unstyled">
                            ${(bv.variablen || []).map(variable => 
                                `<li>${variable.name} ${variable.ist_primitive ? 
                                    '<span class="badge bg-secondary">primitiv</span>' : 
                                    `<a href="berechnungsvorschrift.html?id=${variable.referenz_berechnungsvorschrift_id}" class="badge bg-primary">→ ${variable.referenz_berechnungsvorschrift_id.substring(0, 8)}...</a>`
                                }</li>`
                            ).join('')}
                        </ul>
                    </div>
                </div>
                <div class="mt-3">
                    <a href="berechnungsvorschrift.html?id=${bv.id}" class="btn btn-sm btn-primary">Details</a>
                    <button class="btn btn-sm btn-danger" onclick="loescheBerechnungsvorschrift('${bv.id}')">Löschen</button>
                </div>
            </div>
        </div>
    `;
}

/**
 * Lädt und zeigt alle Berechnungsvorschriften
 */
async function ladeUndZeigeBerechnungsvorschriften(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    try {
        const berechnungsvorschriften = await api.ladeAlleBerechnungsvorschriften();
        
        if (berechnungsvorschriften.length === 0) {
            container.innerHTML = '<div class="alert alert-info">Keine Berechnungsvorschriften gefunden.</div>';
            return;
        }
        
        container.innerHTML = berechnungsvorschriften
            .map(bv => erstelleBerechnungsvorschriftCard(bv))
            .join('');
            
    } catch (error) {
        container.innerHTML = `<div class="alert alert-danger">Fehler beim Laden: ${error.message}</div>`;
    }
}

/**
 * Löscht eine Berechnungsvorschrift
 */
async function loescheBerechnungsvorschrift(id) {
    if (!confirm('Möchten Sie diese Berechnungsvorschrift wirklich löschen?')) {
        return;
    }
    
    try {
        await api.loescheBerechnungsvorschrift(id);
        alert('Berechnungsvorschrift erfolgreich gelöscht!');
        location.reload();
    } catch (error) {
        alert(`Fehler beim Löschen: ${error.message}`);
    }
}
