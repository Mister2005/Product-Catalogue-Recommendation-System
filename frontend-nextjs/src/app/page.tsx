'use client'

import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { getRecommendations, getMetadata, type RecommendationRequest } from '@/lib/api'
import toast from 'react-hot-toast'
import { Search, Sparkles, Filter, ArrowRight } from 'lucide-react'
import RecommendationForm from '@/components/RecommendationForm'
import RecommendationResults from '@/components/RecommendationResults'
import Header from '@/components/Header'
import Footer from '@/components/Footer'

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
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8 max-w-7xl">
        {/* Hero Section */}
        {!showResults && (
          <div className="text-center mb-12 animate-fade-in">
            <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-700 px-4 py-2 rounded-full text-sm font-medium mb-4">
              <Sparkles className="w-4 h-4" />
              <span>AI-Powered Assessment Recommendations</span>
            </div>
            
            <h1 className="text-5xl font-bold text-gray-900 mb-4">
              SHL Assessment
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
                {' '}Recommendation Engine
              </span>
            </h1>
            
            <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
              Discover the perfect assessments for your hiring needs using advanced AI, 
              RAG technology, and multiple intelligent recommendation engines.
            </p>

            {/* Features */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 max-w-4xl mx-auto mb-12">
              {[
                { name: 'Gemini AI', desc: 'AI-powered insights', color: 'blue' },
                { name: 'RAG System', desc: 'Semantic search', color: 'purple' },
                { name: 'NLP Analysis', desc: 'Text matching', color: 'green' },
                { name: 'Clustering', desc: 'Pattern recognition', color: 'orange' },
              ].map((feature, idx) => (
                <div
                  key={idx}
                  className="bg-white p-4 rounded-lg shadow-md hover:shadow-lg transition-shadow"
                >
                  <div className={`text-${feature.color}-600 font-semibold mb-1`}>
                    {feature.name}
                  </div>
                  <div className="text-sm text-gray-600">{feature.desc}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Form or Results */}
        <div className="bg-white rounded-2xl shadow-xl p-8 animate-slide-up">
          {!showResults ? (
            <>
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Search className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    Find Your Perfect Assessment
                  </h2>
                  <p className="text-gray-600">
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
          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-lg shadow-md text-center">
              <div className="text-3xl font-bold text-blue-600 mb-2">100+</div>
              <div className="text-gray-600">Assessments Available</div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-md text-center">
              <div className="text-3xl font-bold text-purple-600 mb-2">4</div>
              <div className="text-gray-600">AI Engines</div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-md text-center">
              <div className="text-3xl font-bold text-green-600 mb-2">99%</div>
              <div className="text-gray-600">Accuracy Rate</div>
            </div>
          </div>
        )}
      </main>

      <Footer />
    </div>
  )
}
