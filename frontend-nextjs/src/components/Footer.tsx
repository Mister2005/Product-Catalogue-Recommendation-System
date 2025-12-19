export default function Footer() {
  return (
    <footer className="bg-dark-secondary border-t border-white/10 text-white py-8 mt-auto">
      <div className="container mx-auto px-4 max-w-7xl">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <h3 className="font-bold text-lg mb-4 text-gradient">About</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Production-ready SHL Assessment Recommendation Engine with AI-powered intelligence,
              RAG technology, and multiple recommendation strategies.
            </p>
          </div>

          <div>
            <h3 className="font-bold text-lg mb-4 text-gradient-cyan">Features</h3>
            <ul className="text-slate-400 text-sm space-y-2">
              <li className="flex items-center gap-2">
                <span className="text-green-400">✓</span> Gemini AI Integration
              </li>
              <li className="flex items-center gap-2">
                <span className="text-green-400">✓</span> RAG-based Search
              </li>
              <li className="flex items-center gap-2">
                <span className="text-green-400">✓</span> PostgreSQL Database
              </li>
              <li className="flex items-center gap-2">
                <span className="text-green-400">✓</span> Redis Caching
              </li>
              <li className="flex items-center gap-2">
                <span className="text-green-400">✓</span> Multiple ML Engines
              </li>
            </ul>
          </div>

          <div>
            <h3 className="font-bold text-lg mb-4 text-gradient">Technology Stack</h3>
            <ul className="text-slate-400 text-sm space-y-2">
              <li>• Next.js 14</li>
              <li>• FastAPI</li>
              <li>• PostgreSQL</li>
              <li>• Redis</li>
              <li>• Docker</li>
            </ul>
          </div>

          <div>
            <h3 className="font-bold text-lg mb-4 text-gradient-cyan">Links</h3>
            <ul className="text-slate-400 text-sm space-y-2">
              <li>
                <a
                  href="https://github.com/Mister2005/Product-Catalogue-Recommendation-System"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-blue-400 transition-all duration-300 relative group inline-block"
                >
                  → GitHub Repository
                  <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-gradient-to-r from-blue-500 to-purple-500 group-hover:w-full transition-all duration-300"></span>
                </a>
              </li>
              <li>
                <a
                  href="https://shl-recommendation-api-30oz.onrender.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-blue-400 transition-all duration-300 relative group inline-block"
                >
                  → API Backend
                  <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-gradient-to-r from-blue-500 to-purple-500 group-hover:w-full transition-all duration-300"></span>
                </a>
              </li>
              <li>
                <a
                  href="https://shl-recommendation-api-30oz.onrender.com/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-blue-400 transition-all duration-300 relative group inline-block"
                >
                  → API Documentation
                  <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-gradient-to-r from-blue-500 to-purple-500 group-hover:w-full transition-all duration-300"></span>
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-white/10 mt-8 pt-6 text-center">
          <p className="text-slate-400 text-sm">
            © 2025 SHL Assessment Recommendation Engine. All rights reserved.
          </p>
          <p className="text-slate-500 text-xs mt-2">
            Built with ❤️ using Next.js, FastAPI, and AI
          </p>
        </div>
      </div>
    </footer>
  )
}
