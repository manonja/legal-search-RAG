"use client";

import {
  QueryRequest,
  QueryResponse,
  api,
} from "@/lib/api"; // Assuming api lib structure
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { v4 as uuidv4 } from "uuid"; // Need to install uuid: npm install uuid @types/uuid

// Define the structure for a single turn in the conversation
interface ConversationTurn {
  id: string; // Unique ID for this turn
  userQuery: string;
  assistantResponse: {
    answer: string;
    sources: string[];
    confidence: number | null;
  } | null;
  isLoading: boolean;
  error: string | null;
  feedback?: "up" | "down"; // Placeholder for future feedback state
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
    localStorage.removeItem("legalChatHistory"); // Clear corrupted data
    return [];
  }
};

export default function RagSearchPage() {
  const [query, setQuery] = useState("");
  const [conversationTurns, setConversationTurns] = useState<ConversationTurn[]>([]);
  const [isClient, setIsClient] = useState(false); // Track client-side mount for localStorage

  // Load from localStorage on client-side mount
  useEffect(() => {
    setIsClient(true);
    setConversationTurns(getInitialTurns());
  }, []);

  // Save to localStorage whenever turns change on the client
  useEffect(() => {
    if (isClient) {
      try {
        localStorage.setItem("legalChatHistory", JSON.stringify(conversationTurns));
      } catch (error) {
        console.error("Failed to save chat history to localStorage:", error);
        // Handle potential storage quota issues if necessary
      }
    }
  }, [conversationTurns, isClient]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const currentQuery = query.trim();
    if (!currentQuery || conversationTurns.some(turn => turn.isLoading)) return; // Prevent search if empty or already loading

    const turnId = uuidv4(); // Generate unique ID for this turn
    const newTurn: ConversationTurn = {
      id: turnId,
      userQuery: currentQuery,
      assistantResponse: null,
      isLoading: true,
      error: null,
    };

    // Add the new turn with loading state
    setConversationTurns((prevTurns) => [...prevTurns, newTurn]);
    setQuery(""); // Clear input field immediately

    try {
      const request: QueryRequest = {
        query: currentQuery,
        max_results: 5, // Keep params as before
        temperature: 0.7,
        max_tokens: 1000,
        // conversation_id: conversationId, // Pass if needed by backend
      };

      const result: QueryResponse = await api.ragSearch(request); // Use your actual API call

      // Update the specific turn with the response
      setConversationTurns((prevTurns) =>
        prevTurns.map((turn) =>
          turn.id === turnId
            ? {
                ...turn,
                isLoading: false,
                assistantResponse: {
                  answer: result.answer,
                  sources: result.sources || [], // Ensure sources is always an array
                  confidence: result.confidence ?? null, // Handle potential undefined confidence
                },
              }
            : turn
        )
      );

      // Optional: Emit event if needed elsewhere
      // window.dispatchEvent(new Event("search-performed"));

    } catch (err) {
      console.error("RAG search error:", err);
      const errorMessage = err instanceof Error ? err.message : "An unknown error occurred.";

      // Update the specific turn with the error
      setConversationTurns((prevTurns) =>
        prevTurns.map((turn) =>
          turn.id === turnId
            ? { ...turn, isLoading: false, error: `Failed to get answer: ${errorMessage}` }
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
    setConversationTurns(prevTurns => prevTurns.map(turn =>
      turn.id === turnId ? { ...turn, feedback: feedbackType } : turn
    ));
    // TODO: Call API to log feedback - create /api/feedback route
    // fetch('/api/feedback', { method: 'POST', body: JSON.stringify({ turnId, feedbackType, ... }) });
  };

  // ---- Render Logic ----

  return (
    <div className="flex flex-col h-[calc(100vh-theme(spacing.16))] bg-gray-50" data-testid="rag-search-page"> {/* Adjust height & background */}
      {/* Header (Optional - Could be simpler for a chat interface) */}
       <header className="text-center py-4 border-b border-gray-200 bg-white sticky top-0 z-10"> {/* Reduced padding, sticky */}
         <h1 className="text-xl text-gray-800 font-semibold">Legal Assistant</h1> {/* Reduced size */}
         {/* <p className="text-sm text-gray-500">AI-powered answers with source references.</p> */}
       </header>

      {/* Conversation Area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6" data-testid="conversation-area"> {/* Removed bg-gray-50 here */}
        {conversationTurns.length === 0 && !isClient && (
             // Optional: Skeleton loading while waiting for client-side mount + localStorage read
             <div className="text-center text-gray-500 pt-10">Loading history...</div>
        )}
         {conversationTurns.length === 0 && isClient && (
             <div className="text-center text-gray-500 pt-10" data-testid="empty-chat-message">
                 Ask a question below to start the conversation.
             </div>
         )}
        {conversationTurns.map((turn) => (
          <div key={turn.id} className="space-y-4" data-testid={`turn-${turn.id}`}>
            {/* User Query */}
            <div className="flex justify-end">
              <div className="bg-blue-500 text-white p-3 rounded-lg max-w-xl shadow" data-testid="user-query">
                <p className="text-sm font-medium mb-1">You</p>
                <p>{turn.userQuery}</p>
              </div>
            </div>

            {/* Assistant Response Area */}
            {/* Render assistant area only if loading, error, or response exists */}
            {(turn.isLoading || turn.error || turn.assistantResponse) && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-200 p-4 rounded-lg max-w-xl shadow-sm w-full" data-testid="assistant-response-area"> {/* Ensure it takes width */}
                  <p className="text-sm font-medium text-gray-600 mb-2">Assistant</p>
                  {turn.isLoading && (
                    <div className="flex items-center gap-2 text-gray-500" data-testid="loading-indicator">
                      <div className="inline-block animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-gray-600"></div>
                      <span>Thinking...</span>
                    </div>
                  )}
                  {turn.error && (
                    <div className="bg-red-100 border border-red-300 text-red-700 px-3 py-2 rounded text-sm" data-testid="error-message">
                      {turn.error}
                    </div>
                  )}
                  {turn.assistantResponse && !turn.isLoading && !turn.error && ( // Only show content if not loading and no error
                    <div data-testid="assistant-content"> {/* Wrapper for content */}
                      <div className="prose prose-sm max-w-none text-gray-800" data-testid="assistant-answer">
                        <ReactMarkdown>
                          {turn.assistantResponse.answer}
                        </ReactMarkdown>
                      </div>

                      {/* Sources (within assistant block) */}
                      {turn.assistantResponse.sources && turn.assistantResponse.sources.length > 0 && (
                        <div className="mt-4 pt-3 border-t border-gray-100" data-testid="sources-section">
                          <h4 className="text-xs font-semibold text-gray-600 mb-2 uppercase">
                            Sources:
                          </h4>
                          <div className="space-y-2">
                            {turn.assistantResponse.sources.map((source, index) => (
                              <div
                                key={index}
                                className="bg-gray-100 rounded p-2 text-xs flex items-center gap-1.5" // Smaller padding & gap
                                data-testid="source-item"
                              >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5 text-gray-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                                </svg>
                                {/* Display only filename for cleaner UI (assuming paths) */}
                                <code className="text-gray-700 break-all">
                                  {source.includes('/') ? source.substring(source.lastIndexOf('/') + 1) : source}
                                </code>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                       {/* Confidence (within assistant block) */}
                      {turn.assistantResponse.confidence !== null && (
                        <div className="mt-3 pt-3 border-t border-gray-100 flex items-center gap-2 text-xs" data-testid="confidence-section">
                          <span className="text-gray-500 font-medium">Confidence:</span>
                          <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                             <div
                                className={`h-1.5 rounded-full ${
                                   turn.assistantResponse.confidence > 0.8
                                   ? "bg-green-500"
                                   : turn.assistantResponse.confidence > 0.5
                                   ? "bg-yellow-500"
                                   : "bg-red-500"
                                }`}
                                style={{ width: `${turn.assistantResponse.confidence * 100}%` }}
                             ></div>
                          </div>
                          <span className={`font-semibold ${
                              turn.assistantResponse.confidence > 0.8 ? "text-green-600" :
                              turn.assistantResponse.confidence > 0.5 ? "text-yellow-600" :
                              "text-red-600"
                          }`} data-testid="confidence-label">
                              {turn.assistantResponse.confidence > 0.8 ? "High" : turn.assistantResponse.confidence > 0.5 ? "Medium" : "Low"}
                              ({(turn.assistantResponse.confidence * 100).toFixed(0)}%)
                          </span>
                        </div>
                      )}

                      {/* Feedback Buttons (within assistant block) */}
                      <div className="mt-3 pt-3 border-t border-gray-100 flex items-center gap-2" data-testid="feedback-section">
                         <span className="text-xs text-gray-500">Was this helpful?</span>
                        <button
                          onClick={() => handleFeedback(turn.id, 'up')}
                          className={`p-1 rounded hover:bg-green-100 disabled:opacity-50 disabled:cursor-not-allowed ${turn.feedback === 'up' ? 'bg-green-100' : ''}`}
                          title="Good answer"
                          disabled={!!turn.feedback} // Disable after feedback
                          data-testid="feedback-up-button"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                          </svg>
                        </button>
                        <button
                          onClick={() => handleFeedback(turn.id, 'down')}
                          className={`p-1 rounded hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed ${turn.feedback === 'down' ? 'bg-red-100' : ''}`}
                          title="Bad answer"
                          disabled={!!turn.feedback} // Disable after feedback
                          data-testid="feedback-down-button"
                        >
                           <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                             <path strokeLinecap="round" strokeLinejoin="round" d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.738 3h4.017c.163 0 .326.02.485.06L17 4m-7 10v5a2 2 0 002 2h.095c.5 0 .905-.405.905-.905 0-.714.211-1.412.608-2.006L17 9V4m-7 10h2m-2 0H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                           </svg>
                        </button>
                        {turn.feedback && <span className="text-xs text-gray-500 italic" data-testid="feedback-confirmation">Thanks!</span>}
                      </div>
                    </div> // End assistant-content wrapper
                  )}
                </div>
              </div>
            )} {/* End conditional rendering for assistant area */}
          </div>
        ))}
      </div>

      {/* Input Area */}
      <div className="p-4 md:p-6 border-t border-gray-200 bg-white sticky bottom-0"> {/* Sticky bottom */}
         {conversationTurns.length > 0 && isClient && ( // Show clear button only on client and if turns exist
             <button
               onClick={handleClearConversation}
               className="absolute top-0 right-4 -mt-6 text-xs text-gray-400 hover:text-red-500 hover:underline bg-white px-2 py-0.5 rounded-t border-l border-t border-r border-gray-200" // Styling adjustments
               title="Clear conversation history"
               data-testid="clear-chat-button"
             >
               Clear Chat
             </button>
         )}
        <form onSubmit={handleSearch} className="flex items-center gap-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a legal question..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            required
            disabled={conversationTurns.some(turn => turn.isLoading)} // Disable input while loading
            data-testid="query-input"
          />
          <button
            type="submit"
            className="bg-gray-800 text-white px-5 py-2 rounded-full font-semibold hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            disabled={!query.trim() || conversationTurns.some(turn => turn.isLoading)}
            data-testid="ask-button"
          >
            {conversationTurns.some(turn => turn.isLoading) ? (
                 // Simple spinner for button
                 <div className="inline-block animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white" data-testid="submit-loading-spinner"></div>
            ) : (
                // Send Icon
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 16.571V11.5a1 1 0 011-1h.094a1 1 0 01.894.553l1.429 4.571a1 1 0 001.169 1.409l7-14a1 1 0 00-1.169-1.409l-5 1.429A1 1 0 0011 3.429V8.5a1 1 0 01-1 1h-.094a1 1 0 01-.894-.553z" />
                </svg>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
