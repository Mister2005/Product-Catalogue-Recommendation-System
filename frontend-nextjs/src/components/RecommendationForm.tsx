'use client'

import { useState } from 'react'
import { type RecommendationRequest, type Metadata } from '../services/api'
import { Loader2, Sparkles } from 'lucide-react'

interface Props {
  metadata?: Metadata
  onSubmit: (request: RecommendationRequest) => void
  isLoading: boolean
}

export default function RecommendationForm({ metadata, onSubmit, isLoading }: Props) {
  const [formData, setFormData] = useState<RecommendationRequest>({
    job_title: '',
    job_family: '',
    job_level: '',
    industry: '',
    required_skills: [],
    test_types: [],
    remote_testing_required: false,
    max_duration: undefined,
    language: 'English',
    num_recommendations: 5,
    engine: 'hybrid',
  })

  const [skillInput, setSkillInput] = useState('')
  const [inputMode, setInputMode] = useState<'manual' | 'upload'>('manual')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  const addSkill = () => {
    if (skillInput.trim() && !formData.required_skills?.includes(skillInput.trim())) {
      setFormData({
        ...formData,
        required_skills: [...(formData.required_skills || []), skillInput.trim()],
      })
      setSkillInput('')
    }
  }

  const removeSkill = (skill: string) => {
    setFormData({
      ...formData,
      required_skills: formData.required_skills?.filter((s) => s !== skill) || [],
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Input Mode Toggle */}
      <div className="flex gap-4 p-1 bg-gray-100 rounded-lg">
        <button
          type="button"
          onClick={() => setInputMode('manual')}
          className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all ${inputMode === 'manual'
            ? 'bg-white text-blue-600 shadow-sm'
            : 'text-gray-600 hover:text-gray-900'
            }`}
        >
          📝 Manual Form
        </button>
        <button
          type="button"
          onClick={() => setInputMode('upload')}
          className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all ${inputMode === 'upload'
            ? 'bg-white text-blue-600 shadow-sm'
            : 'text-gray-600 hover:text-gray-900'
            }`}
        >
          📄 Resume & GitHub
        </button>
      </div>

      {inputMode === 'manual' ? (
        <>
          {/* Job Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Job Title
              </label>
              <input
                type="text"
                value={formData.job_title}
                onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                placeholder="e.g., Software Engineer"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Job Family
              </label>
              <select
                value={formData.job_family}
                onChange={(e) => setFormData({ ...formData, job_family: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              >
                <option value="">Select Job Family</option>
                {metadata?.job_families.map((family) => (
                  <option key={family} value={family}>
                    {family}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Job Level
              </label>
              <select
                value={formData.job_level}
                onChange={(e) => setFormData({ ...formData, job_level: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              >
                <option value="">Select Job Level</option>
                {metadata?.job_levels.map((level) => (
                  <option key={level} value={level}>
                    {level}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Industry
              </label>
              <select
                value={formData.industry}
                onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              >
                <option value="">Select Industry</option>
                {metadata?.industries.map((industry) => (
                  <option key={industry} value={industry}>
                    {industry}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Skills */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Required Skills
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addSkill())}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                placeholder="Type a skill and press Enter"
              />
              <button
                type="button"
                onClick={addSkill}
                className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {formData.required_skills?.map((skill) => (
                <span
                  key={skill}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
                >
                  {skill}
                  <button
                    type="button"
                    onClick={() => removeSkill(skill)}
                    className="hover:text-blue-900"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Options */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Language
              </label>
              <select
                value={formData.language}
                onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              >
                {metadata?.languages.map((lang) => (
                  <option key={lang} value={lang}>
                    {lang}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Duration (minutes)
              </label>
              <input
                type="number"
                value={formData.max_duration || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    max_duration: e.target.value ? parseInt(e.target.value) : undefined,
                  })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                placeholder="e.g., 60"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Recommendation Engine
              </label>
              <select
                value={formData.engine}
                onChange={(e) => setFormData({ ...formData, engine: e.target.value as any })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              >
                <option value="hybrid">🎯 Hybrid (Recommended)</option>
                <option value="gemini">🤖 Gemini AI</option>
                <option value="rag">🔍 RAG Semantic Search</option>
                <option value="nlp">📊 NLP Analysis</option>
                <option value="clustering">🎲 Clustering</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Number of Recommendations
              </label>
              <input
                type="number"
                min="1"
                max="20"
                value={formData.num_recommendations}
                onChange={(e) =>
                  setFormData({ ...formData, num_recommendations: parseInt(e.target.value) })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="remote"
              checked={formData.remote_testing_required}
              onChange={(e) =>
                setFormData({ ...formData, remote_testing_required: e.target.checked })
              }
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="remote" className="text-sm text-gray-700">
              Remote testing required
            </label>
          </div>
        </>
      ) : (
        <>
          {/* Resume & GitHub Upload Mode */}
          <div className="space-y-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-blue-900 mb-4">
                📄 Upload Your Resume & GitHub Profile
              </h3>
              <p className="text-sm text-blue-700 mb-6">
                Our AI will analyze your resume and GitHub profile to automatically extract your skills, experience, and recommend the best assessments for you.
              </p>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Resume/CV *
                  </label>
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={(e) => {
                      const file = e.target.files?.[0]
                      if (file) {
                        setFormData({ ...formData, resume_file: file })
                      }
                    }}
                    className="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 transition-colors"
                  />
                  <p className="text-xs text-gray-500 mt-2">📎 Supports PDF, DOC, DOCX files</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    GitHub Profile URL (Optional)
                  </label>
                  <input
                    type="url"
                    value={formData.github_url || ''}
                    onChange={(e) => setFormData({ ...formData, github_url: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                    placeholder="https://github.com/username"
                  />
                  <p className="text-xs text-gray-500 mt-2">🔍 We'll analyze your repositories and contributions</p>
                </div>
              </div>
            </div>

            {/* Engine Selection for Upload Mode */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Recommendation Engine
              </label>
              <select
                value={formData.engine}
                onChange={(e) => setFormData({ ...formData, engine: e.target.value as any })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              >
                <option value="hybrid">🎯 Hybrid (Recommended)</option>
                <option value="gemini">🤖 Gemini AI</option>
                <option value="rag">🔍 RAG Semantic Search</option>
                <option value="nlp">📊 NLP Analysis</option>
                <option value="clustering">🎲 Clustering</option>
              </select>
            </div>
          </div>
        </>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading}
        className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-6 rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Generating Recommendations...
          </>
        ) : (
          <>
            <Sparkles className="w-5 h-5" />
            Get Recommendations
          </>
        )}
      </button>
    </form>
  )
}
