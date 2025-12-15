"""
Main Entry Point for the RFP Technical Agent System

This script demonstrates how to use the Technical Agent to process RFPs
and generate product recommendations

Usage:
    python main.py [--rfp-number 1|2|3] [--api-key YOUR_GROQ_API_KEY]
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import GROQ_API_KEY
from models import TechnicalAgentOutput
from agents.technical_agent import TechnicalAgentSystem, create_technical_agent
from data.sample_products import get_sample_oem_products
from data.sample_rfps import get_sample_rfp


def print_banner():
    """Print application banner"""
    banner = """
    ╔════════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║       B2B RFP TECHNICAL AGENT SYSTEM                          ║
    ║       Powered by crewAI + Groq LLM                            ║
    ║                                                                ║
    ║       Features:                                                ║
    ║       - Semantic Product Search                                ║
    ║       - Deterministic Spec Matching                           ║
    ║       - Automated Recommendations                              ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_summary_table(output: TechnicalAgentOutput):
    """Print a formatted summary table of recommendations"""
    print("\n" + "=" * 80)
    print("TECHNICAL RECOMMENDATION SUMMARY")
    print("=" * 80)
    print(f"RFP ID: {output.rfp_id}")
    print(f"Processed: {output.processing_timestamp}")
    print(f"Total Items: {output.total_items_processed}")
    print(f"Successful Matches: {output.successful_matches}")
    print(f"Partial Matches: {output.partial_matches}")
    print(f"No Matches: {output.no_matches}")
    print("-" * 80)
    
    # Print summary table
    print("\n{:<6} {:<45} {:<18} {:<8}".format(
        "Item", "RFP Specification", "Recommended SKU", "Score"
    ))
    print("-" * 80)
    
    for row in output.summary_table:
        spec_short = row['rfp_specification'][:42] + "..." if len(row['rfp_specification']) > 45 else row['rfp_specification']
        print("{:<6} {:<45} {:<18} {:<8.1f}%".format(
            row['item_id'],
            spec_short,
            row['recommended_sku'],
            row['match_score']
        ))
    
    print("-" * 80)
    
    # Print alerts if any
    if output.alerts:
        print("\nALERTS:")
        for alert in output.alerts:
            print(f"  ⚠ {alert}")
    
    print("\n")


def print_detailed_recommendations(output: TechnicalAgentOutput):
    """Print detailed recommendations with comparison tables"""
    print("\n" + "=" * 80)
    print("DETAILED RECOMMENDATIONS")
    print("=" * 80)
    
    for rec in output.recommendations:
        print(f"\n{'─' * 80}")
        print(f"ITEM {rec.item_id}: {rec.rfp_spec_raw[:70]}...")
        print(f"{'─' * 80}")
        
        # Print extracted attributes
        print("\nExtracted Attributes:")
        attrs = rec.rfp_attributes.to_normalized_dict()
        for key, value in attrs.items():
            print(f"  • {key}: {value}")
        
        # Print top 3 matches
        print("\nTop 3 OEM Matches:")
        for i, match in enumerate(rec.top_3_matches, 1):
            status_icon = "✓" if match.match_score >= 95 else "○" if match.match_score >= 60 else "✗"
            print(f"  {i}. [{status_icon}] {match.sku_id} - {match.product_name}")
            print(f"      Score: {match.match_score}% ({match.match_status.value})")
            if match.matched_attributes:
                print(f"      Matched: {', '.join(match.matched_attributes)}")
            if match.mismatched_attributes:
                print(f"      Mismatched: {', '.join(match.mismatched_attributes)}")
        
        # Print comparison table
        print("\nComparison Table:")
        print(f"  {'Attribute':<20} {'RFP Req':<15} {'SKU 1':<15} {'SKU 2':<15} {'SKU 3':<15}")
        print(f"  {'-' * 80}")
        
        for row in rec.comparison_table:
            sku1 = f"{'✓' if row.sku_1_match else '✗'} {row.sku_1_value or 'N/A'}"
            sku2 = f"{'✓' if row.sku_2_match else '✗'} {row.sku_2_value or 'N/A'}" if row.sku_2_value else "N/A"
            sku3 = f"{'✓' if row.sku_3_match else '✗'} {row.sku_3_value or 'N/A'}" if row.sku_3_value else "N/A"
            
            print(f"  {row.attribute_name:<20} {str(row.rfp_requirement):<15} {sku1:<15} {sku2:<15} {sku3:<15}")
        
        # Print recommendation
        print(f"\n  ➤ RECOMMENDED: {rec.recommended_sku} ({rec.recommended_sku_score}%)")
        print(f"    {rec.recommendation_notes}")


def save_output_to_json(output: TechnicalAgentOutput, filename: str = None):
    """Save the output to a JSON file"""
    if filename is None:
        filename = f"output/technical_output_{output.rfp_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else "output", exist_ok=True)
    
    # Convert to dict for JSON serialization
    output_dict = output.model_dump()
    
    with open(filename, 'w') as f:
        json.dump(output_dict, f, indent=2, default=str)
    
    print(f"\n✓ Output saved to: {filename}")
    return filename


def run_technical_agent(rfp_text: str, rfp_id: str, api_key: str = None):
    """
    Run the Technical Agent on an RFP document
    
    Args:
        rfp_text: The full RFP document text
        rfp_id: Unique identifier for the RFP
        api_key: Groq API key (optional uses env var if not provided)
        
    Returns:
        TechnicalAgentOutput with all recommendations
    """
    print("\n[1/4] Initializing Technical Agent System...")
    agent = create_technical_agent(groq_api_key=api_key)
    
    print("[2/4] Loading OEM Product Catalog...")
    oem_products = get_sample_oem_products()
    agent.load_oem_products(oem_products)
    print(f"      Loaded {len(oem_products)} products into vector database")
    
    print("[3/4] Processing RFP Document...")
    output = agent.process_rfp(rfp_id=rfp_id, rfp_text=rfp_text)
    
    print("[4/4] Generating Recommendations...")
    
    return output


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="B2B RFP Technical Agent System"
    )
    parser.add_argument(
        "--rfp-number",
        type=int,
        default=1,
        choices=[1, 2, 3],
        help="Sample RFP number to process (1, 2, or 3)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Groq API key (or set GROQ_API_KEY env var)"
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed recommendations with comparison tables"
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Path to save JSON output"
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Get API key
    api_key = args.api_key or GROQ_API_KEY
    if not api_key:
        print("ERROR: No Groq API key provided.")
        print("Please set GROQ_API_KEY environment variable or use --api-key argument")
        sys.exit(1)
    
    # Get sample RFP
    rfp_text = get_sample_rfp(args.rfp_number)
    rfp_id = f"SAMPLE-RFP-{args.rfp_number:03d}"
    
    print(f"Processing Sample RFP #{args.rfp_number}")
    print("-" * 40)
    
    try:
        # Run the agent
        output = run_technical_agent(rfp_text, rfp_id, api_key)
        
        # Print summary
        print_summary_table(output)
        
        # Print detailed recommendations if requested
        if args.detailed:
            print_detailed_recommendations(output)
        
        # Save to JSON if requested
        if args.output_json:
            save_output_to_json(output, args.output_json)
        else:
            save_output_to_json(output)
        
        print("\n✓ Technical Agent processing complete!")
        
    except Exception as e:
        print(f"\n✗ Error during processing: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
