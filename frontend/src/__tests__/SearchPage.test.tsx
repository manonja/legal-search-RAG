import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SearchPage from '@/app/search/page';
import { api, SearchResult, LegacySearchResult } from '@/lib/api';

// Mock the API module
jest.mock('@/lib/api', () => ({
  api: {
    legacySearchDocuments: jest.fn(),
    getDocument: jest.fn(), // Mock getDocument as DocumentModal uses it
  },
  // Need to export all types used by the component and tests
  LegacyQueryRequest: jest.fn(),
  SearchResult: jest.fn(),
  LegacySearchResult: jest.fn(),
}));

// Mock Sentry
jest.mock('@sentry/nextjs', () => ({
  captureException: jest.fn(),
}));

// Mock DocumentModal to avoid testing its internals here
// Ensure the mock component accepts the props used in SearchResultCard
jest.mock('@/components/DocumentModal', () => {
  return function DummyDocumentModal({ isOpen, onClose }: { isOpen: boolean, onClose: () => void }) {
    if (!isOpen) return null;
    return (
      <div data-testid="document-modal">
        <span>Document Modal Content</span>
        <button onClick={onClose}>Close Modal</button>
      </div>
    );
  };
});

describe('SearchPage Integration Tests', () => {
  // Use proper type casting for the mocked api object
  const mockApi = api as jest.Mocked<typeof api>;

  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();
  });

  test('renders search form correctly', () => {
    render(<SearchPage />);
    expect(screen.getByPlaceholderText(/Search legal documents.../i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Search/i })).toBeInTheDocument();
  });

  test('handles successful search and displays results', async () => {
    // Mock data needs to match LegacySearchResult type for the mock function signature
    const mockResults: LegacySearchResult[] = [
      {
        chunk: 'This is the first result chunk about obligations.',
        metadata: { source: 'doc1.txt', document_id: 'id1', page_number: 1, original_file_path: '/path/to/doc1.txt' },
        similarity: 0.85,
        rank: 1,
      },
      {
        chunk: 'Second result discussing contractual obligations.',
        metadata: { source: 'doc2.pdf', document_id: 'id2', original_file_path: '/path/to/doc2.pdf' },
        similarity: 0.75,
        rank: 2,
      },
    ];
    // Mock the specific implementation for this test, returning LegacyQueryResponse structure
    mockApi.legacySearchDocuments.mockResolvedValueOnce({ results: mockResults, total_found: 2 });

    render(<SearchPage />);

    // Simulate user typing a query
    fireEvent.change(screen.getByPlaceholderText(/Search legal documents.../i), {
      target: { value: 'obligation' },
    });

    // Simulate form submission
    fireEvent.click(screen.getByRole('button', { name: /Search/i }));

    // Check for loading state
    expect(screen.getByRole('button', { name: /Searching.../i })).toBeDisabled();

    // Wait for results to appear
    await waitFor(() => {
      expect(screen.getByText(/Found 2 results/i)).toBeInTheDocument();
    });

    // Check if results are rendered (using text content)
    expect(screen.getAllByText(/This is the first result chunk/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Second result discussing contractual/i).length).toBeGreaterThan(0);

    // Check similarity calculation (1 - distance) * 100
    // Use waitFor to ensure elements are present after state update
    await waitFor(() => {
        expect(screen.getByText(/Similarity: 85.0%/)).toBeInTheDocument(); // 1 - 0.15 = 0.85
        expect(screen.getByText(/Similarity: 75.0%/)).toBeInTheDocument(); // 1 - 0.25 = 0.75
    });


    // Check metadata display
    expect(screen.getByText(/doc1.txt/)).toBeInTheDocument();
    expect(screen.getByText(/Page: 1/)).toBeInTheDocument();
    expect(screen.getByText(/doc2.pdf/)).toBeInTheDocument();
    // Page number might not be present for the second result
    expect(screen.queryByText(/Page: 2/)).not.toBeInTheDocument();
  });

  test('displays "no results found" message', async () => {
    // Return structure matching LegacyQueryResponse
    mockApi.legacySearchDocuments.mockResolvedValueOnce({ results: [], total_found: 0 });

    render(<SearchPage />);

    fireEvent.change(screen.getByPlaceholderText(/Search legal documents.../i), {
      target: { value: 'obscure term' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Search/i }));

    // Wait for the message to appear
    await waitFor(() => {
      expect(screen.getByText(/No results found/i)).toBeInTheDocument();
    });
    // Ensure results area is empty
    expect(screen.queryByText(/Similarity:/)).not.toBeInTheDocument();

    // Sentry should NOT be called in the no results case
    // expect(jest.requireMock('@sentry/nextjs').captureException).toHaveBeenCalled();
  });

  test('handles API error during search', async () => {
    const errorMessage = 'Network Error';
    mockApi.legacySearchDocuments.mockRejectedValueOnce(new Error(errorMessage));

    render(<SearchPage />);

    fireEvent.change(screen.getByPlaceholderText(/Search legal documents.../i), {
      target: { value: 'trigger error' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Search/i }));

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/An error occurred while searching. Please try again./i)).toBeInTheDocument();
    });

    // Verify Sentry was called (optional, but good practice)
    expect(jest.requireMock('@sentry/nextjs').captureException).toHaveBeenCalled();
  });

   test('clicking "View Full Document" opens the modal', async () => {
    // Mock data needs to match LegacySearchResult type
    const mockResults: LegacySearchResult[] = [
      {
        chunk: 'Result text to trigger modal.',
        metadata: { source: 'doc-modal.txt', document_id: 'id-modal', original_file_path: '/path/modal.txt' },
        similarity: 0.9,
        rank: 1,
      },
    ];
    // Return structure matching LegacyQueryResponse
    mockApi.legacySearchDocuments.mockResolvedValueOnce({ results: mockResults, total_found: 1 });

    render(<SearchPage />);

    fireEvent.change(screen.getByPlaceholderText(/Search legal documents.../i), {
      target: { value: 'modal test' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Search/i }));

    // Wait for result card and the button within it
    const viewButton = await screen.findByRole('button', { name: /View Full Document/i });

    // Check modal is initially closed
    expect(screen.queryByTestId('document-modal')).not.toBeInTheDocument();

    // Click the button to open the modal
    fireEvent.click(viewButton);

    // Check modal is open by looking for its test id
    await waitFor(() => {
        expect(screen.getByTestId('document-modal')).toBeInTheDocument();
    });
    // Check for content within the mocked modal
    expect(screen.getByText('Document Modal Content')).toBeInTheDocument();

    // Find and click the close button within the mocked modal
    const closeModalButton = screen.getByRole('button', { name: /Close Modal/i });
    fireEvent.click(closeModalButton);

    // Check modal is closed again
    await waitFor(() => {
        expect(screen.queryByTestId('document-modal')).not.toBeInTheDocument();
    });
  });

});
