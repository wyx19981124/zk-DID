import json
import datetime
import os
import time
from web3 import Web3
from Crypto.Hash import keccak


# ==================================================================
# Contract Configuration: AccessRecord
# ==================================================================

artifact2 = 'recorder_sol_AccessRecord'
fn_abi2 = "../owner/contract/{0}.abi".format(artifact2)
fn_bin2 = "../owner/contract/{0}.bin".format(artifact2)
fn_addr2 = "../owner/contract/{0}.addr".format(artifact2)


# ==================================================================
# Web3 Connection Setup
# ==================================================================

# Connect to the local Ethereum node.
w3 = Web3(
    Web3.HTTPProvider(
        'http://127.0.0.1:7545',
        request_kwargs={'timeout': 120}
    )
)

# Retrieve all available accounts.
accounts = w3.eth.accounts


# ==================================================================
# Load AccessRecord Contract
# ==================================================================

with open(fn_abi2, 'r') as f:
    abi2 = json.load(f)

with open(fn_bin2, 'r') as f:
    bytecode2 = f.read()

with open(fn_addr2, 'r') as f:
    addr2 = f.read()

factory2 = w3.eth.contract(
    abi=abi2,
    address=Web3.to_checksum_address(addr2)
)


# ==================================================================
# Contract Read Helper
# ==================================================================

def read_record(factory):
    """
    Read all access records from the recorder contract.

    Parameters
    ----------
    factory : Contract
        Web3 contract instance

    Returns
    -------
    Any
        All stored access records
    """
    output = factory.functions.getAllRecords().call()
    return output


# ==================================================================
# Local JSON Output Helper
# ==================================================================

def write_record_json(input_data):
    """
    Convert the on-chain record tuples into JSON-serializable lists and
    save them to record.json.

    Parameters
    ----------
    input_data : iterable
        On-chain record collection

    Returns
    -------
    list
        List-form record data
    """
    pos = 'proving' + os.sep
    result = []

    for item in input_data:
        temp = list(item)
        result.append(temp)

    with open("record.json", "w+", encoding="utf-8") as f:
        json.dump(result, f)

    return result


# ==================================================================
# Hash Helper
# ==================================================================

def get_keccak(data):
    """
    Compute the Keccak-256 hash of the input string.

    Parameters
    ----------
    data : str
        Input string

    Returns
    -------
    str
        Hexadecimal Keccak-256 digest prefixed with '0x'
    """
    real_data = data.encode()
    k = keccak.new(digest_bits=256)
    k.update(real_data)
    result = k.hexdigest()
    output = "0x" + result
    return output


# ==================================================================
# Name List Processing
# ==================================================================

def read_namelist(file):
    """
    Read namelist.json and generate both raw name+code strings and
    their corresponding Keccak hashes.

    Parameters
    ----------
    file : str
        Filename without the .json suffix

    Returns
    -------
    tuple[list, list]
        (name_list, hash_list)
    """
    with open("{0}.json".format(file), "r", encoding="utf-8") as f:
        data = json.load(f)

    name_list = []
    hash_list = []

    for name, codes in data.items():
        for code in codes:
            name_list.append(name + code)

    for item in name_list:
        hashed_value = get_keccak(item)
        hash_list.append(hashed_value)

    return name_list, hash_list


# ==================================================================
# Record Matching
# ==================================================================

def record_match(hash_list, record_list):
    """
    Match hashed identities against the first field of each on-chain record.

    Parameters
    ----------
    hash_list : list
        List of locally generated Keccak hashes
    record_list : list
        List of on-chain records

    Returns
    -------
    list
        Matching index pairs in the form [name_index, record_index]
    """
    matching_list = []

    for i, hashed_value in enumerate(hash_list):
        for num, record in enumerate(record_list):
            if hashed_value == record[0]:
                matching_list.append([i, num])

    return matching_list


def record_claim(matching_list, name_list):
    """
    Convert matching index pairs into human-readable claim results.

    Parameters
    ----------
    matching_list : list
        Matching index pairs
    name_list : list
        List of name+code identifiers

    Returns
    -------
    list
        Claim results in the form:
        [identifier, "No.X record in RC"]
    """
    claim_list = []

    for item in matching_list:
        claim_list.append([
            name_list[item[0]],
            "No.{0} record in RC".format(item[1])
        ])

    return claim_list


# ==================================================================
# Main Execution Entry
# ==================================================================

def main():
    """
    Read on-chain records, match them with local hashed identities, and
    output the final claim results.
    """
    # --------------------------------------------------------------
    # Step 1: Read On-Chain Records
    # --------------------------------------------------------------
    temp_record = read_record(factory2)

    # --------------------------------------------------------------
    # Step 2: Save Records as Local JSON
    # --------------------------------------------------------------
    record = write_record_json(temp_record)

    # --------------------------------------------------------------
    # Step 3: Load Name List and Generate Hashes
    # --------------------------------------------------------------
    name_list, hash_list = read_namelist("namelist")

    print(hash_list)
    print(record)
    print("")

    # --------------------------------------------------------------
    # Step 4: Match Hashed Identities with Records
    # --------------------------------------------------------------
    matching_list = record_match(hash_list, record)

    print("")

    # --------------------------------------------------------------
    # Step 5: Generate Claim Results
    # --------------------------------------------------------------
    print(record_claim(matching_list, name_list))


# ------------------------------------------------------------------
# Script Entry Point
# ------------------------------------------------------------------
if __name__ == "__main__":
    main()