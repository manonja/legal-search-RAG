import { NextRequest, NextResponse } from 'next/server';
import { LegacyQueryRequest } from '@/lib/api';
import { proxyApiRequest } from '@/lib/apiProxy';

// Disable public access to this endpoint
export const dynamic = 'force-dynamic';

/**
 * POST handler for the /api/search/api endpoint (legacy search)
 * Proxies legacy search requests to the backend API
 */
export async function POST(request: NextRequest) {
  try {
    // Get collection_name from query parameters (if provided)
    const url = new URL(request.url);
    const collectionName = url.searchParams.get('collection_name');

    // Parse the request body
    const requestData: LegacyQueryRequest = await request.json();

    // Construct the endpoint URL with collection_name if provided
    let endpoint = '/api/search/api';
    if (collectionName) {
      endpoint += `?collection_name=${encodeURIComponent(collectionName)}`;
    }

    return await proxyApiRequest(request, {
      endpoint,
      method: 'POST',
      body: requestData
    });
  } catch (error) {
    console.error('Legacy search API error:', error);
    return NextResponse.json(
      { error: 'Failed to execute legacy search' },
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
