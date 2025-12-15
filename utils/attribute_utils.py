"""
Utility functions for the Technical Agent
Handles text normalization attribute extraction helpers and validation
"""

import re
from typing import Optional, Dict, Any, Tuple, List
from config import NORMALIZED_VALUES


def normalize_value(value: str, value_type: str = "general") -> str:
    """
    Normalize a value to its canonical form for consistent matching
    This ensures that Al matches Aluminum and XLPE matches Cross Linked Polyethylene
    """
    if not value:
        return ""
    
    # Convert to lowercase and strip whitespace
    normalized = value.lower().strip()
    
    # Check if we have a known normalization
    if normalized in NORMALIZED_VALUES:
        return NORMALIZED_VALUES[normalized]
    
    return normalized


def extract_voltage(text: str) -> Optional[str]:
    """
    Extract voltage rating from specification text
    Handles formats like 11kV 11 kV 11000V etc
    """
    if not text:
        return None
    
    text = text.lower()
    
    # Pattern for kV format eg 11kV 33kV 11 kV
    kv_pattern = r'(\d+(?:\.\d+)?)\s*kv'
    match = re.search(kv_pattern, text)
    if match:
        return f"{match.group(1)}kv"
    
    # Pattern for V format and convert to kV if above 1000
    v_pattern = r'(\d+(?:\.\d+)?)\s*v(?:olt)?s?'
    match = re.search(v_pattern, text)
    if match:
        voltage = float(match.group(1))
        if voltage >= 1000:
            return f"{voltage/1000}kv"
        return f"{voltage}v"
    
    return None


def extract_cross_section(text: str) -> Optional[str]:
    """
    Extract cross section area from specification text
    Handles formats like 300sqmm 300 sq mm 300mm2 etc
    """
    if not text:
        return None
    
    text = text.lower()
    
    # Pattern for sqmm format
    patterns = [
        r'(\d+(?:\.\d+)?)\s*sq\s*mm',
        r'(\d+(?:\.\d+)?)\s*sqmm',
        r'(\d+(?:\.\d+)?)\s*mm\s*2',
        r'(\d+(?:\.\d+)?)\s*mm²',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return f"{match.group(1)}sqmm"
    
    return None


def extract_core_count(text: str) -> Optional[int]:
    """
    Extract number of cores from specification text
    Handles formats like 3 core 3C 3x 3 Core etc
    """
    if not text:
        return None
    
    text = text.lower()
    
    # Pattern for core count
    patterns = [
        r'(\d+)\s*[-x]\s*core',
        r'(\d+)\s*core',
        r'(\d+)\s*c\s+',
        r'(\d+)c(?:\s|x)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    
    return None


def extract_conductor_material(text: str) -> Optional[str]:
    """
    Extract conductor material from specification text
    Returns normalized value al or cu
    """
    if not text:
        return None
    
    text = text.lower()
    
    # Check for aluminum variants
    if any(term in text for term in ['aluminum', 'aluminium', ' al ', ' al.', '/al']):
        return "al"
    
    # Check for copper variants
    if any(term in text for term in ['copper', ' cu ', ' cu.', '/cu']):
        return "cu"
    
    return None


def extract_insulation(text: str) -> Optional[str]:
    """
    Extract insulation type from specification text
    """
    if not text:
        return None
    
    text = text.lower()
    
    insulation_types = {
        'xlpe': ['xlpe', 'cross linked polyethylene', 'cross-linked polyethylene'],
        'pvc': ['pvc', 'polyvinyl chloride'],
        'epr': ['epr', 'ethylene propylene rubber'],
        'rubber': ['rubber insulated'],
    }
    
    for normalized, variants in insulation_types.items():
        if any(variant in text for variant in variants):
            return normalized
    
    return None


def extract_armouring(text: str) -> Optional[str]:
    """
    Extract armouring type from specification text
    """
    if not text:
        return None
    
    text = text.lower()
    
    # Check for unarmoured first
    if 'unarmoured' in text or 'un-armoured' in text or 'non armoured' in text:
        return "unarmoured"
    
    armouring_types = {
        'gi_strip': ['gi strip', 'galvanized iron strip', 'galvanised iron strip'],
        'gi_wire': ['gi wire', 'galvanized iron wire', 'galvanised iron wire'],
        'swa': ['swa', 'steel wire armour', 'steel wire armored'],
        'sta': ['sta', 'steel tape armour'],
    }
    
    for normalized, variants in armouring_types.items():
        if any(variant in text for variant in variants):
            return normalized
    
    return None


def parse_quantity_and_unit(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse quantity and unit from specification text
    Returns tuple of quantity string and unit string
    """
    if not text:
        return None, None
    
    # Pattern for quantity with unit
    patterns = [
        r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(km|m|meters|metres|coils|drums|lengths)',
        r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(nos?|pcs?|pieces?|units?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            quantity = match.group(1).replace(',', '')
            unit = match.group(2)
            return quantity, unit
    
    return None, None


def validate_attributes(attrs: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate extracted attributes and return status with list of issues
    """
    issues = []
    
    # Check for critical missing attributes
    critical_attrs = ['voltage', 'conductor_material', 'cross_section']
    for attr in critical_attrs:
        if not attrs.get(attr):
            issues.append(f"Missing critical attribute: {attr}")
    
    # Validate voltage format
    if attrs.get('voltage'):
        if not re.match(r'\d+(?:\.\d+)?(?:kv|v)', attrs['voltage']):
            issues.append(f"Invalid voltage format: {attrs['voltage']}")
    
    # Validate core count
    if attrs.get('core_count'):
        if not isinstance(attrs['core_count'], int) or attrs['core_count'] < 1:
            issues.append(f"Invalid core count: {attrs['core_count']}")
    
    is_valid = len(issues) == 0 or len([i for i in issues if 'critical' in i.lower()]) == 0
    
    return is_valid, issues
