import json
import datetime
import os
import time
from web3 import Web3
from Crypto.Hash import keccak


# ==================================================================
# Event Group Configuration
# ==================================================================
# Maps each device group to the supported operation list.
event_groups = {
    'Hub': [
        'Read current temperature',
        'Read current humidity',
        'Read current lightlevel'
    ],
    'Lock': [
        'Lock door',
        'Unlock door',
        'Read lock state',
        'Read door state'
    ],
    'AC controller': [
        'Turn on AC',
        'Turn off AC'
    ],
    'Light Controller': [
        'Turn on light',
        'Turn off light'
    ],
    'Circulator fan': [
        'Turn on circulator fan',
        'Turn off circulator fan'
    ],
    'Air purifier': [
        'Turn on purifier',
        'Turn off purifier'
    ],
    'Humidifier': [
        'Turn on humidifier',
        'Turn off humidifier'
    ]
}


# ==================================================================
# Web3 Connection Setup
# ==================================================================
# Connect to the local Ethereum node (e.g., Ganache).
w3 = Web3(
    Web3.HTTPProvider(
        'http://127.0.0.1:7545',
        request_kwargs={'timeout': 120}
    )
)

# Retrieve all available accounts.
accounts = w3.eth.accounts


# ==================================================================
# Contract Loading: ZKTree
# ==================================================================
artifact = 'ZK_tree_sol_ZKTree'
fn_abi = os.sep.join(['contract', '{0}.abi'.format(artifact)])
fn_bin = os.sep.join(['contract', '{0}.bin'.format(artifact)])
fn_addr = os.sep.join(['contract', '{0}.addr'.format(artifact)])

with open(fn_abi, 'r') as f:
    abi = json.load(f)

with open(fn_bin, 'r') as f:
    bytecode = f.read()

with open(fn_addr, 'r') as f:
    addr = f.read()

factory = w3.eth.contract(
    abi=abi,
    address=Web3.to_checksum_address(addr)
)


# ==================================================================
# Contract Loading: Groth16 Verifier
# ==================================================================
artifact1 = 'verifier_sol_Groth16Verifier'
fn_abi1 = os.sep.join(['contract', '{0}.abi'.format(artifact1)])
fn_bin1 = os.sep.join(['contract', '{0}.bin'.format(artifact1)])
fn_addr1 = os.sep.join(['contract', '{0}.addr'.format(artifact1)])

with open(fn_abi1, 'r') as f:
    abi1 = json.load(f)

with open(fn_bin1, 'r') as f:
    bytecode1 = f.read()

with open(fn_addr1, 'r') as f:
    addr1 = f.read()

factory1 = w3.eth.contract(
    abi=abi1,
    address=Web3.to_checksum_address(addr1)
)


# ==================================================================
# Contract Loading: Access Recorder
# ==================================================================
artifact2 = 'recorder_sol_AccessRecord'
fn_abi2 = os.sep.join(['contract', '{0}.abi'.format(artifact2)])
fn_bin2 = os.sep.join(['contract', '{0}.bin'.format(artifact2)])
fn_addr2 = os.sep.join(['contract', '{0}.addr'.format(artifact2)])

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
# Contract Read Helpers
# ==================================================================

def read_tree_lenth(factory):
    """
    Read the tree length from the ZKTree contract.

    Parameters
    ----------
    factory : Contract
        Web3 contract instance

    Returns
    -------
    Any
        Contract-returned tree length
    """
    output = factory.functions.getLength().call()
    return output


def read_tree(factory):
    """
    Read the full tree data from the ZKTree contract.

    Parameters
    ----------
    factory : Contract
        Web3 contract instance

    Returns
    -------
    Any
        Contract-returned tree data
    """
    output = factory.functions.getTree().call()
    return output


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
# Type Conversion Helpers
# ==================================================================

def type_conversion(input_data):
    """
    Convert a one-dimensional list of hexadecimal strings to integers.

    Parameters
    ----------
    input_data : list
        List of hex strings

    Returns
    -------
    list
        List of integers
    """
    output = []
    for item in input_data:
        output.append(int(item, 16))
    return output


def type_conversion1(input_data):
    """
    Convert a two-dimensional list of hexadecimal strings to integers.

    Parameters
    ----------
    input_data : list
        Nested list of hex strings

    Returns
    -------
    list
        Nested list of integers
    """
    output = []
    for sublist in input_data:
        inter = []
        for item in sublist:
            inter.append(int(item, 16))
        output.append(inter)
    return output


# ==================================================================
# Utility Functions
# ==================================================================

