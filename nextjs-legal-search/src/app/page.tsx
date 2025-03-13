import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="max-w-4xl w-full text-center">
        <h1 className="text-4xl font-bold mb-6">Legal Search RAG</h1>
        <p className="text-xl mb-8">
          Search legal documents with semantic similarity and get AI-powered
          answers
        </p>

        <div className="flex flex-col md:flex-row gap-6 justify-center">
          <Link href="/search" className="btn-primary text-lg py-3 px-6">
            Document Search
          </Link>

          <Link href="/rag-search" className="btn-secondary text-lg py-3 px-6">
            Ask Legal Questions
          </Link>
        </div>

        <div className="mt-16 text-gray-600">
          <h2 className="text-2xl font-semibold mb-4">
            About this application
          </h2>
          <p className="mb-4">
            This application uses a Retrieval-Augmented Generation (RAG) system
            to search through legal documents and provide relevant information
            or answers to your questions.
          </p>
          <p>
            The system combines vector search technology with large language
            models to deliver accurate and contextually relevant results from
            your document collection.
          </p>
        </div>
      </div>
    </main>
  );
}
