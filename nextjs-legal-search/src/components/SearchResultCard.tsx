import { SearchResult } from "@/lib/api";
import { useState } from "react";

interface SearchResultCardProps {
  result: SearchResult;
  query: string;
  index: number;
}

export default function SearchResultCard({
  result,
  query,
  index,
}: SearchResultCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Function to extract a meaningful title from the content
  const extractTitle = (content: string): string => {
    // Try to get the first sentence or first N characters
    const firstSentence = content
      .split(/[.!?]/)
      .filter((s) => s.trim().length > 0)[0];

    if (firstSentence) {
      // Truncate to a reasonable length and add ellipsis if needed
      const truncated = firstSentence.trim().slice(0, 100);
      return truncated.length < firstSentence.trim().length
        ? `${truncated}...`
        : truncated;
    }

    // Fallback to document source if available
    if (result.metadata.source) {
      const filename = result.metadata.source.split("/").pop();
      return filename || `Result ${index + 1}`;
    }

    // Last resort fallback
    return `Result ${index + 1}`;
  };

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

  // Get the display title using our hierarchy of fallbacks
  const displayTitle = extractTitle(result.chunk);

  return (
    <div
      className={`
        mb-8 pb-5 border-b border-gray-200 last:border-b-0 last:mb-0 last:pb-0
        transition-all duration-200 ease-in-out
        hover:bg-gray-50 rounded-lg p-4
      `}
    >
      <div className="flex gap-3 text-sm text-gray-500 mb-3">
        <span>{result.metadata.source || "Unknown Document"}</span>
      </div>

      <h3 className="text-xl font-semibold mb-3 text-gray-900">
        {displayTitle}
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

      <div
        className={`
          text-gray-700 leading-relaxed
          ${!isExpanded && "line-clamp-3"}
          relative
        `}
      >
        {highlightText(result.chunk, query)}
      </div>

      {!isExpanded && result.chunk.length > 250 && (
        <div className="mt-2">
          <button
            className="text-gray-500 hover:text-gray-700 text-sm font-medium hover:underline focus:outline-none focus:ring-2 focus:ring-gray-200 rounded px-2 py-1"
            onClick={() => setIsExpanded(true)}
          >
            Show more
          </button>
        </div>
      )}

      {isExpanded && (
        <div className="mt-2">
          <button
            className="text-gray-500 hover:text-gray-700 text-sm font-medium hover:underline focus:outline-none focus:ring-2 focus:ring-gray-200 rounded px-2 py-1"
            onClick={() => setIsExpanded(false)}
          >
            Show less
          </button>
        </div>
      )}
    </div>
  );
}
