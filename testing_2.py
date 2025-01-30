import re
from typing import Dict, List

def extract_tables_and_fields(method_body: str) -> Dict[str, List[str]]:
    """
    Extracts table names and the fields being fetched from SAP ABAP SELECT queries.
    Handles multiple tables, JOIN clauses (LEFT, RIGHT, FULL, INNER, CROSS, OUTER),
    multi-line queries, and basic alias referencing (e.g. a~matnr).

    Returns:
        A dictionary of { TABLE_NAME: [FIELD1, FIELD2, ...] } in uppercase.
        If a field is ambiguous or references no alias, it will go under a special
        key "__UNMAPPED_FIELDS__".
    """

    # 1) Regex to capture each SELECT statement up to a typical stopping keyword:
    #    INTO, WHERE, ORDER, GROUP, HAVING, ENDSELECT, or the end-of-string.
    select_query_pattern = re.compile(
        r"(?i)\bSELECT\b.*?\bFROM\b.*?(?=\bINTO\b|\bWHERE\b|\bORDER\b|\bGROUP\b|\bHAVING\b|\bENDSELECT\b|$)",
        re.IGNORECASE | re.DOTALL
    )

    # 2) Within each SELECT block, we want to:
    #    - Extract the portion between SELECT and FROM => fields_str
    #    - Extract FROM ... plus any JOIN ... references => from_join_str
    #    We'll later parse them separately.
    split_pattern = re.compile(
        r"(?i)\bSELECT\b\s+(.*?)\s+\bFROM\b\s+(.*)",  # group(1): fields, group(2): from/join block
        re.IGNORECASE | re.DOTALL
    )

    # 3) Regex to identify each table in the FROM / JOIN clause:
    #    - Matches FROM table [AS alias], or
    #      (LEFT|RIGHT|FULL|INNER|CROSS) [OUTER] JOIN table [AS alias]
    #    Captures: (table_name, alias_if_any)
    table_alias_pattern = re.compile(
        r"(?i)\b(?:FROM|(?:(?:LEFT|RIGHT|FULL|INNER|CROSS)\s*(?:OUTER\s*)?)?JOIN)\s+([A-Za-z0-9_]+)"
        r"(?:\s+AS\s+([A-Za-z0-9_]+))?",
        re.IGNORECASE
    )

    # 4) Regex to find field references in the SELECT list (the part after SELECT and before FROM).
    #    We capture something that might look like a~field or just field.
    #    This also handles potential commas, newlines, etc.
    field_pattern = re.compile(
        r"\b([A-Za-z0-9_]+)~([A-Za-z0-9_]+)\b"  # e.g. a~matnr
    )
    #    If we have fields with no alias (e.g., "matnr"), they won't match this pattern.
    #    We'll handle those separately below.

    # Return structure: { TABLE_NAME: set_of_fields }
    # Using sets first to avoid duplicates; we'll convert to a list at the end.
    table_to_fields = {}
    unmapped_fields = set()  # Fields without a clear alias

    # 1) Find all SELECT blocks
    select_blocks = select_query_pattern.findall(method_body)

    for block in select_blocks:
        # 2) Split out the "SELECT ... " portion (fields_str) from "FROM ..." portion (from_join_str)
        match_split = split_pattern.search(block)
        if not match_split:
            continue

        fields_str = match_split.group(1)  # text after SELECT up to FROM
        from_join_str = match_split.group(2)  # text after FROM

        # Trim
        fields_str = fields_str.strip()
        from_join_str = from_join_str.strip()

        # 3) Parse all tables and optional aliases from the FROM/JOIN part
        #    e.g., FROM mara AS a
        #          INNER JOIN makt AS b
        # We'll store them in a dict alias->tablename for easy lookup
        alias_to_table = {}

        for tbl_match in table_alias_pattern.findall(from_join_str):
            raw_table = tbl_match[0]  # e.g. "mara"
            raw_alias = tbl_match[1]  # e.g. "a" or ""

            table_upper = raw_table.upper()
            # If no alias is provided, the "alias" can be the same as table, or we leave it blank
            alias_upper = raw_alias.upper() if raw_alias else table_upper

            # Initialize the set in the result dict if not present
            if table_upper not in table_to_fields:
                table_to_fields[table_upper] = set()

            alias_to_table[alias_upper] = table_upper

        # 4) Extract field references in the SELECT list that have an alias, e.g. a~matnr
        for fmatch in field_pattern.finditer(fields_str):
            alias_found = fmatch.group(1).upper()  # e.g. "A"
            field_found = fmatch.group(2).upper()  # e.g. "MATNR"
            if alias_found in alias_to_table:
                table_name = alias_to_table[alias_found]
                table_to_fields[table_name].add(field_found)
            else:
                # If the alias doesn't match a known table, we put it in an unmapped or keep track
                unmapped_fields.add(field_found)

        # 5) Also capture fields that do not follow the alias~field pattern:
        #    e.g., "matnr, ernam" with no alias. We'll guess they belong to a single table if there's only one,
        #    or we put them in a special set if multiple tables exist.
        # A simple approach: split by comma, remove anything that matched alias~field, and parse what's left.
        # We'll do a naive approach:
        #    1) Remove everything that looks like "alias~field"
        #    2) Split by comma
        #    3) Clean up possible keywords (like DISTINCT, SINGLE) or parentheses
        fields_str_clean = re.sub(r"[A-Za-z0-9_]+~[A-Za-z0-9_]+", "", fields_str)
        # remove double spaces
        fields_str_clean = re.sub(r"\s+", " ", fields_str_clean).strip(", ").strip()

        # Now split by comma
        raw_field_candidates = [f.strip() for f in fields_str_clean.split(",") if f.strip()]

        # We can also remove typical ABAP keywords like "DISTINCT", "SINGLE", "*"
        IGNORE_KEYWORDS = {"DISTINCT", "SINGLE", "*"}

        # Filter
        final_field_candidates = []
        for fc in raw_field_candidates:
            # remove leftover parentheses or "@" or host variable notation
            fc_clean = re.sub(r"[@()\s]+", "", fc, flags=re.IGNORECASE).upper()
            if fc_clean and fc_clean not in IGNORE_KEYWORDS:
                final_field_candidates.append(fc_clean)

        # If there's only one table in alias_to_table, we can safely map these fields to that table
        if len(alias_to_table) == 1 and final_field_candidates:
            # Single entry in alias_to_table
            sole_table = list(alias_to_table.values())[0]
            for fc in final_field_candidates:
                table_to_fields[sole_table].add(fc)
        # If there's no table found or multiple tables, we cannot be certain
        # which table the fields belong to; put them in "unmapped".
        else:
            for fc in final_field_candidates:
                unmapped_fields.add(fc)

    # 6) Convert sets to sorted lists
    final_result = {}
    for tbl, fldset in table_to_fields.items():
        final_result[tbl] = sorted(fldset)

    # If you want to keep track of fields that can't be mapped to a specific table, store them under a special key
    if unmapped_fields:
        final_result["__UNMAPPED_FIELDS__"] = sorted(unmapped_fields)

    return final_result


# -------------- EXAMPLE USAGE --------------
if __name__ == "__main__":
    sample_abap_code = r"""
        SELECT a~atinn,  a~atnam,
                c~clint,  c~imerk,
                d~class,  d~klart AS class_type,
                b~field1, b~field2,
        * Begin of changes by VGORRELA - ITC defect - DE422115
        * Get field5 to populate step tier table type S
        *         b~field3, b~field4
                b~field3, b~field4, b~field5
        * End of changes by VGORRELA - ITC defect - DE422115
            FROM cabn AS a
            INNER JOIN zdt_sd_rule AS b
            ON a~atnam = b~field2
            INNER JOIN ksml AS c
            ON a~atinn = c~imerk AND
            c~klart = @lc_300
            INNER JOIN klah AS d      #EC CI_BUFFJOIN
            ON d~clint EQ c~clint AND
            d~klart EQ @lc_300
        WHERE prog = @lc_ruletb
        INTO TABLE @DATA(lt_characterstics).
    """

    result = extract_tables_and_fields(sample_abap_code)
    print("Extracted tables and fields:")
    for table_name, fields in result.items():
        print(f"TABLE: {table_name}")
        print(f"  FIELDS: {fields}")

