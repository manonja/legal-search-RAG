import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SearchPage from '@/app/search/page'; // Adjust if necessary
import { api, LegacyQueryResponse, LegacySearchResult } from '@/lib/api'; // Adjust if necessary

// Mock the API module
jest.mock('@/lib/api', () => ({
  api: {
    legacySearchDocuments: jest.fn(),
    getDocument: jest.fn(), // Mock if DocumentModal or SearchResultCard uses it
  },
}));

// Mock Sentry
jest.mock('@sentry/nextjs', () => ({
  captureException: jest.fn(),
}));

// Mock useRouter
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

// Mock SearchResultCard to isolate SearchPage logic
// Render basic info for verification
jest.mock('@/components/SearchResultCard', () => {
  return jest.fn(({ result, index }) => (
    <div data-testid={`search-result-card-${index}`}>
      <p>{result.text}</p>
      <span>Source: {result.metadata?.source}</span>
      {result.metadata?.page_number && <span>Page: {result.metadata.page_number}</span>}
      {/* Ensure distance is handled correctly for similarity calculation */}
      <span>Similarity: {result.distance !== undefined ? ((1 - result.distance) * 100).toFixed(1) : 'N/A'}%</span>
      <button>View Full Document</button> {/* Mock button */}
    </div>
  ));
});

// // Removed DocumentModal mock as interaction is tested elsewhere
// jest.mock('@/components/DocumentModal', /* ... */);


