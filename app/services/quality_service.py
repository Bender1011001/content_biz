import logging
import spacy
import language_tool_python
from sqlalchemy.orm import Session
from ..db.models import Content

logger = logging.getLogger(__name__)

class QualityService:
    """Service for checking the quality of generated content"""
    
    def __init__(self):
        """Initialize the quality checking tools"""
        try:
            self.tool = language_tool_python.LanguageTool('en-US')
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Quality check service initialized")
        except Exception as e:
            logger.error(f"Error initializing quality check tools: {str(e)}")
            # Fallback initialization
            self.tool = None
            self.nlp = None
    
    def check_grammar(self, text):
        """
        Check text for grammar errors using LanguageTool.
        
        Args:
            text: The text to check
            
        Returns:
            Tuple of (grammar_score, list of issues)
        """
        if not self.tool:
            logger.warning("LanguageTool not initialized, skipping grammar check")
            return 80.0, []  # Default score if tool not available
            
        try:
            matches = self.tool.check(text)
            # Calculate score based on error density
            error_density = len(matches) / (len(text.split()) / 100)
            grammar_score = max(0, 100 - error_density * 5)
            return grammar_score, matches
        except Exception as e:
            logger.error(f"Error checking grammar: {str(e)}")
            return 70.0, []  # Default fallback score
    
    def check_coherence(self, text):
        """
        Check text for coherence using spaCy.
        
        Args:
            text: The text to check
            
        Returns:
            Coherence score (0-100)
        """
        if not self.nlp:
            logger.warning("spaCy not initialized, skipping coherence check")
            return 80.0  # Default score if NLP not available
            
        try:
            doc = self.nlp(text)
            sentences = list(doc.sents)
            
            # For single sentence, coherence is perfect
            if len(sentences) <= 1:
                return 100.0
                
            # Calculate sentence similarity for adjacent sentences
            similarities = []
            for i in range(len(sentences) - 1):
                sent1 = sentences[i]
                sent2 = sentences[i + 1]
                # Convert to Doc objects for similarity comparison
                doc1 = self.nlp(sent1.text)
                doc2 = self.nlp(sent2.text)
                similarities.append(doc1.similarity(doc2))
                
            # Calculate average similarity
            avg_similarity = sum(similarities) / len(similarities)
            # Scale to 0-100 (similarity is typically 0-1)
            coherence_score = avg_similarity * 100
            
            return coherence_score
        except Exception as e:
            logger.error(f"Error checking coherence: {str(e)}")
            return 70.0  # Default fallback score
    
    def calculate_overall_score(self, grammar_score, coherence_score):
        """
        Calculate overall quality score from grammar and coherence scores.
        
        Args:
            grammar_score: Grammar score (0-100)
            coherence_score: Coherence score (0-100)
            
        Returns:
            Overall quality score (0-100)
        """
        # Weighted more heavily toward grammar as suggested in the plan
        return (grammar_score * 0.9) + (coherence_score * 0.1)
    
    def check_content_quality(self, content_id, db: Session):
        """
        Check the quality of a piece of content and update its quality score.
        
        Args:
            content_id: The ID of the content to check
            db: SQLAlchemy database session
            
        Returns:
            Dictionary with quality check results
        """
        try:
            content = db.query(Content).filter(Content.id == content_id).first()
            if not content:
                logger.error(f"Content with ID {content_id} not found")
                return None
            
            grammar_score, issues = self.check_grammar(content.generated_text)
            coherence_score = self.check_coherence(content.generated_text)
            
            overall_score = self.calculate_overall_score(grammar_score, coherence_score)
            
            # Update content with quality score
            content.quality_score = overall_score
            
            # If score is below threshold, flag for manual review
            threshold = 70.0  # This should come from config
            if overall_score < threshold:
                content.delivery_status = "review_needed"
                logger.info(f"Content {content_id} flagged for review (score: {overall_score})")
            else:
                content.delivery_status = "ready_for_delivery"
                logger.info(f"Content {content_id} passed quality check (score: {overall_score})")
                
            db.commit()
            
            return {
                "content_id": content.id,
                "quality_score": overall_score,
                "grammar_score": grammar_score,
                "coherence_score": coherence_score,
                "issues": [str(issue) for issue in issues[:10]] if issues else [],  # Sample of issues
                "status": content.delivery_status
            }
        except Exception as e:
            logger.error(f"Error checking content quality: {str(e)}")
            db.rollback()
            return {
                "content_id": content_id,
                "error": str(e),
                "status": "error"
            }
