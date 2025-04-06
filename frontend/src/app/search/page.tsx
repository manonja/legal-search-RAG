"use client";

import SearchResultCard from "@/components/SearchResultCard";
import { api, LegacyQueryRequest, LegacySearchResult, SearchResult } from "@/lib/api";
import * as Sentry from "@sentry/nextjs";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function SearchPage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [totalFound, setTotalFound] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const request: LegacyQueryRequest = {
        query_text: query,
        n_results: 10,
        min_similarity: 0.7,
      };

      const response = await api.legacySearchDocuments(request);

      if (!response || !response.results) {
        throw new Error("Invalid response format from API");
      }

      console.log(
        "Search results metadata:",
        response.results.map((r) => r?.metadata || {})
      );

      const mappedResults: SearchResult[] = response.results.map((legacyResult: LegacySearchResult) => {
        let similarityValue = 0;
        if (typeof (legacyResult as any).distance === 'number') {
           similarityValue = 1 - (legacyResult as any).distance;
        } else if (typeof legacyResult.similarity === 'number') {
           similarityValue = legacyResult.similarity;
        }

        const textValue = (legacyResult as any).text || legacyResult.chunk || "";

        return {
          text: textValue,
          metadata: legacyResult.metadata || {},
          distance: 1 - similarityValue,
        };
      });

      setResults(mappedResults);
      setTotalFound(response.total_found || 0);

      window.dispatchEvent(new Event("search-performed"));
    } catch (error: any) {
      console.error("Search error:", error);

      Sentry.captureException(error, {
        tags: {
          component: "SearchPage",
          action: "legacySearchDocuments",
          errorType: error.name || "UnknownError",
          errorCode: error.code || "UNKNOWN_CODE"
        },
        extra: {
          query,
          message: error.message || "No error message",
          stack: error.stack || "No stack trace"
        }
      });

      console.error("Search error details for Sentry:", {
        message: error.message || "No message",
        code: error.code || "No code",
        type: error.name || "Unknown type"
      });

      setError("An error occurred while searching. Please try again.");
      setResults([]);
      setTotalFound(0);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 max-w-4xl pt-16">
      <section className="text-center mb-12">
        <h1 className="text-4xl text-gray-800 font-bold mb-4">
          Document Search
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Search legal documents with semantic similarity to find relevant
          information.
        </p>
      </section>

      <form onSubmit={handleSearch} className="mb-8">
        <div className="max-w-3xl mx-auto">
          <div className="border border-gray-200 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center p-3">
              <span className="mr-3 text-gray-400">🔍</span>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search legal documents..."
                className="flex-1 border-none outline-none text-sm bg-transparent"
                required
                disabled={isLoading}
              />
              <button
                type="submit"
                className="bg-gray-800 text-white px-5 py-1.5 rounded-full font-semibold hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                disabled={isLoading}
                data-testid="search-submit-button"
              >
                {isLoading ? (
                  <div className="inline-block animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white" data-testid="loading-spinner"></div>
                ) : "Search"}
              </button>
            </div>
          </div>
        </div>
      </form>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {results.length > 0 ? (
        <section className="border border-gray-200 rounded-xl overflow-hidden my-10 shadow-sm">
          <div className="p-5">
            <div className="flex justify-between items-center mb-5 text-sm text-gray-500">
              <span>Found {totalFound} results</span>
              <div className="flex items-center gap-1">
                <span>Sort by: Relevance</span>
                <span className="text-gray-400">▼</span>
              </div>
            </div>

            <div className="divide-y divide-gray-100">
              {results.map((result, index) => (
                <SearchResultCard
                  key={index}
                  result={result}
                  query={query}
                  index={index}
                />
              ))}
            </div>
          </div>
        </section>
      ) : (
        !isLoading &&
        hasSearched && (
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
