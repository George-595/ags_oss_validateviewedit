# Changelog

All notable changes to this project will be documented in this file.

## [1.14.0] - 2026-02-22

### Added

- **BGS-Specific Validation Rules**: Added mandatory checks for BGS/NGDC data submissions:
  - Required Groups (`TYPE`, `UNIT`) must be present.
  - Eastings/Northings (`LOCA_NATE`, `LOCA_NATN`) must not be zero or null.
  - Spatial Referencing must be provided in `LOCA_GREF`, `LOCA_LREF`, or `LOCA_LLZ`.

### Changed

- **Improved Alignment with Official BGS Validator**: Updated `validate_file` to correctly categorize messages from the `python-ags4` engine.
  - "FYI" and "Warning" messages are now correctly shown as warnings instead of errors, aligning the total error count with official results.
  - Improved error message formatting with group name and line number context.
