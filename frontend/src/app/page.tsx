import Link from "next/link";

export default function Home() {
  return (
    <div className="container mx-auto px-4 max-w-7xl">
      {/* Hero Section */}
      <section className="text-center py-20">
        <h1 className="text-5xl text-gray-800 font-bold mb-5 leading-tight">
          Legal Search Made Easy
          <br />
          With Generative AI
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
          Search legal documents with semantic similarity and get AI-generated
          answers based on your data.
        </p>
        <div className="flex justify-center gap-4">
          <Link
            href="/search"
            className="bg-gray-800 text-white px-8 py-3 rounded-full font-semibold hover:bg-gray-700 transition-colors inline-block"
          >
            Try it now
          </Link>
          <Link
            href="/book-demo"
            className="bg-white text-gray-800 px-8 py-3 rounded-full font-semibold border border-gray-300 hover:bg-gray-50 transition-colors inline-block"
          >
            Book demo
          </Link>
        </div>
      </section>

      {/* Features Section */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-8 my-16">
        <Link
          href="/search"
          className="group border border-gray-200 rounded-xl p-8 hover:shadow-lg transition-all cursor-pointer bg-white"
        >
          <div className="flex items-start gap-4">
            <span className="text-3xl">🔍</span>
            <div>
              <h3 className="text-xl font-semibold mb-3 text-gray-900 group-hover:text-gray-700">
                Document Search
              </h3>
              <p className="text-gray-600 leading-relaxed">
                Search through your legal documents using semantic similarity to
                find exactly what you need. Our advanced search understands
                context and meaning, not just keywords.
              </p>
              <div className="mt-4 text-gray-800 font-medium flex items-center gap-2">
                Try Document Search
                <svg
                  className="w-4 h-4 transform group-hover:translate-x-1 transition-transform"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </div>
            </div>
          </div>
        </Link>

        <Link
          href="/rag-search"
          className="group border border-gray-200 rounded-xl p-8 hover:shadow-lg transition-all cursor-pointer bg-white"
        >
          <div className="flex items-start gap-4">
            <span className="text-3xl">💬</span>
            <div>
              <h3 className="text-xl font-semibold mb-3 text-gray-900 group-hover:text-gray-700">
                Ask Legal Questions
              </h3>
              <p className="text-gray-600 leading-relaxed">
                Get AI-generated answers to your legal questions based on your
                document corpus. Our RAG system provides accurate, context-aware
                responses with source citations.
              </p>
              <div className="mt-4 text-gray-800 font-medium flex items-center gap-2">
                Try RAG Search
                <svg
                  className="w-4 h-4 transform group-hover:translate-x-1 transition-transform"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </div>
            </div>
          </div>
        </Link>
      </section>

      {/* Demo Section */}
      <section className="border border-gray-200 rounded-xl overflow-hidden my-16 bg-white">
        <div className="p-8">
          <h2 className="text-2xl font-semibold mb-6 text-gray-900">
            Try an Example Search
          </h2>
          <div className="flex items-center p-4 border border-gray-200 rounded-xl mb-6">
            <span className="mr-3 text-gray-500">🔍</span>
            <input
              type="text"
              className="flex-1 bg-transparent border-none outline-none text-base"
              placeholder="Search legal documents..."
              defaultValue="malpractice"
              readOnly
            />
          </div>

          <div className="flex justify-between items-center mb-5 text-sm text-gray-500">
            <span>Found 10 results</span>
            <div className="flex items-center gap-1">
              <span>Sort by: Relevance</span>
              <span className="text-gray-400">▼</span>
            </div>
          </div>

          <div className="space-y-6">
            <div className="border-b border-gray-100 pb-6">
              <h3 className="text-xl font-semibold mb-3 text-gray-900">
                Malpractice cases can also be a complex issue, requiring medical
                expert opinions and often dealing...
              </h3>
              <div className="text-sm text-gray-500 mb-4">
                Similarity: 86.0%
              </div>
              <p className="text-gray-700 leading-relaxed">
                3 malpractice cases can also be a complex issue, requiring
                medical expert opinions and often dealing with competing causes
                and interrelated medical conditions.
              </p>
              <p className="inline-block mt-4 text-blue-600 hover:text-blue-700">
                View Full Document
              </p>
            </div>

            <div className="border-b border-gray-100 pb-6">
              <h3 className="text-xl font-semibold mb-3 text-gray-900">
                Causation in Medical Malpractice Cases (ON)
              </h3>
              <div className="text-sm text-gray-500 mb-4">
                Similarity: 85.4%
              </div>
              <p className="text-gray-700 leading-relaxed">
                2 1. The standard of care in medical malpractice claims is
                established by the practice of other expert physicians or health
                care providers, and is therefore not within the general
                knowledge of most lawyers (see: *Crits v. Sylvester*, [1956]
                O.J. No. 526 (C.A.)). As such, it is difficult or impossible for
                a lawyer to make an informed assessment of the viability of a
                potential case without assistance from an expert or multiple
                experts. Causation in...
              </p>
              <div className="flex items-center gap-2 mt-4">
                <p className="text-blue-600 hover:text-blue-700">
                  View Full Document
                </p>
              </div>
            </div>

            <Link
              href="/search"
              className="inline-flex items-center text-gray-800 font-medium hover:text-gray-600 transition-colors"
            >
              Try your own search
              <svg
                className="w-4 h-4 ml-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
