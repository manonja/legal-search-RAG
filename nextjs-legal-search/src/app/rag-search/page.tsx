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
    <div className="container mx-auto px-4 max-w-7xl">
      {/* Header Section */}
      <section className="text-center py-10">
        <h1 className="text-4xl text-gray-800 font-bold mb-5">
          Ask Legal Questions
        </h1>
        <p className="text-lg text-gray-600 max-w-3xl mx-auto mb-8">
          Get AI-generated answers to your legal questions based on document
          context.
        </p>
      </section>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="mb-8">
        <div className="border border-gray-200 rounded-xl overflow-hidden">
          <div className="flex items-center p-4">
            <span className="mr-3 text-gray-500">💬</span>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a legal question..."
              className="flex-1 border-none outline-none text-base"
              required
            />
            <button
              type="submit"
              className="bg-gray-800 text-white px-6 py-2 rounded-full font-semibold hover:bg-gray-700 transition-colors"
              disabled={isLoading}
            >
              {isLoading ? "Processing..." : "Ask"}
            </button>
          </div>
        </div>
      </form>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {isLoading && (
        <div className="text-center py-10">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-gray-800"></div>
          <p className="mt-4 text-gray-600">Generating answer...</p>
        </div>
      )}

      {/* Results Section */}
      {response && (
        <section className="border border-gray-200 rounded-xl overflow-hidden my-10">
          <div className="p-5">
            <div className="mb-8 pb-5 border-b border-gray-200">
              <h2 className="text-xl font-semibold mb-4 text-gray-900">
                Answer
              </h2>
              <div className="prose max-w-none text-gray-700">
                <ReactMarkdown>{response.answer}</ReactMarkdown>
              </div>
            </div>

            <div className="flex justify-between items-center mb-5">
              <h3 className="text-lg font-medium text-gray-800">
                Based on {response.total_found} document
                {response.total_found !== 1 ? "s" : ""}
              </h3>
              <button
                onClick={() => setShowContext(!showContext)}
                className="bg-gray-100 px-4 py-2 rounded-full text-sm text-gray-700 hover:bg-gray-200 transition-colors"
              >
                {showContext ? "Hide Context" : "Show Context"}
              </button>
            </div>

            {showContext && (
              <div className="space-y-6 mt-4">
                {response.context.map((result, index) => (
                  <div
                    key={index}
                    className="mb-8 pb-5 border-b border-gray-200 last:border-b-0 last:mb-0 last:pb-0"
                  >
                    <div className="flex gap-3 text-sm text-gray-500 mb-3">
                      <span>
                        {result.metadata.source || "Unknown Document"}
                      </span>
                    </div>
                    <div className="flex gap-3 mb-4 flex-wrap">
                      <span className="bg-gray-100 px-3 py-1 rounded-full text-sm text-gray-600">
                        Similarity: {(result.similarity * 100).toFixed(1)}%
                      </span>
                      {result.metadata.page_number && (
                        <span className="bg-gray-100 px-3 py-1 rounded-full text-sm text-gray-600">
                          Page: {result.metadata.page_number}
                        </span>
                      )}
                    </div>
                    <p className="text-gray-700 mb-4 leading-relaxed">
                      {result.chunk}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
