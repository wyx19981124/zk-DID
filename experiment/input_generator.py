import re
import json
import random
from pathlib import Path
from typing import List
from circomlibpy.poseidon import PoseidonHash


# ------------------------------------------------------------------
# BN254 Scalar Field Configuration
# ------------------------------------------------------------------
# All arithmetic is reduced modulo the BN254 scalar field.
P = 21888242871839275222246405745257275088548364400416034343698204186575808495617

# Global Poseidon hash instance.
poseidon = PoseidonHash()


# ==================================================================
# Common Helper Functions
# ==================================================================

def generate_secret_list(n: int) -> List[str]:
    """
    Generate n random 5-digit datablock strings.

    Notes
    -----
    - Leading zeros are preserved.
    - Example valid values: "00000", "04217", "98351".

    Parameters
    ----------
    n : int
        Number of datablocks to generate

    Returns
    -------
    List[str]
        List of 5-digit string datablocks
    """
    return [f"{random.randint(0, 99999):05d}" for _ in range(n)]



def leaf_nodes(level: int) -> int:
    """
    Compute the number of leaf nodes in a full binary tree.

    Parameters
    ----------
    level : int
        Tree level, where level = 1 means the tree has exactly 1 leaf

    Returns
    -------
    int
        Number of leaves in the full binary tree
    """
    return 2 ** (level - 1)



def get_merkle_proof(layers: List[List[int]], leaf_index: int):
    """
    Extract the Merkle proof for one leaf from all tree layers.

    Convention
    ----------
    pathIndices[i] = 0  -> current hash is on the LEFT
    pathIndices[i] = 1  -> current hash is on the RIGHT

    Parameters
    ----------
    layers : List[List[int]]
        All layers of the Merkle tree from leaves to root
    leaf_index : int
        Index of the target leaf in the leaf layer

    Returns
    -------
    tuple
        (root, leaf, path_elements, path_indices)
    """

    # Proof arrays collected from bottom to top.
    path_elements = []
    path_indices = []

    # Start from the target leaf and move upward layer by layer.
    idx = leaf_index

    for layer in layers[:-1]:
        if idx % 2 == 0:
            # Current node is on the left; sibling is on the right.
            sibling_idx = idx + 1
            path_indices.append(0)
        else:
            # Current node is on the right; sibling is on the left.
            sibling_idx = idx - 1
            path_indices.append(1)

        path_elements.append(layer[sibling_idx])
        idx //= 2

    root = layers[-1][0]
    leaf = layers[0][leaf_index]

    return root, leaf, path_elements, path_indices


# ==================================================================
# Plain Merkle Tree Construction
# ==================================================================

def merkle_tree_layers_plain(leaves: List[int]) -> List[List[int]]:
    """
    Build a Merkle tree using plain addition as the parent rule.

    Parent Rule
    -----------
    parent = (left + right) mod P

    Notes
    -----
    This construction is intended for benchmarking or structural testing.
    It is not cryptographically secure.

    Parameters
    ----------
    leaves : List[int]
        Leaf values

    Returns
    -------
    List[List[int]]
        All Merkle tree layers from leaves to root
    """

    layers = []
    layer = [x % P for x in leaves]
    layers.append(layer)

    while len(layer) > 1:
        layer = [
            (layer[i] + layer[i + 1]) % P
            for i in range(0, len(layer), 2)
        ]
        layers.append(layer)

    return layers


# ==================================================================
# MiMC Helper Functions
# ==================================================================

def load_mimc_constants_from_circom(mimc_circom_path: str) -> List[int]:
    """
    Load MiMC round constants from a Circom source file.

    The function searches for a declaration of the form:
        var c[91] = [...];

    Parameters
    ----------
    mimc_circom_path : str
        Path to mimc.circom

    Returns
    -------
    List[int]
        List of 91 MiMC round constants

    Raises
    ------
    ValueError
        If the constants array cannot be found or has the wrong size
    """

    text = Path(mimc_circom_path).read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"var\s+c\[\s*91\s*\]\s*=\s*\[(.*?)\]\s*;", text, flags=re.S)

    if not match:
        raise ValueError("Cannot find 'var c[91] = [...]' in mimc.circom")

    body = match.group(1)
    nums = re.findall(r"\d+", body)
    constants = [int(x) for x in nums]

    if len(constants) != 91:
        raise ValueError(f"Expected 91 constants, got {len(constants)}")

    return constants



