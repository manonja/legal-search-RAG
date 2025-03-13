"use client";

import { api, QueryRequest, RagResponse } from "@/lib/api";
import { useState } from "react";
import ReactMarkdown from "react-markdown";

export default function RagSearchPage() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState<RagResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showContext, setShowContext] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);
    setResponse(null);

    try {
      const request: QueryRequest = {
        query_text: query,
        n_results: 5,
        min_similarity: 0.7,
      };

      const result = await api.ragSearch(request);
      setResponse(result);
    } catch (err) {
      console.error("RAG search error:", err);
      setError(
        "An error occurred while processing your question. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Ask Legal Questions</h1>

      <form onSubmit={handleSearch} className="mb-8">
        <div className="flex flex-col md:flex-row gap-4">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a legal question..."
            className="input flex-grow"
            required
          />
          <button
            type="submit"
            className="btn-primary md:w-auto"
            disabled={isLoading}
          >
            {isLoading ? "Processing..." : "Ask"}
          </button>
        </div>
      </form>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {isLoading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
          <p className="mt-2 text-gray-600">Generating answer...</p>
        </div>
      )}

      {response && (
        <div className="space-y-6">
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">Answer</h2>
            <div className="prose max-w-none">
              <ReactMarkdown>{response.answer}</ReactMarkdown>
            </div>
          </div>

          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium">
              Based on {response.total_found} document
              {response.total_found !== 1 ? "s" : ""}
            </h3>
            <button
              onClick={() => setShowContext(!showContext)}
              className="btn-secondary text-sm"
            >
              {showContext ? "Hide Context" : "Show Context"}
            </button>
          </div>

          {showContext && (
            <div className="space-y-4 mt-4">
              {response.context.map((result, index) => (
                <div key={index} className="card bg-gray-50">
                  <div className="flex justify-between mb-2">
                    <span className="text-sm text-gray-500">
                      Document: {result.metadata.source || "Unknown"}
                    </span>
                    <span className="text-sm text-gray-500">
                      Similarity: {(result.similarity * 100).toFixed(1)}%
                    </span>
                  </div>

                  <div className="prose max-w-none text-sm">
                    <p>{result.chunk}</p>
                  </div>

                  <div className="mt-4 text-sm text-gray-500">
                    {result.metadata.page_number && (
                      <span>Page: {result.metadata.page_number}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
