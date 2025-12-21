import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Types
export interface RecommendationRequest {
    job_title?: string
    job_family?: string
    job_level?: string
    industry?: string
    required_skills?: string[]
    test_types?: string[]
    remote_testing_required?: boolean
    max_duration?: number
    language?: string
    num_recommendations?: number
    engine?: 'gemini' | 'rag' | 'nlp' | 'clustering' | 'hybrid'
    user_id?: string
    resume_file?: File
    github_url?: string
}

export interface Assessment {
    id: string
    name: string
    type: string
    test_types: string[]
    remote_testing: boolean
    adaptive: boolean
    job_family?: string
    job_level?: string
    industries: string[]
    languages: string[]
    skills: string[]
    description?: string
    duration?: number
}

export interface RecommendationScore {
    total_score: number
    relevance_score: number
    skill_match_score?: number
    industry_match_score?: number
    confidence?: number
    explanation?: string
}

export interface RecommendationItem {
    assessment: Assessment
    score: RecommendationScore
    rank: number
}

export interface RecommendationResponse {
    recommendations: RecommendationItem[]
    total_count: number
    engine_used: string
    query_summary: string
    metadata?: any
    recommendation_id?: string
}

export interface Metadata {
    job_families: string[]
    industries: string[]
    skills: string[]
    test_types: string[]
    job_levels: string[]
    languages: string[]
}

// API Functions
export const getRecommendations = async (
    request: RecommendationRequest
): Promise<RecommendationResponse> => {
    // If resume_file is present, use FormData
    if (request.resume_file) {
        const formData = new FormData()

        // Add file
        formData.append('resume_file', request.resume_file)

        // Add other fields
        if (request.job_title) formData.append('job_title', request.job_title)
        if (request.job_family) formData.append('job_family', request.job_family)
        if (request.job_level) formData.append('job_level', request.job_level)
        if (request.industry) formData.append('industry', request.industry)
        if (request.github_url) formData.append('github_url', request.github_url)
        if (request.required_skills) formData.append('required_skills', JSON.stringify(request.required_skills))
        if (request.test_types) formData.append('test_types', JSON.stringify(request.test_types))
        if (request.remote_testing_required !== undefined) formData.append('remote_testing_required', String(request.remote_testing_required))
        if (request.max_duration) formData.append('max_duration', String(request.max_duration))
        if (request.language) formData.append('language', request.language)
        if (request.num_recommendations) formData.append('num_recommendations', String(request.num_recommendations))
        if (request.engine) formData.append('engine', request.engine)
        if (request.user_id) formData.append('user_id', request.user_id)

        const response = await axios.post(`${API_URL}/api/v1/recommend`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        })
        return response.data
    }

    // Otherwise use JSON
    const response = await api.post('/api/v1/recommend', request)
    return response.data
}

export const getAssessments = async (params?: {
    skip?: number
    limit?: number
    job_family?: string
}): Promise<Assessment[]> => {
    const response = await api.get('/api/v1/assessments', { params })
    return response.data
}

export const getAssessment = async (id: string): Promise<Assessment> => {
    const response = await api.get(`/api/v1/assessments/${id}`)
    return response.data
}

export const getMetadata = async (): Promise<Metadata> => {
    const response = await api.get('/api/v1/metadata')
    return response.data
}

export const submitFeedback = async (feedback: {
    recommendation_id: string
    assessment_id: string
    rating: number
    feedback_text?: string
}): Promise<any> => {
    const response = await api.post('/api/v1/feedback', feedback)
    return response.data
}

export interface ChatMessage {
    role: 'user' | 'assistant'
    content: string
}

export interface ChatResponse {
    response: string
    context?: any
}

export const chatWithAI = async (
    message: string,
    history: ChatMessage[] = []
): Promise<ChatResponse> => {
    const response = await api.post('/api/v1/chat', {
        message,
        history
    })
    return response.data
}

// ============================================================================
// NEW SIMPLIFIED API (SHL Assignment)
// ============================================================================

export interface SimpleRecommendRequest {
    query?: string
    url?: string
}

export interface SimpleAssessmentRecommendation {
    url: string
    name: string
    adaptive_support: string
    description: string
    duration: number
    remote_support: string
    test_type: string[]
}

export interface SimpleRecommendResponse {
    recommended_assessments: SimpleAssessmentRecommendation[]
}

/**
 * Get recommendations using the new simplified API
 * Accepts either a natural language query or a URL containing job description
 */
export const getSimpleRecommendations = async (
    request: SimpleRecommendRequest
): Promise<SimpleRecommendResponse> => {
    const response = await api.post('/recommend', request)
    return response.data
}

/**
 * Helper function to get recommendations from a query string
 */
export const getRecommendationsFromQuery = async (
    query: string
): Promise<SimpleRecommendResponse> => {
    return getSimpleRecommendations({ query })
}

/**
 * Helper function to get recommendations from a URL
 */
export const getRecommendationsFromURL = async (
    url: string
): Promise<SimpleRecommendResponse> => {
    return getSimpleRecommendations({ url })
}

/**
 * Get recommendations from a PDF file
 */
export const getRecommendationsFromPDF = async (
    file: File
): Promise<SimpleRecommendResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await axios.post(`${API_URL}/recommend/pdf`, formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    })
    return response.data
}
