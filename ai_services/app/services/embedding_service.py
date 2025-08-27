from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np
from app.core.config import settings
import asyncio
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self._model = None
        self.model_name = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model with proper error handling"""
        try:
            # Try to load the configured model
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Successfully loaded embedding model: {self.model_name}")
            
            # Test the model to get actual dimension
            test_embedding = self._model.encode("test")
            actual_dimension = len(test_embedding)
            
            if actual_dimension != self.dimension:
                logger.warning(f"Configured dimension {self.dimension} doesn't match model dimension {actual_dimension}. Using model dimension.")
                self.dimension = actual_dimension
                
        except Exception as e:
            # Fallback to a reliable model
            logger.warning(f"Failed to load {self.model_name}: {e}. Using fallback model.")
            self._model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            test_embedding = self._model.encode("test")
            self.dimension = len(test_embedding)
            logger.info(f"Using fallback model with dimension: {self.dimension}")
    
    @property
    def model(self):
        if self._model is None:
            self._initialize_model()
        return self._model
    
    async def encode_text(self, text: str):
        """Encode single text to embedding - returns proper format for pgvector"""
        try:
            if not text or text.strip() == "":
                logger.warning("Empty text provided for encoding")
                return None  # Return None instead of zero vector
                
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, 
                self.model.encode, 
                text
            )
            
            # For pgvector, return the numpy array directly or convert to proper format
            # pgvector can handle numpy arrays directly
            return embedding
            
        except Exception as e:
            logger.error(f"Error encoding text '{text}': {e}")
            return None  # Return None on error
    
    async def encode_batch(self, texts: List[str]):
        """Encode multiple texts to embeddings - returns proper format for pgvector"""
        try:
            # Filter out empty texts
            valid_texts = [t for t in texts if t and t.strip() != ""]
            if not valid_texts:
                return [None] * len(texts)
                
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, 
                self.model.encode, 
                valid_texts
            )
            
            # Return numpy arrays for pgvector
            result = []
            text_index = 0
            for text in texts:
                if text and text.strip() != "":
                    result.append(embeddings[text_index])
                    text_index += 1
                else:
                    result.append(None)
            return result
            
        except Exception as e:
            logger.error(f"Error encoding batch: {e}")
            return [None] * len(texts)
    
    def cosine_similarity(self, a, b) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            if a is None or b is None:
                return 0.0
                
            a_array = np.array(a, dtype=np.float32)
            b_array = np.array(b, dtype=np.float32)
            return float(np.dot(a_array, b_array) / (np.linalg.norm(a_array) * np.linalg.norm(b_array)))
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0

# Global instance
embedding_service = EmbeddingService()