def get_time():
    """
    Get the current local timestamp in Unix format.

    Returns
    -------
    int
        Current Unix timestamp
    """
    dtime = datetime.datetime.now()
    now_time = int(time.mktime(dtime.timetuple()))
    return now_time


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


def get_device_info(code):
    """
    Decode an operation code into:
    - operation name
    - device group name

    Parameters
    ----------
    code : int
        1-based flattened operation index

    Returns
    -------
    tuple[str, str]
        (operation_name, device_group_name)
    """
    flat_list = []
    group_list = []

    for group, events in event_groups.items():
        for event in events:
            flat_list.append(event)
            group_list.append(group)

    return flat_list[code - 1], group_list[code - 1]


# ==================================================================
# Contract Write Helpers
# ==================================================================

def write_tree(factory):
    """
    Initialize the tree contract with a fixed example tree state.

    Notes
    -----
    This function appears to be intended for initialization or testing.

    Parameters
    ----------
    factory : Contract
        Web3 contract instance

    Returns
    -------
    int
        Gas used by the transaction
    """
    tree_data = [
        14584785055382556326210907033282734502682828261159016163821002652096312610514,
        14900862344078195670956774596062073688184319731050156699952627034133665496720,
        511423173011514445354949820059241663608825072739744632506386229195935024324,
        2
    ]  # Read current humidity

    tx_hash = factory.functions.setTree(tree_data).transact({'from': accounts[0]})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt['gasUsed']


def write_record(factory, p1, p2, p3, p4):
    """
    Write one validated access record to the recorder contract.

    Parameters
    ----------
    factory : Contract
        Web3 contract instance
    p1 : Any
        Hashed subject identity
    p2 : Any
        Device name
    p3 : Any
        Operation name
    p4 : Any
        Timestamp

    Returns
    -------
    int
        Gas used by the transaction
    """
    tx_hash = factory.functions.writeRecord(p1, p2, p3, p4).transact({'from': accounts[0]})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt['gasUsed']


def read_token(file):
    """
    Load the proving token JSON file.

    Parameters
    ----------
    file : str
        Token filename without extension

    Returns
    -------
    dict
        Parsed token content
    """
    with open("../subject/proving/{0}.json".format(file), "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


# ==================================================================
# Main Execution Entry
# ==================================================================

def main():
    """
    Validate a zero-knowledge access token and store the verified access
    action on-chain.

    Workflow
    --------
    1. Read root and operation code from the tree contract
    2. Load the off-chain token
    3. Validate root consistency
    4. Validate operation-code consistency
    5. Verify Groth16 proof
    6. Derive record fields
    7. Write the record to the access recorder
    8. Print all stored records
    """
    root = read_tree(factory)[0]
    operation_code = read_tree(factory)[-1]

    token = read_token("token")

    # --------------------------------------------------------------
    # Step 1: Root Validation
    # --------------------------------------------------------------
    if token["Root"] != root:
        raise Exception("Error: Invalid root!")
    else:
        print("Root Validation Passed!")

    # --------------------------------------------------------------
    # Step 2: Operation Code Validation
    # --------------------------------------------------------------
    if token["Operation"] != operation_code:
        raise Exception("Error: Mismatched opcode!")
    else:
        print("Operation Code Check Passed!")

    # --------------------------------------------------------------
    # Step 3: Zero-Knowledge Proof Verification
    # --------------------------------------------------------------
    is_valid_proof = factory1.functions.verifyProof(
        type_conversion(token['Zero-knowledge proof'][0]),
        type_conversion1(token['Zero-knowledge proof'][1]),
        type_conversion(token['Zero-knowledge proof'][2]),
        [token['Root']]
    ).call()

    if is_valid_proof != True:
        raise Exception("Error: Invalid Proof!")
    else:
        print("ZKP Verification Passed!")

    # --------------------------------------------------------------
    # Step 4: Derive Record Fields
    # --------------------------------------------------------------
    name = token["Name"]
    nonce = token["Nonce"]

    input_name = get_keccak(name + nonce)
    input_time = get_time()
    input_operation = get_device_info(token["Operation"])[0]
    input_device = get_device_info(token["Operation"])[1]

    # --------------------------------------------------------------
    # Step 5: Write Verified Record
    # --------------------------------------------------------------
    write_record(factory2, input_name, input_device, input_operation, input_time)

    # --------------------------------------------------------------
    # Step 6: Read Back Stored Records
    # --------------------------------------------------------------
    print(read_record(factory2))


# ------------------------------------------------------------------
# Script Entry Point
# ------------------------------------------------------------------
if __name__ == "__main__":
    main()