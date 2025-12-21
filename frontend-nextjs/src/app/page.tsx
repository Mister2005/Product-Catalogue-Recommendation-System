'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { getSimpleRecommendations, type SimpleRecommendRequest, type SimpleRecommendResponse } from '../services/api'
import toast from 'react-hot-toast'
import { Search, Sparkles, Link as LinkIcon, ArrowRight, ExternalLink, FileText } from 'lucide-react'
import Header from '../components/Header'
import Footer from '../components/Footer'

export default function Home() {
  const [query, setQuery] = useState('')
  const [url, setUrl] = useState('')
  const [inputMode, setInputMode] = useState<'query' | 'url' | 'pdf'>('query')
  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [showResults, setShowResults] = useState(false)
  const [pdfRecommendations, setPdfRecommendations] = useState<SimpleRecommendResponse | null>(null)

  // Recommendation mutation
  const recommendationMutation = useMutation({
    mutationFn: getSimpleRecommendations,
    onSuccess: () => {
      setShowResults(true)
      toast.success('Recommendations generated successfully!')
    },
    onError: (error: any) => {
      console.error('Recommendation error:', error)
      const errorMessage = error.response?.data?.detail
        ? (typeof error.response.data.detail === 'string'
          ? error.response.data.detail
          : JSON.stringify(error.response.data.detail))
        : 'Failed to get recommendations'
      toast.error(errorMessage)
    },
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (inputMode === 'pdf') {
      // Handle PDF upload
      if (!pdfFile) {
        toast.error('Please select a PDF file')
        return
      }

      try {
        const { getRecommendationsFromPDF } = await import('../services/api')
        toast.loading('Processing PDF...', { id: 'pdf-upload' })
        const result = await getRecommendationsFromPDF(pdfFile)
        toast.success('Recommendations generated!', { id: 'pdf-upload' })

        // Store PDF recommendations in state
        setPdfRecommendations(result)
        setShowResults(true)
      } catch (error: any) {
        toast.error(error?.response?.data?.detail || 'Failed to process PDF', { id: 'pdf-upload' })
      }
    } else {
      // Handle query or URL
      const request: SimpleRecommendRequest = inputMode === 'query'
        ? { query }
        : { url }

      if (!request.query && !request.url) {
        toast.error('Please enter a query or URL')
        return
      }

      // Clear PDF recommendations when using query/URL
      setPdfRecommendations(null)
      recommendationMutation.mutate(request)
    }
  }

  const handleReset = () => {
    setShowResults(false)
    setQuery('')
    setUrl('')
    setPdfFile(null)
    setPdfRecommendations(null)
    recommendationMutation.reset()
  }

  return (
    <div className="min-h-screen flex flex-col bg-dark-primary relative overflow-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-900/20 via-purple-900/20 to-cyan-900/20 animate-gradient"></div>
        <div className="absolute top-0 -left-4 w-72 h-72 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-float"></div>
        <div className="absolute top-0 -right-4 w-72 h-72 bg-cyan-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-float" style={{ animationDelay: '2s' }}></div>
        <div className="absolute -bottom-8 left-20 w-72 h-72 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-float" style={{ animationDelay: '4s' }}></div>
      </div>

      <Header />

      <main className="flex-1 container mx-auto px-4 py-8 max-w-5xl relative z-10">
        {/* Hero Section */}
        {!showResults && (
          <div className="text-center mb-12 animate-fade-in-up">
            <div className="inline-flex items-center gap-2 glass px-4 py-2 rounded-full text-sm font-medium mb-4 border border-blue-500/30">
              <Sparkles className="w-4 h-4 text-blue-400" />
              <span className="text-slate-300">SHL AI Intern Assignment</span>
            </div>

            <h1 className="text-5xl md:text-6xl font-bold mb-4">
              <span className="text-white">SHL Assessment</span>
              <br />
              <span className="text-gradient animate-gradient">Recommendation System</span>
            </h1>

            <p className="text-xl text-slate-400 max-w-3xl mx-auto mb-8 leading-relaxed">
              Get personalized assessment recommendations using natural language queries or job description URLs.
            </p>
          </div>
        )}

        {/* Form or Results */}
        <div className="glass-strong rounded-2xl shadow-glow-lg p-8 animate-fade-in-up border border-white/10">
          {!showResults ? (
            <>
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg shadow-glow-sm">
                  <Search className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-white">
                    Find Your Perfect Assessment
                  </h2>
                  <p className="text-slate-400">
                    Enter a query or job description URL
                  </p>
                </div>
              </div>

              {/* Input Mode Toggle */}
              <div className="flex gap-2 mb-6">
                <button
                  type="button"
                  onClick={() => setInputMode('query')}
                  className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all ${inputMode === 'query'
                    ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-glow-sm'
                    : 'glass text-slate-400 hover:text-white'
                    }`}
                >
                  <Search className="w-4 h-4 inline mr-2" />
                  Query
                </button>
                <button
                  type="button"
                  onClick={() => setInputMode('url')}
                  className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all ${inputMode === 'url'
                    ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-glow-sm'
                    : 'glass text-slate-400 hover:text-white'
                    }`}
                >
                  <LinkIcon className="w-4 h-4 inline mr-2" />
                  URL
                </button>
                <button
                  type="button"
                  onClick={() => setInputMode('pdf')}
                  className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all ${inputMode === 'pdf'
                    ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-glow-sm'
                    : 'glass text-slate-400 hover:text-white'
                    }`}
                >
                  <FileText className="w-4 h-4 inline mr-2" />
                  PDF
                </button>
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-6">
                {inputMode === 'query' ? (
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Job Description or Requirements
                    </label>
                    <textarea
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder="e.g., I am hiring for Java developers who can also collaborate effectively with my business teams"
                      className="w-full px-4 py-3 bg-dark-secondary border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all min-h-[120px]"
                      required
                    />
                  </div>
                ) : inputMode === 'url' ? (
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Job Description URL
                    </label>
                    <input
                      type="url"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      placeholder="https://example.com/job-description"
                      className="w-full px-4 py-3 bg-dark-secondary border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                      required
                    />
                  </div>
                ) : (
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Upload Job Description PDF
                    </label>
                    <div className="relative">
                      <input
                        type="file"
                        accept=".pdf"
                        onChange={(e) => setPdfFile(e.target.files?.[0] || null)}
                        className="w-full px-4 py-3 bg-dark-secondary border border-white/10 rounded-lg text-white file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-500 file:text-white hover:file:bg-blue-600 file:cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                        required
                      />
                    </div>
                    {pdfFile && (
                      <p className="mt-2 text-sm text-slate-400">
                        Selected: {pdfFile.name}
                      </p>
                    )}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={recommendationMutation.isPending}
                  className="w-full bg-gradient-to-r from-blue-500 to-purple-500 text-white py-4 px-6 rounded-lg font-semibold hover:shadow-glow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {recommendationMutation.isPending ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      Generating Recommendations...
                    </>
                  ) : (
                    <>
                      Get Recommendations
                      <ArrowRight className="w-5 h-5" />
                    </>
                  )}
                </button>
              </form>
            </>
          ) : (
            <div>
              {/* Results Header */}
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-white mb-1">
                    Recommended Assessments
                  </h2>
                  <p className="text-slate-400">
                    {(pdfRecommendations?.recommended_assessments.length || recommendationMutation.data?.recommended_assessments.length || 0)} assessments found
                  </p>
                </div>
                <button
                  onClick={handleReset}
                  className="glass px-4 py-2 rounded-lg text-slate-300 hover:text-white transition-all"
                >
                  New Search
                </button>
              </div>

              {/* Results List */}
              <div className="space-y-4">
                {(pdfRecommendations?.recommended_assessments || recommendationMutation.data?.recommended_assessments || []).map((rec, index) => (
                  <div
                    key={index}
                    className="glass p-6 rounded-lg hover-lift border border-white/10 animate-fade-in-up"
                    style={{ animationDelay: `${index * 0.1}s` }}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="flex items-center justify-center w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 text-white font-bold text-sm">
                            {index + 1}
                          </span>
                          <h3 className="text-lg font-semibold text-white">
                            {rec.name}
                          </h3>
                        </div>

                        <button
                          onClick={() => {
                            // Open in new tab without referrer using about:blank trick
                            const newWindow = window.open('about:blank', '_blank');
                            if (newWindow) {
                              newWindow.opener = null;
                              newWindow.location.href = rec.url;
                            }
                          }}
                          className="ml-11 inline-flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors text-sm cursor-pointer bg-transparent border-none p-0"
                        >
                          <ExternalLink className="w-4 h-4" />
                          View Assessment
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {(pdfRecommendations?.recommended_assessments.length === 0 || recommendationMutation.data?.recommended_assessments.length === 0) && (
                <div className="text-center py-12">
                  <p className="text-slate-400">No recommendations found. Try a different query.</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Info Section */}
        {!showResults && (
          <div className="mt-12 glass p-6 rounded-lg animate-fade-in-up border border-white/10" style={{ animationDelay: '0.3s' }}>
            <h3 className="text-lg font-semibold text-white mb-3">How it works</h3>
            <ul className="space-y-2 text-slate-400">
              <li className="flex items-start gap-2">
                <span className="text-blue-400 mt-1">•</span>
                <span>Enter a natural language query describing your hiring needs</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-400 mt-1">•</span>
                <span>Or provide a URL to a job description page</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-400 mt-1">•</span>
                <span>Get 1-10 personalized assessment recommendations</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-400 mt-1">•</span>
                <span>All recommendations are Individual Test Solutions from SHL</span>
              </li>
            </ul>
          </div>
        )}
      </main>

      <Footer />
    </div>
  )
}
