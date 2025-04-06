"use client";

import { api, QueryRequest, QueryResponse } from "@/lib/api";
import { useState } from "react";
import ReactMarkdown from "react-markdown";

export default function RagSearchPage() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showContext, setShowContext] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversationHistory, setConversationHistory] = useState<
    Array<{ role: string; content: string }>
  >([]);

  // Function to clear conversation
  const handleClearConversation = () => {
    setConversationHistory([]);
    setResponse(null);
    setError(null);
    setQuery(""); // Also clear the input field
    // Optionally reset conversationId if you track it server-side
    // setConversationId(null);
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

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const request: QueryRequest = {
        query: query,
        max_results: 5,
        temperature: 0.7,
        max_tokens: 1000,
      };

      const result = await api.ragSearch(request);
      setResponse(result);

      // Update conversation history
      if (conversationId) {
        setConversationHistory([
          ...conversationHistory,
          { role: "user", content: query },
          { role: "assistant", content: result.answer },
        ]);
      } else {
        setConversationHistory([
          { role: "user", content: query },
          { role: "assistant", content: result.answer },
        ]);
      }

      // Clear the query input for the next question
      setQuery("");

      // Emit search event
      window.dispatchEvent(new Event("search-performed"));
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
          Legal Assistant
        </h1>
        <p className="text-lg text-gray-600 max-w-3xl mx-auto mb-8">
          Ask questions about legal documents and get AI-powered answers with
          source references.
        </p>
      </section>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="mb-8">
        <div className="border border-gray-200 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center p-4">
            <span className="mr-3 text-gray-500">💬</span>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={
                conversationHistory.length > 0
                  ? "Ask a follow-up question..."
                  : "What would you like to know about legal matters?"
              }
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
          <p className="mt-4 text-gray-600">Processing your question...</p>
        </div>
      )}

      {conversationHistory.length > 0 && (
        <div className="border border-gray-200 rounded-xl overflow-hidden shadow-sm mb-8">
          <div className="p-5">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-medium">Conversation History</h2>
              <button
                onClick={handleClearConversation}
                className="text-sm text-gray-500 hover:text-gray-700 hover:underline"
                title="Clear conversation history"
              >
                Clear Chat
              </button>
            </div>
            <div className="space-y-4">
              {conversationHistory.map((msg, index) => (
                <div
                  key={index}
                  className={`p-4 rounded-lg ${
                    msg.role === "user"
                      ? "bg-gray-50 ml-10"
                      : "bg-white border border-gray-200 mr-10"
                  }`}
                >
                  <p className="text-sm font-medium text-gray-600 mb-2">
                    {msg.role === "user" ? "You" : "Assistant"}
                  </p>
                  <div className="text-gray-800">
                    {msg.role === "assistant" ? (
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    ) : (
                      msg.content
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {response && (
        <section className="border border-gray-200 rounded-xl overflow-hidden shadow-sm">
          <div className="p-6">
            {/* Sources */}
            {response.sources && response.sources.length > 0 && (
              <div className="mt-6 pt-6 border-t border-gray-100">
                <h3 className="text-base font-medium text-gray-700 mb-4">
                  Sources
                </h3>
                <div className="space-y-3">
                  {response.sources.map((source, index) => (
                    <div
                      key={index}
                      className="bg-gray-50 rounded-lg p-3 text-sm flex items-center gap-2"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-gray-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                      </svg>
                      <code className="text-gray-700 break-all">{source}</code>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Confidence */}
            {response.confidence !== undefined && (
              <div className="mt-4 flex items-center gap-2 text-sm">
                <span className="text-gray-600">
                  Confidence:{" "}
                  {response.confidence > 0.8
                    ? "High"
                    : response.confidence > 0.5
                      ? "Medium"
                      : "Low"}
                </span>
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      response.confidence > 0.8
                        ? "bg-green-500"
                        : response.confidence > 0.5
                          ? "bg-yellow-500"
                          : "bg-red-500"
                    }`}
                    style={{ width: `${response.confidence * 100}%` }}
                  ></div>
                </div>
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
