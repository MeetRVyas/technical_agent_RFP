"""
Utility modules for the RFP Technical Agent
"""

from utils.attribute_utils import (
    normalize_value,
    extract_voltage,
    extract_cross_section,
    extract_core_count,
    extract_conductor_material,
    extract_insulation,
    extract_armouring,
    parse_quantity_and_unit,
    validate_attributes
)

from utils.match_engine import SpecMatchEngine
from utils.vector_db import VectorDatabase

__all__ = [
    'normalize_value',
    'extract_voltage',
    'extract_cross_section',
    'extract_core_count',
    'extract_conductor_material',
    'extract_insulation',
    'extract_armouring',
    'parse_quantity_and_unit',
    'validate_attributes',
    'SpecMatchEngine',
    'VectorDatabase'
]
