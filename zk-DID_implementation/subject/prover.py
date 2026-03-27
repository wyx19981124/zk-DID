import os
import json
import random



# ==================================================================
# Helper Functions
# ==================================================================

def generate_three_digit_str():
    """
    Generate a random 3-digit numeric string.

    Returns
    -------
    str
        Random 3-digit string, e.g. "007", "135", "928"
    """
    return f"{random.randint(0, 999):03d}"


def str_to_list(input_data):
    """
    Convert exported Solidity calldata text into a Python list.

    Notes
    -----
    This function wraps the raw calldata string with brackets and
    evaluates it as a Python list expression.

    Parameters
    ----------
    input_data : str
        Raw calldata string

    Returns
    -------
    list
        Parsed proof data list
    """
    inter = "[" + input_data + "]"
    inter_list = eval(inter)
    output_list = inter_list
    return output_list

def read_json(file):
    """
    Read a JSON file by basename.

    Parameters
    ----------
    file : str
        Filename without the .json suffix

    Returns
    -------
    dict
        Parsed JSON content
    """
    with open("{0}.json".format(file), "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def write_json(file, data):
    """
    Write data to a JSON file by basename.

    Parameters
    ----------
    file : str
        Filename without the .json suffix
    data : dict
        Data to be serialized

    Returns
    -------
    None
    """
    with open("{0}.json".format(file), "w+", encoding="utf-8") as f:
        json.dump(data, f)


# ==================================================================
# Main Execution Entry
# ==================================================================

def main():
    """
    Generate a zero-knowledge token and update the local name list.

    Workflow
    --------
    1. Read user name input
    2. Generate nonce
    3. Produce witness
    4. Generate proof
    5. Export Solidity calldata
    6. Read public root
    7. Save token.json
    8. Update namelist.json
    """
    token = {}
    namelist = {}

    # --------------------------------------------------------------
    # Step 1: Collect Basic Token Information
    # --------------------------------------------------------------
    name = input("Please input your name!")
    operation = 2  # Read current temperature
    nonce = generate_three_digit_str()

    # --------------------------------------------------------------
    # Step 2: Prepare Working Directory / Proving Path
    # --------------------------------------------------------------
    print(os.getcwd())
    os.chdir(os.getcwd())

    pos = 'proving' + os.sep

    # --------------------------------------------------------------
    # Step 3: Generate Witness
    # --------------------------------------------------------------
    witness_output = os.popen(
        r"node {0}generate_witness.js {0}merkle_proof.wasm {0}input.json {0}witness.wtns".format(pos)
    ).read()
    print(witness_output)

    # --------------------------------------------------------------
    # Step 4: Generate Groth16 Proof
    # --------------------------------------------------------------
    prove_output = os.popen(
        r"snarkjs groth16 prove {0}multiplier2_0001.zkey {0}witness.wtns {0}proof.json {0}public.json".format(pos)
    ).read()
    print(prove_output)

    # --------------------------------------------------------------
    # Step 5: Export Solidity Calldata
    # --------------------------------------------------------------
    zkp = os.popen(
        r"snarkjs zkey export soliditycalldata {0}public.json {0}proof.json".format(pos)
    ).read()

    # --------------------------------------------------------------
    # Step 6: Load Public Root
    # --------------------------------------------------------------
    with open("{0}public.json".format(pos), "r", encoding="utf-8") as f:
        root = int(json.load(f)[0])

    zkp_list = str_to_list(zkp)

    # --------------------------------------------------------------
    # Step 7: Construct Token
    # --------------------------------------------------------------
    token["Name"] = name
    token["Operation"] = operation
    token["Nonce"] = nonce
    token["Zero-knowledge proof"] = zkp_list
    token["Root"] = root

    with open("{0}token.json".format(pos), "w+", encoding="utf-8") as f:
        json.dump(token, f)

    print(token)

    # --------------------------------------------------------------
    # Step 8: Update Name List
    # --------------------------------------------------------------
    namelist = read_json("namelist")
    print(namelist)

    if name not in namelist:
        namelist[name] = []

    namelist[name].append(str(nonce))

    print(namelist)
    write_json("namelist", namelist)


# ------------------------------------------------------------------
# Script Entry Point
# ------------------------------------------------------------------
if __name__ == "__main__":
    main()