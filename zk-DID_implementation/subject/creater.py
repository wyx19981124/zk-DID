import json


# ==================================================================
# JSON Generation Function
# ==================================================================

def generate_json(filename: str = "namelist.json"):
    """
    Generate a JSON file mapping names to identifier lists.

    Parameters
    ----------
    filename : str, optional
        Output JSON filename

    Returns
    -------
    None
    """

    # --------------------------------------------------------------
    # Step 1: Construct Data
    # --------------------------------------------------------------
    # Dictionary structure:
    #   key   -> user name
    #   value -> list of associated IDs (strings)
    data = {
        "Alice": ["001", "003"],
        "Bob": ["005"]
    }

    # --------------------------------------------------------------
    # Step 2: Write JSON File
    # --------------------------------------------------------------
    # Use UTF-8 encoding to ensure compatibility.
    with open(filename, "w+", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # --------------------------------------------------------------
    # Step 3: Confirmation Output
    # --------------------------------------------------------------
    print(f"[DONE] JSON file created: {filename}")


# ==================================================================
# Script Entry Point
# ==================================================================

if __name__ == "__main__":
    generate_json()
