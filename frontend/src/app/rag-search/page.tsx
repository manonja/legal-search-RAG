"use client";

import { api, RagRequest, RagResponse } from "@/lib/api";
import { useState } from "react";
import ReactMarkdown from "react-markdown";

export default function RagSearchPage() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState<RagResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showContext, setShowContext] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversationHistory, setConversationHistory] = useState<
    Array<{ role: string; content: string }>
  >([]);

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
      const request: RagRequest = {
        query: query,
        n_results: 5,
        min_similarity: 0.7,
        model: "gpt-4",
        temperature: 0,
        max_tokens: 1000,
      };

      // Add conversation ID if this is a follow-up question
      if (conversationId) {
        request.conversation_id = conversationId;
        request.messages = conversationHistory;
      }

      const result = await api.ragSearch(request);
      setResponse(result);

      // Update conversation history
      setConversationId(result.conversation_id);
      setConversationHistory([
        ...conversationHistory,
        { role: "user", content: query },
        { role: "assistant", content: result.answer },
      ]);

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
                conversationId
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
            <h2 className="text-lg font-medium mb-4">Conversation History</h2>
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
            {/* Answer Section */}
            <div className="prose max-w-none mb-6">
              <ReactMarkdown>{response.answer}</ReactMarkdown>
            </div>

            {/* Usage Information */}
            {response.usage && (
              <div className="flex justify-between items-center text-sm text-gray-500 border-t border-gray-100 pt-4 mb-6">
                <div>
                  Tokens: {response.usage.input_tokens} input +{" "}
                  {response.usage.output_tokens} output ={" "}
                  {response.usage.total_tokens} total
                </div>
                <div className="font-medium">
                  Cost: ${response.usage.cost.toFixed(4)}
                </div>
              </div>
            )}

            {/* Source Documents */}
            <div className="mb-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-800">
                  Source Documents
                </h3>
                <span className="text-sm text-gray-500">
                  {response.source_documents.length} source
                  {response.source_documents.length !== 1 ? "s" : ""}
                </span>
              </div>
              <div className="space-y-4">
                {response.source_documents.map((source, index) => (
                  <div
                    key={index}
                    className="p-4 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-medium text-gray-900">
                        {source.metadata.filename || "Unknown Source"}
                      </h4>
                      <span className="text-sm text-gray-500">
                        {(source.similarity * 100).toFixed(1)}% match
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 line-clamp-2">
                      {source.content}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Context Details */}
            <div className="border-t border-gray-100 pt-6">
              <div className="flex justify-between items-center mb-4">
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
                <div className="space-y-6">
                  {response.source_documents.map((result, index) => (
                    <div
                      key={index}
                      className="pb-6 border-b border-gray-100 last:border-b-0 last:pb-0"
                    >
                      <div className="flex justify-between items-center mb-3">
                        <span className="text-sm text-gray-500">
                          {result.metadata.filename || "Unknown Document"}
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
                      <p className="text-gray-700 leading-relaxed">
                        {highlightText(result.content, query)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
