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
            tran_data = tran_df[tran_df.get('HEADING', '') == 'DATA'] if 'HEADING' in tran_df.columns else tran_df
            first_tran = tran_data.iloc[0] if not tran_data.empty else tran_df.iloc[-1]
            # extract basic info if exists
            metadata['version'] = str(first_tran.get('TRAN_AGS', 'Unknown'))
            metadata['producer'] = str(first_tran.get('TRAN_PROD', 'Unknown'))
            
        # Using basic check_file for errors
        error_report = AGS4.check_file(filepath)
        
        errors = []
        warnings = []
        is_valid = True
        
        if error_report:
           if isinstance(error_report, dict):
               for rule, item_list in error_report.items():
                   # Skip metadata and summary from the main issues list
                   if rule.lower().startswith(("summary of data", "metadata")):
                       continue
                       
                   if isinstance(item_list, list):
                       for item in item_list:
                           if isinstance(item, dict):
                               desc = item.get('desc', '')
                               group = item.get('group', 'General')
                               line = item.get('line', '')
                               
                               # Better classification based on BGS patterns
                               msg = f"[{group}{' Line ' + str(line) if str(line) and str(line) != '-' else ''}] {rule}: {desc}"
                               
                               is_fyi = "fyi" in rule.lower() or "fyi" in desc.lower() or "information" in desc.lower()
                               is_warning = "warning" in rule.lower() or "warning" in desc.lower()
                               
                               if is_fyi or is_warning:
                                   warnings.append(msg)
                               else:
                                   errors.append(msg)
                           else:
                               errors.append(f"{rule}: {str(item)}")
                   else:
                       errors.append(f"{rule}: {str(item_list)}")
           else:
               errors.append(str(error_report))

        # BGS Specific Validation Rules
        if tables:
            # 1. Required Groups (TYPE, UNIT)
            required_groups = ['TYPE', 'UNIT']
            missing_groups = [g for g in required_groups if g not in tables or tables[g].empty]
            if missing_groups:
                errors.append(f"[BGS] Required groups missing: {', '.join(missing_groups)}")

            # 2. Easting/Northing checks in LOCA
            if 'LOCA' in tables:
                loca_df = tables['LOCA']
                for idx, row in loca_df.iterrows():
                    loca_id = str(row.get('LOCA_ID', f'Row {idx+1}')).strip()
                    # Skip rows that are not data (some parsers might include headers as rows if they failed)
                    if not loca_id or loca_id.upper() in ['ID', 'TYPE', 'UNIT', 'DATA']:
                        continue
                        
                    # check NATE and NATN
                    nate = str(row.get('LOCA_NATE', '')).strip()
                    natn = str(row.get('LOCA_NATN', '')).strip()
                    
                    if not nate or nate == '0' or nate == '0.0' or not natn or natn == '0' or natn == '0.0':
                        errors.append(f"[LOCA {loca_id}] BGS: LOCA_NATE / LOCA_NATN contains zeros or null values")

                # 3. Spatial Referencing
                spatial_fields = ['LOCA_GREF', 'LOCA_LREF', 'LOCA_LLZ']
                has_spatial = False
                for field in spatial_fields:
                    if field in loca_df.columns and not loca_df[field].replace('', pd.NA).dropna().empty:
                        has_spatial = True
                        break
                if not has_spatial:
                    errors.append("[BGS] Spatial referencing system not in LOCA_GREF, LOCA_LREF or LOCA_LLZ")

        # Set final validity
        if errors:
            is_valid = False
              
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
    """Extracts project-wide metadata and borehole-specific data for visualization."""
    try:
        tables, headings = AGS4.AGS4_to_dataframe(filepath)
        
        # 1. Extract Project Metadata (PROJ & TRAN)
        project_info = {
            'name': 'Unknown Project',
            'client': 'Unknown Client',
            'contractor': 'Unknown Contractor',
            'date': '',
            'ags_version': '4.x'
        }
        
        if 'PROJ' in tables and not tables['PROJ'].empty:
            proj_df = tables['PROJ'].fillna('')
            proj_data = proj_df[proj_df.get('HEADING', '') == 'DATA'] if 'HEADING' in proj_df.columns else proj_df
            first_proj = proj_data.iloc[0] if not proj_data.empty else proj_df.iloc[-1]
            project_info['name'] = str(first_proj.get('PROJ_NAME', 'Unknown Project'))
            project_info['client'] = str(first_proj.get('PROJ_CLNT', 'Unknown Client'))
            project_info['contractor'] = str(first_proj.get('PROJ_CONT', 'Unknown Contractor'))

        if 'TRAN' in tables and not tables['TRAN'].empty:
            tran_df = tables['TRAN'].fillna('')
            tran_data = tran_df[tran_df.get('HEADING', '') == 'DATA'] if 'HEADING' in tran_df.columns else tran_df
            first_tran = tran_data.iloc[0] if not tran_data.empty else tran_df.iloc[-1]
            project_info['ags_version'] = str(first_tran.get('TRAN_AGS', '4.0'))
            project_info['date'] = str(first_tran.get('TRAN_DATE', ''))

        loca_df = tables.get('LOCA', pd.DataFrame())
        geol_df = tables.get('GEOL', pd.DataFrame())
        samp_df = tables.get('SAMP', pd.DataFrame())
        ispt_df = tables.get('ISPT', pd.DataFrame())
        wstd_df = tables.get('WSTD', pd.DataFrame())
        cdia_df = tables.get('CDIA', pd.DataFrame())
        hdia_df = tables.get('HDIA', pd.DataFrame())
        llpl_df = tables.get('LLPL', pd.DataFrame())
        lnmc_df = tables.get('LNMC', pd.DataFrame())
        weth_df = tables.get('WETH', pd.DataFrame())
        disc_df = tables.get('DISC', pd.DataFrame())
        horn_df = tables.get('HORN', pd.DataFrame())
        
        # Clean dataframes
        for df in [loca_df, geol_df, samp_df, ispt_df, wstd_df, cdia_df, hdia_df, llpl_df, lnmc_df, weth_df, disc_df, horn_df]:
            if not df.empty:
                df.fillna('', inplace=True)

        holes = []
        if not loca_df.empty:
            # Find the ID column
            id_col = 'LOCA_ID' if 'LOCA_ID' in loca_df.columns else None
            if not id_col:
                cols = [c for c in loca_df.columns if 'ID' in c.upper()]
                if cols: id_col = cols[0]

            if not id_col:
                return {'holes': []}

            for _, row in loca_df.iterrows():
                loca_id = str(row.get(id_col, '')).strip()
                if not loca_id or loca_id.upper() in ['ID', 'TYPE', 'UNIT', 'DATA', id_col.upper()]:
                    continue 
                
                try:
                    depth_val = row.get('LOCA_FDEP', 0)
                    depth = float(depth_val) if depth_val and str(depth_val).strip() else 0
                    # Extract Coordinates
                    east = row.get('LOCA_NATE', '')
                    north = row.get('LOCA_NATN', '')
                    east = float(east) if str(east).strip() else None
                    north = float(north) if str(north).strip() else None
                except (ValueError, TypeError):
                    depth, east, north = 0, None, None
                
                # Extract Geology
                hole_geol = []
                geol_id_col = id_col if id_col in geol_df.columns else 'LOCA_ID'
                if not geol_df.empty and geol_id_col in geol_df.columns:
                    hole_geol_df = geol_df[geol_df[geol_id_col].astype(str).str.strip() == loca_id]
                    for _, g_row in hole_geol_df.iterrows():
                        try:
                            top = float(g_row.get('GEOL_TOP', 0) or 0)
                            base = float(g_row.get('GEOL_BASE', 0) or 0)
                        except (ValueError, TypeError):
                            top, base = 0, 0
                        hole_geol.append({'top': top, 'bottom': base, 'description': str(g_row.get('GEOL_DESC', '')).strip(), 'legend': str(g_row.get('GEOL_LEG', '')).strip()})
                hole_geol.sort(key=lambda x: x['top'])

                # Extract Samples (SAMP)
                hole_samples = []
                samp_id_col = id_col if id_col in samp_df.columns else 'LOCA_ID'
                if not samp_df.empty and samp_id_col in samp_df.columns:
                    hole_samp_df = samp_df[samp_df[samp_id_col].astype(str).str.strip() == loca_id]
                    for _, s_row in hole_samp_df.iterrows():
                        try:
                            s_top = float(s_row.get('SAMP_TOP', 0) or 0)
                        except (ValueError, TypeError):
                            s_top = 0
                        hole_samples.append({'top': s_top, 'type': str(s_row.get('SAMP_TYPE', '')).strip(), 'ref': str(s_row.get('SAMP_REF', '')).strip(), 'id': str(s_row.get('SAMP_ID', '')).strip()})
                hole_samples.sort(key=lambda x: x['top'])

                # Extract SPT Tests (ISPT)
                hole_spts = []
                ispt_id_col = id_col if id_col in ispt_df.columns else 'LOCA_ID'
                if not ispt_df.empty and ispt_id_col in ispt_df.columns:
                    hole_ispt_df = ispt_df[ispt_df[ispt_id_col].astype(str).str.strip() == loca_id]
                    for _, i_row in hole_ispt_df.iterrows():
                        try:
                            i_top = float(i_row.get('ISPT_TOP', 0) or 0)
                            n_val = str(i_row.get('ISPT_NVAL', '')).strip()
                            try:
                                n_num = float(n_val) if n_val else None
                            except (ValueError, TypeError):
                                n_num = None
                        except (ValueError, TypeError):
                            i_top, n_val, n_num = 0, '', None
                        hole_spts.append({'top': i_top, 'n_value': n_val, 'n_numeric': n_num})
                hole_spts.sort(key=lambda x: x['top'])

                # Extract Water Strikes (WSTD)
                hole_water = []
                wstd_id_col = id_col if id_col in wstd_df.columns else 'LOCA_ID'
                if not wstd_df.empty and wstd_id_col in wstd_df.columns:
                    hole_wstd_df = wstd_df[wstd_df[wstd_id_col].astype(str).str.strip() == loca_id]
                    for _, w_row in hole_wstd_df.iterrows():
                        try:
                            w_depth = float(w_row.get('WSTD_DEP', 0) or 0)
                        except (ValueError, TypeError):
                            w_depth = 0
                        hole_water.append({
                            'depth': w_depth,
                            'time': str(w_row.get('WSTD_TIME', '')).strip(),
                            'remarks': str(w_row.get('WSTD_REM', '')).strip()
                        })
                hole_water.sort(key=lambda x: x['depth'])

                # Extract Casings (CDIA)
                hole_casings = []
                cdia_id_col = id_col if id_col in cdia_df.columns else 'LOCA_ID'
                if not cdia_df.empty and cdia_id_col in cdia_df.columns:
                    hole_cdia_df = cdia_df[cdia_df[cdia_id_col].astype(str).str.strip() == loca_id]
                    for _, c_row in hole_cdia_df.iterrows():
                        try:
                            c_depth = float(c_row.get('CDIA_DEP', 0) or 0)
                            c_dia = float(c_row.get('CDIA_DIA', 0) or 0)
                        except (ValueError, TypeError):
                            c_depth, c_dia = 0, 0
                        hole_casings.append({'depth': c_depth, 'diameter': c_dia})
                hole_casings.sort(key=lambda x: x['depth'])

                # Extract Hole Diameters (HDIA)
                hole_dias = []
                hdia_id_col = id_col if id_col in hdia_df.columns else 'LOCA_ID'
                if not hdia_df.empty and hdia_id_col in hdia_df.columns:
                    hole_hdia_df = hdia_df[hdia_df[hdia_id_col].astype(str).str.strip() == loca_id]
                    for _, h_row in hole_hdia_df.iterrows():
                        try:
                            h_depth = float(h_row.get('HDIA_DEP', 0) or 0)
                            h_dia = float(h_row.get('HDIA_DIA', 0) or 0)
                        except (ValueError, TypeError):
                            h_depth, h_dia = 0, 0
                        hole_dias.append({'depth': h_depth, 'diameter': h_dia})
                hole_dias.sort(key=lambda x: x['depth'])

                # Extract Lab Tests (LLPL & LNMC)
                hole_lab = []
                # Simple heuristic: moisture content is very common
                lnmc_id_col = id_col if id_col in lnmc_df.columns else 'LOCA_ID'
                if not lnmc_df.empty and lnmc_id_col in lnmc_df.columns:
                    hole_lnmc_df = lnmc_df[lnmc_df[lnmc_id_col].astype(str).str.strip() == loca_id]
                    for _, m_row in hole_lnmc_df.iterrows():
                        try:
                            m_depth = float(m_row.get('SAMP_TOP', 0) or 0)
                            m_val = float(m_row.get('LNMC_MC', 0) or 0)
                        except (ValueError, TypeError):
                            continue
                        hole_lab.append({'depth': m_depth, 'type': 'MC', 'value': m_val})

                llpl_id_col = id_col if id_col in llpl_df.columns else 'LOCA_ID'
                if not llpl_df.empty and llpl_id_col in llpl_df.columns:
                    hole_llpl_df = llpl_df[llpl_df[llpl_id_col].astype(str).str.strip() == loca_id]
                    for _, l_row in hole_llpl_df.iterrows():
                        try:
                            l_depth = float(l_row.get('SAMP_TOP', 0) or 0)
                            ll = float(l_row.get('LLPL_LL', 0) or 0)
                            pl = float(l_row.get('LLPL_PL', 0) or 0)
                        except (ValueError, TypeError):
                            continue
                        if ll: hole_lab.append({'depth': l_depth, 'type': 'LL', 'value': ll})
                        if pl: hole_lab.append({'depth': l_depth, 'type': 'PL', 'value': pl})
                
                hole_lab.sort(key=lambda x: x['depth'])

                # Extract Weathering (WETH)
                hole_weth = []
                weth_id_col = id_col if id_col in weth_df.columns else 'LOCA_ID'
                if not weth_df.empty and weth_id_col in weth_df.columns:
                    hole_weth_df = weth_df[weth_df[weth_id_col].astype(str).str.strip() == loca_id]
                    for _, wt_row in hole_weth_df.iterrows():
                        try:
                            wt_top = float(wt_row.get('WETH_TOP', 0) or 0)
                            wt_base = float(wt_row.get('WETH_BASE', 0) or 0)
                        except (ValueError, TypeError):
                            wt_top, wt_base = 0, 0
                        hole_weth.append({
                            'top': wt_top,
                            'bottom': wt_base,
                            'desc': str(wt_row.get('WETH_DESC', wt_row.get('WETH_WETH', ''))).strip()
                        })

                # Extract Orientation (HORN) - use first record usually
                orientation = {'inclination': 90, 'azimuth': 0}
                horn_id_col = id_col if id_col in horn_df.columns else 'LOCA_ID'
                if not horn_df.empty and horn_id_col in horn_df.columns:
                    hole_horn_df = horn_df[horn_df[horn_id_col].astype(str).str.strip() == loca_id]
                    if not hole_horn_df.empty:
                        try:
                            h_row = hole_horn_df.iloc[0]
                            orientation['inclination'] = float(h_row.get('HORN_INC', 90) or 90)
                            orientation['azimuth'] = float(h_row.get('HORN_AZI', 0) or 0)
                        except (ValueError, TypeError):
                            pass

                holes.append({
                    'id': loca_id,
                    'max_depth': depth or (hole_geol[-1]['bottom'] if hole_geol else 0),
                    'east': east,
                    'north': north,
                    'orientation': orientation,
                    'geology': hole_geol,
                    'samples': hole_samples,
                    'spts': hole_spts,
                    'water': hole_water,
                    'casings': hole_casings,
                    'diameters': hole_dias,
                    'lab': hole_lab,
                    'weathering': hole_weth
                })
        
        holes.sort(key=lambda x: x['id'])
        return {
            'project': project_info,
            'summary': {
                'total_holes': len(holes),
                'total_depth': sum(h['max_depth'] for h in holes)
            },
            'holes': holes
        }
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
