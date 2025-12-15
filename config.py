"""
Configuration file for the RFP Technical Agent System
Contains all constants weights and thresholds for deterministic scoring
"""

import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LLM_MODEL = "groq/llama-3.1-70b-versatile"

# Minimum match threshold below which we flag as no viable match
MINIMUM_MATCH_THRESHOLD = 60.0

# Attribute weights for deterministic spec matching
# These weights determine how important each attribute is in the final score
# All weights must sum to 1.0 for proper percentage calculation
ATTRIBUTE_WEIGHTS = {
    "voltage": 0.25,           # Critical safety parameter
    "conductor_material": 0.20,  # Core material specification
    "cross_section": 0.15,      # Size and capacity
    "core_count": 0.15,         # Number of cores
    "insulation": 0.10,         # Insulation type
    "armouring": 0.10,          # Protection type
    "sheathing": 0.05,          # Outer protection
}

# Normalized values mapping for flexible matching
# This helps match variations like Al vs Aluminum or Cu vs Copper
NORMALIZED_VALUES = {
    # Conductor materials
    "aluminum": "al",
    "aluminium": "al",
    "al": "al",
    "copper": "cu",
    "cu": "cu",
    
    # Insulation types
    "xlpe": "xlpe",
    "cross linked polyethylene": "xlpe",
    "pvc": "pvc",
    "polyvinyl chloride": "pvc",
    "epr": "epr",
    "ethylene propylene rubber": "epr",
    
    # Armouring types
    "gi strip": "gi_strip",
    "galvanized iron strip": "gi_strip",
    "galvanised iron strip": "gi_strip",
    "gi wire": "gi_wire",
    "galvanized iron wire": "gi_wire",
    "galvanised iron wire": "gi_wire",
    "steel wire": "swa",
    "swa": "swa",
    "steel wire armoured": "swa",
    "steel wire armour": "swa",
    "unarmoured": "unarmoured",
    "none": "unarmoured",
    
    # Sheathing
    "pvc": "pvc",
    "pe": "pe",
    "polyethylene": "pe",
    "lszh": "lszh",
    "low smoke zero halogen": "lszh",
}

# Vector database configuration
VECTOR_DB_PATH = "data/oem_products_faiss"
EMBEDDING_DIMENSION = 384

# Top K candidates to retrieve from vector search
TOP_K_CANDIDATES = 5

# Number of final recommendations to show
TOP_N_RECOMMENDATIONS = 3