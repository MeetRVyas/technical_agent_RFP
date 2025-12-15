"""
Data models for the RFP Technical Agent
Pydantic models ensure type safety and validation across the system
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class MatchStatus(str, Enum):
    """Status indicators for SKU matching results"""
    EXACT_MATCH = "exact_match"
    CLOSE_MATCH = "close_match"
    PARTIAL_MATCH = "partial_match"
    NO_MATCH = "no_match"


class ExtractedAttributes(BaseModel):
    """
    Normalized technical attributes extracted from RFP or OEM datasheet
    All values are lowercased and normalized for consistent comparison
    """
    voltage: Optional[str] = Field(default=None, description="Voltage rating eg 11kV 33kV")
    conductor_material: Optional[str] = Field(default=None, description="Conductor material Al or Cu")
    cross_section: Optional[str] = Field(default=None, description="Cross section area eg 300sqmm")
    core_count: Optional[int] = Field(default=None, description="Number of cores eg 3 for 3 core")
    insulation: Optional[str] = Field(default=None, description="Insulation type eg XLPE PVC")
    armouring: Optional[str] = Field(default=None, description="Armouring type eg GI Strip SWA")
    sheathing: Optional[str] = Field(default=None, description="Outer sheath material")
    
    def to_normalized_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with only non null values"""
        return {k: v for k, v in self.model_dump().items() if v is not None}


class RFPItem(BaseModel):
    """Single item from the RFP scope of supply"""
    item_id: int = Field(description="Unique identifier for this item in the RFP")
    rfp_spec_raw: str = Field(description="Original raw specification text from RFP")
    quantity: Optional[str] = Field(default=None, description="Required quantity")
    unit: Optional[str] = Field(default=None, description="Unit of measurement")
    extracted_attributes: ExtractedAttributes = Field(
        default_factory=ExtractedAttributes,
        description="Normalized technical attributes extracted by LLM"
    )


class OEMProduct(BaseModel):
    """OEM product from the internal catalog"""
    sku_id: str = Field(description="Internal SKU identifier")
    product_name: str = Field(description="Product display name")
    datasheet_text: str = Field(description="Full datasheet text for embedding")
    specs: ExtractedAttributes = Field(description="Normalized product specifications")
    category: Optional[str] = Field(default=None, description="Product category")


class SpecMatchResult(BaseModel):
    """Result of matching a single OEM SKU against an RFP item"""
    sku_id: str
    product_name: str
    match_score: float = Field(description="Match percentage 0 to 100")
    match_status: MatchStatus
    matched_attributes: List[str] = Field(default_factory=list)
    mismatched_attributes: List[str] = Field(default_factory=list)
    missing_attributes: List[str] = Field(default_factory=list)
    deviation_notes: List[str] = Field(default_factory=list)


class ComparisonRow(BaseModel):
    """Single row in the comparison table"""
    attribute_name: str
    rfp_requirement: Optional[str]
    sku_1_value: Optional[str]
    sku_1_match: bool
    sku_2_value: Optional[str]
    sku_2_match: bool
    sku_3_value: Optional[str]
    sku_3_match: bool


class ItemRecommendation(BaseModel):
    """Complete recommendation for a single RFP item"""
    item_id: int
    rfp_spec_raw: str
    rfp_attributes: ExtractedAttributes
    top_3_matches: List[SpecMatchResult]
    comparison_table: List[ComparisonRow]
    recommended_sku: str
    recommended_sku_score: float
    recommendation_notes: str


class TechnicalAgentOutput(BaseModel):
    """Final output from the Technical Agent to be consumed by Main and Pricing agents"""
    rfp_id: str
    processing_timestamp: str
    total_items_processed: int
    successful_matches: int
    partial_matches: int
    no_matches: int
    recommendations: List[ItemRecommendation]
    summary_table: List[Dict[str, Any]] = Field(
        description="Simplified table mapping RFP items to recommended SKUs"
    )
    alerts: List[str] = Field(
        default_factory=list,
        description="Any warnings or alerts about the matching process"
    )
