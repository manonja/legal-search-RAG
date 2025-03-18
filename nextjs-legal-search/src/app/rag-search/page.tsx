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

  // Function to highlight matching text
  const highlightText = (text: string, searchQuery: string) => {
    if (!searchQuery.trim()) return text;

    // Create regex pattern from search terms
    const terms = searchQuery
      .trim()
      .split(/\s+/)
      .map((term) => term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
      .join("|");

    const regex = new RegExp(`(${terms})`, "gi");
    const parts = text.split(regex);

    return parts.map((part, i) =>
      regex.test(part) ? (
        <span key={i} className="bg-yellow-100 font-medium">
          {part}
        </span>
      ) : (
        part
      )
    );
  };

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

  const renderAnswer = (answer: string) => {
    // Split the answer into sections
    const sections = answer.split("\n\n").filter((section) => section.trim());

    return sections.map((section, index) => {
      // Regular markdown content
      return (
        <div key={index} className="mb-4">
          <ReactMarkdown>{section}</ReactMarkdown>
        </div>
      );
    });
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
                {renderAnswer(response.answer)}
              </div>
            </div>

            {/* Document Sources Section */}
            <div className="mb-8 pb-5 border-b border-gray-200">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-800">
                  Source Documents
                </h3>
                <span className="text-sm text-gray-500">
                  {response.document_sources.length} unique document
                  {response.document_sources.length !== 1 ? "s" : ""}
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {response.document_sources.map((source, index) => (
                  <div
                    key={index}
                    className="p-4 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-medium text-gray-900">
                        {source.title}
                      </h4>
                      <span className="text-sm text-gray-500">
                        {(source.similarity * 100).toFixed(1)}% match
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-between items-center mb-5">
              <h3 className="text-lg font-medium text-gray-800">
                Context Details
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
                    <div className="flex justify-between items-center mb-3">
                      <span className="text-sm text-gray-500">
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
                      {highlightText(result.chunk, query)}
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
