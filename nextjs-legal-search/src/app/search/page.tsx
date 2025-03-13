"use client";

import { api, QueryRequest, SearchResult } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function SearchPage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [totalFound, setTotalFound] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const request: QueryRequest = {
        query_text: query,
        n_results: 10,
        min_similarity: 0.7,
      };

      const response = await api.searchDocuments(request);

      setResults(response.results);
      setTotalFound(response.total_found);
    } catch (err) {
      console.error("Search error:", err);
      setError("An error occurred while searching. Please try again.");
      setResults([]);
      setTotalFound(0);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 max-w-7xl">
      {/* Header Section */}
      <section className="text-center py-10">
        <h1 className="text-4xl text-gray-800 font-bold mb-5">
          Document Search
        </h1>
        <p className="text-lg text-gray-600 max-w-3xl mx-auto mb-8">
          Search legal documents with semantic similarity to find relevant
          information.
        </p>
      </section>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="mb-8">
        <div className="border border-gray-200 rounded-xl overflow-hidden">
          <div className="flex items-center p-4">
            <span className="mr-3 text-gray-500">🔍</span>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search legal documents..."
              className="flex-1 border-none outline-none text-base"
              required
            />
            <button
              type="submit"
              className="bg-gray-800 text-white px-6 py-2 rounded-full font-semibold hover:bg-gray-700 transition-colors"
              disabled={isLoading}
            >
              {isLoading ? "Searching..." : "Search"}
            </button>
          </div>
        </div>
      </form>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* Results Section */}
      {results.length > 0 ? (
        <section className="border border-gray-200 rounded-xl overflow-hidden my-10">
          <div className="p-5">
            <div className="flex justify-between items-center mb-5 text-sm text-gray-500">
              <span>Found {totalFound} results</span>
              <div className="flex items-center gap-1 cursor-pointer">
                Sort by: Relevance ▼
              </div>
            </div>

            {results.map((result, index) => (
              <div
                key={index}
                className="mb-8 pb-5 border-b border-gray-200 last:border-b-0 last:mb-0 last:pb-0"
              >
                <div className="flex gap-3 text-sm text-gray-500 mb-3">
                  <span>{result.metadata.source || "Unknown Document"}</span>
                </div>
                <h3 className="text-xl font-semibold mb-3 text-gray-900">
                  {result.metadata.title || `Result ${index + 1}`}
                </h3>
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
        </section>
      ) : (
        !isLoading &&
        query && (
          <div className="text-center py-10">
            <p className="text-gray-600 text-lg">
              No results found. Try a different search term.
            </p>
          </div>
        )
      )}

      {isLoading && (
        <div className="text-center py-10">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-gray-800"></div>
          <p className="mt-4 text-gray-600">Searching documents...</p>
        </div>
      )}
    </div>
  );
}
