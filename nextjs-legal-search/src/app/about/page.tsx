export default function AboutPage() {
  return (
    <div className="container mx-auto px-4 max-w-7xl">
      {/* Header Section */}
      <section className="text-center py-10">
        <h1 className="text-4xl text-gray-800 font-bold mb-5">About</h1>
        <p className="text-lg text-gray-600 max-w-3xl mx-auto mb-8">
          Powerful legal research using generative AI
        </p>
      </section>

      {/* Content Section */}
      <section className="border border-gray-200 rounded-xl overflow-hidden my-10">
        <div className="p-16">
          <div className="prose max-w-none text-gray-700">
            <h2 className="text-2xl font-semibold mb-4 text-gray-900">
              Mission
            </h2>
            <p className="mb-6">
              Prae8 is a Retrieval-Augmented Generation (RAG) system
              specifically designed for legal document search. We combine vector
              search with large language model capabilities to provide accurate
              answers to legal queries based on your document corpus.
            </p>

            <h2 className="text-2xl font-semibold mb-4 text-gray-900">
              Features
            </h2>
            <ul className="space-y-2 mb-6">
              <li className="flex items-start">
                <span className="text-gray-800 mr-2">•</span>
                <span>
                  <strong>Document Processing Pipeline:</strong> Multi-format
                  support (PDF, DOC/DOCX), intelligent text chunking, and
                  semantic preservation
                </span>
              </li>
              <li className="flex items-start">
                <span className="text-gray-800 mr-2">•</span>
                <span>
                  <strong>Vector Search Infrastructure:</strong> Embeddings with
                  ChromaDB integration
                </span>
              </li>
              <li className="flex items-start">
                <span className="text-gray-800 mr-2">•</span>
                <span>
                  <strong>RAG-Powered Q&A:</strong> Ask legal questions and get
                  AI-generated answers based on your document corpus
                </span>
              </li>
            </ul>

            <h2 className="text-2xl font-semibold mb-4 text-gray-900">
              Technology
            </h2>
            <p className="mb-6">
              Our system is built using modern technologies to ensure
              performance, reliability, and scalability:
            </p>
            <ul className="space-y-2 mb-6">
              <li className="flex items-start">
                <span className="text-gray-800 mr-2">•</span>
                <span>
                  <strong>Backend:</strong> Python, FastAPI, LangChain, ChromaDB
                </span>
              </li>
              <li className="flex items-start">
                <span className="text-gray-800 mr-2">•</span>
                <span>
                  <strong>Frontend:</strong> Next.js, TypeScript, Tailwind CSS
                </span>
              </li>
              <li className="flex items-start">
                <span className="text-gray-800 mr-2">•</span>
                <span>
                  <strong>Document Processing:</strong> PyMuPDF, python-docx
                </span>
              </li>
              <li className="flex items-start">
                <span className="text-gray-800 mr-2">•</span>
                <span>
                  <strong>AI:</strong> OpenAI API for embeddings and completions
                </span>
              </li>
            </ul>

            <h2 className="text-2xl font-semibold mb-4 text-gray-900">
              Performance
            </h2>
            <p className="mb-6">
              Our system achieves 83% accuracy in legal QA benchmarks with sub-2
              second latency for query processing. We continuously improve our
              system through comprehensive testing protocols covering various
              legal query types.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
