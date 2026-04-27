import { NextResponse } from 'next/server';

// Assuming the FastAPI backend is available at this URL inside docker
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: Request) {
    try {
        const body = await request.json();

        // Create a unique cache key based on the payload (we can use query string for caching fetch)
        // Next.js fetch caching works best with GET requests, but since this is a POST, 
        // we can use Next.js unstable_cache or just standard fetch with 'force-cache' if the backend supported GET.
        // For POST, we can pass options to fetch to cache it.
        const res = await fetch(`${BACKEND_URL}/api/v1/recommend`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
            // Cache the POST request using Next.js specific extensions
            // Cache for 1 hour (3600 seconds) to avoid redundant LLM calls
            next: { revalidate: 3600 } 
        });

        if (!res.ok) {
            const errorText = await res.text();
            console.error(`Backend returned ${res.status}: ${errorText}`);
            return NextResponse.json({ error: 'Failed to fetch from backend' }, { status: res.status });
        }

        const data = await res.json();
        return NextResponse.json(data);

    } catch (error) {
        console.error('API Route Error:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
