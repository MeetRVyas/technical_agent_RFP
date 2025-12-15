# RFP-Agentic-AI

# B2B RFP Technical Agent System

A multi-agent system for automating RFP (Request for Proposal) response processing in the B2B industrial products sector. This Technical Agent is part of a larger system designed to handle the complete RFP response workflow for cables and wires manufacturing.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      TECHNICAL AGENT SYSTEM                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     │
│   │  RFP Parser │     │  Attribute  │     │   Product   │     │
│   │    Agent    │────▶│  Extractor  │────▶│   Matcher   │     │
│   │   (LLM)     │     │   (LLM)     │     │   Agent     │     │
│   └─────────────┘     └─────────────┘     └─────────────┘     │
│          │                   │                   │             │
│          ▼                   ▼                   ▼             │
│   ┌─────────────────────────────────────────────────────┐     │
│   │              DETERMINISTIC COMPONENTS               │     │
│   │  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │     │
│   │  │  Attribute  │  │ Spec Match  │  │   Vector   │  │     │
│   │  │  Normalizer │  │   Engine    │  │  Database  │  │     │
│   │  └─────────────┘  └─────────────┘  └────────────┘  │     │
│   └─────────────────────────────────────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Key Design Principles

1. **Separation of Concerns**: LLM is used ONLY for text extraction and summarization. All scoring and matching is done via deterministic symbolic logic.

2. **Weighted Attribute Matching**: The Spec Match Engine uses a configurable weighted scoring system:
   - Voltage: 25%
   - Conductor Material: 20%
   - Cross Section: 15%
   - Core Count: 15%
   - Insulation: 10%
   - Armouring: 10%
   - Sheathing: 5%

3. **Semantic Search + Symbolic Scoring**: First retrieves candidates using vector similarity, then applies deterministic scoring.

## Installation

```bash
# Install dependencies
pip install crewai crewai-tools langchain langchain-groq faiss-cpu pandas numpy python-dotenv pydantic

# Set your Groq API key
export GROQ_API_KEY="your-api-key-here"
```

## Usage

### Run Component Tests (No API Required)

```bash
cd rfp_agent
python test_components.py
```

This validates:
- Attribute extraction functions
- Value normalization
- Spec Match Engine scoring
- Vector database search
- Full matching pipeline
- Edge cases

### Run Full System

```bash
# Process sample RFP #1
python main.py --api-key YOUR_GROQ_API_KEY

# Process specific sample RFP
python main.py --rfp-number 2 --api-key YOUR_GROQ_API_KEY

# Show detailed recommendations
python main.py --detailed --api-key YOUR_GROQ_API_KEY
```

## Project Structure

```
____________________________
├── config.py                 # Configuration and constants
├── models.py                 # Pydantic data models
├── main.py                   # Main entry point
├── test_components.py        # Component test suite
├── agents/
│   ├── __init__.py
│   └── technical_agent.py    # crewAI Technical Agent
├── utils/
│   ├── __init__.py
│   ├── attribute_utils.py    # Attribute extraction helpers
│   ├── match_engine.py       # Deterministic spec matching
│   └── vector_db.py          # FAISS vector database
└── data/
    ├── __init__.py
    ├── sample_products.py    # OEM product catalog
    └── sample_rfps.py        # Sample RFP documents
```

## Sample Input

The system comes with sample RFP documents and OEM products for testing:

### Sample RFP (NTPC Thermal Power Project)
```
Item No. 1: HT Power Cable
Description: 11kV, 3 Core, 300 sq.mm, Aluminum Conductor, XLPE Insulated,
GI Strip Armoured, PVC Sheathed Power Cable
Quantity: 25 km
```

### Sample OEM Product
```
SKU: HV-AL-XLPE-001
Product: 11kV 3C x 300sqmm Al XLPE GI Strip Armoured Cable
Specs:
  - Voltage: 11kV
  - Conductor: Aluminum
  - Cross Section: 300 sq mm
  - Cores: 3
  - Insulation: XLPE
  - Armour: GI Strip
  - Sheath: PVC
```

## Output Format

The Technical Agent produces a structured output containing:

1. **Summary Table**: Quick overview of RFP items and recommended SKUs
2. **Detailed Recommendations**: For each item:
   - Extracted attributes
   - Top 3 matching OEM products with scores
   - Comparison table
   - Deviation notes
3. **JSON Export**: Full output saved for downstream agents

## Integration with Other Agents

The Technical Agent output is designed to be consumed by:

1. **Main Agent**: Receives the summary table and overall recommendations
2. **Pricing Agent**: Receives the product SKUs to calculate pricing

### Output JSON Structure

```json
{
  "rfp_id": "SAMPLE-RFP-001",
  "processing_timestamp": "2025-01-15T10:30:00",
  "total_items_processed": 4,
  "successful_matches": 3,
  "partial_matches": 1,
  "no_matches": 0,
  "summary_table": [
    {
      "item_id": 1,
      "rfp_specification": "11kV 3C x 300sqmm...",
      "recommended_sku": "HV-AL-XLPE-001",
      "match_score": 100.0,
      "match_status": "exact_match"
    }
  ],
  "recommendations": [...],
  "alerts": []
}
```

## Customization

### Adding New Products

Edit `data/sample_products.py` to add new OEM products:

```python
OEMProduct(
    sku_id="YOUR-SKU-ID",
    product_name="Product Name",
    datasheet_text="Full datasheet text for embedding...",
    specs=ExtractedAttributes(
        voltage="11kv",
        conductor_material="al",
        ...
    )
)
```

### Adjusting Weights

Edit `config.py` to modify attribute weights:

```python
ATTRIBUTE_WEIGHTS = {
    "voltage": 0.30,        # Increase voltage importance
    "conductor_material": 0.25,
    ...
}
```