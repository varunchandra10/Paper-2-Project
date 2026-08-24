import os
import json

def check_notebook(filepath):
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            nb = json.load(f)
        
        errors = []
        for cell_idx, cell in enumerate(nb.get("cells", [])):
            for out in cell.get("outputs", []):
                if out.get("output_type") == "error":
                    errors.append({
                        "cell_idx": cell_idx,
                        "ename": out.get("ename"),
                        "evalue": out.get("evalue"),
                        "traceback": out.get("traceback")
                    })
        return errors
    except Exception as e:
        print(f"Failed to read {filepath}: {e}")
        return None

def main():
    notebooks = [
        "c:/Users/kvcsu_ht23nk8/OneDrive/Desktop/all_Projects/Projects/agentic_projects/Paper-2-Project/backend/tests/phase1_to_5_test.ipynb",
        "c:/Users/kvcsu_ht23nk8/OneDrive/Desktop/all_Projects/Projects/agentic_projects/Paper-2-Project/backend/tests/test.ipynb"
    ]
    
    found_any = False
    for nb_path in notebooks:
        errs = check_notebook(nb_path)
        if errs:
            found_any = True
            print(f"\n[ERROR] FOUND {len(errs)} ERRORS IN {os.path.basename(nb_path)}:")
            for err in errs:
                print(f"  * Cell {err['cell_idx']}: {err['ename']} - {err['evalue']}")
                # Print first 5 lines of traceback
                tb = err["traceback"]
                if tb:
                    print("    Traceback:")
                    for line in tb[:8]:
                        # Strip ansi escape sequences from traceback line
                        clean_line = line.replace("\u001b", "").replace("[0;31m", "").replace("[0m", "")
                        print(f"      {clean_line.strip()}")
        else:
            if errs is not None:
                print(f"[OK] No errors found in {os.path.basename(nb_path)}")
                
    if found_any:
        # Exit with error code to signify errors present
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    import sys
    main()
