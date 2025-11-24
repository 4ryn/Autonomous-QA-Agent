import logging
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from config import settings
import uuid
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.embedding_model = None
        self.client = None
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self._initialize_embedding_model()
        self._initialize_qdrant_client()
    
    def _initialize_embedding_model(self):
        """Initialize the embedding model"""
        try:
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading embedding model: {str(e)}")
            raise
    
    def _initialize_qdrant_client(self):
        """Initialize Qdrant client"""
        try:
            # Priority: Use cloud if URL and API key are provided
            if settings.QDRANT_URL and settings.QDRANT_API_KEY:
                # Cloud instance
                logger.info(f"Connecting to Qdrant Cloud: {settings.QDRANT_URL}")
                
                # Clean URL (remove trailing slash if present)
                url = settings.QDRANT_URL.rstrip('/')
                
                self.client = QdrantClient(
                    url=url,
                    api_key=settings.QDRANT_API_KEY,
                    timeout=60,
                    prefer_grpc=False  # Use REST API instead of gRPC for better Windows compatibility
                )
                logger.info("Connected to Qdrant Cloud successfully")
            elif settings.QDRANT_USE_CLOUD:
                # Cloud requested but missing credentials
                logger.error("Qdrant Cloud selected but URL or API key missing")
                raise ValueError(
                    "Qdrant Cloud requires both QDRANT_URL and QDRANT_API_KEY in .env file.\n"
                    "Sign up at https://cloud.qdrant.io/ to get your credentials."
                )
            else:
                # Local instance
                logger.info(f"Connecting to local Qdrant: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
                self.client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                    timeout=60,
                    prefer_grpc=False
                )
                logger.info("Connected to local Qdrant successfully")
            
            # Test connection
            try:
                collections = self.client.get_collections()
                logger.info(f"Qdrant connection verified. Found {len(collections.collections)} collection(s)")
            except Exception as e:
                logger.error(f"Failed to verify Qdrant connection: {str(e)}")
                raise
                
        except ValueError as e:
            logger.error(str(e))
            raise
        except Exception as e:
            logger.error(f"Error initializing Qdrant client: {str(e)}")
            if settings.QDRANT_URL:
                logger.error("Check your Qdrant Cloud URL and API key")
                logger.error(f"URL: {settings.QDRANT_URL}")
                logger.error("Troubleshooting:")
                logger.error("1. Verify URL has no trailing slash")
                logger.error("2. Check API key is correct")
                logger.error("3. Ensure cluster is running in Qdrant Cloud dashboard")
                logger.error("4. Check firewall/VPN settings")
                logger.error("5. Run: python test_qdrant_connection.py")
            else:
                logger.error("Make sure Qdrant is running locally")
            raise
    
    def create_collection(self, force_recreate: bool = False):
        """Create or recreate the Qdrant collection"""
        try:
            collections = self.client.get_collections().collections
            collection_exists = any(col.name == self.collection_name for col in collections)
            
            if collection_exists and force_recreate:
                logger.info(f"Deleting existing collection: {self.collection_name}")
                self.client.delete_collection(self.collection_name)
                collection_exists = False
            
            if not collection_exists:
                logger.info(f"Creating collection: {self.collection_name}")
                # Get embedding dimension
                test_embedding = self.embedding_model.encode(["test"])
                vector_size = len(test_embedding[0])
                
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Collection created with vector size: {vector_size}")
            else:
                logger.info(f"Collection already exists: {self.collection_name}")
            
            return True
        except Exception as e:
            logger.error(f"Error creating collection: {str(e)}")
            return False
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        try:
            embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return []
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to the vector store"""
        try:
            if not documents:
                logger.warning("No documents to add")
                return False
            
            logger.info(f"Adding {len(documents)} documents to vector store")
            
            # Extract texts for embedding
            texts = [doc['content'] for doc in documents]
            
            # Generate embeddings
            embeddings = self.generate_embeddings(texts)
            
            if not embeddings:
                logger.error("Failed to generate embeddings")
                return False
            
            # Create points for Qdrant
            points = []
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "content": doc['content'],
                        "metadata": doc['metadata']
                    }
                )
                points.append(point)
            
            # Upload to Qdrant in batches
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
                logger.info(f"Uploaded batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}")
            
            logger.info(f"Successfully added {len(documents)} documents")
            return True
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            return False
    
    def search(self, query: str, top_k: int = 5, filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            logger.info(f"Searching for: {query}")
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])[0].tolist()
            
            # Build filter if provided (but skip if causing issues)
            search_filter = None
            if filter_dict:
                try:
                    conditions = []
                    for key, value in filter_dict.items():
                        conditions.append(
                            FieldCondition(
                                key=f"metadata.{key}",
                                match=MatchValue(value=value)
                            )
                        )
                    if conditions:
                        search_filter = Filter(must=conditions)
                except Exception as filter_error:
                    logger.warning(f"Could not apply filter, searching without it: {str(filter_error)}")
                    search_filter = None
            
            # Search in Qdrant
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=search_filter
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result.payload['content'],
                    "metadata": result.payload['metadata'],
                    "score": result.score
                })
            
            logger.info(f"Found {len(formatted_results)} results")
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching: {str(e)}")
            # Try again without filter
            if filter_dict:
                logger.info("Retrying search without filter")
                return self.search(query, top_k, filter_dict=None)
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        try:
            # Use raw HTTP request to avoid Pydantic validation issues
            import requests
            
            if settings.QDRANT_URL and settings.QDRANT_API_KEY:
                url = f"{settings.QDRANT_URL.rstrip('/')}:{settings.QDRANT_PORT if ':' not in settings.QDRANT_URL else ''}/collections/{self.collection_name}".replace('::', ':')
                headers = {"api-key": settings.QDRANT_API_KEY}
                response = requests.get(url, headers=headers, timeout=10)
            else:
                url = f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}/collections/{self.collection_name}"
                response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})
                return {
                    "name": self.collection_name,
                    "points_count": result.get('points_count', 0),
                    "vectors_count": result.get('vectors_count', 0),
                    "status": result.get('status', 'unknown')
                }
            else:
                logger.warning(f"Could not get collection info: {response.status_code}")
                return {"name": self.collection_name, "points_count": 0}
                
        except Exception as e:
            logger.warning(f"Error getting collection info (non-critical): {str(e)}")
            # Return default values - this is non-critical
            return {
                "name": self.collection_name,
                "points_count": 0,
                "vectors_count": 0,
                "status": "unknown"
            }
    
    def clear_collection(self) -> bool:
        """Clear all documents from the collection"""
        try:
            logger.info(f"Clearing collection: {self.collection_name}")
            self.client.delete_collection(self.collection_name)
            self.create_collection()
            logger.info("Collection cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            return False