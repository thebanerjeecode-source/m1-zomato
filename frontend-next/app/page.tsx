"use client";

import { useState } from 'react';
import './page.css'; // Let's assume we copy the rest of index.css into page.css or keep it modular

export default function Home() {
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setResults(null);

        const formData = new FormData(e.currentTarget);
        const payload = {
            location: formData.get('location'),
            cuisine: formData.get('cuisine'),
            budget: formData.get('budget'),
            min_rating: parseFloat(formData.get('min_rating') as string) || 0.0,
            additional_preferences: formData.get('additional_preferences') || null,
            top_n: 5
        };

        try {
            // Send request through our Next.js API route to handle rate limiting and caching
            const res = await fetch('/api/recommend', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!res.ok) throw new Error("Failed to fetch recommendations");
            const data = await res.json();
            setResults(data);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="app-container">
            <header className="app-header">
                <h1>Crave<span>AI</span></h1>
                <p>Discover the perfect dining experience tailored to your taste.</p>
            </header>

            <main className="main-content">
                <section className="form-section">
                    <form className="preferences-form" onSubmit={onSubmit}>
                        <div className="form-group">
                            <label htmlFor="location">Location</label>
                            <input type="text" id="location" name="location" placeholder="e.g. Bellandur" required />
                        </div>
                        <div className="form-group">
                            <label htmlFor="cuisine">Cuisine</label>
                            <input type="text" id="cuisine" name="cuisine" placeholder="e.g. North Indian" required />
                        </div>
                        <div className="form-group">
                            <label htmlFor="budget">Budget Level</label>
                            <select id="budget" name="budget" defaultValue="medium">
                                <option value="low">Low</option>
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label htmlFor="min_rating">Min Rating</label>
                            <input type="number" id="min_rating" name="min_rating" min="0" max="5" step="0.1" defaultValue="0.0" />
                        </div>
                        <div className="form-group full-width">
                            <label htmlFor="additional_preferences">Additional Preferences</label>
                            <textarea id="additional_preferences" name="additional_preferences" rows={2} placeholder="e.g. rooftop seating"></textarea>
                        </div>
                        <button type="submit" className="submit-btn" disabled={loading}>
                            {loading ? <div className="loader"></div> : <span>Get Recommendations</span>}
                        </button>
                    </form>
                </section>

                <section className="results-section">
                    {error && (
                        <div className="empty-state" style={{ borderColor: 'var(--danger)' }}>
                            <div className="empty-icon">⚠️</div>
                            <p style={{ color: 'var(--danger)' }}>{error}</p>
                        </div>
                    )}
                    
                    {results?.warnings && results.warnings.length > 0 && (
                        <div className="results-meta">
                            <strong>Note:</strong> Used LLM: {results.used_llm ? 'Yes' : 'No'} | Model: {results.model || 'N/A'}
                            <ul>
                                {results.warnings.map((w: string, i: number) => <li key={i}>{w}</li>)}
                            </ul>
                        </div>
                    )}

                    <div className="recommendations-container">
                        {!results && !error && (
                            <div className="empty-state">
                                <div className="empty-icon">🍽️</div>
                                <p>Fill out your preferences to see AI recommendations here.</p>
                            </div>
                        )}

                        {results?.recommendations?.map((rec: any, index: number) => (
                            <div key={rec.id || index} className="rec-card" style={{ animationDelay: `${index * 0.1}s` }}>
                                <div className="rec-header">
                                    <div className="rec-title">
                                        <div className="rec-rank">{rec.rank || index + 1}</div>
                                        <div className="rec-name">{rec.name || 'Unknown'}</div>
                                    </div>
                                    <div className="rec-rating">{rec.rating ? `${rec.rating} ★` : 'No Rating'}</div>
                                </div>
                                <div className="rec-meta">
                                    <span>📍 {rec.location || 'Unknown'}</span>
                                    <span>💰 {rec.cost ? `₹${rec.cost} for two` : 'Cost N/A'}</span>
                                </div>
                                <div className="rec-cuisines">
                                    {rec.cuisines?.map((c: string) => (
                                        <span key={c} className="cuisine-tag">{c}</span>
                                    ))}
                                </div>
                                <div className="rec-explanation">
                                    <strong>Why we recommend this</strong>
                                    {rec.explanation}
                                </div>
                            </div>
                        ))}
                    </div>
                </section>
            </main>
        </div>
    );
}
