'use client'

import { type RecommendationResponse } from '../services/api'
import { Award, Clock, Globe, Users, Star, ArrowLeft, Download } from 'lucide-react'

interface Props {
  data?: RecommendationResponse
  isLoading: boolean
  onReset: () => void
}

export default function RecommendationResults({ data, isLoading, onReset }: Props) {
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
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Your Personalized Recommendations
          </h2>
          <p className="text-gray-600">
            {data.query_summary} • {data.total_count} results • Engine: {data.engine_used}
          </p>
        </div>
        <button
          onClick={onReset}
          className="flex items-center gap-2 px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
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
              className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 rounded-full font-bold">
                      {item.rank}
                    </span>
                    <h3 className="text-xl font-semibold text-gray-900">
                      {assessment.name}
                    </h3>
                  </div>
                  <p className="text-sm text-gray-500 mb-2">{assessment.type}</p>
                  {assessment.description && (
                    <p className="text-gray-700 text-sm">{assessment.description}</p>
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
                    <div className="text-xs text-gray-500">Job Family</div>
                    <div className="text-sm font-medium">{assessment.job_family || 'General'}</div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Award className="w-4 h-4 text-gray-400" />
                  <div>
                    <div className="text-xs text-gray-500">Job Level</div>
                    <div className="text-sm font-medium">{assessment.job_level || 'All Levels'}</div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-gray-400" />
                  <div>
                    <div className="text-xs text-gray-500">Duration</div>
                    <div className="text-sm font-medium">{assessment.duration ? `${assessment.duration} min` : 'Varies'}</div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Globe className="w-4 h-4 text-gray-400" />
                  <div>
                    <div className="text-xs text-gray-500">Languages</div>
                    <div className="text-sm font-medium">{assessment.languages?.join(', ') || 'English'}</div>
                  </div>
                </div>
              </div>

              {/* Tags */}
              <div className="space-y-2">
                {assessment.test_types.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    <span className="text-xs font-medium text-gray-500">Test Types:</span>
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
                    <span className="text-xs font-medium text-gray-500">Skills:</span>
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
                    <span className="text-xs font-medium text-gray-500">Industries:</span>
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
                <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">
                    <strong>Why recommended:</strong> {score.explanation}
                  </p>
                  {score.confidence && (
                    <p className="text-xs text-gray-500 mt-1">
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
        <button className="flex items-center gap-2 px-6 py-3 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors">
          <Download className="w-4 h-4" />
          Export Results
        </button>
      </div>
    </div>
  )
}
