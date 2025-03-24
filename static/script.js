async function executeQuery() {
    const input = document.getElementById('queryInput').value;
    const resultsDiv = document.getElementById('results');
    
    resultsDiv.innerHTML = '<div class="loading">🔍 Searching...</div>';
    
    try {
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ query: input })
        });
        
        const data = await response.json();
        
        if (data.error) {
            resultsDiv.innerHTML = `<div class="error">⚠️ Error: ${data.error}</div>`;
            return;
        }

        let html = `<div class="query-display">SQL: <code>${data.query}</code></div>`;
        
        if (data.results.length > 0) {
            html += `<table>
                <thead><tr>${Object.keys(data.results[0]).map(k => `<th>${k}</th>`).join('')}</tr></thead>
                <tbody>${data.results.map(row => 
                    `<tr>${Object.values(row).map(v => `<td>${v}</td>`).join('')}</tr>`
                ).join('')}</tbody>
            </table>`;
        } else {
            html += '<div class="no-results">No results found</div>';
        }
        
        resultsDiv.innerHTML = html;
    } catch (error) {
        resultsDiv.innerHTML = `<div class="error">⚠️ Connection error: ${error.message}</div>`;
    }
}