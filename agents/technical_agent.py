"""
Technical Agent for B2B RFP Response System
Built using crewAI framework

This agent handles
1 Parsing RFP documents to extract Scope of Supply
2 Extracting normalized technical attributes using LLM
3 Performing semantic search for matching OEM products  
4 Computing deterministic Spec Match scores using weighted attributes
5 Generating comparison tables and final recommendations

The key design principle is separation of concerns
- LLM is used ONLY for text extraction and summarization
- Scoring and matching is done via deterministic symbolic logic
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from pydantic import Field

# Import our custom modules
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import (
    RFPItem, 
    OEMProduct, 
    ExtractedAttributes,
    ItemRecommendation,
    TechnicalAgentOutput,
    MatchStatus
)
from config import (
    GROQ_API_KEY, 
    LLM_MODEL, 
    TOP_N_RECOMMENDATIONS,
    TOP_K_CANDIDATES,
    MINIMUM_MATCH_THRESHOLD
)
from utils.match_engine import SpecMatchEngine
from utils.vector_db import VectorDatabase


# ============================================================================
# CUSTOM TOOLS FOR THE TECHNICAL AGENT
# These tools encapsulate specific functionality that the agent can use
# ============================================================================

class ScopeExtractorTool(BaseTool):
    """
    Tool to extract Scope of Supply items from RFP text
    Uses LLM for natural language understanding of RFP format
    """
    name: str = "scope_extractor"
    description: str = """
    Extracts the Scope of Supply section from an RFP document text.
    Input should be the full RFP text content.
    Returns a structured list of items with their specifications.
    """
    
    def _run(self, rfp_text: str) -> str:
        """
        Parse RFP text to extract scope of supply items
        The actual parsing happens in the agents task using LLM
        This tool returns a formatted prompt for extraction
        """
        # This tool prepares the text for LLM extraction
        # The actual extraction is done by the LLM in the task
        extraction_prompt = f"""
        Extract all items from the Scope of Supply section of this RFP.
        For each item identify:
        - Item number or ID
        - Product description/specification
        - Quantity if mentioned
        - Unit of measurement if mentioned
        
        RFP TEXT:
        {rfp_text[:8000]}  # Limit to avoid token overflow
        
        Return as JSON array with format:
        [
            {{
                "item_id": 1,
                "rfp_spec_raw": "full specification text",
                "quantity": "100",
                "unit": "km"
            }}
        ]
        """
        return extraction_prompt


class AttributeExtractorTool(BaseTool):
    """
    Tool to extract normalized technical attributes from specification text
    Combines LLM extraction with rule based normalization
    """
    name: str = "attribute_extractor"
    description: str = """
    Extracts technical attributes from a cable/wire specification text.
    Input is a single product specification string.
    Returns normalized attributes like voltage, conductor material, core count etc.
    """
    
    def _run(self, spec_text: str) -> str:
        """
        Generate prompt for attribute extraction
        The normalization happens after LLM response
        """
        extraction_prompt = f"""
        Extract technical attributes from this cable/wire specification:
        "{spec_text}"
        
        Extract these attributes if present:
        - voltage: The voltage rating (eg 11kV, 33kV)
        - conductor_material: Aluminum (Al) or Copper (Cu)
        - cross_section: Cross sectional area (eg 300sqmm)
        - core_count: Number of cores (eg 3 for 3 core)
        - insulation: Insulation type (eg XLPE, PVC)
        - armouring: Armour type (eg GI Strip, SWA, Unarmoured)
        - sheathing: Outer sheath material (eg PVC, PE)
        
        Return as JSON object with these exact keys.
        Use null for attributes not found in the specification.
        """
        return extraction_prompt


class ProductSearchTool(BaseTool):
    """
    Tool to search OEM product database for matching products
    Uses vector similarity search followed by deterministic scoring
    """
    name: str = "product_search"
    description: str = """
    Searches the OEM product database to find products matching the given specification.
    Input is the product specification text.
    Returns top matching products with their match scores.
    """
    
    # Store reference to vector database
    vector_db: Optional[VectorDatabase] = Field(default=None, exclude=True)
    match_engine: Optional[SpecMatchEngine] = Field(default=None, exclude=True)
    
    def __init__(self, vector_db: VectorDatabase = None, match_engine: SpecMatchEngine = None):
        super().__init__()
        object.__setattr__(self, 'vector_db', vector_db)
        object.__setattr__(self, 'match_engine', match_engine)
    
    def _run(self, spec_text: str) -> str:
        """
        Search for matching products
        This combines semantic search with deterministic scoring
        """
        if self.vector_db is None:
            return json.dumps({"error": "Vector database not initialized"})
        
        # Perform semantic search to get candidates
        candidates = self.vector_db.similarity_search(spec_text, k=TOP_K_CANDIDATES)
        
        # Return candidate SKUs for further processing
        results = []
        for product in candidates:
            results.append({
                "sku_id": product.sku_id,
                "product_name": product.product_name,
                "specs": product.specs.model_dump()
            })
        
        return json.dumps(results, indent=2)


class SpecMatchTool(BaseTool):
    """
    Tool for deterministic spec matching
    NO LLM involvement - pure algorithmic scoring
    """
    name: str = "spec_matcher"
    description: str = """
    Calculates the spec match percentage between RFP requirements and OEM product specs.
    This is a deterministic calculation using weighted attributes.
    Input should be JSON with rfp_attrs and oem_attrs.
    """
    
    match_engine: Optional[SpecMatchEngine] = Field(default=None, exclude=True)
    
    def __init__(self, match_engine: SpecMatchEngine = None):
        super().__init__()
        object.__setattr__(self, 'match_engine', match_engine)
    
    def _run(self, input_json: str) -> str:
        """
        Calculate deterministic spec match score
        """
        if self.match_engine is None:
            return json.dumps({"error": "Match engine not initialized"})
        
        try:
            data = json.loads(input_json)
            rfp_attrs = ExtractedAttributes(**data.get('rfp_attrs', {}))
            oem_attrs = ExtractedAttributes(**data.get('oem_attrs', {}))
            
            score, matched, mismatched, missing = self.match_engine.calculate_match_score(
                rfp_attrs, oem_attrs
            )
            
            return json.dumps({
                "match_score": score,
                "matched_attributes": matched,
                "mismatched_attributes": mismatched,
                "missing_attributes": missing
            })
            
        except Exception as e:
            return json.dumps({"error": str(e)})


# ============================================================================
# TECHNICAL AGENT CLASS
# Main orchestrator that uses crewAI to coordinate the workflow
# ============================================================================

class TechnicalAgentSystem:
    """
    Technical Agent System for RFP Processing
    
    This class orchestrates the complete workflow
    1 Extract scope of supply from RFP
    2 Extract attributes for each item
    3 Search for matching OEM products
    4 Calculate deterministic match scores
    5 Generate comparison tables
    6 Produce final recommendations
    """
    
    def __init__(self, groq_api_key: str = None):
        """
        Initialize the Technical Agent System
        
        Args:
            groq_api_key: API key for Groq LLM service
        """
        self.api_key = groq_api_key or GROQ_API_KEY
        
        # Initialize components
        self.match_engine = SpecMatchEngine()
        self.vector_db = VectorDatabase()
        
        # Initialize tools
        self.scope_tool = ScopeExtractorTool()
        self.attr_tool = AttributeExtractorTool()
        self.search_tool = ProductSearchTool(
            vector_db=self.vector_db, 
            match_engine=self.match_engine
        )
        self.match_tool = SpecMatchTool(match_engine=self.match_engine)
        
        # Setup LLM configuration for crewAI
        self.llm_config = {
            "model": LLM_MODEL,
            "api_key": self.api_key,
            "temperature": 0.4
        }
        
        # Create the agents
        self._create_agents()
    
    def _create_agents(self):
        """
        Create the crewAI agents for the technical workflow
        We use multiple specialized agents for better separation of concerns
        """
        
        # Agent 1: RFP Parser
        # Responsible for extracting scope of supply from RFP documents
        self.rfp_parser_agent = Agent(
            role="RFP Document Parser",
            goal="Extract and structure the Scope of Supply from RFP documents accurately",
            backstory="""You are an expert in parsing industrial RFP documents, 
            particularly for electrical cables and wires. You have years of experience 
            reading complex technical specifications and can identify product requirements 
            even when they are written in different formats.""",
            tools=[self.scope_tool],
            llm=self.llm_config,
            verbose=True,
            allow_delegation=False
        )
        
        # Agent 2: Attribute Extractor
        # Responsible for extracting normalized technical attributes
        self.attr_extractor_agent = Agent(
            role="Technical Attribute Extractor",
            goal="Extract normalized technical attributes from cable specifications",
            backstory="""You are a cable engineering specialist who understands 
            IEC, IS, and BS standards for power cables. You can read any specification 
            and extract key attributes like voltage, conductor material, insulation type, 
            and armoring in a normalized format.""",
            tools=[self.attr_tool],
            llm=self.llm_config,
            verbose=True,
            allow_delegation=False
        )
        
        # Agent 3: Product Matcher
        # Responsible for finding and scoring OEM products
        self.product_matcher_agent = Agent(
            role="OEM Product Matcher",
            goal="Find the best matching OEM products for each RFP requirement",
            backstory="""You are an expert in cable product catalogs and can quickly 
            identify which internal SKUs best match external requirements. You understand 
            that matching must consider all technical parameters with appropriate weights.""",
            tools=[self.search_tool, self.match_tool],
            llm=self.llm_config,
            verbose=True,
            allow_delegation=False
        )
    
    def load_oem_products(self, products: List[OEMProduct]):
        """
        Load OEM products into the vector database
        This should be called once during system setup
        """
        self.vector_db.initialize_from_products(products)
        # Reinitialize search tool with updated database
        self.search_tool = ProductSearchTool(
            vector_db=self.vector_db,
            match_engine=self.match_engine
        )
    
    def process_rfp(
        self, 
        rfp_id: str, 
        rfp_text: str
    ) -> TechnicalAgentOutput:
        """
        Process a complete RFP document
        
        This is the main entry point that orchestrates the full workflow
        
        Args:
            rfp_id: Unique identifier for the RFP
            rfp_text: Full text content of the RFP document
            
        Returns:
            TechnicalAgentOutput with all recommendations
        """
        timestamp = datetime.now().isoformat()
        
        # Step 1: Extract scope of supply items
        scope_items = self._extract_scope_of_supply(rfp_text)
        
        if not scope_items:
            return TechnicalAgentOutput(
                rfp_id=rfp_id,
                processing_timestamp=timestamp,
                total_items_processed=0,
                successful_matches=0,
                partial_matches=0,
                no_matches=0,
                recommendations=[],
                summary_table=[],
                alerts=["Failed to extract any items from RFP Scope of Supply"]
            )
        
        # Step 2: Process each item
        recommendations = []
        alerts = []
        successful = 0
        partial = 0
        no_match = 0
        
        for item in scope_items:
            try:
                recommendation = self._process_single_item(item)
                recommendations.append(recommendation)
                
                # Track match statistics
                if recommendation.recommended_sku_score >= 95:
                    successful += 1
                elif recommendation.recommended_sku_score >= MINIMUM_MATCH_THRESHOLD:
                    partial += 1
                else:
                    no_match += 1
                    alerts.append(
                        f"Item {item.item_id}: No suitable match found. "
                        f"Best score was {recommendation.recommended_sku_score}%"
                    )
                    
            except Exception as e:
                alerts.append(f"Error processing item {item.item_id}: {str(e)}")
                no_match += 1
        
        # Step 3: Build summary table
        summary_table = self._build_summary_table(recommendations)
        
        return TechnicalAgentOutput(
            rfp_id=rfp_id,
            processing_timestamp=timestamp,
            total_items_processed=len(scope_items),
            successful_matches=successful,
            partial_matches=partial,
            no_matches=no_match,
            recommendations=recommendations,
            summary_table=summary_table,
            alerts=alerts
        )
    
    def _extract_scope_of_supply(self, rfp_text: str) -> List[RFPItem]:
        """
        Extract scope of supply items from RFP text using LLM
        
        This is where LLM is used for natural language understanding
        The extraction task is delegated to the crewAI agent
        """
        # Create extraction task
        extract_task = Task(
            description=f"""
            Parse the following RFP document and extract ALL items from the Scope of Supply section.
            
            For each item extract:
            1. Item number or sequential ID
            2. Complete product specification text
            3. Quantity if mentioned
            4. Unit of measurement if mentioned
            
            RFP DOCUMENT:
            {rfp_text[:10000]}
            
            Return your response as a valid JSON array with this exact format:
            [
                {{
                    "item_id": 1,
                    "rfp_spec_raw": "11kV 3C x 300sqmm Al XLPE Cable GI Strip Armoured",
                    "quantity": "50",
                    "unit": "km"
                }}
            ]
            
            IMPORTANT: Return ONLY the JSON array, no other text.
            """,
            expected_output="A JSON array of scope of supply items",
            agent=self.rfp_parser_agent
        )
        
        # Execute with crew
        crew = Crew(
            agents=[self.rfp_parser_agent],
            tasks=[extract_task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        
        # Parse result
        try:
            # Handle CrewOutput object
            result_text = str(result)
            
            # Clean up the result - find JSON array in response
            import re
            json_match = re.search(r'\[[\s\S]*\]', result_text)
            if json_match:
                items_data = json.loads(json_match.group())
            else:
                # Try parsing the whole result
                items_data = json.loads(result_text)
            
            items = []
            for item_data in items_data:
                item = RFPItem(
                    item_id=item_data.get('item_id', len(items) + 1),
                    rfp_spec_raw=item_data.get('rfp_spec_raw', ''),
                    quantity=item_data.get('quantity'),
                    unit=item_data.get('unit')
                )
                # Extract attributes for this item
                item.extracted_attributes = self._extract_attributes(item.rfp_spec_raw)
                items.append(item)
            
            return items
            
        except Exception as e:
            print(f"Error parsing scope extraction result: {e}")
            return []
    
    def _extract_attributes(self, spec_text: str) -> ExtractedAttributes:
        """
        Extract normalized attributes from specification text
        
        Uses LLM for extraction then normalizes the results
        """
        # Create extraction task
        extract_task = Task(
            description=f"""
            Extract technical attributes from this cable specification:
            "{spec_text}"
            
            Extract these attributes (use null if not found):
            - voltage: Voltage rating (eg "11kV", "33kV")
            - conductor_material: "Al" for Aluminum, "Cu" for Copper
            - cross_section: Cross sectional area (eg "300sqmm")
            - core_count: Number as integer (eg 3 for 3-core)
            - insulation: Type (eg "XLPE", "PVC")
            - armouring: Type (eg "GI Strip", "SWA", "Unarmoured")
            - sheathing: Material (eg "PVC", "PE")
            
            Return ONLY a JSON object with these exact keys.
            Example:
            {{
                "voltage": "11kV",
                "conductor_material": "Al",
                "cross_section": "300sqmm",
                "core_count": 3,
                "insulation": "XLPE",
                "armouring": "GI Strip",
                "sheathing": "PVC"
            }}
            """,
            expected_output="A JSON object with extracted attributes",
            agent=self.attr_extractor_agent
        )
        
        crew = Crew(
            agents=[self.attr_extractor_agent],
            tasks=[extract_task],
            process=Process.sequential,
            verbose=False
        )
        
        result = crew.kickoff()
        
        try:
            result_text = str(result)
            
            # Find JSON object in response
            import re
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                attrs_data = json.loads(json_match.group())
            else:
                attrs_data = json.loads(result_text)
            
            # Normalize values
            from utils.attribute_utils import normalize_value
            
            normalized = {}
            for key, value in attrs_data.items():
                if value is not None:
                    if key == 'core_count':
                        normalized[key] = int(value) if value else None
                    elif isinstance(value, str):
                        normalized[key] = normalize_value(value.lower().strip(), key)
                    else:
                        normalized[key] = value
            
            return ExtractedAttributes(**normalized)
            
        except Exception as e:
            print(f"Error extracting attributes: {e}")
            # Fallback to rule based extraction
            from utils.attribute_utils import (
                extract_voltage, extract_cross_section, extract_core_count,
                extract_conductor_material, extract_insulation, extract_armouring
            )
            
            return ExtractedAttributes(
                voltage=extract_voltage(spec_text),
                conductor_material=extract_conductor_material(spec_text),
                cross_section=extract_cross_section(spec_text),
                core_count=extract_core_count(spec_text),
                insulation=extract_insulation(spec_text),
                armouring=extract_armouring(spec_text)
            )
    
    def _process_single_item(self, item: RFPItem) -> ItemRecommendation:
        """
        Process a single RFP item to find matching OEM products
        
        This combines semantic search with deterministic scoring
        """
        # Step 1: Semantic search for candidates
        candidates = self.vector_db.similarity_search(
            item.rfp_spec_raw, 
            k=TOP_K_CANDIDATES
        )
        
        if not candidates:
            return ItemRecommendation(
                item_id=item.item_id,
                rfp_spec_raw=item.rfp_spec_raw,
                rfp_attributes=item.extracted_attributes,
                top_3_matches=[],
                comparison_table=[],
                recommended_sku="NO_MATCH",
                recommended_sku_score=0.0,
                recommendation_notes="No candidate products found in database"
            )
        
        # Step 2: Calculate deterministic match scores for each candidate
        scored_candidates = []
        for candidate in candidates:
            match_result = self.match_engine.match_product(item, candidate)
            scored_candidates.append((candidate, match_result))
        
        # Step 3: Sort by match score and take top 3
        scored_candidates.sort(key=lambda x: x[1].match_score, reverse=True)
        top_3 = scored_candidates[:TOP_N_RECOMMENDATIONS]
        
        top_3_products = [c[0] for c in top_3]
        top_3_matches = [c[1] for c in top_3]
        
        # Step 4: Generate comparison table
        comparison_table = self.match_engine.generate_comparison_table(item, top_3_products)
        
        # Step 5: Select best match
        best_match = top_3_matches[0] if top_3_matches else None
        
        # Generate recommendation notes
        if best_match:
            if best_match.match_status == MatchStatus.EXACT_MATCH:
                notes = "Excellent match. Product meets all RFP specifications."
            elif best_match.match_status == MatchStatus.CLOSE_MATCH:
                notes = f"Good match with minor deviations: {', '.join(best_match.deviation_notes[:2])}"
            elif best_match.match_status == MatchStatus.PARTIAL_MATCH:
                notes = f"Partial match. Consider requesting custom SKU. Issues: {', '.join(best_match.deviation_notes[:2])}"
            else:
                notes = "No suitable match found. Custom SKU required."
        else:
            notes = "No products found in database matching this specification."
        
        return ItemRecommendation(
            item_id=item.item_id,
            rfp_spec_raw=item.rfp_spec_raw,
            rfp_attributes=item.extracted_attributes,
            top_3_matches=top_3_matches,
            comparison_table=comparison_table,
            recommended_sku=best_match.sku_id if best_match else "NO_MATCH",
            recommended_sku_score=best_match.match_score if best_match else 0.0,
            recommendation_notes=notes
        )
    
    def _build_summary_table(
        self, 
        recommendations: List[ItemRecommendation]
    ) -> List[Dict[str, Any]]:
        """
        Build a simplified summary table for Main Agent and Pricing Agent
        """
        summary = []
        for rec in recommendations:
            summary.append({
                "item_id": rec.item_id,
                "rfp_specification": rec.rfp_spec_raw,
                "recommended_sku": rec.recommended_sku,
                "match_score": rec.recommended_sku_score,
                "match_status": rec.top_3_matches[0].match_status.value if rec.top_3_matches else "no_match",
                "notes": rec.recommendation_notes
            })
        return summary


# ============================================================================
# CONVENIENCE FUNCTION FOR STANDALONE USAGE
# ============================================================================

def create_technical_agent(
    groq_api_key: str = None,
    oem_products: List[OEMProduct] = None
) -> TechnicalAgentSystem:
    """
    Factory function to create and initialize the Technical Agent
    
    Args:
        groq_api_key: API key for Groq LLM
        oem_products: List of OEM products to load into database
        
    Returns:
        Initialized TechnicalAgentSystem ready for processing
    """
    agent = TechnicalAgentSystem(groq_api_key=groq_api_key)
    
    if oem_products:
        agent.load_oem_products(oem_products)
    
    return agent
