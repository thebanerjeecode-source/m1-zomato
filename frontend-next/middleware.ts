import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Simple in-memory store for rate limiting (For demonstration in standalone mode)
// In a true distributed production environment, use Redis (e.g., Upstash)
const rateLimit = new Map<string, { count: number, timestamp: number }>();
const WINDOW_MS = 60 * 1000; // 1 minute
const MAX_REQUESTS = 10; // 10 requests per minute per IP

export function middleware(request: NextRequest) {
    if (request.nextUrl.pathname.startsWith('/api/recommend')) {
        const ip = request.ip || request.headers.get('x-forwarded-for') || '127.0.0.1';
        const now = Date.now();
        
        const record = rateLimit.get(ip);
        
        if (!record) {
            rateLimit.set(ip, { count: 1, timestamp: now });
        } else {
            if (now - record.timestamp > WINDOW_MS) {
                // Reset window
                rateLimit.set(ip, { count: 1, timestamp: now });
            } else {
                record.count += 1;
                if (record.count > MAX_REQUESTS) {
                    return NextResponse.json(
                        { error: 'Too Many Requests. Please try again later.' },
                        { status: 429 }
                    );
                }
            }
        }
    }
    
    return NextResponse.next();
}

export const config = {
    matcher: '/api/:path*',
};