describe('SearchPage Integration Tests', () => {
  const mockApi = api as jest.Mocked<typeof api>;

  beforeEach(() => {
    jest.clearAllMocks();
     mockApi.legacySearchDocuments.mockResolvedValue({
       results: [],
       total_found: 0
     });
  });

  test('renders search form correctly', () => {
    render(<SearchPage />);
    expect(screen.getByPlaceholderText(/Search legal documents.../i)).toBeInTheDocument();
    expect(screen.getByTestId('search-submit-button')).toBeInTheDocument();
    expect(screen.getByTestId('search-submit-button')).toHaveTextContent('Search');
  });

  test('handles successful search and displays results', async () => {
    // --- Setup Mock Data ---
    // Ensure mock data aligns with the SearchResult type expected after mapping
    // The component maps `similarity` to `distance = 1 - similarity`
    const mockApiResponse: LegacyQueryResponse = {
       results: [
        // Provide similarity OR distance if your component mapping uses it
        { chunk: 'Obligation result 1', metadata: { source: 'doc1.txt', document_id: 'id1', page_number: 1, original_file_path: '/path/doc1.txt'}, similarity: 0.85, rank: 1 },
        { chunk: 'Obligation result 2', metadata: { source: 'doc2.pdf', document_id: 'id2', original_file_path: '/path/doc2.pdf'}, similarity: 0.75, rank: 2 },
       ],
       total_found: 2
    };
    mockApi.legacySearchDocuments.mockResolvedValueOnce(mockApiResponse);

    render(<SearchPage />);
    const input = screen.getByPlaceholderText(/Search legal documents.../i);
    const submitButton = screen.getByTestId('search-submit-button');

    // --- Action ---
    fireEvent.change(input, { target: { value: 'obligation' } });
    fireEvent.click(submitButton);

    // --- Assertions ---

    // Wait specifically for the button to become disabled AND spinner to appear
    await waitFor(() => {
        expect(submitButton).toBeDisabled();
        expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });

    // Wait for API call and results rendering
    await waitFor(() => {
      expect(api.legacySearchDocuments).toHaveBeenCalledTimes(1);
      expect(api.legacySearchDocuments).toHaveBeenCalledWith({
        query_text: 'obligation',
        n_results: 10,
        min_similarity: 0.7,
      });
    });

    // Wait for UI updates after loading finishes
    await waitFor(() => {
      expect(screen.getByText(/Found 2 results/i)).toBeInTheDocument();
      // Check content rendered by the mocked SearchResultCard
      expect(screen.getByText('Obligation result 1')).toBeInTheDocument();
      expect(screen.getByText('Obligation result 2')).toBeInTheDocument();
      expect(screen.getByText('Source: doc1.txt')).toBeInTheDocument();
      expect(screen.getByText('Page: 1')).toBeInTheDocument();
      expect(screen.getByText('Source: doc2.pdf')).toBeInTheDocument();
      // Check similarity based on mapped distance in SearchResult (distance = 1 - similarity)
      expect(screen.getByText('Similarity: 85.0%')).toBeInTheDocument(); // 1 - (1 - 0.85) = 0.85
      expect(screen.getByText('Similarity: 75.0%')).toBeInTheDocument(); // 1 - (1 - 0.75) = 0.75

      // Final check: loading indicators gone, button enabled
      expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument();
      expect(screen.queryByText(/Searching documents.../i)).not.toBeInTheDocument(); // Loading text below results
      expect(submitButton).toBeEnabled();
    });
  });

  test('displays "no results found" message', async () => {
    mockApi.legacySearchDocuments.mockResolvedValueOnce({ results: [], total_found: 0 });
    render(<SearchPage />);
    const input = screen.getByPlaceholderText(/Search legal documents.../i);
    const submitButton = screen.getByTestId('search-submit-button');

    fireEvent.change(input, { target: { value: 'obscure term' } });
    fireEvent.click(submitButton);

     // Wait for button to disable and spinner
    await waitFor(() => {
        expect(submitButton).toBeDisabled();
        expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });


    // Wait for the "no results" message to appear
    await waitFor(() => {
      expect(screen.getByText(/No results found. Try a different search term./i)).toBeInTheDocument();
    });

    // Verify API was called
    expect(api.legacySearchDocuments).toHaveBeenCalledTimes(1);
    // Ensure no result cards are rendered
    expect(screen.queryByTestId(/search-result-card-/)).not.toBeInTheDocument();
     // Ensure loading indicators are gone and button re-enabled
    expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument();
    expect(screen.queryByText(/Searching documents.../i)).not.toBeInTheDocument();
    expect(submitButton).toBeEnabled();
  });

  test('handles API error during search', async () => {
    const errorMessage = 'Network Error';
    mockApi.legacySearchDocuments.mockRejectedValueOnce(new Error(errorMessage));
    render(<SearchPage />);
    const input = screen.getByPlaceholderText(/Search legal documents.../i);
    const submitButton = screen.getByTestId('search-submit-button');

    fireEvent.change(input, { target: { value: 'trigger error' } });
    fireEvent.click(submitButton);

    // Wait for button to disable and spinner
    await waitFor(() => {
        expect(submitButton).toBeDisabled();
        expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });

    // Wait for the error message UI update
    await waitFor(() => {
      expect(screen.getByText(/An error occurred while searching. Please try again./i)).toBeInTheDocument();
    });

    // Verify API call and Sentry call
    expect(api.legacySearchDocuments).toHaveBeenCalledTimes(1);
    expect(jest.requireMock('@sentry/nextjs').captureException).toHaveBeenCalled();
     // Ensure loading indicators are gone and button re-enabled
    expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument();
    expect(screen.queryByText(/Searching documents.../i)).not.toBeInTheDocument();
    expect(submitButton).toBeEnabled(); // Button should be enabled after error
  });

  // Removed the modal interaction part of the test as it tests mocked component internals
  test('renders "View Full Document" button within result card mock', async () => {
      const mockResultsData: LegacySearchResult[] = [
        { chunk: 'Result text.', metadata: { source: 'doc-modal.txt', document_id: 'id-modal', original_file_path: '/path/modal.txt'}, similarity: 0.9, rank: 1 },
      ];
      mockApi.legacySearchDocuments.mockResolvedValueOnce({ results: mockResultsData, total_found: 1 });

      render(<SearchPage />);

      fireEvent.change(screen.getByPlaceholderText(/Search legal documents.../i), { target: { value: 'modal test' } });
      fireEvent.click(screen.getByTestId('search-submit-button'));

      // Wait for the result card and find the button inside it
      const viewButton = await screen.findByRole('button', { name: /View Full Document/i });
      expect(viewButton).toBeInTheDocument();

      // // Modal interaction logic removed - test this with SearchResultCard unit/integration tests
      // expect(screen.queryByTestId('document-modal')).not.toBeInTheDocument();
      // fireEvent.click(viewButton);
      // await waitFor(() => { /* ... */ });
      // fireEvent.click(closeModalButton);
      // await waitFor(() => { /* ... */ });
    });

});
