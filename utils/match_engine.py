"""
Deterministic Spec Match Engine
This module handles the symbolic weighted attribute matching
NO LLM calls are made here - pure algorithmic scoring
"""

from typing import List, Dict, Tuple, Optional
from models import (
    ExtractedAttributes, 
    OEMProduct, 
    RFPItem, 
    SpecMatchResult, 
    MatchStatus,
    ComparisonRow
)
from config import ATTRIBUTE_WEIGHTS, MINIMUM_MATCH_THRESHOLD
from utils.attribute_utils import normalize_value


class SpecMatchEngine:
    """
    Engine for deterministic spec matching between RFP requirements and OEM products
    Uses weighted attribute comparison with normalization
    """
    
    def __init__(self, weights: Dict[str, float] = None):
        """
        Initialize the match engine with custom or default weights
        
        Args:
            weights: Optional custom weights dictionary. Must sum to 1.0
        """
        self.weights = weights or ATTRIBUTE_WEIGHTS
        
        # Validate weights sum to 1.0 with small tolerance for floating point
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
    
    def calculate_match_score(
        self, 
        rfp_attrs: ExtractedAttributes, 
        oem_attrs: ExtractedAttributes
    ) -> Tuple[float, List[str], List[str], List[str]]:
        """
        Calculate weighted match score between RFP requirements and OEM product specs
        
        This is the core deterministic algorithm
        No LLM involvement - pure symbolic comparison
        
        Args:
            rfp_attrs: Extracted attributes from RFP item
            oem_attrs: Extracted attributes from OEM product
            
        Returns:
            Tuple of score, matched_attrs, mismatched_attrs, missing_attrs
        """
        score = 0.0
        matched = []
        mismatched = []
        missing = []
        
        rfp_dict = rfp_attrs.to_normalized_dict()
        oem_dict = oem_attrs.to_normalized_dict()
        
        for attr_name, weight in self.weights.items():
            rfp_value = rfp_dict.get(attr_name)
            oem_value = oem_dict.get(attr_name)
            
            # Case 1: RFP doesnt specify this attribute
            # We give full weight since OEM product can have any value
            if rfp_value is None:
                score += weight
                continue
            
            # Case 2: RFP specifies but OEM doesnt have this attribute
            # This is a missing attribute - no score
            if oem_value is None:
                missing.append(attr_name)
                continue
            
            # Case 3: Both have values - compare them
            match_result = self._compare_attribute(attr_name, rfp_value, oem_value)
            
            if match_result == 1.0:
                # Exact match
                score += weight
                matched.append(attr_name)
            elif match_result > 0:
                # Partial match for compatible values
                score += weight * match_result
                mismatched.append(f"{attr_name} (partial)")
            else:
                # No match
                mismatched.append(attr_name)
        
        # Convert to percentage
        final_score = round(score * 100, 2)
        
        return final_score, matched, mismatched, missing
    
    def _compare_attribute(
        self, 
        attr_name: str, 
        rfp_value: any, 
        oem_value: any
    ) -> float:
        """
        Compare a single attribute and return match score 0 to 1
        
        Handles special comparison logic for different attribute types
        """
        # Normalize both values
        if isinstance(rfp_value, str):
            rfp_normalized = normalize_value(rfp_value, attr_name)
        else:
            rfp_normalized = rfp_value
            
        if isinstance(oem_value, str):
            oem_normalized = normalize_value(oem_value, attr_name)
        else:
            oem_normalized = oem_value
        
        # Exact match after normalization
        if rfp_normalized == oem_normalized:
            return 1.0
        
        # Special handling for voltage - must be exact or higher
        if attr_name == "voltage":
            return self._compare_voltage(rfp_normalized, oem_normalized)
        
        # Special handling for cross section - can be equal or higher
        if attr_name == "cross_section":
            return self._compare_cross_section(rfp_normalized, oem_normalized)
        
        # Special handling for core count - must be exact
        if attr_name == "core_count":
            return 1.0 if rfp_normalized == oem_normalized else 0.0
        
        # Default string comparison - no match if not equal
        return 0.0
    
    def _compare_voltage(self, rfp_voltage: str, oem_voltage: str) -> float:
        """
        Compare voltage ratings
        OEM can be equal or higher than RFP requirement
        Higher voltage gets partial credit as its overengineered
        """
        try:
            # Extract numeric values
            rfp_num = float(rfp_voltage.replace('kv', '').replace('v', ''))
            oem_num = float(oem_voltage.replace('kv', '').replace('v', ''))
            
            # Exact match
            if abs(rfp_num - oem_num) < 0.1:
                return 1.0
            
            # OEM is higher - acceptable but overengineered
            if oem_num > rfp_num:
                return 0.8
            
            # OEM is lower - not acceptable
            return 0.0
            
        except (ValueError, AttributeError):
            return 0.0
    
    def _compare_cross_section(self, rfp_cs: str, oem_cs: str) -> float:
        """
        Compare cross section areas
        OEM can be equal or higher than RFP requirement
        """
        try:
            # Extract numeric values
            rfp_num = float(rfp_cs.replace('sqmm', ''))
            oem_num = float(oem_cs.replace('sqmm', ''))
            
            # Exact match
            if abs(rfp_num - oem_num) < 0.1:
                return 1.0
            
            # OEM is higher - acceptable
            if oem_num > rfp_num:
                return 0.9
            
            # OEM is lower - not acceptable
            return 0.0
            
        except (ValueError, AttributeError):
            return 0.0
    
    def match_product(
        self, 
        rfp_item: RFPItem, 
        oem_product: OEMProduct
    ) -> SpecMatchResult:
        """
        Match a single OEM product against an RFP item
        Returns a complete match result with all details
        """
        score, matched, mismatched, missing = self.calculate_match_score(
            rfp_item.extracted_attributes,
            oem_product.specs
        )
        
        # Determine match status based on score
        if score >= 95:
            status = MatchStatus.EXACT_MATCH
        elif score >= 80:
            status = MatchStatus.CLOSE_MATCH
        elif score >= MINIMUM_MATCH_THRESHOLD:
            status = MatchStatus.PARTIAL_MATCH
        else:
            status = MatchStatus.NO_MATCH
        
        # Generate deviation notes for mismatches
        deviation_notes = self._generate_deviation_notes(
            rfp_item.extracted_attributes,
            oem_product.specs,
            mismatched,
            missing
        )
        
        return SpecMatchResult(
            sku_id=oem_product.sku_id,
            product_name=oem_product.product_name,
            match_score=score,
            match_status=status,
            matched_attributes=matched,
            mismatched_attributes=mismatched,
            missing_attributes=missing,
            deviation_notes=deviation_notes
        )
    
    def _generate_deviation_notes(
        self,
        rfp_attrs: ExtractedAttributes,
        oem_attrs: ExtractedAttributes,
        mismatched: List[str],
        missing: List[str]
    ) -> List[str]:
        """
        Generate human readable deviation notes for the technical team
        """
        notes = []
        rfp_dict = rfp_attrs.to_normalized_dict()
        oem_dict = oem_attrs.to_normalized_dict()
        
        for attr in mismatched:
            # Remove partial marker if present
            attr_clean = attr.replace(' (partial)', '')
            rfp_val = rfp_dict.get(attr_clean, 'N/A')
            oem_val = oem_dict.get(attr_clean, 'N/A')
            notes.append(f"RFP requires {attr_clean}={rfp_val}, OEM has {oem_val}")
        
        for attr in missing:
            rfp_val = rfp_dict.get(attr, 'N/A')
            notes.append(f"RFP requires {attr}={rfp_val}, OEM spec not available")
        
        return notes
    
    def generate_comparison_table(
        self,
        rfp_item: RFPItem,
        top_3_products: List[OEMProduct]
    ) -> List[ComparisonRow]:
        """
        Generate a comparison table showing RFP requirements vs Top 3 SKUs
        This table helps the technical team visualize matches and deviations
        """
        comparison = []
        rfp_dict = rfp_item.extracted_attributes.to_normalized_dict()
        
        # Get all attribute names to compare
        all_attrs = list(self.weights.keys())
        
        for attr_name in all_attrs:
            rfp_value = rfp_dict.get(attr_name)
            
            # Get values from top 3 products
            sku_values = []
            sku_matches = []
            
            for i, product in enumerate(top_3_products):
                oem_dict = product.specs.to_normalized_dict()
                oem_value = oem_dict.get(attr_name)
                sku_values.append(str(oem_value) if oem_value else "N/A")
                
                # Determine if its a match
                if rfp_value is None:
                    sku_matches.append(True)  # No requirement means anything matches
                elif oem_value is None:
                    sku_matches.append(False)
                else:
                    match_score = self._compare_attribute(attr_name, rfp_value, oem_value)
                    sku_matches.append(match_score > 0)
            
            # Pad with None if less than 3 products
            while len(sku_values) < 3:
                sku_values.append(None)
                sku_matches.append(False)
            
            row = ComparisonRow(
                attribute_name=attr_name,
                rfp_requirement=str(rfp_value) if rfp_value else "Not specified",
                sku_1_value=sku_values[0],
                sku_1_match=sku_matches[0],
                sku_2_value=sku_values[1],
                sku_2_match=sku_matches[1],
                sku_3_value=sku_values[2],
                sku_3_match=sku_matches[2],
            )
            comparison.append(row)
        
        return comparison
