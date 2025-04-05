import { NextRequest, NextResponse } from 'next/server';
import { proxyApiRequest } from '@/lib/apiProxy';

// Disable public access to this endpoint and increase the limit for file uploads
export const dynamic = 'force-dynamic';
export const config = {
  api: {
    bodyParser: false,
  },
};

/**
 * POST handler for the /api/documents/upload endpoint
 * Proxies document upload requests to the backend API
 */
export async function POST(request: NextRequest) {
  try {
    return await proxyApiRequest(request, {
      endpoint: '/api/documents/upload',
      method: 'POST',
      contentType: 'multipart/form-data'
    });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to upload document' },
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
