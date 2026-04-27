document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('preferences-form');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = document.querySelector('.btn-text');
    const btnLoader = document.getElementById('btn-loader');
    const resultsContainer = document.getElementById('recommendations-container');
    const resultsMeta = document.getElementById('results-meta');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // UI Loading State
        submitBtn.disabled = true;
        btnText.classList.add('hidden');
        btnLoader.classList.remove('hidden');
        resultsMeta.classList.add('hidden');
        resultsContainer.innerHTML = '';

        // Gather form data
        const formData = new FormData(form);
        const payload = {
            location: formData.get('location'),
            cuisine: formData.get('cuisine'),
            budget: formData.get('budget'),
            min_rating: parseFloat(formData.get('min_rating')) || 0.0,
            additional_preferences: formData.get('additional_preferences') || null,
            top_n: 5
        };

        try {
            const response = await fetch('http://localhost:8000/api/v1/recommend', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            renderResults(data);

        } catch (error) {
            console.error('Error fetching recommendations:', error);
            resultsContainer.innerHTML = `
                <div class="empty-state" style="border-color: var(--danger);">
                    <div class="empty-icon">⚠️</div>
                    <p style="color: var(--danger);">Failed to fetch recommendations. Ensure the backend is running on port 8000.</p>
                </div>
            `;
        } finally {
            // Revert Loading State
            submitBtn.disabled = false;
            btnText.classList.remove('hidden');
            btnLoader.classList.add('hidden');
        }
    });

    function renderResults(data) {
        // Render Meta/Warnings
        if (data.warnings && data.warnings.length > 0) {
            resultsMeta.classList.remove('hidden');
            let metaHtml = `<strong>Note:</strong> Used LLM: ${data.used_llm ? 'Yes' : 'No'} | Model: ${data.model || 'N/A'}`;
            metaHtml += `<ul>`;
            data.warnings.forEach(w => {
                metaHtml += `<li>${w}</li>`;
            });
            metaHtml += `</ul>`;
            resultsMeta.innerHTML = metaHtml;
        }

        if (!data.recommendations || data.recommendations.length === 0) {
            resultsContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🔍</div>
                    <p>No restaurants found matching your criteria. Try relaxing your filters.</p>
                </div>
            `;
            return;
        }

        // Render Cards
        let delay = 0;
        data.recommendations.forEach((rec, index) => {
            const card = document.createElement('div');
            card.className = 'rec-card';
            card.style.animationDelay = `${delay}s`;
            delay += 0.1;

            const name = rec.name || 'Unknown';
            const location = rec.location || 'Unknown Location';
            const rating = rec.rating ? `${rec.rating} ★` : 'No Rating';
            const cost = rec.cost ? `₹${rec.cost} for two` : 'Cost N/A';
            const cuisines = rec.cuisines ? rec.cuisines.map(c => `<span class="cuisine-tag">${c}</span>`).join('') : '';
            const explanation = rec.explanation || 'Matches your criteria.';

            card.innerHTML = `
                <div class="rec-header">
                    <div class="rec-title">
                        <div class="rec-rank">${rec.rank || (index + 1)}</div>
                        <div class="rec-name">${name}</div>
                    </div>
                    <div class="rec-rating">${rating}</div>
                </div>
                
                <div class="rec-meta">
                    <span>📍 ${location}</span>
                    <span>💰 ${cost}</span>
                </div>
                
                <div class="rec-cuisines">
                    ${cuisines}
                </div>
                
                <div class="rec-explanation">
                    <strong>Why we recommend this</strong>
                    ${explanation}
                </div>
            `;
            resultsContainer.appendChild(card);
        });
    }
});
