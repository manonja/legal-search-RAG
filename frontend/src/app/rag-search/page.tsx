"use client";

import {
  QueryResponse as ApiQueryResponse,
  QueryRequest,
  api,
} from "@/lib/api"; // Assuming api lib structure
import * as Sentry from "@sentry/nextjs";
import { ChangeEvent, FormEvent, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { v4 as uuidv4 } from "uuid"; // Need to install uuid: npm install uuid @types/uuid
import AuthGuard from "@/components/auth/AuthGuard";

// Define local interfaces to match the actual response structure
interface SourceItem {
  filename: string;
  document_id: string;
}

// Our local QueryResponse that matches the actual API response structure
interface QueryResponse extends Omit<ApiQueryResponse, "sources"> {
  sources: SourceItem[];
}

// Define the structure for a single turn in the conversation
interface ConversationTurn {
  id: string; // Unique ID for this turn
  userQuery: string;
  assistantResponse: {
    answer: string;
    sources: SourceItem[];
    confidence: number | null;
  } | null;
  isLoading: boolean;
  error: string | null;
  feedback?: "up" | "down"; // Placeholder for future feedback state
  collectionName?: string; // Added collection name to track which collection was used
}

// Helper function to get initial state from localStorage
const getInitialTurns = (): ConversationTurn[] => {
  if (typeof window === "undefined") {
    return []; // Return empty array during SSR/build
  }
  try {
    const storedTurns = localStorage.getItem("legalChatHistory");
    return storedTurns ? JSON.parse(storedTurns) : [];
  } catch (error) {
    console.error("Failed to parse chat history from localStorage:", error);
    if (process.env.NODE_ENV === "production") {
      Sentry.captureException(error);
    }
    localStorage.removeItem("legalChatHistory"); // Clear corrupted data
    return [];
  }
};

// --- Standalone Input Form Component ---

interface QueryInputFormProps {
  value: string;
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  isLoading: boolean;
  isSticky?: boolean;
  collectionName: string;
  onCollectionChange: (event: ChangeEvent<HTMLSelectElement>) => void;
}

const QueryInputForm = ({
  value,
  onChange,
  onSubmit,
  isLoading,
  isSticky = false,
  collectionName,
  onCollectionChange,
}: QueryInputFormProps) => (
  <form
    onSubmit={onSubmit} // Use passed onSubmit
    className={`flex flex-col gap-3 ${isSticky ? "p-4 md:p-6 border-t border-gray-200 bg-white sticky bottom-0 z-10" : "mb-8"}`}
  >
    <div
      className={`flex-1 border border-gray-200 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow ${isSticky ? "" : "max-w-3xl mx-auto"}`}
    >
      <div className="flex items-center p-3">
        <span className="mr-3 text-gray-400">💬</span>
        <input
          type="text"
          value={value} // Use passed value
          onChange={onChange} // Use passed onChange
          placeholder="Ask a legal question..."
          className="flex-1 border-none outline-none text-sm bg-transparent"
          required
          disabled={isLoading} // Use passed isLoading
          data-testid="query-input"
        />
        <button
          type="submit"
          className="bg-gray-800 text-white px-5 py-1.5 rounded-full font-semibold hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
          disabled={!value.trim() || isLoading} // Use passed value and isLoading
          data-testid="ask-button"
        >
          {isLoading ? (
            <div
              className="inline-block animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"
              data-testid="submit-loading-spinner"
            ></div>
          ) : (
            "Ask"
          )}
        </button>
      </div>
    </div>

    <div className={`flex justify-end text-sm ${isSticky ? "" : "max-w-3xl mx-auto"}`}>
      <label htmlFor="collection" className="text-gray-600 mr-2">Collection:</label>
      <select
        id="collection"
        value={collectionName}
        onChange={onCollectionChange}
        className="border border-gray-200 rounded-md p-1 text-sm"
        disabled={isLoading}
      >
        <option value="demo_docs_collection">Demo Documents</option>
        {/* Add other collection options as needed */}
      </select>
    </div>
  </form>
);

export default function RagSearchPage() {
  const [query, setQuery] = useState("");
  const [collectionName, setCollectionName] = useState<string>("demo_docs_collection");
  const [conversationTurns, setConversationTurns] = useState<
    ConversationTurn[]
  >([]);
  const [isClient, setIsClient] = useState(false); // Track client-side mount for localStorage
  const conversationEndRef = useRef<HTMLDivElement>(null); // Ref for scrolling

  // Load from localStorage on client-side mount
  useEffect(() => {
    setIsClient(true);
    setConversationTurns(getInitialTurns());

    // Load saved collection from localStorage
    const savedCollection = localStorage.getItem('ragCollectionName');
    if (savedCollection) {
      setCollectionName(savedCollection);
    }
  }, []);

  // Save to localStorage whenever turns change on the client
  useEffect(() => {
    if (isClient) {
      try {
        localStorage.setItem(
          "legalChatHistory",
          JSON.stringify(conversationTurns)
        );
      } catch (error) {
        console.error("Failed to save chat history to localStorage:", error);
        // Handle potential storage quota issues if necessary
      }
    }
  }, [conversationTurns, isClient]);

  // Save collection selection to localStorage
  useEffect(() => {
    if (isClient && collectionName) {
      localStorage.setItem('ragCollectionName', collectionName);
    }
  }, [collectionName, isClient]);

  // Auto-scroll to bottom when conversation turns update
  useEffect(() => {
    if (conversationTurns.length > 0) {
      conversationEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [conversationTurns]); // Dependency array includes conversationTurns

  const handleSearch = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const currentQuery = query.trim();
    const currentLoading = conversationTurns.some((turn) => turn.isLoading);
    if (!currentQuery || currentLoading) return;

    const turnId = uuidv4();
    const newTurn: ConversationTurn = {
      id: turnId,
      userQuery: currentQuery,
      assistantResponse: null,
      isLoading: true,
      error: null,
      collectionName: collectionName, // Store the collection used for this query
    };

    setConversationTurns((prevTurns) => [...prevTurns, newTurn]);
    setQuery("");

    try {
      const request: QueryRequest = {
        query: currentQuery,
        max_results: 5,
        temperature: 0.7,
        max_tokens: 1000,
      };

      // Type assert the response as our local QueryResponse and pass collection name
      const result = (await api.ragSearch(request, collectionName)) as unknown as QueryResponse;

      // Now update with the properly typed result
      setConversationTurns((prevTurns) =>
        prevTurns.map((turn) =>
          turn.id === turnId
            ? {
                ...turn,
                isLoading: false,
                assistantResponse: {
                  answer: result.answer,
                  sources: result.sources || [],
                  confidence: result.confidence ?? null,
                },
              }
            : turn
        )
      );
    } catch (err) {
      console.error("RAG search error:", err);
      if (process.env.NODE_ENV === "production" && err instanceof Error) {
        Sentry.captureException(err);
      }
      const errorMessage =
        err instanceof Error ? err.message : "An unknown error occurred.";

      setConversationTurns((prevTurns) =>
        prevTurns.map((turn) =>
          turn.id === turnId
            ? {
                ...turn,
                isLoading: false,
                error: `Failed to get answer: ${errorMessage}`,
              }
            : turn
        )
      );
    }
  };

  const handleClearConversation = () => {
    setConversationTurns([]);
    // localStorage is cleared automatically by the useEffect hook
    setQuery("");
  };

  // Placeholder for feedback handler (Phase 2/3)
  const handleFeedback = (turnId: string, feedbackType: "up" | "down") => {
    console.log(`Feedback for turn ${turnId}: ${feedbackType}`);
    // Logic to update turn state and call API will go here
    setConversationTurns((prevTurns) =>
      prevTurns.map((turn) =>
        turn.id === turnId ? { ...turn, feedback: feedbackType } : turn
      )
    );
    // TODO: Call API to log feedback - create /api/feedback route
    // fetch('/api/feedback', { method: 'POST', body: JSON.stringify({ turnId, feedbackType, ... }) });
  };

  // Simple handler for input change
  const handleQueryChange = (event: ChangeEvent<HTMLInputElement>) => {
    setQuery(event.target.value);
  };

  // Handler for collection change
  const handleCollectionChange = (event: ChangeEvent<HTMLSelectElement>) => {
    setCollectionName(event.target.value);
  };

  if (!isClient) {
    // Initial server render or loading state before hydration
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-gray-500">Loading Assistant...</div>
        {/* Or a more sophisticated skeleton loader */}
      </div>
    );
  }

  if (conversationTurns.length === 0) {
    // Render Landing Page View
    return (
      <div
        className="container mx-auto px-4 max-w-4xl pt-16"
        data-testid="landing-page"
      >
        <section className="text-center mb-12">
          <h1 className="text-4xl text-gray-800 font-bold mb-4">
            Legal Assistant
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Ask questions about legal documents and get AI-powered answers with
            source references.
          </p>
        </section>
        <QueryInputForm
          isSticky={false}
          value={query}
          onChange={handleQueryChange}
          onSubmit={handleSearch}
          isLoading={false}
          collectionName={collectionName}
          onCollectionChange={handleCollectionChange}
        />
      </div>
    );
  } else {
    // Render Chat Interface View
    // Calculate overall loading state *only* for the chat view
    const isOverallLoading = conversationTurns.some((turn) => turn.isLoading);
    return (
      <AuthGuard>
        <div
          className="flex flex-col h-[calc(100vh-theme(spacing.16))] bg-gray-50"
          data-testid="chat-interface"
        >
          <header className="text-center py-4 border-b border-gray-200 bg-white sticky top-0 z-20">
            <h1 className="text-xl text-gray-800 font-semibold">
              Legal Assistant
            </h1>
            {/* Clear button positioned absolutely relative to header or viewport */}
            {isClient && (
              <button
                onClick={handleClearConversation}
                className="absolute top-2 right-4 text-xs text-gray-400 hover:text-red-500 hover:underline p-2"
                title="Clear conversation history"
                data-testid="clear-chat-button"
              >
                Clear Chat
              </button>
            )}
          </header>

          {/* Conversation Area */}
          <div
            className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6"
            data-testid="conversation-area"
          >
            {conversationTurns.map((turn) => (
              <div
                key={turn.id}
                className="space-y-4"
                data-testid={`turn-${turn.id}`}
              >
                {/* User Query - Centered */}
                <div className="flex justify-center">
                  <div
                    className="bg-blue-400 text-white p-3 rounded-lg max-w-xl shadow mx-auto"
                    data-testid="user-query"
                  >
                    <p className="text-sm font-medium mb-1">You</p>
                    <p>{turn.userQuery}</p>
                    {turn.collectionName && (
                      <p className="text-xs opacity-75 mt-1">Collection: {turn.collectionName}</p>
                    )}
                  </div>
                </div>

                {/* Assistant Response Area - Centered */}
                {(turn.isLoading || turn.error || turn.assistantResponse) && (
                  <div className="flex justify-center">
                    <div
                      className="bg-white border border-gray-200 p-4 rounded-lg max-w-xl shadow-sm w-full mx-auto"
                      data-testid="assistant-response-area"
                    >
                      <p className="text-sm font-medium text-gray-600 mb-2">
                        Assistant
                      </p>
                      {/* Loading, Error, Content rendering remains the same as before */}
                      {turn.isLoading && (
                        <div
                          className="flex items-center gap-2 text-gray-500"
                          data-testid="loading-indicator"
                        >
                          <div className="inline-block animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-gray-600"></div>
                          <span>Thinking...</span>
                        </div>
                      )}
                      {turn.error && (
                        <div
                          className="bg-red-100 border border-red-300 text-red-700 px-3 py-2 rounded text-sm"
                          data-testid="error-message"
                        >
                          {turn.error}
                        </div>
                      )}
                      {turn.assistantResponse &&
                        !turn.isLoading &&
                        !turn.error && (
                          <div data-testid="assistant-content">
                            {/* Answer */}
                            <div
                              className="prose prose-sm max-w-none text-gray-800"
                              data-testid="assistant-answer"
                            >
                              <ReactMarkdown>
                                {turn.assistantResponse.answer}
                              </ReactMarkdown>
                            </div>
                            {/* Sources */}
                            {turn.assistantResponse?.sources &&
                              turn.assistantResponse.sources.length > 0 && (
                                <div
                                  className="mt-4 pt-3 border-t border-gray-100"
                                  data-testid="sources-section"
                                >
                                  <p className="text-sm font-medium text-gray-500 mb-2">
                                    Sources
                                  </p>
                                  <ul className="space-y-1">
                                    {turn.assistantResponse.sources.map(
                                      (source, idx) => (
                                        <li
                                          key={idx}
                                          className="text-xs text-blue-600 hover:underline"
                                          data-testid={`source-${idx}`}
                                        >
                                          <a
                                            href={`/documents/${encodeURIComponent(
                                              source.document_id
                                            )}`}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                          >
                                            {source.filename ||
                                              source.document_id ||
                                              `Source ${idx + 1}`}
                                          </a>
                                        </li>
                                      )
                                    )}
                                  </ul>
                                </div>
                              )}
                            {/* Feedback UI placeholder */}
                            <div
                              className="mt-4 flex items-center justify-end gap-2"
                              data-testid="feedback-buttons"
                            >
                              <button
                                onClick={() => handleFeedback(turn.id, "up")}
                                className={`text-xs px-2 py-1 rounded-full ${
                                  turn.feedback === "up"
                                    ? "bg-green-100 text-green-800"
                                    : "text-gray-500 hover:bg-gray-100"
                                }`}
                                title="This was helpful"
                                data-testid="feedback-up"
                              >
                                👍 Helpful
                              </button>
                              <button
                                onClick={() => handleFeedback(turn.id, "down")}
                                className={`text-xs px-2 py-1 rounded-full ${
                                  turn.feedback === "down"
                                    ? "bg-red-100 text-red-800"
                                    : "text-gray-500 hover:bg-gray-100"
                                }`}
                                title="This was not helpful"
                                data-testid="feedback-down"
                              >
                                👎 Not helpful
                              </button>
                            </div>
                          </div>
                        )}
                    </div>
                  </div>
                )}
              </div>
            ))}
            <div ref={conversationEndRef} />
          </div>

          {/* Sticky Input Form at Bottom */}
          <QueryInputForm
            isSticky={true}
            value={query}
            onChange={handleQueryChange}
            onSubmit={handleSearch}
            isLoading={isOverallLoading}
            collectionName={collectionName}
            onCollectionChange={handleCollectionChange}
          />
        </div>
      </AuthGuard>
    );
  }
}
