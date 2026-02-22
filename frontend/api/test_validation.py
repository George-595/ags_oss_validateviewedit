import sys
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd

# Add current directory to path
import os
sys.path.append(os.path.dirname(__file__))

import ags_service

class TestValidation(unittest.TestCase):

    @patch('ags_service.AGS4')
    def test_classification_and_bgs_rules(self, mock_ags4):
        # Setup mock error report
        mock_error_report = {
            "AGS Format Rule 2a": [
                {"line": 1, "group": "PROJ", "desc": "Is not terminated by <CR> and <LF> characters."}
            ],
            "FYI (Related to Rule 16)": [
                {"line": 17, "group": "ABBR", "desc": "LOCA_TYPE: Description of abbreviation \"CP\" is \"Cable Percussion\" but it should be \"Cable percussion (shell and auger)\""}
            ],
            "Warning Message": [
                {"line": 2, "group": "PROJ", "desc": "Just a warning"}
            ]
        }
        mock_ags4.check_file.return_value = mock_error_report

        # Setup mock tables
        mock_tables = {
            'PROJ': pd.DataFrame([{'PROJ_ID': 'TEST'}]),
            'LOCA': pd.DataFrame([
                {'LOCA_ID': 'BH01', 'LOCA_NATE': '123', 'LOCA_NATN': '456', 'LOCA_GREF': 'OSGB36'},
                {'LOCA_ID': 'BH02', 'LOCA_NATE': '0', 'LOCA_NATN': '0'} # Should trigger BGS error
            ])
            # Missing TYPE and UNIT should trigger BGS error
        }
        mock_ags4.AGS4_to_dataframe.return_value = (mock_tables, {})

        result = ags_service.validate_file("fake.ags")

        # Check classification
        self.assertEqual(len(result['errors']), 4) # 1 Rule 2a + 2 BGS (missing groups + BH02 nate/natn) + 1 BGS (BH01 spatial? no, BH01 has GREF)
        # Wait, let's re-calculate:
        # 1. Rule 2a (Error)
        # 2. [BGS] Required groups missing: TYPE, UNIT (Error)
        # 3. [LOCA BH02] BGS: LOCA_NATE / LOCA_NATN contains zeros or null values (Error)
        # 4. BH01 has LOCA_GREF. BH02 has nothing. So 4. Spatial referencing... (Error)
        
        self.assertEqual(len(result['warnings']), 2) # 1 FYI + 1 Warning
        self.assertFalse(result['is_valid'])

        print("Verification successful!")
        for e in result['errors']:
            print(f"Error: {e}")
        for w in result['warnings']:
            print(f"Warning: {w}")

if __name__ == '__main__':
    unittest.main()
