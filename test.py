import csv
import re
import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

# ========= Core Logic (same idea as previous script) ========= #

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
    Returns: (rows, fieldnames) for writing out.
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

        result = 'Out of Range'  # default

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


# ========= Tkinter GUI ========= #

class ModuleValidatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Module ID Range Validator")

        # Paths
        self.text_path_var = tk.StringVar()
        self.csv_path_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Select files and click Validate")

        # Text file row
        tk.Label(root, text="Text file (.txt):").grid(row=0, column=0, padx=8, pady=8, sticky="e")
        tk.Entry(root, textvariable=self.text_path_var, width=60).grid(row=0, column=1, padx=8, pady=8)
        tk.Button(root, text="Browse", command=self.browse_text).grid(row=0, column=2, padx=8, pady=8)

        # CSV file row
        tk.Label(root, text="CSV file (.csv):").grid(row=1, column=0, padx=8, pady=8, sticky="e")
        tk.Entry(root, textvariable=self.csv_path_var, width=60).grid(row=1, column=1, padx=8, pady=8)
        tk.Button(root, text="Browse", command=self.browse_csv).grid(row=1, column=2, padx=8, pady=8)

        # Validate button
        tk.Button(root, text="Validate Ranges", command=self.run_validation, width=20).grid(
            row=2, column=1, padx=8, pady=12
        )

        # Status label
        tk.Label(root, textvariable=self.status_var, fg="blue").grid(
            row=3, column=0, columnspan=3, padx=8, pady=8
        )

    def browse_text(self):
        path = filedialog.askopenfilename(
            title="Select Text File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if path:
            self.text_path_var.set(path)

    def browse_csv(self):
        path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if path:
            self.csv_path_var.set(path)

    def run_validation(self):
        text_path = self.text_path_var.get().strip()
        csv_path = self.csv_path_var.get().strip()

        if not text_path or not csv_path:
            messagebox.showerror("Error", "Please select both the text file and the CSV file.")
            return

        text_file = Path(text_path)
        csv_file = Path(csv_path)

        if not text_file.is_file():
            messagebox.showerror("Error", f"Text file not found:\n{text_file}")
            return
        if not csv_file.is_file():
            messagebox.showerror("Error", f"CSV file not found:\n{csv_file}")
            return

        try:
            self.status_var.set("Parsing text file...")
            self.root.update_idletasks()
            module_entries = parse_module_ranges(text_file)
            if not module_entries:
                messagebox.showerror(
                    "Error",
                    "No module ranges found in the text file after '$ Module ID Range'."
                )
                self.status_var.set("Failed: No module ranges found.")
                return

            self.status_var.set("Validating CSV ranges...")
            self.root.update_idletasks()
            rows, fieldnames = validate_csv_against_modules(csv_file, module_entries)

            # Output CSV path
            out_path = csv_file.with_name(csv_file.stem + "_validated.csv")

            with out_path.open('w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            self.status_var.set(f"Done. Output: {out_path.name}")
            messagebox.showinfo(
                "Success",
                f"Validation complete.\n\nOutput written to:\n{out_path}"
            )
        except Exception as e:
            self.status_var.set("Error during validation.")
            messagebox.showerror("Error", f"An error occurred:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ModuleValidatorApp(root)
    root.mainloop()
