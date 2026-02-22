def check_file(filepath_or_buffer, standard_AGS4_dictionary=None, rename_duplicate_headers=True, encoding='utf-8'):
    """Validate AGS4 file against AGS4 rules.

    Parameters
    ----------
    filepath_or_buffer : strFile path (str, pathlib.Path), or StringIO.
        Path to AGS4 file or any object with a read() method (such as an open
        file or StringIO) to be checked.
    standard_AGS4_dict : str
        Path to .ags file with standard AGS4 dictionary or version number
        (should be one of '4.1.1', '4.1', '4.0.4', '4.0.3', '4.0').
    rename_duplicate_headers: bool, default=True
        Rename duplicate headers if found. Neither AGS4 tables nor Pandas
        dataframes allow duplicate headers, therefore a number will be appended
        to duplicates to make them unique.
    encoding : str, default='utf-8'
        Encoding of text file.

    Returns
    -------
    dict
        Dictionary contains AGS4 error in input file.
    """

    import hashlib
    from python_ags4 import check

    ags_errors = {}

    # Line checks
    if _is_file_like(filepath_or_buffer):
        f = filepath_or_buffer
        f.seek(0)
        if hasattr(f, 'encoding') and getattr(f, 'encoding', None) != encoding and hasattr(f, 'reconfigure'):
            f.reconfigure(encoding=encoding)
        close_file = False
    else:
        f = open(filepath_or_buffer, "r", newline='', encoding=encoding, errors="replace")
        close_file = True

    try:
        # Preflight check for AGS3 files and to calculate SHA256 hash of file
        sha256_hash = hashlib.sha256()

        for i, line in enumerate(f, start=1):
            ags_errors = check.is_ags3_like(line, i, ags_errors=ags_errors)

            # Exit if ags3_like line is found
            if ('AGS Format Rule 3' in ags_errors) and ('AGS3' in ags_errors['AGS Format Rule 3'][0]['desc']):
                ags_errors = check.add_error_msg(ags_errors, 'Validator Process Error', '-', '',
                                                 'Validation terminated due to suspected AGS3 file. Please fix errors and try again.')
                return ags_errors

            # Perform SHA256 checksum calculation
            sha256_hash.update(line.encode(encoding))

        # Reset file stream to the beginning to start AGS4 checks
        f.seek(0)

        # Initiate group name and headings list
        group = ''
        headings = []

        logger.info('Checking lines...')

        for i, line in enumerate(f, start=1):

            # Track headings to be used with group checks
            if line.strip('"').startswith("GROUP"):
                # Reset group name and headings list at the beginning each group
                group = ''
                headings = []

                try:
                    group = line.rstrip().strip('"').split('","')[1]

                except IndexError:
                    # GROUP name not available (Rule 19 should catch this error)
                    pass

            elif line.strip('"').startswith("HEADING"):
                headings = line.rstrip().split('","')
                headings = [item.strip('"') for item in headings]

            # Call line Checks
            ags_errors = check.rule_1(line, i, ags_errors=ags_errors, encoding=encoding)
            ags_errors = check.rule_2a(line, i, ags_errors=ags_errors)
            ags_errors = check.rule_3(line, i, ags_errors=ags_errors)
            ags_errors = check.rule_4_1(line, i, ags_errors=ags_errors)
            ags_errors = check.rule_4_2(line, i, group=group, headings=headings, ags_errors=ags_errors)
            ags_errors = check.rule_5(line, i, ags_errors=ags_errors)
            ags_errors = check.rule_6(line, i, ags_errors=ags_errors)
            ags_errors = check.rule_7_1(line, i, ags_errors=ags_errors)
            ags_errors = check.rule_19(line, i, ags_errors=ags_errors)
            ags_errors = check.rule_19a(line, i, group=group, ags_errors=ags_errors)
            ags_errors = check.rule_19b_1(line, i, group=group, ags_errors=ags_errors)

        # Add additional information about how Rule 1 is implemented if infringements are detected
        if 'AGS Format Rule 1' in ags_errors:
            msg = "AGS4 Rule 1 is interpreted as allowing both standard ASCII characters (Unicode code points 0-127) "\
                  "and extended ASCII characters (Unicode code points 160-255). "\
                  "Please beware that extended ASCII characters differ based on the encoding used when the file was created. "\
                  "The validator defaults to 'utf-8' encoding as it is the most widely used encoding compatible with Unicode. "\
                  "The user can override this default if the file encoding is different but, "\
                  "it is highly recommended that the 'utf-8' encoding be used when creating AGS4 files. "\
                  "(Hint: If not 'utf-8', then the encoding is most likely to be 'windows-1252' aka 'cp1252')"
            ags_errors = check.add_error_msg(ags_errors, 'General', '', '', msg)

        # Import data into Pandas dataframes to run group checks
        logger.info('Loading tables...')

        f.seek(0)
        tables, headings, line_numbers = AGS4_to_dataframe(f, get_line_numbers=True, rename_duplicate_headers=rename_duplicate_headers)

        # Group Checks
        logger.info('Checking headings and groups...')

        ags_errors = check.rule_2(tables, headings, line_numbers, ags_errors=ags_errors)
        ags_errors = check.rule_2b(tables, headings, line_numbers, ags_errors=ags_errors)
        ags_errors = check.rule_8(tables, headings, line_numbers, ags_errors=ags_errors)
        ags_errors = check.rule_12(tables, headings, ags_errors=ags_errors)
        ags_errors = check.rule_13(tables, headings, line_numbers, ags_errors=ags_errors)
        ags_errors = check.rule_14(tables, headings, line_numbers, ags_errors=ags_errors)
        ags_errors = check.rule_15(tables, headings, line_numbers, ags_errors=ags_errors)

        # Not able to locate any other files in same folder for an already opened file/stream:
        if close_file:
            ags_errors = check.rule_20(tables, headings, filepath_or_buffer, ags_errors=ags_errors)

        ags_errors = check.is_TRAN_AGS_valid(tables, headings, line_numbers, ags_errors=ags_errors)

        # Dictionary Based Checks

        # Pick path to standard dictionary
        if standard_AGS4_dictionary in [None, '4.1.1', '4.1', '4.0.4', '4.0.3', '4.0']:
            # Filepath to the standard dictionary will be picked based on version
            # number if a valid version number is provided. If it is not specified
            # at all, then the filepath will be selected based on the value of
            # TRAN_AGS in the TRAN table.
            standard_AGS4_dictionary = check.pick_standard_dictionary(tables=tables, dict_version=standard_AGS4_dictionary)

        # Import standard dictionary file into Pandas dataframes
        tables_std_dict, _ = AGS4_to_dataframe(standard_AGS4_dictionary)

        # Combine standard dictionary with DICT table in input file to create an extended dictionary
        # This extended dictionary is used to check the file schema
        dictionary = check.combine_DICT_tables(tables_std_dict, tables)

        logger.info('Checking file schema...')

        ags_errors = check.rule_7_2(headings, dictionary, line_numbers, ags_errors=ags_errors)
        ags_errors = check.rule_9(headings, dictionary, line_numbers, ags_errors=ags_errors)
        ags_errors = check.rule_10a(tables, headings, dictionary, line_numbers, ags_errors=ags_errors)
        ags_errors = check.rule_10b(tables, headings, dictionary, line_numbers, ags_errors=ags_errors)
        ags_errors = check.rule_10c(tables, headings, dictionary, line_numbers, ags_errors=ags_errors)
        ags_errors = check.rule_11(tables, headings, dictionary, ags_errors=ags_errors)
        ags_errors = check.rule_16(tables, headings, dictionary, ags_errors=ags_errors)
        ags_errors = check.rule_17(tables, headings, dictionary, ags_errors=ags_errors)
        # Note: rule_18() has to be called after rule_9() as it relies on rule_9() to flag non-standard headings.
        ags_errors = check.rule_18(tables, headings, ags_errors=ags_errors)
        ags_errors = check.rule_19b_2(tables, headings, dictionary, line_numbers, ags_errors=ags_errors)
        ags_errors = check.rule_19b_3(tables, headings, dictionary, line_numbers, ags_errors=ags_errors)

        # Warnings
        # TO BE ADDED

        # FYI
        ags_errors = check.fyi_16_1(tables, headings, tables_std_dict['ABBR'], ags_errors=ags_errors)

        # Add summary of data
        for val in check.get_data_summary(tables):
            ags_errors = check.add_error_msg(ags_errors, 'Summary of data', '', '', val)

    except AGS4Error as err:
        logger.exception(err)

        ags_errors = check.add_error_msg(ags_errors, 'General', '-', '',
                                         'Could not complete validation. Please fix listed errors and try again.')
        ags_errors = check.add_error_msg(ags_errors, 'Validator Process Error', '-', '', str(err))

    except UnboundLocalError as err:
        logger.exception(err)

        # The presence of a byte-order-mark (BOM) in the same row as first
        # "GROUP" line can cause this exception. This will be caught by line
        # checks for Rule 1 (since the BOM is not an ASCII character) and Rule 3
        # (since the BOM precedes the string "GROUP"). The BOM encoding can be
        # ignored by setting the 'encoding' argument to 'utf-8-sig'.
        f.seek(0)

        tables, headings, line_numbers = AGS4_to_dataframe(f, encoding='utf-8-sig',
                                                           get_line_numbers=True, rename_duplicate_headers=rename_duplicate_headers)

        # Add warning to error log
        msg = 'This file seems to be encoded with a byte-order-mark (BOM). It is highly recommended that the '\
              'file be saved without BOM encoding to avoid issues with other software.'
        ags_errors = check.add_error_msg(ags_errors, 'General', '', '', msg)

    except Exception as err:
        logger.exception(err)

        ags_errors = check.add_error_msg(ags_errors, 'General', '-', '',
                                         'Could not complete validation. Please fix listed errors and try again.')
        ags_errors = check.add_error_msg(ags_errors, 'Validator Process Error', '-', '', str(err))

    finally:
        if close_file:
            f.close()

        # Add metadata
        ags_errors = check.add_meta_data(filepath_or_buffer, standard_AGS4_dictionary, ags_errors=ags_errors,
                                         encoding=encoding)

        if ('AGS Format Rule 3' in ags_errors) and ('AGS3' in ags_errors['AGS Format Rule 3'][0]['desc']):
            # If AGS3 file is detected, the for loop in which the SHA256 hash is
            # calculated will be terminated, therefore report it as "Not calculated"
            ags_errors = check.add_error_msg(ags_errors, 'Metadata', 'SHA256 hash', '', 'Not calculated')

        else:
            ags_errors = check.add_error_msg(ags_errors, 'Metadata', 'SHA256 hash', '', sha256_hash.hexdigest())

        return ags_errors

