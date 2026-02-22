import os
from python_ags4 import AGS4
import pandas as pd
import json

def validate_file(filepath: str) -> dict:
    """
    Validates an AGS file using the python-ags4 library.
    Translates the output into a clean JSON structure for the frontend.
    """
    try:
        # check_file runs the validation against the selected or detected AGS4 version
        # It returns tuple: (error_list, warning_list, summary_dict)
        # However, documentation states standard usage. Let's inspect the returns or fallback safely.
        
        # Note: python-ags4 1.1.0 `check_file` returns dict of DataFrames or raw error string.
        # We will capture it. (For now returning mock/basic response until we test the exact struct)
        
        # Let's perform basic extraction first
        tables, headings = AGS4.AGS4_to_dataframe(filepath)
        
        # Let's run check file
        # We'll need to parse the standard text report or dict. 
        # For MVP, we will extract some basic meta from TRAN table
        
        metadata = {}
        if tables and 'TRAN' in tables and not tables['TRAN'].empty:
            tran_df = tables['TRAN']
            # extract basic info if exists
            metadata['version'] = tran_df.get('TRAN_AGS', pd.Series(['Unknown'])).iloc[0]
            metadata['producer'] = tran_df.get('TRAN_PROD', pd.Series(['Unknown'])).iloc[0]
            
            
        # Using basic check_file for errors
        error_report = AGS4.check_file(filepath)
        
        errors = []
        warnings = []
        is_valid = True
        
        if error_report:
           is_valid = False
           if isinstance(error_report, dict):
               for rule, item_list in error_report.items():
                   # The keys are things like "AGS Format Rule 19a" or "Summary of data"
                   # The values are often lists of dicts, e.g. [{'line': 2, 'group': 'PROJ', 'desc': 'Error'}]
                   if rule.startswith("Summary of data") or rule.startswith("Metadata"):
                       continue # Skip these from the error table
                       
                   if isinstance(item_list, list):
                       for item in item_list:
                           if isinstance(item, dict):
                               desc = item.get('desc', '')
                               group = item.get('group', 'General')
                               line = item.get('line', '')
                               msg = f"[{group}{' Line ' + str(line) if str(line) and str(line) != '-' else ''}] {rule}: {desc}"
                               
                               if "Warning" in rule or "warning" in desc.lower():
                                   warnings.append(msg)
                               else:
                                   errors.append(msg)
                           else:
                               errors.append(f"{rule}: {str(item)}")
                   else:
                       errors.append(f"{rule}: {str(item_list)}")
           else:
               errors.append(str(error_report))

        # Check if valid despite issues (warnings only)
        if not errors and warnings:
             is_valid = True
             
        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "metadata": metadata
        }
        
    except Exception as e:
        return {
            "is_valid": False,
            "errors": [f"Fatal error analyzing file: {str(e)}"],
            "warnings": [],
            "metadata": {}
        }

def convert_to_excel(ags_filepath: str, excel_filepath: str):
    """Converts an AGS file to an Excel file using python-ags4."""
    tables, headings = AGS4.AGS4_to_dataframe(ags_filepath)
    # The library doesn't have a direct to_excel function, 
    # but we can write the dataframes as sheets.
    with pd.ExcelWriter(excel_filepath, engine='openpyxl') as writer:
        for group_name, df in tables.items():
            df.to_excel(writer, sheet_name=group_name, index=False)

def convert_to_ags(excel_filepath: str, ags_filepath: str):
    """Converts an Excel file back to an AGS file."""
    # Reading all sheets
    excel_data = pd.read_excel(excel_filepath, sheet_name=None, dtype=str)
    
    tables = {}
    headings = {}
    
    for group_name, df in excel_data.items():
        tables[group_name] = df
        headings[group_name] = df.columns.tolist()
        
    AGS4.dataframe_to_AGS4(tables, headings, ags_filepath)

def get_parsed_data(filepath: str) -> dict:
    """Returns the AGS file as a JSON dict: { group_name: [ {col: val, ...}, ... ] }"""
    try:
        tables, headings = AGS4.AGS4_to_dataframe(filepath)
        result = {}
        for group, df in tables.items():
            # Convert NaNs to empty strings so it serializes properly to JSON
            result[group] = df.fillna("").to_dict(orient='records')
        return result
    except Exception as e:
        return {"error": str(e)}

def save_parsed_data(data: dict, output_filepath: str):
    """Takes JSON data and saves it back to an AGS file."""
    try:
        tables = {}
        headings = {}
        for group, records in data.items():
            if records:
                df = pd.DataFrame(records)
                tables[group] = df
                headings[group] = list(df.columns)
            else:
                tables[group] = pd.DataFrame()
                headings[group] = []
        AGS4.dataframe_to_AGS4(tables, headings, output_filepath)
        return True
    except Exception as e:
        raise Exception(f"Failed to save AGS: {str(e)}")

def get_stratigraphy_data(filepath: str) -> dict:
    """Extracts LOCA and GEOL data for stratigraphic column rendering."""
    try:
        tables, headings = AGS4.AGS4_to_dataframe(filepath)
        loca_df = tables.get('LOCA', pd.DataFrame())
        geol_df = tables.get('GEOL', pd.DataFrame())
        
        holes = []
        if not loca_df.empty:
            for _, row in loca_df.iterrows():
                loca_id = row.get('LOCA_ID', '')
                try:
                    depth = float(row.get('LOCA_FDEP', 0) or 0)
                except ValueError:
                    depth = 0
                
                hole_geol = []
                if not geol_df.empty and 'LOCA_ID' in geol_df.columns:
                    hole_geol_df = geol_df[geol_df['LOCA_ID'] == loca_id]
                    for _, g_row in hole_geol_df.iterrows():
                        try:
                            # Safely cast depths
                            top = float(g_row.get('GEOL_TOP', 0) or 0)
                            base = float(g_row.get('GEOL_BASE', 0) or 0)
                        except ValueError:
                            top, base = 0, 0
                            
                        hole_geol.append({
                            'top': top,
                            'bottom': base,
                            'description': str(g_row.get('GEOL_DESC', '')),
                            'legend': str(g_row.get('GEOL_LEG', ''))
                        })
                
                holes.append({
                    'id': str(loca_id),
                    'max_depth': depth,
                    'geology': hole_geol
                })
        return {'holes': holes}
    except Exception as e:
        return {"error": str(e)}

def cleanup_task(src_path: str, dst_path: str):
    """Background task generator to delete temporary files after download."""
    from fastapi import BackgroundTasks
    tasks = BackgroundTasks()
    
    def remove_files():
        try:
            if os.path.exists(src_path):
                os.remove(src_path)
            if os.path.exists(dst_path):
                os.remove(dst_path)
        except Exception as e:
            print(f"Error cleaning up files: {e}")
            
    tasks.add_task(remove_files)
    return tasks
