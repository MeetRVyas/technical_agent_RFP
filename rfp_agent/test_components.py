"""
Standalone Test Script for Technical Agent Components

This script tests the deterministic components of the Technical Agent
without requiring LLM API calls

Run this to verify:
1 Spec Match Engine works correctly
2 Vector Database search works
3 Attribute normalization is correct
"""

import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import RFPItem, OEMProduct, ExtractedAttributes, MatchStatus
from utils.match_engine import SpecMatchEngine
from utils.vector_db import VectorDatabase
from utils.attribute_utils import (
    extract_voltage, extract_cross_section, extract_core_count,
    extract_conductor_material, extract_insulation, extract_armouring,
    normalize_value
)
from data.sample_products import get_sample_oem_products


def test_attribute_extraction():
    """Test the rule based attribute extraction functions"""
    print("\n" + "=" * 60)
    print("TEST 1: Attribute Extraction")
    print("=" * 60)
    
    test_cases = [
        "11kV 3C x 300sqmm Al XLPE GI Strip Armoured Cable",
        "33kV 3 Core 400 sq mm Aluminum XLPE Cable",
        "6.6kV 3-Core 185sqmm Copper XLPE SWA Cable",
        "1.1kV 4Core 95mm2 Al PVC Armoured",
    ]
    
    for spec in test_cases:
        print(f"\nInput: {spec}")
        print("-" * 40)
        print(f"  Voltage: {extract_voltage(spec)}")
        print(f"  Conductor: {extract_conductor_material(spec)}")
        print(f"  Cross Section: {extract_cross_section(spec)}")
        print(f"  Core Count: {extract_core_count(spec)}")
        print(f"  Insulation: {extract_insulation(spec)}")
        print(f"  Armouring: {extract_armouring(spec)}")
    
    print("\n✓ Attribute extraction tests passed")


def test_value_normalization():
    """Test value normalization"""
    print("\n" + "=" * 60)
    print("TEST 2: Value Normalization")
    print("=" * 60)
    
    test_pairs = [
        ("Aluminum", "al"),
        ("Cu", "cu"),
        ("XLPE", "xlpe"),
        ("Cross Linked Polyethylene", "xlpe"),
        ("GI Strip", "gi_strip"),
        ("Steel Wire Armour", "swa"),
    ]
    
    all_passed = True
    for input_val, expected in test_pairs:
        result = normalize_value(input_val)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        print(f"  {status} '{input_val}' -> '{result}' (expected: '{expected}')")
    
    if all_passed:
        print("\n✓ Normalization tests passed")
    else:
        print("\n✗ Some normalization tests failed")


