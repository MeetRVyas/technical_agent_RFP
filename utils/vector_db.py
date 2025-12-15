"""
Vector Database Handler for OEM Product Semantic Search
Uses FAISS for efficient similarity search on product datasheets
"""

import os
import json
import pickle
from typing import List, Optional
import numpy as np

try:
    import faiss
except ImportError:
    faiss = None
    print("Warning: FAISS not installed. Vector search will use fallback method.")

from models import OEMProduct, ExtractedAttributes
from config import VECTOR_DB_PATH, EMBEDDING_DIMENSION, TOP_K_CANDIDATES


class SimpleEmbedder:
    """
    Simple TF-IDF based embedder for when we dont have access to neural embeddings
    This provides a fallback that works without external API calls
    """
    
    def __init__(self, dimension: int = EMBEDDING_DIMENSION):
        self.dimension = dimension
        self.vocabulary = {}
        self.idf = {}
        self.fitted = False
    
    def fit(self, texts: List[str]):
        """Build vocabulary from corpus"""
        # Build vocabulary
        doc_freq = {}
        all_words = set()
        
        for text in texts:
            words = self._tokenize(text)
            unique_words = set(words)
            all_words.update(unique_words)
            
            for word in unique_words:
                doc_freq[word] = doc_freq.get(word, 0) + 1
        
        # Keep top N words by document frequency
        sorted_words = sorted(doc_freq.items(), key=lambda x: x[1], reverse=True)
        top_words = sorted_words[:self.dimension]
        
        self.vocabulary = {word: idx for idx, (word, _) in enumerate(top_words)}
        
        # Calculate IDF
        n_docs = len(texts)
        self.idf = {word: np.log(n_docs / (df + 1)) for word, df in doc_freq.items()}
        
        self.fitted = True
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        # Convert to lowercase and split on non alphanumeric
        import re
        words = re.findall(r'\b[a-z0-9]+\b', text.lower())
        return words
    
    def embed(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        if not self.fitted:
            raise ValueError("Embedder must be fitted before embedding")
        
        words = self._tokenize(text)
        
        # Calculate TF
        tf = {}
        for word in words:
            tf[word] = tf.get(word, 0) + 1
        
        # Normalize TF
        max_tf = max(tf.values()) if tf else 1
        tf = {word: count / max_tf for word, count in tf.items()}
        
        # Build vector
        vector = np.zeros(self.dimension)
        for word, word_tf in tf.items():
            if word in self.vocabulary:
                idx = self.vocabulary[word]
                word_idf = self.idf.get(word, 0)
                vector[idx] = word_tf * word_idf
        
        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts"""
        embeddings = np.zeros((len(texts), self.dimension))
        for i, text in enumerate(texts):
            embeddings[i] = self.embed(text)
        return embeddings


class VectorDatabase:
    """
    Vector database for storing and searching OEM product embeddings
    Uses FAISS for efficient nearest neighbor search
    """
    
    def __init__(self, db_path: str = VECTOR_DB_PATH):
        self.db_path = db_path
        self.embedder = SimpleEmbedder(EMBEDDING_DIMENSION)
        self.index = None
        self.products: List[OEMProduct] = []
        self.is_initialized = False
    
    def initialize_from_products(self, products: List[OEMProduct]):
        """
        Build the vector index from a list of OEM products
        This should be called once during setup
        """
        if not products:
            raise ValueError("No products provided to initialize database")
        
        self.products = products
        
        # Extract datasheet texts for embedding
        texts = [p.datasheet_text for p in products]
        
        # Fit embedder on corpus
        self.embedder.fit(texts)
        
        # Generate embeddings
        embeddings = self.embedder.embed_batch(texts)
        
        # Build FAISS index
        if faiss is not None:
            self.index = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
            self.index.add(embeddings.astype(np.float32))
        else:
            # Fallback: store embeddings directly
            self.embeddings = embeddings
        
        self.is_initialized = True
    
    def save(self):
        """Save the vector database to disk"""
        os.makedirs(os.path.dirname(self.db_path) or '.', exist_ok=True)
        
        # Save products
        products_data = [p.model_dump() for p in self.products]
        with open(f"{self.db_path}_products.json", 'w') as f:
            json.dump(products_data, f, indent=2)
        
        # Save embedder state
        embedder_state = {
            'vocabulary': self.embedder.vocabulary,
            'idf': self.embedder.idf,
            'fitted': self.embedder.fitted,
            'dimension': self.embedder.dimension
        }
        with open(f"{self.db_path}_embedder.pkl", 'wb') as f:
            pickle.dump(embedder_state, f)
        
        # Save FAISS index or embeddings
        if faiss is not None and self.index is not None:
            faiss.write_index(self.index, f"{self.db_path}_faiss.index")
        elif hasattr(self, 'embeddings'):
            np.save(f"{self.db_path}_embeddings.npy", self.embeddings)
    
    def load(self) -> bool:
        """Load the vector database from disk"""
        try:
            # Load products
            with open(f"{self.db_path}_products.json", 'r') as f:
                products_data = json.load(f)
            self.products = [OEMProduct(**p) for p in products_data]
            
            # Load embedder state
            with open(f"{self.db_path}_embedder.pkl", 'rb') as f:
                embedder_state = pickle.load(f)
            self.embedder.vocabulary = embedder_state['vocabulary']
            self.embedder.idf = embedder_state['idf']
            self.embedder.fitted = embedder_state['fitted']
            self.embedder.dimension = embedder_state['dimension']
            
            # Load FAISS index or embeddings
            faiss_path = f"{self.db_path}_faiss.index"
            embeddings_path = f"{self.db_path}_embeddings.npy"
            
            if faiss is not None and os.path.exists(faiss_path):
                self.index = faiss.read_index(faiss_path)
            elif os.path.exists(embeddings_path):
                self.embeddings = np.load(embeddings_path)
            
            self.is_initialized = True
            return True
            
        except FileNotFoundError:
            return False
    
    def similarity_search(
        self, 
        query_text: str, 
        k: int = TOP_K_CANDIDATES
    ) -> List[OEMProduct]:
        """
        Search for top K similar products based on query text
        
        Args:
            query_text: The RFP specification text to match
            k: Number of results to return
            
        Returns:
            List of OEMProduct objects sorted by similarity
        """
        if not self.is_initialized:
            raise ValueError("Vector database not initialized. Call initialize_from_products first.")
        
        # Embed query
        query_embedding = self.embedder.embed(query_text)
        
        if faiss is not None and self.index is not None:
            # FAISS search
            distances, indices = self.index.search(
                query_embedding.reshape(1, -1).astype(np.float32), 
                min(k, len(self.products))
            )
            results = [self.products[idx] for idx in indices[0] if idx < len(self.products)]
        else:
            # Fallback: cosine similarity search
            similarities = np.dot(self.embeddings, query_embedding)
            top_indices = np.argsort(similarities)[::-1][:k]
            results = [self.products[idx] for idx in top_indices]
        
        return results
    
    def get_product_by_sku(self, sku_id: str) -> Optional[OEMProduct]:
        """Retrieve a specific product by SKU ID"""
        for product in self.products:
            if product.sku_id == sku_id:
                return product
        return None
