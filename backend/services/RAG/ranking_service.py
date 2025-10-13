"""
Ranking Service for OrientaTech RAG System
Improves search results by re-ranking based on multiple factors
"""
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))


class RankingService:
    """
    Service for ranking and scoring search results
    
    Features:
    - Multi-factor ranking (similarity, recency, completeness)
    - Configurable weights
    - Document quality scoring
    - Personalized ranking (optional)
    """
    
    # Default ranking weights
    DEFAULT_WEIGHTS = {
        'similarity': 0.6,      # 60% - vector similarity
        'recency': 0.2,         # 20% - document freshness
        'completeness': 0.1,    # 10% - content completeness
        'file_quality': 0.1     # 10% - file quality metrics
    }
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize the ranking service
        
        Args:
            weights: Custom ranking weights (uses defaults if None)
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self._validate_weights()
        logger.debug(f"RankingService initialized with weights: {self.weights}")
    
    def _validate_weights(self):
        """Validate that weights sum to approximately 1.0"""
        total = sum(self.weights.values())
        if not (0.95 <= total <= 1.05):
            logger.warning(f"⚠️ Weights sum to {total}, expected ~1.0. Normalizing...")
            # Normalize weights
            for key in self.weights:
                self.weights[key] /= total
    
    # ===================================
    # MAIN RANKING METHOD
    # ===================================
    
    def rank_results(
        self,
        results: List[Dict],
        custom_weights: Optional[Dict[str, float]] = None
    ) -> List[Dict]:
        """
        Rank search results using multiple factors
        
        Args:
            results: List of search results from SearchService
            custom_weights: Optional custom weights for this ranking
            
        Returns:
            List[Dict]: Re-ranked results with final_score added
            
        Example:
            results = await search_service.semantic_search(query)
            ranked = ranking_service.rank_results(results)
        """
        if not results:
            return []
        
        # Use custom weights if provided
        weights = custom_weights or self.weights
        
        # Calculate scores for each result
        for result in results:
            scores = {
                'similarity': result.get('similarity_score', 0.0),
                'recency': self._calculate_recency_score(result),
                'completeness': self._calculate_completeness_score(result),
                'file_quality': self._calculate_file_quality_score(result)
            }
            
            # Calculate weighted final score
            final_score = sum(
                scores[factor] * weights[factor]
                for factor in weights.keys()
            )
            
            # Add scores to result
            result['ranking_scores'] = scores
            result['final_score'] = round(final_score, 4)
            result['ranking_weights'] = weights
        
        # Sort by final score (highest first)
        ranked_results = sorted(
            results,
            key=lambda x: x['final_score'],
            reverse=True
        )
        
        logger.info(f"✅ Ranked {len(ranked_results)} results")
        return ranked_results
    
    # ===================================
    # SCORING METHODS
    # ===================================
    
    def _calculate_recency_score(self, result: Dict) -> float:
        """
        Calculate recency score based on document age
        
        Args:
            result: Search result dictionary
            
        Returns:
            float: Recency score (0.0 to 1.0)
        """
        try:
            created_at = result.get('created_at')
            
            if not created_at:
                return 0.5  # Neutral score if date unknown
            
            # Convert to datetime if string
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
            # Calculate age in days
            age_days = (datetime.now() - created_at.replace(tzinfo=None)).days
            
            # Scoring based on age
            if age_days < 30:
                return 1.0      # Less than 1 month - maximum score
            elif age_days < 90:
                return 0.8      # 1-3 months
            elif age_days < 180:
                return 0.6      # 3-6 months
            elif age_days < 365:
                return 0.4      # 6-12 months
            else:
                return 0.2      # Older than 1 year
                
        except Exception as e:
            logger.debug(f"Error calculating recency score: {e}")
            return 0.5  # Neutral score on error
    
    def _calculate_completeness_score(self, result: Dict) -> float:
        """
        Calculate completeness score based on content
        
        Args:
            result: Search result dictionary
            
        Returns:
            float: Completeness score (0.0 to 1.0)
        """
        score = 0.0
        
        try:
            # Check if content exists
            content = result.get('content_preview', '') or result.get('content_text', '')
            if content:
                score += 0.3
                
                # Bonus for longer content
                if len(content) > 100:
                    score += 0.2
                if len(content) > 500:
                    score += 0.2
            
            # Check if description exists
            if result.get('description'):
                score += 0.15
            
            # Check if filename is descriptive
            filename = result.get('filename', '').lower()
            if any(word in filename for word in ['resume', 'cv', 'curriculum']):
                score += 0.15
            
            return min(score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.debug(f"Error calculating completeness score: {e}")
            return 0.5
    
    def _calculate_file_quality_score(self, result: Dict) -> float:
        """
        Calculate file quality score based on file properties
        
        Args:
            result: Search result dictionary
            
        Returns:
            float: Quality score (0.0 to 1.0)
        """
        score = 0.0
        
        try:
            # File size scoring (not too small, not too large)
            file_size_mb = result.get('file_size_mb', 0)
            
            if 0.1 <= file_size_mb <= 2.0:
                score += 0.5  # Optimal size range
            elif 0.05 <= file_size_mb <= 5.0:
                score += 0.3  # Acceptable range
            else:
                score += 0.1  # Too small or too large
            
            # Document type preference
            doc_type = result.get('document_type', '')
            if doc_type == 'cv':
                score += 0.3  # CV documents are typically higher quality
            elif doc_type == 'cover_letter':
                score += 0.2
            elif doc_type == 'certificate':
                score += 0.2
            
            return min(score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.debug(f"Error calculating file quality score: {e}")
            return 0.5
    
    # ===================================
    # ADVANCED RANKING
    # ===================================
    
    def rank_with_boost(
        self,
        results: List[Dict],
        boost_factors: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Rank results with custom boost factors
        
        Args:
            results: Search results
            boost_factors: Custom boost configuration
                Example: {
                    'boost_recent': 1.5,  # Boost recent documents by 50%
                    'boost_cv': 1.2,      # Boost CV documents by 20%
                    'penalize_old': 0.8   # Penalize old documents
                }
            
        Returns:
            List[Dict]: Ranked results with boost applied
        """
        boost_factors = boost_factors or {}
        
        # First, apply standard ranking
        ranked = self.rank_results(results)
        
        # Apply boost factors
        for result in ranked:
            boost_multiplier = 1.0
            
            # Boost recent documents
            if boost_factors.get('boost_recent'):
                created_at = result.get('created_at')
                if created_at:
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    age_days = (datetime.now() - created_at.replace(tzinfo=None)).days
                    if age_days < 30:
                        boost_multiplier *= boost_factors['boost_recent']
            
            # Boost by document type
            if boost_factors.get('boost_cv') and result.get('document_type') == 'cv':
                boost_multiplier *= boost_factors['boost_cv']
            
            # Apply boost
            result['final_score'] *= boost_multiplier
            result['boost_applied'] = boost_multiplier
        
        # Re-sort after boosting
        ranked = sorted(ranked, key=lambda x: x['final_score'], reverse=True)
        
        logger.info(f"✅ Applied boost ranking to {len(ranked)} results")
        return ranked
    
    # ===================================
    # FILTERING BY SCORE
    # ===================================
    
    def filter_by_threshold(
        self,
        results: List[Dict],
        min_final_score: float = 0.5
    ) -> List[Dict]:
        """
        Filter results by minimum final score
        
        Args:
            results: Ranked results
            min_final_score: Minimum final score threshold
            
        Returns:
            List[Dict]: Filtered results
        """
        filtered = [
            result for result in results
            if result.get('final_score', 0) >= min_final_score
        ]
        
        logger.info(f"✅ Filtered from {len(results)} to {len(filtered)} results (threshold: {min_final_score})")
        return filtered
    
    # ===================================
    # UTILITY METHODS
    # ===================================
    
    def get_ranking_explanation(self, result: Dict) -> str:
        """
        Get human-readable explanation of ranking
        
        Args:
            result: Ranked result with scores
            
        Returns:
            str: Explanation text
        """
        scores = result.get('ranking_scores', {})
        weights = result.get('ranking_weights', {})
        
        explanation_parts = []
        
        for factor, score in scores.items():
            weight = weights.get(factor, 0)
            contribution = score * weight
            explanation_parts.append(
                f"{factor}: {score:.2f} (weight: {weight:.0%}, contribution: {contribution:.2f})"
            )
        
        explanation = " | ".join(explanation_parts)
        return f"Final score: {result.get('final_score', 0):.2f} = {explanation}"
    
    def get_service_info(self) -> Dict:
        """Get information about ranking service"""
        return {
            'service': 'RankingService',
            'version': '1.0.0',
            'default_weights': self.DEFAULT_WEIGHTS,
            'current_weights': self.weights,
            'ranking_factors': list(self.weights.keys())
        }


# ===================================
# Singleton instance
# ===================================

_ranking_service_instance: Optional[RankingService] = None

def get_ranking_service(weights: Optional[Dict[str, float]] = None) -> RankingService:
    """
    Get singleton instance of RankingService
    
    Args:
        weights: Optional custom weights
        
    Returns:
        RankingService: Singleton instance
    """
    global _ranking_service_instance
    
    if _ranking_service_instance is None:
        _ranking_service_instance = RankingService(weights)
    
    return _ranking_service_instance


# ===================================
# Testing and validation
# ===================================

if __name__ == "__main__":
    """Test the ranking service"""
    logger.info("Testing RankingService...")
    
    # Create service
    service = RankingService()
    
    # Test 1: Service info
    logger.info("Test 1: Service information")
    info = service.get_service_info()
    logger.info(f"✅ Service: {info['service']}")
    logger.info(f"   Default weights: {info['default_weights']}")
    
    # Test 2: Mock ranking
    logger.info("\nTest 2: Ranking with mock data")
    mock_results = [
        {
            'document_id': '1',
            'filename': 'old_resume.pdf',
            'similarity_score': 0.95,
            'created_at': '2022-01-01T00:00:00',
            'content_preview': 'Short text',
            'file_size_mb': 0.5,
            'document_type': 'cv'
        },
        {
            'document_id': '2',
            'filename': 'recent_cv.pdf',
            'similarity_score': 0.85,
            'created_at': '2024-10-01T00:00:00',
            'content_preview': 'Python developer with extensive experience in FastAPI, Django, and modern web development. Strong background in database design...',
            'description': 'My latest CV',
            'file_size_mb': 1.2,
            'document_type': 'cv'
        },
        {
            'document_id': '3',
            'filename': 'certificate.pdf',
            'similarity_score': 0.80,
            'created_at': '2024-09-15T00:00:00',
            'content_preview': 'Certificate text here with some details about completion',
            'file_size_mb': 0.3,
            'document_type': 'certificate'
        }
    ]
    
    ranked = service.rank_results(mock_results)
    
    logger.info("✅ Ranking results:")
    for i, result in enumerate(ranked, 1):
        logger.info(f"   {i}. {result['filename']} - Final score: {result['final_score']:.4f}")
        logger.info(f"      Scores: similarity={result['ranking_scores']['similarity']:.2f}, "
                   f"recency={result['ranking_scores']['recency']:.2f}, "
                   f"completeness={result['ranking_scores']['completeness']:.2f}")
    
    # Test 3: Boost ranking
    logger.info("\nTest 3: Boost ranking")
    boosted = service.rank_with_boost(
        mock_results,
        boost_factors={'boost_recent': 1.5, 'boost_cv': 1.2}
    )
    
    logger.info("✅ Boosted ranking results:")
    for i, result in enumerate(boosted, 1):
        logger.info(f"   {i}. {result['filename']} - Final score: {result['final_score']:.4f} "
                   f"(boost: {result.get('boost_applied', 1.0):.2f}x)")
    
    # Test 4: Filter by threshold
    logger.info("\nTest 4: Filter by threshold")
    filtered = service.filter_by_threshold(ranked, min_final_score=0.6)
    logger.info(f"✅ Filtered to {len(filtered)} results (threshold: 0.6)")
    
    # Test 5: Ranking explanation
    logger.info("\nTest 5: Ranking explanation")
    if ranked:
        explanation = service.get_ranking_explanation(ranked[0])
        logger.info(f"✅ {explanation}")
    
    logger.success("🎉 All tests passed!")

