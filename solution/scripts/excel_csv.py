import argparse
import os
import re
import pandas as pd

def safe_name(s):
    return re.sub(r'[^0-9A-Za-z._-]+', '_', s).strip('_')

def convert_file(xlsx_path, out_dir):
    try:
        sheets = pd.read_excel(xlsx_path, sheet_name=None, engine=None)
    except Exception as e:
        print(f"SKIP {xlsx_path}: read error: {e}")
        return 0

    base = os.path.splitext(os.path.basename(xlsx_path))[0]
    written = 0
    for sheet_name, df in sheets.items():
        if len(sheets) == 1:
            out_name = f"{safe_name(base)}.csv"
        else:
            out_name = f"{safe_name(base)}__{safe_name(str(sheet_name))}.csv"
        out_path = os.path.join(out_dir, out_name)
        try:
            df.to_csv(out_path, index=False)
            written += 1
            print(f"WROTE {out_path}")
        except Exception as e:
            print(f"ERROR writing {out_path}: {e}")
    return written

def main():
    p = argparse.ArgumentParser(description="Convert all .xlsx/.xls/.xsls files in a folder to CSVs (one CSV per sheet).")
    p.add_argument("src", nargs="?", default=".", help="Source folder to scan (default: current dir)")
    p.add_argument("--out", "-o", default="./csv_output", help="Output folder (default: ./csv_output)")
    p.add_argument("--exts", default="xlsx,xls,xsls", help="Comma-separated extensions to match (default: xlsx,xls,xsls)")
    args = p.parse_args()

    exts = {f".{e.lower().lstrip('.')}" for e in args.exts.split(",")}
    os.makedirs(args.out, exist_ok=True)

    total_files = 0
    total_written = 0
    for root, _, files in os.walk(args.src):
        for fn in files:
            if os.path.splitext(fn)[1].lower() in exts:
                total_files += 1
                path = os.path.join(root, fn)
                total_written += convert_file(path, args.out)

    print(f"Done. Files scanned: {total_files}, CSVs written: {total_written}")

if __name__ == "__main__":
    main()