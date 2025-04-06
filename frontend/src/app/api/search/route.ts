import { NextRequest, NextResponse } from 'next/server';
import { SearchQuery } from '@/lib/api';
import { proxyApiRequest } from '@/lib/apiProxy';

// Disable public access to this endpoint
export const dynamic = 'force-dynamic';

/**
 * POST handler for the /api/search endpoint
 * Proxies search requests to the backend API
 */
export async function POST(request: NextRequest) {
  try {
    const requestData: SearchQuery = await request.json();
    return await proxyApiRequest(request, {
      endpoint: '/api/search/',
      method: 'POST',
      body: requestData
    });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to search documents' },
      { status: 500 }
    );
  }
}

// Disable all other HTTP methods for this endpoint
export async function GET() {
  return new Response(null, { status: 405 });
}

export async function PUT() {
  return new Response(null, { status: 405 });
}

export async function DELETE() {
  return new Response(null, { status: 405 });
}

export async function PATCH() {
  return new Response(null, { status: 405 });
}
