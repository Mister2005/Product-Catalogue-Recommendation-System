export default function Footer() {
  return (
    <footer className="bg-gray-900 text-white py-8 mt-auto">
      <div className="container mx-auto px-4 max-w-7xl">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <h3 className="font-bold text-lg mb-4">About</h3>
            <p className="text-gray-400 text-sm">
              Production-ready SHL Assessment Recommendation Engine with AI-powered intelligence,
              RAG technology, and multiple recommendation strategies.
            </p>
          </div>

          <div>
            <h3 className="font-bold text-lg mb-4">Features</h3>
            <ul className="text-gray-400 text-sm space-y-2">
              <li>✓ Gemini AI Integration</li>
              <li>✓ RAG-based Search</li>
              <li>✓ PostgreSQL Database</li>
              <li>✓ Redis Caching</li>
              <li>✓ Multiple ML Engines</li>
            </ul>
          </div>

          <div>
            <h3 className="font-bold text-lg mb-4">Technology Stack</h3>
            <ul className="text-gray-400 text-sm space-y-2">
              <li>• Next.js 14</li>
              <li>• FastAPI</li>
              <li>• PostgreSQL</li>
              <li>• Redis</li>
              <li>• Docker</li>
            </ul>
          </div>

          <div>
            <h3 className="font-bold text-lg mb-4">Links</h3>
            <ul className="text-gray-400 text-sm space-y-2">
              <li>
                <a
                  href="https://github.com/Mister2005/Product-Catalogue-Recommendation-System"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-blue-400 transition-colors"
                >
                  → GitHub Repository
                </a>
              </li>
              <li>
                <a
                  href="https://shl-recommendation-api-30oz.onrender.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-blue-400 transition-colors"
                >
                  → API Backend
                </a>
              </li>
              <li>
                <a
                  href="https://shl-recommendation-api-30oz.onrender.com/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-blue-400 transition-colors"
                >
                  → API Documentation
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-6 text-center text-gray-400 text-sm">
          <p>© 2025 SHL Assessment Recommendation Engine. All rights reserved.</p>
        </div>
      </div>
    </footer>
  )
}
