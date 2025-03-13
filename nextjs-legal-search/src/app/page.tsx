import Link from "next/link";

export default function Home() {
  return (
    <div className="container mx-auto px-4 max-w-7xl">
      {/* Hero Section */}
      <section className="text-center py-20">
        <h1 className="text-5xl text-gray-800 font-bold mb-5 leading-tight">
          Legal Research Made Easy
          <br />
          With Generative AI
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
          Search legal documents with semantic similarity and AI generated
          answers based on your data.
          <br />
        </p>
        <div>
          <Link
            href="/signup"
            className="bg-gray-800 text-white px-8 py-3 rounded-full font-semibold mr-4 hover:bg-gray-800 transition-colors inline-block"
          >
            Start Free
          </Link>
          <span className="text-gray-600">2-week free trial.</span>
        </div>
      </section>

      {/* Features Section */}
      <section className="flex justify-center gap-5 my-12 flex-wrap">
        <Link
          href="/search"
          className="border border-gray-200 rounded-lg px-6 py-4 flex items-center gap-3 hover:shadow-md transition-all cursor-pointer"
        >
          <span className="text-xl">🔍</span>
          <span className="font-medium">Document Search</span>
        </Link>
        <Link
          href="/rag-search"
          className="border border-gray-200 rounded-lg px-6 py-4 flex items-center gap-3 hover:shadow-md transition-all cursor-pointer"
        >
          <span className="text-xl">💬</span>
          <span className="font-medium">Ask Legal Questions</span>
        </Link>
      </section>

      {/* Search Section */}
      <section className="border border-gray-200 rounded-xl overflow-hidden my-10">
        <div className="flex items-center p-4 border-b border-gray-200">
          <span className="mr-3 text-gray-500">🔍</span>
          <input
            type="text"
            className="flex-1 border-none outline-none text-base"
            placeholder="Search legal documents..."
            defaultValue="non-compete AND enforc*"
          />
        </div>

        <div className="p-5">
          <div className="flex justify-between items-center mb-5 text-sm text-gray-500">
            <span>5651 Results</span>
            <div className="flex items-center gap-1 cursor-pointer">
              Sort by: Relevance ▼
            </div>
          </div>

          <div className="mb-8 pb-5 border-b border-gray-200">
            <div className="flex gap-3 text-sm text-gray-500 mb-3">
              <span>14 F.3d 941</span>
              <span>|</span>
              <span>4th Cir.</span>
              <span>|</span>
              <span>1993</span>
            </div>
            <h3 className="text-xl font-semibold mb-3 text-gray-900">
              Php Healthcare Corporation v. Emsa Limited Partnership
            </h3>
            <div className="flex gap-3 mb-4 flex-wrap">
              <span className="bg-gray-100 px-3 py-1 rounded-full text-sm text-gray-600">
                Overview
              </span>
              <span className="bg-gray-100 px-3 py-1 rounded-full text-sm text-gray-600">
                Non-Compete
              </span>
              <span className="bg-gray-100 px-3 py-1 rounded-full text-sm text-gray-600">
                Enforceability
              </span>
            </div>
            <p className="text-gray-700 mb-4 leading-relaxed">
              "The only issue before us, as the parties agree, Appellant's Br.
              2; Appellee's Br. 1, is whether the district court erred in ruling
              that the 'limitation on practice' provision in EMSA's contracts
              with its Millington physician-employees was invalid and
              unenforceable under Florida law."
            </p>
            <div className="text-sm text-gray-500 flex items-center gap-2">
              <span>17m ago</span>
            </div>
          </div>

          <div className="mb-8 pb-5 border-b border-gray-200">
            <div className="flex gap-3 text-sm text-gray-500 mb-3">
              <span>203 F. App'x 450</span>
              <span>|</span>
              <span>4th Cir.</span>
              <span>|</span>
              <span>2006</span>
            </div>
            <h3 className="text-xl font-semibold mb-3 text-gray-900">
              McGough v. Nalco Company
            </h3>
            <div className="flex gap-3 mb-4 flex-wrap">
              <span className="bg-gray-100 px-3 py-1 rounded-full text-sm text-gray-600">
                Overview
              </span>
              <span className="bg-gray-100 px-3 py-1 rounded-full text-sm text-gray-600">
                Non-Compete
              </span>
              <span className="bg-gray-100 px-3 py-1 rounded-full text-sm text-gray-600">
                Injunction
              </span>
              <span className="bg-gray-100 px-3 py-1 rounded-full text-sm text-gray-600">
                Trade Secrets
              </span>
            </div>
            <p className="text-gray-700 mb-4 leading-relaxed">
              "A preliminary injunction is an 'extraordinary remedy' involving
              the exercise of very far-reaching power to be granted only
              sparingly and in limited circumstances."
            </p>
            <div className="text-sm text-gray-500 flex items-center gap-2">
              <span>16m ago</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
