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
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Document Search</h1>

      <form onSubmit={handleSearch} className="mb-8">
        <div className="flex flex-col md:flex-row gap-4">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your search query..."
            className="input flex-grow"
            required
          />
          <button
            type="submit"
            className="btn-primary md:w-auto"
            disabled={isLoading}
          >
            {isLoading ? "Searching..." : "Search"}
          </button>
        </div>
      </form>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {results.length > 0 ? (
        <div>
          <p className="mb-4 text-gray-600">Found {totalFound} results</p>

          <div className="space-y-6">
            {results.map((result, index) => (
              <div key={index} className="card">
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-gray-500">
                    Document: {result.metadata.source || "Unknown"}
                  </span>
                  <span className="text-sm text-gray-500">
                    Similarity: {(result.similarity * 100).toFixed(1)}%
                  </span>
                </div>

                <div className="prose max-w-none">
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
        </div>
      ) : (
        !isLoading &&
        query && (
          <p className="text-gray-600">
            No results found. Try a different search term.
          </p>
        )
      )}
    </div>
  );
}
