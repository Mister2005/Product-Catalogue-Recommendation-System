export default function Header() {
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4 py-4 max-w-7xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-xl">
              S
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">SHL Recommendations</h1>
              <p className="text-xs text-gray-500">v2.0 Production</p>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-6">
            <a href="/" className="text-gray-700 hover:text-blue-600 transition-colors">
              Home
            </a>
            <a href="/docs" className="text-gray-700 hover:text-blue-600 transition-colors">
              API Docs
            </a>
            <a
              href="https://github.com/Mister2005/Product-Catalogue-Recommendation-System"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-700 hover:text-blue-600 transition-colors"
            >
              GitHub
            </a>
          </nav>
        </div>
      </div>
    </header>
  )
}