def mimc7(
    x_in: int,
    k: int,
    c: List[int],
    nrounds: int = 91,
    p: int = P
) -> int:
    """
    Compute the MiMC7 permutation.

    Parameters
    ----------
    x_in : int
        Input value
    k : int
        Key / round seed
    c : List[int]
        Round constants
    nrounds : int, optional
        Number of rounds
    p : int, optional
        Field modulus

    Returns
    -------
    int
        MiMC7 output in the field
    """

    x_in %= p
    k %= p

    t7_prev = 0

    for i in range(nrounds):
        if i == 0:
            t = (k + x_in) % p
        else:
            t = (k + t7_prev + c[i]) % p

        # Compute t^7 efficiently by repeated squaring / multiplication.
        t2 = (t * t) % p
        t4 = (t2 * t2) % p
        t6 = (t4 * t2) % p
        t7 = (t6 * t) % p

        if i < nrounds - 1:
            t7_prev = t7
        else:
            return (t7 + k) % p

    raise RuntimeError("Unreachable")



def multi_mimc7(
    inputs: List[int],
    k: int,
    c: List[int],
    nrounds: int = 91,
    p: int = P
) -> int:
    """
    Compute MultiMiMC7 over a list of inputs.

    This matches the iterative sponge-like update pattern commonly used
    in Circom-based MiMC constructions.

    Parameters
    ----------
    inputs : List[int]
        Input sequence
    k : int
        Initial key / state
    c : List[int]
        Round constants
    nrounds : int, optional
        Number of rounds
    p : int, optional
        Field modulus

    Returns
    -------
    int
        Final MultiMiMC7 digest
    """

    r = k % p

    for x in inputs:
        x %= p
        out_i = mimc7(x, r, c, nrounds=nrounds, p=p)
        r = (r + x + out_i) % p

    return r



def merkle_tree_layers_mimc(leaves: List[int], constants: List[int]) -> List[List[int]]:
    """
    Build a Merkle tree using MultiMiMC7([left, right]).

    Parameters
    ----------
    leaves : List[int]
        Leaf values
    constants : List[int]
        MiMC round constants

    Returns
    -------
    List[List[int]]
        All Merkle tree layers from leaves to root
    """

    layers = []
    layer = [x % P for x in leaves]
    layers.append(layer)

    while len(layer) > 1:
        layer = [
            multi_mimc7([layer[i], layer[i + 1]], 0, constants)
            for i in range(0, len(layer), 2)
        ]
        layers.append(layer)

    return layers


# ==================================================================
# Poseidon Merkle Tree Construction
# ==================================================================

def merkle_tree_layers_poseidon(leaves: List[int]) -> List[List[int]]:
    """
    Build a Merkle tree using Poseidon(2) as the parent hash.

    Parameters
    ----------
    leaves : List[int]
        Leaf values

    Returns
    -------
    List[List[int]]
        All Merkle tree layers from leaves to root
    """

    layers = []
    layer = [x % P for x in leaves]
    layers.append(layer)

    while len(layer) > 1:
        layer = [
            poseidon.hash(2, [layer[i], layer[i + 1]])
            for i in range(0, len(layer), 2)
        ]
        layers.append(layer)

    return layers


# ==================================================================
# JSON Output Helper
# ==================================================================

def save_input_json(
    out_path: Path,
    root: int,
    leaf: int,
    path_elements: List[int],
    path_indices: List[int]
) -> None:
    """
    Save one Merkle proof input as a JSON file.

    Notes
    -----
    - Field elements are serialized as strings.
    - pathIndices are kept as integers because they are boolean flags.

    Parameters
    ----------
    out_path : Path
        Output JSON path
    root : int
        Merkle root
    leaf : int
        Target leaf
    path_elements : List[int]
        Sibling nodes along the authentication path
    path_indices : List[int]
        Direction bits for the proof path
    """

    data = {
        "root": str(root),
        "leaf": str(leaf),
        "pathElements": [str(x) for x in path_elements],
        "pathIndices": path_indices,
    }

    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ==================================================================
# Plain Input Generation
# ==================================================================

