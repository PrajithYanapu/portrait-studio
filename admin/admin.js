
const API = window.PORTRAIT_CONFIG.API_BASE;

const records = document.querySelector('#records');
const status = document.querySelector('#status');

let authHeader = null;

function getAuth() {
    if (authHeader) return authHeader;

    const username = prompt('Admin username:');
    if (username === null) throw new Error('Login cancelled');

    const password = prompt('Admin password:');
    if (password === null) throw new Error('Login cancelled');

    authHeader = 'Basic ' + btoa(username + ':' + password);
    return authHeader;
}

function escapeHtml(s) {
    return String(s ?? '').replace(/[&<>"']/g, c => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    })[c]);
}

async function apiRequest(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            Authorization: getAuth()
        }
    });

    if (response.status === 401) {
        authHeader = null;
        throw new Error('Invalid admin credentials. Refresh and try again.');
    }

    if (!response.ok) {
        throw new Error(`Request failed: ${response.status} ${await response.text()}`);
    }

    return response;
}

async function load() {
    status.textContent = 'Loading...';
    records.innerHTML = '';

    try {
        const response = await apiRequest(API + '/api/admin/portraits');
        const rows = await response.json();

        status.textContent = `${rows.length} record(s)`;

        if (!rows.length) {
            records.innerHTML = '<p class="empty-state">No portraits found.</p>';
            return;
        }

        records.innerHTML = rows.map(x => `
            <article class="card">
                <h2>${escapeHtml(x.customer_name)}</h2>

                <p class="meta">
                    ${escapeHtml(x.style)}
                    · ${new Date(x.created_at).toLocaleString()}
                    · Downloads: ${Number(x.download_count || 0)}
                </p>

                <div class="photos">
                    <figure class="photo-item">
                        <figcaption>Original photo</figcaption>
                        <img src="${escapeHtml(x.original_url)}" alt="Original upload">
                        <a class="download-btn"
                           href="${escapeHtml(x.original_url)}"
                           download
                           target="_blank"
                           rel="noopener noreferrer">
                           Download Original
                        </a>
                    </figure>

                    <figure class="photo-item">
                        <figcaption>Generated portrait</figcaption>
                        <img src="${escapeHtml(x.generated_url)}" alt="Generated portrait">
                        <a class="download-btn"
                           href="${escapeHtml(x.generated_url)}"
                           download
                           target="_blank"
                           rel="noopener noreferrer">
                           Download Portrait
                        </a>
                    </figure>
                </div>

                <div class="card-actions">
                    <button class="delete-btn"
                            data-id="${escapeHtml(x.id)}"
                            data-name="${escapeHtml(x.customer_name)}">
                        Delete Portrait
                    </button>
                </div>
            </article>
        `).join('');

    } catch (error) {
        status.textContent = error.message;
    }
}

records.addEventListener('click', async event => {
    const button = event.target.closest('.delete-btn');
    if (!button) return;

    const id = button.dataset.id;
    const name = button.dataset.name;

    if (!confirm(`Permanently delete both images and the record for ${name}?`)) {
        return;
    }

    button.disabled = true;
    button.textContent = 'Deleting...';

    try {
        await apiRequest(
            API + '/api/admin/portraits/' + encodeURIComponent(id),
            { method: 'DELETE' }
        );

        alert('Portrait deleted successfully.');
        await load();

    } catch (error) {
        alert('Delete failed: ' + error.message);
        button.disabled = false;
        button.textContent = 'Delete Portrait';
    }
});

document.querySelector('#refresh').addEventListener('click', load);

load();
