import { NextRequest, NextResponse } from 'next/server';
import { proxyApiRequest } from '@/lib/apiProxy';

// Disable public access to this endpoint
export const dynamic = 'force-dynamic';

/**
 * GET handler for the /api/documents/[id] endpoint
 * Proxies document retrieval requests to the backend API
 */
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const documentId = params.id;
    return await proxyApiRequest(null, {
      endpoint: `/api/documents/${encodeURIComponent(documentId)}`,
      method: 'GET'
    });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to retrieve document' },
      { status: 500 }
    );
  }
}

// Disable all other HTTP methods for this endpoint
export async function POST() {
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