def generate_plain_inputs(out_dir: Path) -> None:
    """
    Generate JSON inputs for plain-addition Merkle circuits.

    Parameters
    ----------
    out_dir : Path
        Root output directory
    """

    plain_dir = out_dir / "plain"
    plain_dir.mkdir(parents=True, exist_ok=True)

    for level in range(1, 21):
        n = leaf_nodes(level)
        datablocks = generate_secret_list(n)

        # Plain circuits do not hash raw datablocks into leaves.
        # The datablock integer itself is directly mapped into the field.
        leaves = [int(x) % P for x in datablocks]

        layers = merkle_tree_layers_plain(leaves)

        leaf_index = random.randint(0, n - 1)
        root, leaf, path_elements, path_indices = get_merkle_proof(layers, leaf_index)

        out_file = plain_dir / f"input_level_{level}.json"
        save_input_json(out_file, root, leaf, path_elements, path_indices)

        print(f"[plain]    level={level:2d}, leaves={n:6d}, chosen_leaf_index={leaf_index}")


# ==================================================================
# MiMC Input Generation
# ==================================================================

def generate_mimc_inputs(out_dir: Path, mimc_circom_path: str) -> None:
    """
    Generate JSON inputs for MiMC-based Merkle circuits.

    Parameters
    ----------
    out_dir : Path
        Root output directory
    mimc_circom_path : str
        Path to mimc.circom for extracting round constants
    """

    mimc_dir = out_dir / "mimc"
    mimc_dir.mkdir(parents=True, exist_ok=True)

    constants = load_mimc_constants_from_circom(mimc_circom_path)

    for level in range(1, 21):
        n = leaf_nodes(level)
        datablocks = generate_secret_list(n)

        # Raw datablock -> MiMC leaf hash.
        leaves = [mimc7(int(x), 0, constants) for x in datablocks]

        layers = merkle_tree_layers_mimc(leaves, constants)

        leaf_index = random.randint(0, n - 1)
        root, leaf, path_elements, path_indices = get_merkle_proof(layers, leaf_index)

        out_file = mimc_dir / f"input_level_{level}.json"
        save_input_json(out_file, root, leaf, path_elements, path_indices)

        print(f"[mimc]     level={level:2d}, leaves={n:6d}, chosen_leaf_index={leaf_index}")


# ==================================================================
# Poseidon Input Generation
# ==================================================================

def generate_poseidon_inputs(out_dir: Path) -> None:
    """
    Generate JSON inputs for Poseidon-based Merkle circuits.

    Parameters
    ----------
    out_dir : Path
        Root output directory
    """

    poseidon_dir = out_dir / "poseidon"
    poseidon_dir.mkdir(parents=True, exist_ok=True)

    for level in range(1, 21):
        n = leaf_nodes(level)
        datablocks = generate_secret_list(n)

        # Raw datablock -> Poseidon leaf hash.
        leaves = [poseidon.hash(1, [int(x)]) for x in datablocks]

        layers = merkle_tree_layers_poseidon(leaves)

        leaf_index = random.randint(0, n - 1)
        root, leaf, path_elements, path_indices = get_merkle_proof(layers, leaf_index)

        out_file = poseidon_dir / f"input_level_{level}.json"
        save_input_json(out_file, root, leaf, path_elements, path_indices)

        print(f"[poseidon] level={level:2d}, leaves={n:6d}, chosen_leaf_index={leaf_index}")


# ==================================================================
# Main Execution Entry
# ==================================================================

def main() -> None:
    """
    Main entry for generating all Merkle proof input JSON files.

    Output Structure
    ----------------
    merkle_inputs/
        plain/
        mimc/
        poseidon/
    """

    # Use a fixed seed such as random.seed(42) for reproducible experiments.
    random.seed()

    output_dir = Path("merkle_inputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Update this path according to the local environment if needed.
    mimc_circom_path = "mimc.circom"

    generate_plain_inputs(output_dir)
    generate_mimc_inputs(output_dir, mimc_circom_path)
    generate_poseidon_inputs(output_dir)

    print("\nAll input files generated under:", output_dir.resolve())


# ------------------------------------------------------------------
# Script Entry Point
# ------------------------------------------------------------------
if __name__ == "__main__":
    main()