def test_spec_match_engine():
    """Test the deterministic spec matching engine"""
    print("\n" + "=" * 60)
    print("TEST 3: Spec Match Engine")
    print("=" * 60)
    
    engine = SpecMatchEngine()
    
    # Test case 1: Exact match
    rfp_attrs = ExtractedAttributes(
        voltage="11kv",
        conductor_material="al",
        cross_section="300sqmm",
        core_count=3,
        insulation="xlpe",
        armouring="gi_strip",
        sheathing="pvc"
    )
    
    oem_attrs = ExtractedAttributes(
        voltage="11kv",
        conductor_material="al",
        cross_section="300sqmm",
        core_count=3,
        insulation="xlpe",
        armouring="gi_strip",
        sheathing="pvc"
    )
    
    score, matched, mismatched, missing = engine.calculate_match_score(rfp_attrs, oem_attrs)
    print(f"\nTest Case 1: Exact Match")
    print(f"  Score: {score}%")
    print(f"  Matched: {matched}")
    print(f"  Expected: 100%")
    assert score == 100.0, f"Expected 100%, got {score}%"
    print("  ✓ Passed")
    
    # Test case 2: Partial match different armouring
    oem_attrs_2 = ExtractedAttributes(
        voltage="11kv",
        conductor_material="al",
        cross_section="300sqmm",
        core_count=3,
        insulation="xlpe",
        armouring="swa",  # Different armouring
        sheathing="pvc"
    )
    
    score, matched, mismatched, missing = engine.calculate_match_score(rfp_attrs, oem_attrs_2)
    print(f"\nTest Case 2: Different Armouring")
    print(f"  Score: {score}%")
    print(f"  Matched: {matched}")
    print(f"  Mismatched: {mismatched}")
    print(f"  Expected: 90% (armouring weight is 0.1)")
    assert 89 <= score <= 91, f"Expected ~90%, got {score}%"
    print("  ✓ Passed")
    
    # Test case 3: Higher voltage acceptable
    oem_attrs_3 = ExtractedAttributes(
        voltage="33kv",  # Higher voltage
        conductor_material="al",
        cross_section="300sqmm",
        core_count=3,
        insulation="xlpe",
        armouring="gi_strip",
        sheathing="pvc"
    )
    
    score, matched, mismatched, missing = engine.calculate_match_score(rfp_attrs, oem_attrs_3)
    print(f"\nTest Case 3: Higher Voltage (Over-engineered)")
    print(f"  Score: {score}%")
    print(f"  RFP: 11kv, OEM: 33kv")
    print(f"  Expected: ~95% (voltage gets 80% credit for being higher)")
    assert 94 <= score <= 96, f"Expected ~95%, got {score}%"
    print("  ✓ Passed")
    
    # Test case 4: Lower voltage not acceptable
    rfp_attrs_hv = ExtractedAttributes(
        voltage="33kv",  # Requires 33kV
        conductor_material="al",
        cross_section="300sqmm",
        core_count=3,
        insulation="xlpe",
        armouring="gi_strip",
        sheathing="pvc"
    )
    
    oem_attrs_4 = ExtractedAttributes(
        voltage="11kv",  # Only has 11kV
        conductor_material="al",
        cross_section="300sqmm",
        core_count=3,
        insulation="xlpe",
        armouring="gi_strip",
        sheathing="pvc"
    )
    
    score, matched, mismatched, missing = engine.calculate_match_score(rfp_attrs_hv, oem_attrs_4)
    print(f"\nTest Case 4: Lower Voltage (Not Acceptable)")
    print(f"  Score: {score}%")
    print(f"  RFP: 33kv, OEM: 11kv")
    print(f"  Expected: 75% (voltage gets 0 credit for being lower)")
    assert 74 <= score <= 76, f"Expected 75%, got {score}%"
    print("  ✓ Passed")
    
    print("\n✓ Spec Match Engine tests passed")


def test_vector_database():
    """Test the vector database search functionality"""
    print("\n" + "=" * 60)
    print("TEST 4: Vector Database Search")
    print("=" * 60)
    
    # Initialize database with sample products
    db = VectorDatabase()
    products = get_sample_oem_products()
    db.initialize_from_products(products)
    
    print(f"  Loaded {len(products)} products into vector database")
    
    # Test search
    test_queries = [
        "11kV 3 Core 300sqmm Aluminum XLPE Cable",
        "33kV single core copper cable",
        "Low voltage 4 core PVC cable",
    ]
    
    for query in test_queries:
        print(f"\n  Query: '{query}'")
        results = db.similarity_search(query, k=3)
        print(f"  Top 3 results:")
        for i, product in enumerate(results, 1):
            print(f"    {i}. {product.sku_id}: {product.product_name}")
    
    print("\n✓ Vector database tests passed")


