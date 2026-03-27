import json
import datetime
import os
import time
from pathlib import Path
from web3 import Web3


# ==================================================================
# Web3 Connection Setup
# ==================================================================

# Connect to the local Ethereum node.
w3 = Web3(
    Web3.HTTPProvider(
        "http://127.0.0.1:7545",
        request_kwargs={"timeout": 120}
    )
)

# Retrieve all available accounts.
accounts = w3.eth.accounts

# Use the first account as the default deployer.
DEPLOYER = accounts[0]

print("[INFO] Connected to local Ethereum node")
print("[INFO] Deployer account:", DEPLOYER)
print("[INFO] Available accounts:", accounts)


# ==================================================================
# Contract Configuration
# ==================================================================

# Directory containing compiled contract artifacts.
CONTRACT_DIR = Path("contract")

# Contracts to deploy in sequence.
CONTRACT_ARTIFACTS = [
    "ZK_tree_sol_ZKTree",
    "recorder_sol_AccessRecord",
    "verifier_sol_Groth16Verifier",
]


# ==================================================================
# Helper Functions
# ==================================================================

def build_artifact_paths(artifact: str):
    """
    Build ABI, BIN, and ADDR file paths for one contract artifact.

    Parameters
    ----------
    artifact : str
        Contract artifact name without file extension

    Returns
    -------
    tuple[Path, Path, Path]
        Paths for ABI, BIN, and ADDR files
    """
    abi_path = CONTRACT_DIR / f"{artifact}.abi"
    bin_path = CONTRACT_DIR / f"{artifact}.bin"
    addr_path = CONTRACT_DIR / f"{artifact}.addr"
    return abi_path, bin_path, addr_path



def load_contract_artifacts(artifact: str):
    """
    Load ABI and bytecode for one contract.

    Parameters
    ----------
    artifact : str
        Contract artifact name

    Returns
    -------
    tuple[list, str, Path]
        ABI, bytecode, and output address path
    """
    abi_path, bin_path, addr_path = build_artifact_paths(artifact)

    if not abi_path.exists():
        raise FileNotFoundError(f"Missing ABI file: {abi_path}")
    if not bin_path.exists():
        raise FileNotFoundError(f"Missing BIN file: {bin_path}")

    with open(abi_path, "r", encoding="utf-8") as f:
        abi = json.load(f)

    with open(bin_path, "r", encoding="utf-8") as f:
        bytecode = f.read().strip()

    return abi, bytecode, addr_path



def deploy_contract(artifact: str, from_account: str):
    """
    Deploy one contract and save its deployed address.

    Parameters
    ----------
    artifact : str
        Contract artifact name
    from_account : str
        Ethereum account used for deployment

    Returns
    -------
    dict
        Deployment result summary
    """
    print("\n" + "=" * 70)
    print(f"[STEP] Deploying contract: {artifact}")

    abi, bytecode, addr_path = load_contract_artifacts(artifact)

    print(f"[INFO] ABI loaded for: {artifact}")
    print(f"[INFO] Bytecode length: {len(bytecode)}")

    # Create contract factory.
    factory = w3.eth.contract(abi=abi, bytecode=bytecode)

    # Send deployment transaction.
    start_time = time.perf_counter()
    tx_hash = factory.constructor().transact({"from": from_account})
    print("[INFO] Deployment transaction hash:", tx_hash.hex())

    # Wait until the transaction is mined.
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    end_time = time.perf_counter()

    print("[INFO] Contract deployed successfully")
    print("[INFO] Contract address:", receipt.contractAddress)
    print(f"[INFO] Deployment time: {end_time - start_time:.6f}s")

    # Save the deployed address for later use.
    with open(addr_path, "w", encoding="utf-8") as f:
        f.write(receipt.contractAddress)

    print(f"[DONE] Address saved to: {addr_path}")

    return {
        "artifact": artifact,
        "contract_address": receipt.contractAddress,
        "transaction_hash": tx_hash.hex(),
        "block_number": receipt.blockNumber,
        "gas_used": receipt.gasUsed,
        "deployment_time": end_time - start_time,
        "address_file": str(addr_path),
    }


# ==================================================================
# Main Execution Entry
# ==================================================================

def main():
    """
    Deploy all configured contracts in sequence.
    """
    deployment_results = []

    print("\n[INFO] Starting multi-contract deployment...")
    print("[INFO] Deployment timestamp:", datetime.datetime.now())

    for artifact in CONTRACT_ARTIFACTS:
        result = deploy_contract(artifact, DEPLOYER)
        deployment_results.append(result)

    print("\n" + "=" * 70)
    print("[SUMMARY] All contracts deployed")

    for result in deployment_results:
        print(f"- {result['artifact']}: {result['contract_address']}")


# ------------------------------------------------------------------
# Script Entry Point
# ------------------------------------------------------------------
if __name__ == "__main__":
    main()
