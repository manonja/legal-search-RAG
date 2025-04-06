import { api, DocumentResponse, LegacySearchResult } from "@/lib/api";
import { Dialog, Transition } from "@headlessui/react";
import { Fragment, useEffect, useState } from "react";

interface DocumentModalProps {
  isOpen: boolean;
  onClose: () => void;
  document: LegacySearchResult | null;
}

export default function DocumentModal({
  isOpen,
  onClose,
  document,
}: DocumentModalProps) {
  const [fullDocument, setFullDocument] = useState<DocumentResponse | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchFullDocument() {
      // Use document_id if available, otherwise fallback (though source is likely wrong)
      const docId = document?.metadata?.document_id;
      const docSource = document?.metadata?.source;

      if (!docId && !docSource) {
        setError("Missing document identifier to fetch details.");
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        // Prefer document_id if available
        const identifier = docId || docSource!;
        const response = await api.getDocument(identifier);
        setFullDocument(response);
      } catch (err) {
        console.error("Error fetching document:", err);
        setError("Failed to load the full document. Please try again.");
      } finally {
        setIsLoading(false);
      }
    }

    if (isOpen && document) {
      fetchFullDocument();
    } else {
      setFullDocument(null);
      setError(null);
    }
  }, [isOpen, document]);

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-4xl transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                <Dialog.Title
                  as="h3"
                  className="text-lg font-medium leading-6 text-gray-900 mb-4"
                >
                  {fullDocument?.metadata?.title ||
                    document?.metadata?.source ||
                    "Document Details"}
                </Dialog.Title>

                {/* Display Metadata: Page Number and Original Path */}
                <div className="mb-4 space-y-2 text-sm text-gray-600">
                  {document?.metadata?.page_number && (
                    <div>
                      <span className="font-medium">Page:</span> {document.metadata.page_number}
                    </div>
                  )}
                  {document?.metadata?.original_file_path && (
                    <div>
                       <span className="font-medium">Original File:</span>
                       <span className="italic break-all">{document.metadata.original_file_path}</span>
                    </div>
                  )}
                </div>

                <div className="mt-2">
                  <div className="prose max-w-none">
                    {isLoading ? (
                      <div className="flex items-center justify-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
                      </div>
                    ) : error ? (
                      <div className="text-red-600 py-4">{error}</div>
                    ) : (
                      <div>
                        <p className="text-gray-700 whitespace-pre-wrap mb-4">
                          {fullDocument?.content ||
                            document?.chunk ||
                            "No content available"}
                        </p>
                        {fullDocument?.chunks &&
                          fullDocument.chunks.length > 1 && (
                            <div className="mt-4 pt-4 border-t border-gray-200">
                              <h4 className="text-sm font-medium text-gray-500 mb-2">
                                Document Chunks
                              </h4>
                              <div className="space-y-2">
                                {fullDocument.chunks.map((chunk, index) => (
                                  <div
                                    key={index}
                                    className="text-sm text-gray-600 p-3 rounded"
                                  >
                                    {chunk}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                      </div>
                    )}
                  </div>
                </div>

                <div className="mt-6 flex justify-end">
                  <button
                    type="button"
                    className="inline-flex justify-center rounded-md border border-transparent bg-gray-100 px-4 py-2 text-sm font-medium text-gray-900 hover:bg-gray-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-500 focus-visible:ring-offset-2"
                    onClick={onClose}
                  >
                    Close
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}
