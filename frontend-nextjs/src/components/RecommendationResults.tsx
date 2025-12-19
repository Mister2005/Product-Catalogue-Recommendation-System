'use client'

import { useState } from 'react'
import { type RecommendationResponse } from '../services/api'
import { Award, Clock, Globe, Users, Sparkles, ArrowLeft, Download, Loader2, Star } from 'lucide-react'
import toast from 'react-hot-toast'

interface Props {
  data?: RecommendationResponse
  isLoading: boolean
  onReset: () => void
}

export default function RecommendationResults({ data, isLoading, onReset }: Props) {
  const [isExporting, setIsExporting] = useState(false)

  const handleExportPDF = async () => {
    if (!data) return

    setIsExporting(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:10000'}/api/v1/export-pdf`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error('Failed to generate PDF')
      }

      // Get the PDF blob
      const blob = await response.blob()

      // Create download link
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `SHL_Recommendations_${new Date().toISOString().split('T')[0]}.pdf`
      document.body.appendChild(a)
      a.click()

      // Cleanup
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      toast.success('PDF downloaded successfully!')
    } catch (error) {
      console.error('PDF export error:', error)
      toast.error('Failed to export PDF')
    } finally {
      setIsExporting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!data) return null

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-100'
    if (score >= 0.6) return 'text-blue-600 bg-blue-100'
    if (score >= 0.4) return 'text-yellow-600 bg-yellow-100'
    return 'text-orange-600 bg-orange-100'
  }

  const getScoreStars = (score: number) => {
    return Math.round(score * 5)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between pb-6 border-b">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">
            Your Personalized Recommendations
          </h2>
          <p className="text-slate-400">
            {data.query_summary} • {data.total_count} results • Engine: {data.engine_used}
          </p>
        </div>
        <button
          onClick={onReset}
          className="flex items-center gap-2 px-4 py-2 text-blue-400 hover:bg-blue-500/10 rounded-lg transition-all border border-blue-500/30"
        >
          <ArrowLeft className="w-4 h-4" />
          New Search
        </button>
      </div>

      {/* Recommendations */}
      <div className="space-y-4">
        {data.recommendations.map((item, index) => {
          const assessment = item.assessment
          const score = item.score

          return (
            <div
              key={assessment.id}
              className="glass border border-white/10 rounded-lg p-6 hover-lift hover-glow animate-fade-in-up"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 rounded-full font-bold">
                      {item.rank}
                    </span>
                    <h3 className="text-xl font-semibold text-white">
                      {assessment.name}
                    </h3>
                  </div>
                  <p className="text-sm text-slate-400 mb-2">{assessment.type}</p>
                  {assessment.description && (
                    <p className="text-slate-300 text-sm">{assessment.description}</p>
                  )}
                </div>

                <div className="text-right">
                  <div
                    className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getScoreColor(
                      score.total_score
                    )}`}
                  >
                    {(score.total_score * 100).toFixed(0)}% Match
                  </div>
                  <div className="flex mt-2">
                    {[...Array(5)].map((_, i) => (
                      <Star
                        key={i}
                        className={`w-4 h-4 ${i < getScoreStars(score.total_score)
                          ? 'text-yellow-400 fill-yellow-400'
                          : 'text-gray-300'
                          }`}
                      />
                    ))}
                  </div>
                </div>
              </div>

              {/* Details */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-gray-400" />
                  <div>
                    <div className="text-xs text-slate-500">Job Family</div>
                    <div className="text-sm font-medium text-white">{assessment.job_family || 'General'}</div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-yellow-400" />
                  <div>
                    <div className="text-xs text-slate-500">Job Level</div>
                    <div className="text-sm font-medium text-white">{assessment.job_level || 'All Levels'}</div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-gray-400" />
                  <div>
                    <div className="text-xs text-slate-500">Duration</div>
                    <div className="text-sm font-medium text-white">{assessment.duration ? `${assessment.duration} min` : 'Varies'}</div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Globe className="w-4 h-4 text-gray-400" />
                  <div>
                    <div className="text-xs text-slate-500">Languages</div>
                    <div className="text-sm font-medium text-white">{assessment.languages?.join(', ') || 'English'}</div>
                  </div>
                </div>
              </div>

              {/* Tags */}
              <div className="space-y-2">
                {assessment.test_types.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    <span className="text-xs font-medium text-slate-400">Test Types:</span>
                    {assessment.test_types.map((type) => (
                      <span
                        key={type}
                        className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs"
                      >
                        {type}
                      </span>
                    ))}
                  </div>
                )}

                {assessment.skills.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    <span className="text-xs font-medium text-slate-400">Skills:</span>
                    {assessment.skills.slice(0, 5).map((skill) => (
                      <span
                        key={skill}
                        className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs"
                      >
                        {skill}
                      </span>
                    ))}
                    {assessment.skills.length > 5 && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                        +{assessment.skills.length - 5} more
                      </span>
                    )}
                  </div>
                )}

                {assessment.industries.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    <span className="text-xs font-medium text-slate-400">Industries:</span>
                    {assessment.industries.slice(0, 3).map((industry) => (
                      <span
                        key={industry}
                        className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs"
                      >
                        {industry}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Features */}
              <div className="flex gap-3 mt-4 pt-4 border-t">
                {assessment.remote_testing && (
                  <span className="inline-flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                    ✓ Remote Testing
                  </span>
                )}
                {assessment.adaptive && (
                  <span className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                    ✓ Adaptive
                  </span>
                )}
              </div>

              {/* Score Details */}
              {score.explanation && (
                <div className="mt-4 p-3 bg-dark-tertiary/50 rounded-lg border border-white/10">
                  <p className="text-sm text-slate-300">
                    <strong>Why recommended:</strong> {score.explanation}
                  </p>
                  {score.confidence && (
                    <p className="text-xs text-slate-400 mt-1">
                      Confidence: {(score.confidence * 100).toFixed(0)}%
                    </p>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Export Button */}
      <div className="flex justify-center pt-6">
        <button
          onClick={handleExportPDF}
          disabled={isExporting}
          className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:shadow-glow-md transition-all hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isExporting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Generating PDF...
            </>
          ) : (
            <>
              <Download className="w-4 h-4" />
              Export Results
            </>
          )}
        </button>
      </div>
    </div>
  )
}
