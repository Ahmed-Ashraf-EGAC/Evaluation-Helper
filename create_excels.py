import math
import os

import pandas as pd


def get_txt_filenames(folder_path):
    """Get all .txt filenames (without extension) in the given folder."""
    return [
        os.path.splitext(f)[0] for f in os.listdir(folder_path) if f.endswith(".pdf")
    ]


def split_list(lst, n):
    """Split list lst into n nearly equal parts."""
    k, m = divmod(len(lst), n)
    return [lst[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)] for i in range(n)]


def create_excel_from_filenames(filenames, columns, case_id_col, output_path):
    """Create an Excel file with given filenames as Case ID."""
    data = []
    for name in filenames:
        row = ["" for _ in columns]
        if case_id_col in columns:
            idx = columns.index(case_id_col)
            row[idx] = name
        data.append(row)
    df = pd.DataFrame(data, columns=columns)
    df.to_excel(output_path, index=False)


if __name__ == "__main__":
    # --- User parameters ---
    txt_folder = r"itr-3\human-verdicts"  # Change to your folder path
    template_excel = "QA-merged.xlsx"
    case_id_col = "Case ID"  # Change if your column is named differently

    # --- Load template columns ---
    df_old = pd.read_excel(template_excel)
    df_old_columns = df_old.columns.tolist()

    # --- Get filenames ---
    filenames = get_txt_filenames(txt_folder)
    if not filenames:
        print("No .txt files found in the folder.")
        exit(1)

    # --- Split filenames into n parts ---
    split_filenames = split_list(filenames, 3)

    # --- Create Excel files ---
    for i, part in enumerate(split_filenames, 1):
        output_file = f"output_part_{i}.xlsx"
        create_excel_from_filenames(part, df_old_columns, case_id_col, output_file)
        print(f"Created {output_file} with {len(part)} rows.")
