document.addEventListener('DOMContentLoaded', () => {
    const actionCards = document.querySelectorAll('.action-card');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const statusMessage = document.getElementById('status-message');

    function showStatus(message, type) {
        statusMessage.textContent = message;
        statusMessage.className = `status-message ${type}`;
        
        // Hide after 5 seconds
        setTimeout(() => {
            statusMessage.classList.add('hidden');
        }, 5000);
    }

    actionCards.forEach(card => {
        card.addEventListener('click', async () => {
            const script = card.getAttribute('data-script');
            const username = usernameInput.value.trim();
            const password = passwordInput.value.trim();

            if (!username || !password) {
                showStatus('Please enter your email/username and password first.', 'error');
                return;
            }

            // Visual feedback
            const originalText = card.querySelector('h3').textContent;
            card.querySelector('h3').textContent = 'Starting...';
            card.style.pointerEvents = 'none';
            card.style.opacity = '0.7';

            try {
                const response = await fetch('/api/run', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        script: script,
                        username: username,
                        password: password
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    showStatus(data.message, 'success');
                } else {
                    showStatus(data.message, 'error');
                }
            } catch (error) {
                showStatus('Network error: Could not reach the server.', 'error');
            } finally {
                // Restore button state
                card.querySelector('h3').textContent = originalText;
                card.style.pointerEvents = 'auto';
                card.style.opacity = '1';
            }
        });
    });

    // Insights logic
    const refreshBtn = document.getElementById('refresh-insights-btn');
    const insightsContainer = document.getElementById('insights-container');

    async function loadInsights() {
        refreshBtn.textContent = 'Loading...';
        try {
            const response = await fetch('/api/insights/latest');
            const result = await response.json();
            
            if (response.ok && result.data && result.data.length > 0) {
                let html = '<ul class="insights-list">';
                result.data.forEach((item, index) => {
                    html += `
                        <li class="insight-item">
                            <span class="insight-likes">${item.likes} <span style="font-size: 0.8rem; font-weight: normal; color: var(--text-secondary)">likes</span></span>
                            <a href="${item.url}" target="_blank" class="insight-link">${item.url.replace('https://poshmark.com', '')}</a>
                        </li>
                    `;
                });
                html += '</ul>';
                insightsContainer.innerHTML = html;
            } else {
                insightsContainer.innerHTML = `<p style="color: var(--text-secondary); font-style: italic; font-size: 0.9rem;">${result.message || 'No insights data found.'}</p>`;
            }
        } catch (err) {
            insightsContainer.innerHTML = '<p style="color: #cc0000; font-size: 0.9rem;">Failed to fetch insights.</p>';
        } finally {
            refreshBtn.textContent = 'Refresh';
        }
    }

    refreshBtn.addEventListener('click', loadInsights);
    
    // Attempt to load on startup just in case
    loadInsights();
});
