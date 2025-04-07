import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import RagSearchPage from '@/app/rag-search/page';

// Define our mock response types
interface SourceItem {
  filename: string;
  document_id: string;
}

interface MockQueryResponse {
  answer: string;
  sources: SourceItem[];
  confidence: number;
}

// Mock the API module first, before importing other modules
jest.mock('@/lib/api', () => ({
  api: {
    ragSearch: jest.fn(),
  },
  // We don't need to export QueryResponse as we're not using it directly
}));

// Import the mocked API after mocking
import { api } from '@/lib/api';

// Mock Sentry if needed
jest.mock('@sentry/nextjs', () => ({
  captureException: jest.fn(),
}));

// Mock ReactMarkdown to avoid complex rendering issues in tests
jest.mock('react-markdown', () => {
  return jest.fn(({ children }) => <div data-testid="markdown-content">{children}</div>);
});

// Mock scrollIntoView - not implemented in JSDOM
window.HTMLElement.prototype.scrollIntoView = jest.fn();

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: jest.fn((key: string) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock UUID for predictable IDs
jest.mock('uuid', () => ({
  v4: jest.fn(() => 'mocked-uuid'),
}));

describe('RagSearchPage', () => {
  const mockApi = api as jest.Mocked<typeof api>;

  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.clear();

    // Default mock response - using any to bypass TypeScript's strict checking
    // This works because the component will handle the response appropriately
    mockApi.ragSearch.mockResolvedValue({
      answer: 'This is a test answer.',
      sources: [
        { filename: 'document1.pdf', document_id: 'doc1' },
        { filename: 'document2.pdf', document_id: 'doc2' },
      ],
      confidence: 0.85,
    } as any);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders landing page initially', () => {
    render(<RagSearchPage />);

    expect(screen.getByText('Legal Assistant')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Ask a legal question...')).toBeInTheDocument();
    expect(screen.getByTestId('ask-button')).toBeInTheDocument();
    expect(screen.getByTestId('landing-page')).toBeInTheDocument();

    // Conversation area should not be visible
    expect(screen.queryByTestId('conversation-area')).not.toBeInTheDocument();
  });

  test('handles user query submission and displays assistant response', async () => {
    // Mock API implementation that delays the response
    mockApi.ragSearch.mockImplementationOnce(() => {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve({
            answer: 'This is a test answer.',
            sources: [
              { filename: 'document1.pdf', document_id: 'doc1' },
              { filename: 'document2.pdf', document_id: 'doc2' },
            ],
            confidence: 0.85,
          } as any); // Type assertion to bypass TypeScript errors
        }, 100); // Add delay to ensure loading state is visible
      });
    });

    render(<RagSearchPage />);

    // Get input and submit button
    const inputField = screen.getByPlaceholderText('Ask a legal question...');
    const submitButton = screen.getByTestId('ask-button');

    // Enter a query and submit
    fireEvent.change(inputField, { target: { value: 'What is product liability?' } });
    fireEvent.click(submitButton);

    // First verify the loading state appears right after submission
    // Using findByTestId instead of getByTestId to allow time for rendering
    const loadingIndicator = await screen.findByTestId('loading-indicator');
    expect(loadingIndicator).toBeInTheDocument();

    // Verify the query was submitted
    expect(mockApi.ragSearch).toHaveBeenCalledWith(expect.objectContaining({
      query: 'What is product liability?',
    }));

    // Verify the response is rendered after loading completes
    await waitFor(() => {
      // Check user query displayed
      expect(screen.getByText('You')).toBeInTheDocument();
      expect(screen.getByText('What is product liability?')).toBeInTheDocument();

      // Check assistant response displayed
      expect(screen.getByText('Assistant')).toBeInTheDocument();
      expect(screen.getByTestId('markdown-content')).toHaveTextContent('This is a test answer.');

      // Check sources displayed
      expect(screen.getByText('Sources:')).toBeInTheDocument();
      expect(screen.getAllByTestId('source-item').length).toBe(2);
      expect(screen.getByText('document1.pdf')).toBeInTheDocument();
      expect(screen.getByText('document2.pdf')).toBeInTheDocument();

      // Check confidence displayed
      expect(screen.getByText('Confidence:')).toBeInTheDocument();
      expect(screen.getByTestId('confidence-label')).toHaveTextContent('High (85%)');

      // Check feedback UI
      expect(screen.getByText('Was this helpful?')).toBeInTheDocument();
      expect(screen.getByTestId('feedback-up-button')).toBeInTheDocument();
      expect(screen.getByTestId('feedback-down-button')).toBeInTheDocument();
    });

    // Chat interface should be visible now
    expect(screen.getByTestId('chat-interface')).toBeInTheDocument();
  });

  test('handles errors when submitting a query', async () => {
    mockApi.ragSearch.mockRejectedValueOnce(new Error('API Error'));

    render(<RagSearchPage />);

    // Get input and submit button
    const inputField = screen.getByPlaceholderText('Ask a legal question...');
    const submitButton = screen.getByTestId('ask-button');

    // Enter a query and submit
    fireEvent.change(inputField, { target: { value: 'This will cause an error' } });
    fireEvent.click(submitButton);

    // Verify the query was submitted
    await waitFor(() => {
      expect(mockApi.ragSearch).toHaveBeenCalledWith(expect.objectContaining({
        query: 'This will cause an error',
      }));
    });

    // Verify error message is displayed
    await waitFor(() => {
      expect(screen.getByTestId('error-message')).toBeInTheDocument();
      expect(screen.getByTestId('error-message')).toHaveTextContent('Failed to get answer: API Error');
    });
  });

  test('handles duplicate sources', async () => {
    // Mock response with duplicate sources
    mockApi.ragSearch.mockResolvedValueOnce({
      answer: 'This is a test answer with duplicate sources.',
      sources: [
        { filename: 'duplicate.pdf', document_id: 'doc1' },
        { filename: 'duplicate.pdf', document_id: 'doc2' }, // Same filename, different ID
        { filename: 'unique.pdf', document_id: 'doc3' },
      ],
      confidence: 0.75,
    } as any);

    render(<RagSearchPage />);

    // Get input and submit button
    const inputField = screen.getByPlaceholderText('Ask a legal question...');
    const submitButton = screen.getByTestId('ask-button');

    // Enter a query and submit
    fireEvent.change(inputField, { target: { value: 'Query with duplicate sources' } });
    fireEvent.click(submitButton);

    // Verify response with deduplicated sources
    await waitFor(() => {
      // Should only have 2 source items (duplicate.pdf should only appear once)
      expect(screen.getAllByTestId('source-item').length).toBe(2);
      expect(screen.getByText('duplicate.pdf')).toBeInTheDocument();
      expect(screen.getByText('unique.pdf')).toBeInTheDocument();
    });
  });

  test('provides feedback on assistant response', async () => {
    render(<RagSearchPage />);

    // Submit a query
    const inputField = screen.getByPlaceholderText('Ask a legal question...');
    const submitButton = screen.getByTestId('ask-button');

    fireEvent.change(inputField, { target: { value: 'Test query for feedback' } });
    fireEvent.click(submitButton);

    // Wait for response
    await waitFor(() => {
      expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    });

    // Click positive feedback button
    const upButton = screen.getByTestId('feedback-up-button');
    fireEvent.click(upButton);

    // Verify feedback was recorded
    await waitFor(() => {
      expect(screen.getByText('Thanks!')).toBeInTheDocument();
      expect(upButton).toBeDisabled();
      expect(screen.getByTestId('feedback-down-button')).toBeDisabled();
    });
  });

  test('clears conversation history', async () => {
    render(<RagSearchPage />);

    // Submit a query to initiate conversation
    const inputField = screen.getByPlaceholderText('Ask a legal question...');
    const submitButton = screen.getByTestId('ask-button');

    fireEvent.change(inputField, { target: { value: 'Initial query' } });
    fireEvent.click(submitButton);

    // Wait for response
    await waitFor(() => {
      expect(screen.getByTestId('chat-interface')).toBeInTheDocument();
    });

    // Clear the conversation
    const clearButton = screen.getByTestId('clear-chat-button');
    fireEvent.click(clearButton);

    // Verify the landing page is back
    await waitFor(() => {
      expect(screen.getByTestId('landing-page')).toBeInTheDocument();
      expect(screen.queryByTestId('chat-interface')).not.toBeInTheDocument();
    });

    // Verify local storage was cleared
    expect(localStorageMock.clear).toHaveBeenCalled();
  });

  test('loads conversation history from localStorage', async () => {
    // Set up mock conversation history in localStorage
    const mockHistory = [
      {
        id: 'stored-id-1',
        userQuery: 'Stored question',
        assistantResponse: {
          answer: 'Stored answer',
          sources: [{ filename: 'stored-doc.pdf', document_id: 'stored-doc-id' }],
          confidence: 0.9
        },
        isLoading: false,
        error: null
      }
    ];

    localStorageMock.getItem.mockReturnValue(JSON.stringify(mockHistory));

    render(<RagSearchPage />);

    // Verify the stored conversation is loaded
    await waitFor(() => {
      expect(screen.getByText('Stored question')).toBeInTheDocument();
      expect(screen.getByText('Stored answer')).toBeInTheDocument();
      expect(screen.getByText('stored-doc.pdf')).toBeInTheDocument();
      expect(screen.getByTestId('chat-interface')).toBeInTheDocument();
    });
  });

  test('handles multiple conversation turns', async () => {
    // Reset localStorage mock completely
    localStorageMock.clear();
    // Make sure getItem returns null for this test
    localStorageMock.getItem.mockReturnValue(null);

    // Reset the mock APIs
    mockApi.ragSearch.mockReset();

    // Important: Reset the UUID mock to ensure different IDs
    const mockUuid = require('uuid');
    mockUuid.v4.mockImplementationOnce(() => 'first-turn-id');
    mockUuid.v4.mockImplementationOnce(() => 'second-turn-id');

    // First query response
    mockApi.ragSearch.mockImplementationOnce(() => {
      console.log("Executing first mock response");
      return Promise.resolve({
        answer: 'This is a test answer.',
        sources: [
          { filename: 'document1.pdf', document_id: 'doc1' } as any,
          { filename: 'document2.pdf', document_id: 'doc2' } as any,
        ],
        confidence: 0.85,
      });
    });

    // Second query response
    mockApi.ragSearch.mockImplementationOnce(() => {
      console.log("Executing second mock response");
      return Promise.resolve({
        answer: 'Second answer is different.',
        sources: [{ filename: 'second-doc.pdf', document_id: 'doc-second' } as any],
        confidence: 0.65,
      });
    });

    // Create a fresh render instance
    const { getByText, findByText, findAllByText, getByPlaceholderText, getByTestId, getAllByTestId, queryByTestId } = render(
      <RagSearchPage />
    );

    // Verify landing page is visible initially
    expect(getByTestId('landing-page')).toBeInTheDocument();

    // ------ First Query ------
    console.log("Submitting first query");
    const inputField = getByPlaceholderText('Ask a legal question...');
    const submitButton = getByTestId('ask-button');

    fireEvent.change(inputField, { target: { value: 'First query' } });
    fireEvent.click(submitButton);

    // Wait for first response
    console.log("Waiting for first response");
    await findByText('This is a test answer.');

    // Check that the first API was called
    expect(mockApi.ragSearch).toHaveBeenCalledTimes(1);

    // ------ Second Query ------
    console.log("Submitting second query");
    const secondInputField = getByPlaceholderText('Ask a legal question...');
    const secondSubmitButton = getByTestId('ask-button');

    fireEvent.change(secondInputField, { target: { value: 'Second query' } });
    fireEvent.click(secondSubmitButton);

    // Wait for second response
    console.log("Waiting for second response");
    await findAllByText('Second answer is different.');

    // Check that both APIs were called
    expect(mockApi.ragSearch).toHaveBeenCalledTimes(2);

    // Now capture all conversation turns
    const turns = getAllByTestId(/^turn-/);
    console.log(`Found ${turns.length} turns with IDs:`,
      turns.map(t => t.getAttribute('data-testid')));

    // Log the content of each turn for debugging
    turns.forEach((turn, i) => {
      console.log(`Turn ${i} content:`, turn.textContent);
    });

    // Check we have two turns
    expect(turns.length).toBe(2);

    // Check for both queries and answers using individual assertions
    // This is more diagnostic than the combined assertion
    const hasFirstQuery = turns.some(turn => turn.textContent?.includes('First query'));
    const hasFirstAnswer = turns.some(turn => turn.textContent?.includes('This is a test answer.'));
    const hasSecondQuery = turns.some(turn => turn.textContent?.includes('Second query'));
    const hasSecondAnswer = turns.some(turn => turn.textContent?.includes('Second answer is different.'));

    expect(hasFirstQuery).toBe(true);
    expect(hasFirstAnswer).toBe(true);
    expect(hasSecondQuery).toBe(true);
    expect(hasSecondAnswer).toBe(true);

    // Now check for source and confidence elements
    await findAllByText('second-doc.pdf');
    await findAllByText('Medium (65%)');
  });
});
