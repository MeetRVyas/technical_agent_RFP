"""
Sample RFP Documents for Testing the Technical Agent

These represent realistic RFP documents from PSUs and LSTK contractors
"""


SAMPLE_RFP_1 = """
REQUEST FOR PROPOSAL
RFP No: NTPC/PKG-01/CABLES/2025
Project: 2x660MW Super Thermal Power Project
Authority: NTPC Limited

SCOPE OF SUPPLY

The following cables are required for the power distribution system:

Item No. 1: HT Power Cable
Description: 11kV, 3 Core, 300 sq.mm, Aluminum Conductor, XLPE Insulated, 
GI Strip Armoured, PVC Sheathed Power Cable
Quantity: 25 km
Delivery: Within 6 months from PO

Item No. 2: HT Power Cable  
Description: 33kV, 3 Core, 400 sq.mm, Aluminum Conductor, XLPE Insulated,
GI Strip Armoured Power Cable for Switchyard Connection
Quantity: 8 km
Delivery: Within 6 months from PO

Item No. 3: LT Power Cable
Description: 1.1kV, 4 Core, 95 sq.mm, Aluminum, PVC Insulated,
GI Strip Armoured Cable for Auxiliary Power Distribution
Quantity: 45 km
Delivery: Within 4 months from PO

Item No. 4: Control Cable
Description: 1.1kV, 12 Core, 2.5 sq.mm, Copper Conductor, PVC Insulated,
GI Strip Armoured Control Cable
Quantity: 30 km
Delivery: Within 4 months from PO

TECHNICAL SPECIFICATIONS:
All cables shall conform to IS 7098 Part 2 / IEC 60502-2 standards.
Conductor shall be stranded and compacted.
Insulation shall be extruded type.

TESTING REQUIREMENTS:
1. Type Tests as per IS 7098
2. Routine Tests on each drum
3. Acceptance Tests at site
4. High Voltage Test
5. Insulation Resistance Test
6. Conductor Resistance Test

SUBMISSION DEADLINE: 30 days from RFP publication date
"""


SAMPLE_RFP_2 = """
TENDER DOCUMENT
Tender No: PGCIL/SR/2025/CABLES/001
Project: 400kV Transmission Line Extension
Organization: Power Grid Corporation of India Limited

BILL OF QUANTITIES - CABLES

Sl. No. 1
Cable Type: 11kV 3C x 240sqmm Al XLPE Armoured Cable
Application: Substation internal wiring
Required Quantity: 15 kilometers
Specifications: XLPE insulated, GI Strip armoured, PVC sheathed
Standards: IS 7098 Part 2

Sl. No. 2  
Cable Type: 33kV Single Core 500sqmm Copper XLPE Cable
Application: Underground transmission
Required Quantity: 20 kilometers
Specifications: XLPE insulated, Unarmoured with copper screen, HDPE sheath
Standards: IEC 60502-2

Sl. No. 3
Cable Type: 6.6kV 3 Core 185sqmm Aluminum XLPE Cable
Application: Medium voltage distribution
Required Quantity: 35 kilometers
Specifications: XLPE insulation, GI Strip armour, PVC outer sheath

Sl. No. 4
Cable Type: 1.1kV 4Core 70sqmm Copper PVC Armoured Cable  
Application: Low voltage power distribution
Required Quantity: 50 kilometers
Specifications: PVC insulated, GI Strip armoured

QUALITY ASSURANCE REQUIREMENTS:
- Pre-dispatch inspection at manufacturers works
- Type test reports for all cable types
- Routine test certificates
- Third party inspection by PGCIL approved agency

BID SUBMISSION: Within 45 days
DELIVERY SCHEDULE: 8-12 weeks from order confirmation
"""


SAMPLE_RFP_3 = """
ENQUIRY FOR CABLES
Reference: BHEL/PROJ/2025/ENQ/089
Project: Industrial Automation Upgrade
Client: Bharat Heavy Electricals Limited

MATERIAL REQUIREMENT LIST

1. High Voltage Cable
   Specification: 11 kV grade, 3 core, 300 mm2 cross-section, 
   Aluminum conductor with XLPE insulation and Steel Wire Armour
   Unit: Running Meter
   Quantity: 12000 meters

2. Medium Voltage Cable
   Specification: 6.6kV rated, 3 core cable, 120 sq mm copper conductor,
   XLPE insulated with SWA protection
   Unit: Meter
   Quantity: 8500 meters

3. Low Tension Power Cable
   Specification: 1100V working voltage, 4 core, 95mm2 aluminum,
   PVC insulated and armoured
   Unit: Meter  
   Quantity: 25000 meters

4. Instrumentation Cable
   Specification: 1.1kV, 12 pairs, 1.5sqmm copper, overall screened,
   armoured instrumentation cable
   Unit: Meter
   Quantity: 15000 meters

NOTE: All cables must be from IS/IEC approved manufacturers.
Factory Acceptance Test (FAT) mandatory before dispatch.

LAST DATE FOR QUOTATION: 21 days from enquiry date
"""


def get_sample_rfp(rfp_number: int = 1) -> str:
    """
    Get a sample RFP document for testing
    
    Args:
        rfp_number: 1, 2, or 3 to select different sample RFPs
        
    Returns:
        RFP document text
    """
    rfps = {
        1: SAMPLE_RFP_1,
        2: SAMPLE_RFP_2,
        3: SAMPLE_RFP_3
    }
    return rfps.get(rfp_number, SAMPLE_RFP_1)
