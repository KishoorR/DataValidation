import csv
import re
from pathlib import Path
import pandas as pd
import gradio as gr

# ========= Core Logic (same as earlier, slightly refactored) ========= #

def normalize_csv_component(name: str) -> str:
    """
    Normalize component name from CSV.
    Example: 'BODY-LWR-FRT-STRUCTURE' -> 'body_lwr_frt_structure'
    """
    return name.strip().lower().replace('-', '_')


def normalize_text_component(name_raw: str) -> str:
    """
    Normalize component name from text file line.
    Example:
      'M_BODY_LWR_FRT_STRUCTURE_EVEK_SCC_LHD_V0.k'
        -> 'body_lwr_frt_structure_evek_scc_lhd_v0'
    """
    s = name_raw.strip().lower()
    if s.startswith('m_'):
        s = s[2:]

    # cut at first space or dot – we just want the main token
    cut_pos = len(s)
    for ch in [' ', '.']:
        idx = s.find(ch)
        if idx != -1 and idx < cut_pos:
            cut_pos = idx
    s = s[:cut_pos]

    s = s.replace('-', '_')
    return s


def parse_module_ranges(text_path: Path):
    """
    Parse the text file to extract module ranges starting from '$ Module ID Range'.
    Returns a list of dicts: [{'norm_name': ..., 'start': int, 'end': int, 'raw': ...}, ...]
    """
    entries = []
    in_section = False

    # Regex: $ <start> <end> <rest_of_line>
    line_re = re.compile(r'^\$\s+(\d+)\s+(\d+)\s+(.*)$')

    with text_path.open('r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            stripped = line.strip()

            if not in_section:
                # Look for the section header
                if stripped.startswith('$ Module ID Range'):
                    in_section = True
                continue

            # Once in section, only consider lines matching our pattern
            m = line_re.match(stripped)
            if not m:
                # Ignore non-matching lines in the section
                continue

            start_str, end_str, rest = m.groups()
            try:
                start = int(start_str)
                end = int(end_str)
            except ValueError:
                continue

            norm_name = normalize_text_component(rest)
            entries.append(
                {
                    'norm_name': norm_name,
                    'start': start,
                    'end': end,
                    'raw': rest,
                }
            )

    return entries


def validate_csv_against_modules(csv_in: Path, module_entries):
    """
    For each row in the CSV, check if its (Start, End) range is fully
    contained within any text-file range for the same component.
    Returns: list of rows (dicts) + fieldnames.
    """
    rows = []
    with csv_in.open('r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if fieldnames is None:
            raise ValueError("CSV appears to have no header.")

        # Ensure 'Result' column exists
        if 'Result' not in fieldnames:
            fieldnames.append('Result')

        for row in reader:
            rows.append(row)

    for row in rows:
        comp_name = row.get('Items') or row.get('Component') or ''
        start_str = (row.get('Start') or '').strip()
        end_str = (row.get('End') or '').strip()

        try:
            csv_start = int(start_str)
            csv_end = int(end_str)
        except ValueError:
            # Invalid numbers -> treat as out of range
            row['Result'] = 'Out of Range'
            continue

        csv_norm = normalize_csv_component(comp_name)

        # Find all module entries whose normalized name matches this component
        matching_entries = [
            e for e in module_entries
            if csv_norm in e['norm_name']
        ]

        if not matching_entries:
            # No matching component in text file
            row['Result'] = 'Out of Range'
            continue

        # Check if this CSV range is fully contained in any of the matching ranges
        in_range = any(
            (e['start'] <= csv_start <= csv_end <= e['end'])
            for e in matching_entries
        )

        row['Result'] = 'In Range' if in_range else 'Out of Range'

    return rows, fieldnames


# ========= Gradio UI Wrapper ========= #

def validate_ui(text_file, csv_file):
    """
    Gradio callback:
    - text_file, csv_file are temp files from Gradio upload
    - returns a DataFrame preview + a downloadable CSV file
    """
    if text_file is None or csv_file is None:
        return pd.DataFrame(), None

    text_path = Path(text_file.name)
    csv_path = Path(csv_file.name)

    # Parse text ranges
    module_entries = parse_module_ranges(text_path)
    if not module_entries:
        # Return empty + no file if parsing fails
        return pd.DataFrame(), None

    # Validate CSV
    rows, fieldnames = validate_csv_against_modules(csv_path, module_entries)

    # Build DataFrame for preview
    df = pd.DataFrame(rows, columns=fieldnames)

    # Write updated CSV to a temp file for download
    out_path = csv_path.with_name(csv_path.stem + "_validated.csv")
    with out_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return df, str(out_path)


with gr.Blocks() as demo:
    gr.Markdown("## Module ID Range Validator (Gradio UI)")

    with gr.Row():
        text_input = gr.File(label="Text file (.txt) with `$ Module ID Range` section")
        csv_input = gr.File(label="CSV file (.csv) with Items/Start/End/Result")

    validate_btn = gr.Button("Validate Ranges")

    gr.Markdown("### Validation Result Preview")
    df_output = gr.DataFrame(label="Validated CSV Preview", interactive=False)

    gr.Markdown("### Download Updated CSV")
    file_output = gr.File(label="Download validated CSV")

    validate_btn.click(
        fn=validate_ui,
        inputs=[text_input, csv_input],
        outputs=[df_output, file_output],
    )

demo.launch()
