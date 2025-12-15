"""
Sample OEM Product Data for Testing
This file contains dummy product datasheets representing internal SKU catalog
"""

from models import OEMProduct, ExtractedAttributes


def get_sample_oem_products():
    """
    Returns a list of sample OEM products representing the internal catalog
    These products will be loaded into the vector database for matching
    """
    
    products = [
        # High Voltage Cables
        OEMProduct(
            sku_id="HV-AL-XLPE-001",
            product_name="11kV 3C x 300sqmm Al XLPE GI Strip Armoured Cable",
            category="High Voltage Cables",
            datasheet_text="""
            Product: 11kV 3 Core 300 sq mm Aluminum XLPE Insulated GI Strip Armoured Cable
            Voltage Rating: 11kV (11000V)
            Conductor: Aluminum (Al), Stranded
            Cross Section: 300 sq mm per core
            Number of Cores: 3
            Insulation: Cross-linked Polyethylene (XLPE)
            Armour: Galvanized Iron (GI) Strip
            Outer Sheath: PVC (Polyvinyl Chloride)
            Standards: IS 7098 Part 2, IEC 60502-2
            Applications: Underground power distribution, Industrial installations
            Current Rating: 435A at 25C ground temperature
            """,
            specs=ExtractedAttributes(
                voltage="11kv",
                conductor_material="al",
                cross_section="300sqmm",
                core_count=3,
                insulation="xlpe",
                armouring="gi_strip",
                sheathing="pvc"
            )
        ),
        
        OEMProduct(
            sku_id="HV-AL-XLPE-002",
            product_name="11kV 3C x 240sqmm Al XLPE GI Strip Armoured Cable",
            category="High Voltage Cables",
            datasheet_text="""
            Product: 11kV 3 Core 240 sq mm Aluminum XLPE Insulated GI Strip Armoured Cable
            Voltage Rating: 11kV
            Conductor: Aluminum, Stranded compacted
            Cross Section: 240 sq mm
            Number of Cores: 3
            Insulation: XLPE (Cross-linked Polyethylene)
            Armour: GI Strip Armoured
            Outer Sheath: PVC Black
            Standards: IS 7098, IEC 60502
            """,
            specs=ExtractedAttributes(
                voltage="11kv",
                conductor_material="al",
                cross_section="240sqmm",
                core_count=3,
                insulation="xlpe",
                armouring="gi_strip",
                sheathing="pvc"
            )
        ),
        
        OEMProduct(
            sku_id="HV-CU-XLPE-001",
            product_name="11kV 3C x 300sqmm Cu XLPE SWA Cable",
            category="High Voltage Cables",
            datasheet_text="""
            Product: 11kV 3 Core 300 sq mm Copper XLPE Insulated Steel Wire Armoured Cable
            Voltage Rating: 11kV
            Conductor: Copper (Cu), Stranded
            Cross Section: 300 sq mm per core
            Number of Cores: 3
            Insulation: XLPE
            Armour: Steel Wire Armour (SWA)
            Outer Sheath: PVC
            Standards: IEC 60502-2, BS 6622
            Current Rating: 580A
            """,
            specs=ExtractedAttributes(
                voltage="11kv",
                conductor_material="cu",
                cross_section="300sqmm",
                core_count=3,
                insulation="xlpe",
                armouring="swa",
                sheathing="pvc"
            )
        ),
        
        OEMProduct(
            sku_id="HV-AL-XLPE-003",
            product_name="33kV 3C x 400sqmm Al XLPE GI Strip Armoured Cable",
            category="High Voltage Cables",
            datasheet_text="""
            Product: 33kV 3 Core 400 sq mm Aluminum XLPE GI Strip Armoured Cable
            Voltage Rating: 33kV (33000V)
            Conductor: Aluminum
            Cross Section: 400 sq mm
            Number of Cores: 3
            Insulation: XLPE
            Armour: GI Strip
            Sheath: PVC
            Standards: IS 7098 Part 2
            """,
            specs=ExtractedAttributes(
                voltage="33kv",
                conductor_material="al",
                cross_section="400sqmm",
                core_count=3,
                insulation="xlpe",
                armouring="gi_strip",
                sheathing="pvc"
            )
        ),
        
        # Medium Voltage Cables
        OEMProduct(
            sku_id="MV-AL-XLPE-001",
            product_name="6.6kV 3C x 185sqmm Al XLPE GI Strip Cable",
            category="Medium Voltage Cables",
            datasheet_text="""
            Product: 6.6kV 3 Core 185 sq mm Aluminum XLPE GI Strip Armoured Cable
            Voltage Rating: 6.6kV
            Conductor: Aluminum stranded
            Cross Section: 185 sq mm
            Cores: 3
            Insulation: XLPE
            Armour: Galvanized Iron Strip
            Sheath: PVC
            """,
            specs=ExtractedAttributes(
                voltage="6.6kv",
                conductor_material="al",
                cross_section="185sqmm",
                core_count=3,
                insulation="xlpe",
                armouring="gi_strip",
                sheathing="pvc"
            )
        ),
        
        OEMProduct(
            sku_id="MV-CU-XLPE-001",
            product_name="6.6kV 3C x 120sqmm Cu XLPE SWA Cable",
            category="Medium Voltage Cables",
            datasheet_text="""
            Product: 6.6kV 3 Core 120 sq mm Copper XLPE Steel Wire Armoured Cable
            Voltage: 6.6kV
            Conductor: Copper
            Size: 120 sq mm
            Cores: 3
            Insulation: Cross-linked Polyethylene
            Armour: SWA Steel Wire
            Outer: PVC sheath
            """,
            specs=ExtractedAttributes(
                voltage="6.6kv",
                conductor_material="cu",
                cross_section="120sqmm",
                core_count=3,
                insulation="xlpe",
                armouring="swa",
                sheathing="pvc"
            )
        ),
        
        # Low Voltage Cables
        OEMProduct(
            sku_id="LV-AL-PVC-001",
            product_name="1.1kV 4C x 95sqmm Al PVC Armoured Cable",
            category="Low Voltage Cables",
            datasheet_text="""
            Product: 1.1kV 4 Core 95 sq mm Aluminum PVC Insulated Armoured Cable
            Voltage: 1.1kV (1100V)
            Conductor: Aluminum
            Cross Section: 95 sq mm
            Cores: 4
            Insulation: PVC
            Armour: GI Strip
            Sheath: PVC
            Standards: IS 1554 Part 1
            """,
            specs=ExtractedAttributes(
                voltage="1.1kv",
                conductor_material="al",
                cross_section="95sqmm",
                core_count=4,
                insulation="pvc",
                armouring="gi_strip",
                sheathing="pvc"
            )
        ),
        
        OEMProduct(
            sku_id="LV-CU-PVC-001",
            product_name="1.1kV 4C x 70sqmm Cu PVC Armoured Cable",
            category="Low Voltage Cables",
            datasheet_text="""
            Product: 1.1kV 4 Core 70 sq mm Copper PVC Armoured Power Cable
            Voltage Rating: 1.1kV
            Conductor Material: Copper (Cu)
            Cross Section Area: 70 sq mm
            Number of Cores: 4
            Insulation Type: PVC (Polyvinyl Chloride)
            Armour Type: GI Strip Armoured
            Outer Sheath: PVC Black
            """,
            specs=ExtractedAttributes(
                voltage="1.1kv",
                conductor_material="cu",
                cross_section="70sqmm",
                core_count=4,
                insulation="pvc",
                armouring="gi_strip",
                sheathing="pvc"
            )
        ),
        
        # Single Core Cables
        OEMProduct(
            sku_id="SC-AL-XLPE-001",
            product_name="11kV 1C x 630sqmm Al XLPE Cable",
            category="Single Core Cables",
            datasheet_text="""
            Product: 11kV Single Core 630 sq mm Aluminum XLPE Insulated Unarmoured Cable
            Voltage: 11kV
            Conductor: Aluminum
            Cross Section: 630 sq mm
            Cores: 1 (Single Core)
            Insulation: XLPE
            Armour: Unarmoured
            Sheath: HDPE
            """,
            specs=ExtractedAttributes(
                voltage="11kv",
                conductor_material="al",
                cross_section="630sqmm",
                core_count=1,
                insulation="xlpe",
                armouring="unarmoured",
                sheathing="pe"
            )
        ),
        
        OEMProduct(
            sku_id="SC-CU-XLPE-001",
            product_name="33kV 1C x 500sqmm Cu XLPE Cable",
            category="Single Core Cables",
            datasheet_text="""
            Product: 33kV Single Core 500 sq mm Copper XLPE Unarmoured Cable
            Voltage Rating: 33kV
            Conductor: Copper stranded compacted
            Cross Section: 500 sq mm
            Cores: 1
            Insulation: XLPE Cross-linked Polyethylene
            Screen: Copper wire screen
            Sheath: HDPE High Density Polyethylene
            """,
            specs=ExtractedAttributes(
                voltage="33kv",
                conductor_material="cu",
                cross_section="500sqmm",
                core_count=1,
                insulation="xlpe",
                armouring="unarmoured",
                sheathing="pe"
            )
        ),
        
        # Control Cables
        OEMProduct(
            sku_id="CC-CU-PVC-001",
            product_name="1.1kV 12C x 2.5sqmm Cu PVC Control Cable",
            category="Control Cables",
            datasheet_text="""
            Product: 1.1kV 12 Core 2.5 sq mm Copper PVC Control Cable Armoured
            Voltage: 1.1kV
            Conductor: Copper annealed
            Cross Section: 2.5 sq mm
            Cores: 12
            Insulation: PVC
            Armour: GI Strip
            Sheath: PVC
            Application: Control and instrumentation
            """,
            specs=ExtractedAttributes(
                voltage="1.1kv",
                conductor_material="cu",
                cross_section="2.5sqmm",
                core_count=12,
                insulation="pvc",
                armouring="gi_strip",
                sheathing="pvc"
            )
        ),
        
        # Special Purpose Cable
        OEMProduct(
            sku_id="SP-AL-EPR-001",
            product_name="11kV 3C x 185sqmm Al EPR Mining Cable",
            category="Special Purpose",
            datasheet_text="""
            Product: 11kV 3 Core 185 sq mm Aluminum EPR Insulated Mining Cable
            Voltage: 11kV
            Conductor: Aluminum
            Cross Section: 185 sq mm
            Cores: 3
            Insulation: EPR (Ethylene Propylene Rubber)
            Armour: Double SWA
            Sheath: PCP (Polychloroprene)
            Application: Mining and harsh environments
            """,
            specs=ExtractedAttributes(
                voltage="11kv",
                conductor_material="al",
                cross_section="185sqmm",
                core_count=3,
                insulation="epr",
                armouring="swa",
                sheathing="pvc"
            )
        ),
    ]
    
    return products
