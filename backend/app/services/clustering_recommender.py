"""
Clustering-based recommendation engine using K-Means and PCA
"""
from typing import List, Dict
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA

from app.models.schemas import RecommendationRequest, RecommendationItem, RecommendationScore, AssessmentResponse
from app.core.logging import log


class ClusteringRecommender:
    """
    Clustering-based recommender using K-Means and PCA for dimensionality reduction
    """
    
    def __init__(self, n_clusters: int = 10):
        """Initialize clustering recommender"""
        self.n_clusters = n_clusters
        self.kmeans = None
        self.pca_reducer = None  # Changed from umap_reducer to pca_reducer
        self.scaler = StandardScaler()
        self.vectorizer = TfidfVectorizer(max_features=500, ngram_range=(1, 2))
        self.assessments_cache = []
        self.cluster_labels = None
        self.feature_matrix = None
    
    def _create_features(self, assessment: dict) -> str:
        """Create feature representation"""
        parts = [
            assessment.get('name', ''),
            assessment.get('type', ''),
            assessment.get('job_family', ''),
            assessment.get('job_level', ''),
            assessment.get('description', '')
        ]
        
        return " ".join(filter(None, parts))
    
    def fit(self, db):
        """Fit clustering model"""
        log.info("Fitting clustering recommender")
        
        response = db.table("assessments").select("*").execute()
        assessments = response.data
        self.assessments_cache = assessments
        
        if not assessments:
            log.warning("No assessments found")
            return
        
        # Create feature documents
        documents = [self._create_features(a) for a in assessments]
        
        # Create TF-IDF features
        tfidf_features = self.vectorizer.fit_transform(documents).toarray()
        
        # Add numerical features
        numerical_features = []
        for assessment in assessments:
            features = [
                1 if assessment.get('remote_testing', False) else 0,
                1 if assessment.get('adaptive', False) else 0,
                assessment.get('duration', 60) or 60,
                0,  # skills count
                0   # industries count
            ]
            numerical_features.append(features)
        
        numerical_features = np.array(numerical_features)
        numerical_features = self.scaler.fit_transform(numerical_features)
        
        # Combine features
        self.feature_matrix = np.hstack([tfidf_features, numerical_features])
        
        # Dimensionality reduction with PCA (much faster than UMAP)
        try:
            if len(assessments) > self.n_clusters and self.feature_matrix.shape[1] > 10:
                # Use PCA for fast dimensionality reduction
                n_components = min(50, len(assessments) - 1, self.feature_matrix.shape[1] - 1)
                log.info(f"Starting PCA reduction: {self.feature_matrix.shape[0]} -> {n_components} dims")
                
                self.pca_reducer = PCA(
                    n_components=n_components,
                    random_state=42
                )
                reduced_features = self.pca_reducer.fit_transform(self.feature_matrix)
                log.info(f"✅ PCA completed in <1s: {self.feature_matrix.shape[0]} -> {reduced_features.shape[1]} dimensions")
            else:
                reduced_features = self.feature_matrix
                log.info("Skipping PCA reduction (insufficient data)")
        except Exception as e:
            log.warning(f"PCA reduction failed: {e}, using original features")
            reduced_features = self.feature_matrix
            self.pca_reducer = None
        
        # Clustering
        n_clusters = min(self.n_clusters, len(assessments), len(assessments) // 2 + 1)
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
        self.cluster_labels = self.kmeans.fit_predict(reduced_features)
        
        log.info(f"✅ Clustering fitted with {n_clusters} clusters on {len(assessments)} assessments")
    
    def _create_query_features(self, request: RecommendationRequest) -> np.ndarray:
        """Create feature vector from request"""
        # Text features
        parts = []
        if request.job_title:
            parts.append(request.job_title)
        if request.job_family:
            parts.append(request.job_family)
        if request.job_level:
            parts.append(request.job_level)
        if request.required_skills:
            parts.extend(request.required_skills)
        if request.industry:
            parts.append(request.industry)
        
        query_doc = " ".join(parts) if parts else "general"
        tfidf_features = self.vectorizer.transform([query_doc]).toarray()
        
        # Numerical features
        numerical = [
            1 if request.remote_testing_required else 0,
            0,  # adaptive
            request.max_duration or 60,
            len(request.required_skills) if request.required_skills else 0,
            1 if request.industry else 0
        ]
        numerical_features = self.scaler.transform([numerical])
        
        # Combine
        combined = np.hstack([tfidf_features, numerical_features])
        
        # Apply PCA if fitted
        if self.pca_reducer:
            combined = self.pca_reducer.transform(combined)
        
        return combined
    
    async def recommend(
        self, 
        request: RecommendationRequest, 
        db
    ) -> List[RecommendationItem]:
        """
        Generate recommendations using clustering
        """
        log.info(f"Clustering recommendation for: {request.dict()}")
        
        if self.kmeans is None:
            self.fit(db)
        
        # Create query features
        query_features = self._create_query_features(request)
        
        # Predict cluster
        query_cluster = self.kmeans.predict(query_features)[0]
        log.info(f"Query assigned to cluster {query_cluster}")
        
        # Get assessments in same cluster
        cluster_indices = np.where(self.cluster_labels == query_cluster)[0]
        
        # Calculate distances within cluster
        cluster_assessments = [(idx, self.assessments_cache[idx]) for idx in cluster_indices]
        
        # Calculate distances to cluster center
        cluster_center = self.kmeans.cluster_centers_[query_cluster]
        
        scored_assessments = []
        for idx, assessment in cluster_assessments:
            # Get assessment features
            if self.pca_reducer:
                assessment_features = self.pca_reducer.transform(self.feature_matrix[idx:idx+1])
            else:
                assessment_features = self.feature_matrix[idx:idx+1]
            
            # Calculate distance to query
            distance = np.linalg.norm(query_features - assessment_features)
            similarity = 1 / (1 + distance)
            
            scored_assessments.append((assessment, similarity, idx))
        
        # Sort by similarity
        scored_assessments.sort(key=lambda x: x[1], reverse=True)
        
        # Create recommendations
        recommendations = []
        
        for assessment, similarity, idx in scored_assessments:
            if len(recommendations) >= request.num_recommendations:
                break
            
            # Apply filters
            if request.remote_testing_required and not assessment.get('remote_testing', False):
                continue
            
            if request.max_duration and assessment.get('duration') and assessment.get('duration', 0) > request.max_duration:
                continue
            
            if request.language:
                languages = ['English']
                if request.language not in languages:
                    continue
            
            assessment_response = self._db_to_response(assessment)
            
            score = RecommendationScore(
                total_score=similarity,
                relevance_score=similarity,
                confidence=similarity,
                explanation=f"Cluster {query_cluster}, Similarity: {similarity:.2f}"
            )
            
            recommendations.append(RecommendationItem(
                assessment=assessment_response,
                score=score,
                rank=len(recommendations) + 1
            ))
        
        log.info(f"Clustering returned {len(recommendations)} recommendations")
        return recommendations
    
    def _db_to_response(self, assessment: dict) -> AssessmentResponse:
        """Convert database model to response schema"""
        return AssessmentResponse(
            id=assessment.get('id', ''),
            name=assessment.get('name', 'Unknown Assessment'),
            type=assessment.get('type', 'Assessment'),
            test_types=assessment.get('test_types', []) if isinstance(assessment.get('test_types'), list) else [],
            remote_testing=assessment.get('remote_testing', False),
            adaptive=assessment.get('adaptive', False),
            job_family=assessment.get('job_family') or None,
            job_level=assessment.get('job_level') or None,
            industries=assessment.get('industries', []) if isinstance(assessment.get('industries'), list) else [],
            languages=assessment.get('languages', ['English']) if isinstance(assessment.get('languages'), list) else [],
            skills=assessment.get('skills', []) if isinstance(assessment.get('skills'), list) else [],
            description=assessment.get('description', ''),
            duration=assessment.get('duration') or None
        )

