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
        
        # Clean dataframes
        if not loca_df.empty:
            loca_df = loca_df.fillna('')
        if not geol_df.empty:
            geol_df = geol_df.fillna('')

        holes = []
        if not loca_df.empty:
            # Find the ID column - could be LOCA_ID or HOLE_ID depending on version
            id_col = 'LOCA_ID' if 'LOCA_ID' in loca_df.columns else None
            
            if not id_col:
                # Fallback to looking for any column containing ID
                cols = [c for c in loca_df.columns if 'ID' in c.upper()]
                if cols: id_col = cols[0]

            if not id_col:
                return {'holes': []}

            for _, row in loca_df.iterrows():
                loca_id = str(row.get(id_col, '')).strip()
                # Skip rows with no ID or rows that look like AGS meta (headers/units)
                if not loca_id or loca_id.upper() in ['ID', 'TYPE', 'UNIT', 'DATA', id_col.upper()]:
                    continue 
                
                try:
                    depth_val = row.get('LOCA_FDEP', 0)
                    depth = float(depth_val) if depth_val and str(depth_val).strip() else 0
                except (ValueError, TypeError):
                    depth = 0
                
                hole_geol = []
                # Find ID column in GEOL
                geol_id_col = id_col if id_col in geol_df.columns else 'LOCA_ID'
                
                if not geol_df.empty and geol_id_col in geol_df.columns:
                    # Filter geol rows for this hole
                    hole_geol_df = geol_df[geol_df[geol_id_col].astype(str).str.strip() == loca_id]
                    
                    for _, g_row in hole_geol_df.iterrows():
                        try:
                            # Safely cast depths
                            top_val = g_row.get('GEOL_TOP', 0)
                            base_val = g_row.get('GEOL_BASE', 0)
                            top = float(top_val) if top_val and str(top_val).strip() else 0
                            base = float(base_val) if base_val and str(base_val).strip() else 0
                        except (ValueError, TypeError):
                            top, base = 0, 0
                        
                        # Only add if it has some meat (base > top or has desc)
                        desc = str(g_row.get('GEOL_DESC', '')).strip()
                        legend = str(g_row.get('GEOL_LEG', '')).strip()
                        
                        if base > top or desc or legend:
                            hole_geol.append({
                                'top': top,
                                'bottom': base,
                                'description': desc,
                                'legend': legend
                            })
                
                # Sort geology by depth
                hole_geol.sort(key=lambda x: x['top'])
                
                holes.append({
                    'id': loca_id,
                    'max_depth': depth or (hole_geol[-1]['bottom'] if hole_geol else 0),
                    'geology': hole_geol
                })
        
        # Finally, sort holes by ID
        holes.sort(key=lambda x: x['id'])
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
