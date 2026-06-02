import os
 
# Qdrant
QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
 
# Collection name
COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "jewellery-2")
 
CLIP_MODEL_NAME: str  = os.getenv("CLIP_MODEL_NAME", "ViT-L-14")
CLIP_PRETRAINED: str  = os.getenv("CLIP_PRETRAINED", "datacomp_xl_s13b_b90k")
DINO_MODEL_NAME: str  = os.getenv("DINO_MODEL_NAME", "facebook/dinov2-base")
 
CLIP_EMBED_DIM: int   = 768
DINO_EMBED_DIM: int   = 768
 
# API settings
MAX_FILE_MB: int      = int(os.getenv("MAX_FILE_MB", "10"))
DEFAULT_TOP_K: int    = int(os.getenv("DEFAULT_TOP_K", "10"))
MAX_TOP_K: int        = int(os.getenv("MAX_TOP_K", "500"))
DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
MAX_PAGE_SIZE: int     = int(os.getenv("MAX_PAGE_SIZE", "100"))
 
ALLOWED_CONTENT_TYPES: set = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
 
# Ingestion settings
INGEST_BATCH_SIZE: int = int(os.getenv("INGEST_BATCH_SIZE", "32"))
 
# Logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()