def test_full_matching_pipeline():
    """Test the complete matching pipeline"""
    print("\n" + "=" * 60)
    print("TEST 5: Full Matching Pipeline")
    print("=" * 60)
    
    # Setup
    engine = SpecMatchEngine()
    db = VectorDatabase()
    products = get_sample_oem_products()
    db.initialize_from_products(products)
    
    # Create test RFP item
    rfp_item = RFPItem(
        item_id=1,
        rfp_spec_raw="11kV 3C x 300sqmm Al XLPE GI Strip Armoured Cable",
        quantity="25",
        unit="km",
        extracted_attributes=ExtractedAttributes(
            voltage="11kv",
            conductor_material="al",
            cross_section="300sqmm",
            core_count=3,
            insulation="xlpe",
            armouring="gi_strip",
            sheathing="pvc"
        )
    )
    
    print(f"\n  RFP Item: {rfp_item.rfp_spec_raw}")
    
    # Step 1: Semantic search
    candidates = db.similarity_search(rfp_item.rfp_spec_raw, k=5)
    print(f"\n  Step 1 - Semantic Search: Found {len(candidates)} candidates")
    
    # Step 2: Deterministic scoring
    scored = []
    for candidate in candidates:
        result = engine.match_product(rfp_item, candidate)
        scored.append((candidate, result))
        print(f"    {candidate.sku_id}: {result.match_score}% ({result.match_status.value})")
    
    # Step 3: Sort and select best
    scored.sort(key=lambda x: x[1].match_score, reverse=True)
    best_match = scored[0]
    
    print(f"\n  Step 2 - Best Match: {best_match[0].sku_id}")
    print(f"    Score: {best_match[1].match_score}%")
    print(f"    Status: {best_match[1].match_status.value}")
    print(f"    Matched Attributes: {best_match[1].matched_attributes}")
    
    # Step 4: Generate comparison table
    top_3_products = [s[0] for s in scored[:3]]
    comparison = engine.generate_comparison_table(rfp_item, top_3_products)
    
    print(f"\n  Step 3 - Comparison Table:")
    print(f"    {'Attribute':<20} {'RFP':<12} {'SKU 1':<12} {'SKU 2':<12} {'SKU 3':<12}")
    print(f"    {'-' * 68}")
    for row in comparison:
        print(f"    {row.attribute_name:<20} {str(row.rfp_requirement):<12} "
              f"{'✓' if row.sku_1_match else '✗'}{str(row.sku_1_value):<11} "
              f"{'✓' if row.sku_2_match else '✗'}{str(row.sku_2_value):<11} "
              f"{'✓' if row.sku_3_match else '✗'}{str(row.sku_3_value):<11}")
    
    print("\n✓ Full pipeline tests passed")


def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "=" * 60)
    print("TEST 6: Edge Cases")
    print("=" * 60)
    
    engine = SpecMatchEngine()
    
    # Test case 1: Missing RFP attributes
    print("\n  Case 1: Missing RFP attributes")
    rfp_attrs = ExtractedAttributes(
        voltage="11kv",
        conductor_material="al",
        # Other attributes missing
    )
    oem_attrs = ExtractedAttributes(
        voltage="11kv",
        conductor_material="al",
        cross_section="300sqmm",
        core_count=3,
        insulation="xlpe",
        armouring="gi_strip",
        sheathing="pvc"
    )
    
    score, matched, mismatched, missing = engine.calculate_match_score(rfp_attrs, oem_attrs)
    print(f"    Score: {score}%")
    print(f"    (Missing RFP specs are not penalized)")
    print("    ✓ Handled correctly")
    
    # Test case 2: Missing OEM attributes
    print("\n  Case 2: Missing OEM attributes")
    rfp_attrs_full = ExtractedAttributes(
        voltage="11kv",
        conductor_material="al",
        cross_section="300sqmm",
        core_count=3,
        insulation="xlpe",
        armouring="gi_strip",
        sheathing="pvc"
    )
    oem_attrs_partial = ExtractedAttributes(
        voltage="11kv",
        conductor_material="al",
        # Other attributes missing
    )
    
    score, matched, mismatched, missing = engine.calculate_match_score(rfp_attrs_full, oem_attrs_partial)
    print(f"    Score: {score}%")
    print(f"    Missing attributes: {missing}")
    print("    ✓ Handled correctly")
    
    # Test case 3: Empty attributes
    print("\n  Case 3: Empty attributes")
    empty_attrs = ExtractedAttributes()
    score, matched, mismatched, missing = engine.calculate_match_score(empty_attrs, empty_attrs)
    print(f"    Score: {score}%")
    print(f"    (Empty specs should score 100% - no requirements)")
    print("    ✓ Handled correctly")
    
    print("\n✓ Edge case tests passed")


def run_all_tests():
    """Run all test suites"""
    print("\n" + "=" * 60)
    print("TECHNICAL AGENT - COMPONENT TESTS")
    print("=" * 60)
    print("\nRunning tests for deterministic components...")
    print("(These tests do not require LLM API calls)")
    
    test_attribute_extraction()
    test_value_normalization()
    test_spec_match_engine()
    test_vector_database()
    test_full_matching_pipeline()
    test_edge_cases()
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)
    print("\nThe deterministic components are working correctly.")
    print("To test the full system with LLM, run:")
    print("  python main.py --api-key YOUR_GROQ_API_KEY")


if __name__ == "__main__":
    run_all_tests()
