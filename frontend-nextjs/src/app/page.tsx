'use client'

import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { getRecommendations, getMetadata, type RecommendationRequest } from '../services/api'
import toast from 'react-hot-toast'
import { Search, Sparkles, Filter, ArrowRight } from 'lucide-react'
import RecommendationForm from '../components/RecommendationForm'
import RecommendationResults from '../components/RecommendationResults'
import Header from '../components/Header'
import Footer from '../components/Footer'

export default function Home() {
  const [showResults, setShowResults] = useState(false)

  // Fetch metadata
  const { data: metadata, isLoading: metadataLoading } = useQuery({
    queryKey: ['metadata'],
    queryFn: getMetadata,
  })

  // Recommendation mutation
  const recommendationMutation = useMutation({
    mutationFn: getRecommendations,
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

  const handleSubmit = (request: RecommendationRequest) => {
    recommendationMutation.mutate(request)
  }

  const handleReset = () => {
    setShowResults(false)
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

      <main className="flex-1 container mx-auto px-4 py-8 max-w-7xl relative z-10">
        {/* Hero Section */}
        {!showResults && (
          <div className="text-center mb-12 animate-fade-in-up">
            <div className="inline-flex items-center gap-2 glass px-4 py-2 rounded-full text-sm font-medium mb-4 border border-blue-500/30">
              <Sparkles className="w-4 h-4 text-blue-400" />
              <span className="text-slate-300">AI-Powered Assessment Recommendations</span>
            </div>

            <h1 className="text-5xl md:text-6xl font-bold mb-4">
              <span className="text-white">SHL Assessment</span>
              <br />
              <span className="text-gradient animate-gradient">Recommendation Engine</span>
            </h1>

            <p className="text-xl text-slate-400 max-w-3xl mx-auto mb-8 leading-relaxed">
              Discover the perfect assessments for your hiring needs using advanced AI,
              RAG technology, and multiple intelligent recommendation engines.
            </p>

            {/* Features */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 max-w-4xl mx-auto mb-12">
              {[
                { name: 'Gemini AI', desc: 'AI-powered insights', color: 'blue', delay: '0s' },
                { name: 'RAG System', desc: 'Semantic search', color: 'purple', delay: '0.1s' },
                { name: 'NLP Analysis', desc: 'Text matching', color: 'cyan', delay: '0.2s' },
                { name: 'Clustering', desc: 'Pattern recognition', color: 'green', delay: '0.3s' },
              ].map((feature, idx) => (
                <div
                  key={idx}
                  className="glass p-4 rounded-lg hover-lift hover-glow animate-scale-in"
                  style={{ animationDelay: feature.delay }}
                >
                  <div className={`text-${feature.color}-400 font-semibold mb-1`}>
                    {feature.name}
                  </div>
                  <div className="text-sm text-slate-400">{feature.desc}</div>
                </div>
              ))}
            </div>
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
                    Fill in your requirements to get personalized recommendations
                  </p>
                </div>
              </div>

              <RecommendationForm
                metadata={metadata}
                onSubmit={handleSubmit}
                isLoading={recommendationMutation.isPending || metadataLoading}
              />
            </>
          ) : (
            <RecommendationResults
              data={recommendationMutation.data}
              isLoading={recommendationMutation.isPending}
              onReset={handleReset}
            />
          )}
        </div>

        {/* Stats Section */}
        {!showResults && (
          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6 animate-fade-in-up" style={{ animationDelay: '0.4s' }}>
            <div className="glass p-6 rounded-lg text-center hover-lift border border-white/10">
              <div className="text-3xl font-bold text-gradient mb-2">517</div>
              <div className="text-slate-400">Assessments Available</div>
            </div>
            <div className="glass p-6 rounded-lg text-center hover-lift border border-white/10">
              <div className="text-3xl font-bold text-gradient-cyan mb-2">5</div>
              <div className="text-slate-400">AI Engines</div>
            </div>
            <div className="glass p-6 rounded-lg text-center hover-lift border border-white/10">
              <div className="text-3xl font-bold text-gradient mb-2">99.9%</div>
              <div className="text-slate-400">Uptime</div>
            </div>
          </div>
        )}
      </main>

      <Footer />
    </div>
  )
}
