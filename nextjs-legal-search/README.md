# Legal Search Next.js Frontend

This is the frontend application for the Legal Search RAG system. It provides a modern, responsive user interface for searching legal documents using the FastAPI backend.

## Features

- Modern UI with responsive design
- Real-time search with debounced input
- Document preview and highlighting
- RAG-powered answers to legal questions
- Authentication and user management (optional)

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- FastAPI backend running (see main project README)

### Installation

1. Clone the repository
2. Install dependencies:

```bash
npm install
# or
yarn install
```

3. Create a `.env.local` file with the following variables:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. Start the development server:

```bash
npm run dev
# or
yarn dev
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

- `app/` - Next.js 13+ App Router
- `components/` - Reusable UI components
- `lib/` - Utility functions and API clients
- `public/` - Static assets

## Deployment

This application can be deployed to Vercel, Netlify, or any other Next.js-compatible hosting platform.

```bash
npm run build
# or
yarn build
```

## License

See the main project repository for license information.
