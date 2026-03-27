from pathlib import Path

# ------------------------------------------------------------------
# Output Directory Configuration
# ------------------------------------------------------------------
# All generated Circom files will be stored in this directory.
OUT_DIR = Path("circuits")
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ==================================================================
# Plain Merkle Circuit Generator (Addition-based)
# ==================================================================

def gen_plain_circom(depth: int) -> str:
    """
    Generate a Circom circuit using plain addition as the hash function.

    Notes
    -----
    - This is NOT cryptographically secure.
    - Used for benchmarking / comparison purposes only.

    Parameters
    ----------
    depth : int
        Depth of the Merkle tree

    Returns
    -------
    str
        Generated Circom circuit as a string
    """

    # --------------------------------------------------------------
    # Edge Case: depth = 0
    # --------------------------------------------------------------
    # In this case, the leaf is the root.
    if depth == 0:
        return f"""pragma circom 2.1.6;

/**
 * Merkle inclusion proof using plain addition
 * depth = 0 means root == leaf
 */
template MerkleProofPlain(DEPTH) {{
    signal input root;
    signal input leaf;

    leaf === root;

    log("hash value", leaf);
    log("root value ", root);
}}

component main {{ public [root] }} = MerkleProofPlain({depth});
"""

    # --------------------------------------------------------------
    # General Case: depth > 0
    # --------------------------------------------------------------
    return f"""pragma circom 2.1.6;

/**
 * Merkle inclusion proof using plain addition
 *
 * Public Inputs:
 *   - root
 *
 * Private Inputs:
 *   - leaf
 *   - pathElements[DEPTH]
 *   - pathIndices[DEPTH]
 *
 * Direction Bit:
 *   b_i = 0 => current node is LEFT child
 *   b_i = 1 => current node is RIGHT child
 *
 * Parent Rule:
 *   parent = left + right
 */
template MerkleProofPlain(DEPTH) {{

    // ----------------------------
    // Public Signals
    // ----------------------------
    signal input root;

    // ----------------------------
    // Private Signals
    // ----------------------------
    signal input leaf;
    signal input pathElements[DEPTH];
    signal input pathIndices[DEPTH];

    // ----------------------------
    // Internal Signals
    // ----------------------------
    signal hash[DEPTH + 1];
    signal left[DEPTH];
    signal right[DEPTH];

    // Initialize leaf
    hash[0] <== leaf;

    // ----------------------------------------------------------
    // Iterative Merkle Path Computation
    // ----------------------------------------------------------
    for (var i = 0; i < DEPTH; i++) {{

        // Enforce boolean constraint: b_i ∈ {{0,1}}
        pathIndices[i] * (pathIndices[i] - 1) === 0;

        // Conditional selection without branching
        // Avoids control flow (Circom constraint-friendly)
        left[i]  <== hash[i] + pathIndices[i] * (pathElements[i] - hash[i]);
        right[i] <== pathElements[i] + pathIndices[i] * (hash[i] - pathElements[i]);

        // Plain "hash" (addition)
        hash[i + 1] <== left[i] + right[i];
    }}

    // Final root consistency check
    hash[DEPTH] === root;

    log("hash value", hash[DEPTH]);
    log("root value ", root);
}}

component main {{ public [root] }} = MerkleProofPlain({depth});
"""


# ==================================================================
# MiMC-Based Merkle Circuit Generator
# ==================================================================

def gen_mimc_circom(depth: int) -> str:
    """
    Generate a Circom circuit using MultiMiMC7 hash.

    Parameters
    ----------
    depth : int
        Depth of the Merkle tree

    Returns
    -------
    str
        Generated Circom circuit
    """

    if depth == 0:
        return f"""pragma circom 2.1.6;

include "circomlib/mimc.circom";

/** depth = 0 => root == leaf */
template MerkleProof(DEPTH) {{
    signal input root;
    signal input leaf;

    leaf === root;

    log("hash value", leaf);
    log("root value ", root);
}}

component main {{ public [root] }} = MerkleProof({depth});
"""

    return f"""pragma circom 2.1.6;

include "mimc.circom";

/** Merkle inclusion proof using MultiMiMC7 */
template MerkleProof(DEPTH) {{

    // Public
    signal input root;

    // Private
    signal input leaf;
    signal input pathElements[DEPTH];
    signal input pathIndices[DEPTH];

    // Internal
    signal hash[DEPTH + 1];
    signal left[DEPTH];
    signal right[DEPTH];
    component H[DEPTH];

    hash[0] <== leaf;

    for (var i = 0; i < DEPTH; i++) {{

        pathIndices[i] * (pathIndices[i] - 1) === 0;

        left[i]  <== hash[i] + pathIndices[i] * (pathElements[i] - hash[i]);
        right[i] <== pathElements[i] + pathIndices[i] * (hash[i] - pathElements[i]);

        H[i] = MultiMiMC7(2, 91);
        H[i].in[0] <== left[i];
        H[i].in[1] <== right[i];
        H[i].k <== 0;

        hash[i + 1] <== H[i].out;
    }}

    hash[DEPTH] === root;

    log("hash value", hash[DEPTH]);
    log("root value ", root);
}}

component main {{ public [root] }} = MerkleProof({depth});
"""


# ==================================================================
# Poseidon-Based Merkle Circuit Generator
# ==================================================================

def gen_poseidon_circom(depth: int) -> str:
    """
    Generate a Circom circuit using Poseidon hash.
    """

    if depth == 0:
        return f"""pragma circom 2.1.6;

include "circomlib/poseidon.circom";

/** depth = 0 => root == leaf */
template MerkleProof(DEPTH) {{
    signal input root;
    signal input leaf;

    leaf === root;

    log("hash value", leaf);
    log("root value ", root);
}}

component main {{ public [root] }} = MerkleProof({depth});
"""

    return f"""pragma circom 2.1.6;

include "poseidon.circom";

/** Merkle inclusion proof using Poseidon(2) */
template MerkleProof(DEPTH) {{

    signal input root;

    signal input leaf;
    signal input pathElements[DEPTH];
    signal input pathIndices[DEPTH];

    signal hash[DEPTH + 1];
    signal left[DEPTH];
    signal right[DEPTH];
    component H[DEPTH];

    hash[0] <== leaf;

    for (var i = 0; i < DEPTH; i++) {{

        pathIndices[i] * (pathIndices[i] - 1) === 0;

        left[i]  <== hash[i] + pathIndices[i] * (pathElements[i] - hash[i]);
        right[i] <== pathElements[i] + pathIndices[i] * (hash[i] - pathElements[i]);

        H[i] = Poseidon(2);
        H[i].inputs[0] <== left[i];
        H[i].inputs[1] <== right[i];

        hash[i + 1] <== H[i].out;
    }}

    hash[DEPTH] === root;

    log("hash value", hash[DEPTH]);
    log("root value ", root);
}}

component main {{ public [root] }} = MerkleProof({depth});
"""


# ==================================================================
# Main Execution Entry
# ==================================================================

def main():
    """
    Generate Circom files for depths 0–19.

    For each depth:
        - plain_depth_X.circom
        - mimc_depth_X.circom
        - poseidon_depth_X.circom
    """

    for depth in range(20):

        plain_file = OUT_DIR / f"plain_depth_{depth}.circom"
        mimc_file = OUT_DIR / f"mimc_depth_{depth}.circom"
        poseidon_file = OUT_DIR / f"poseidon_depth_{depth}.circom"

        # Write generated circuits
        plain_file.write_text(gen_plain_circom(depth), encoding="utf-8")
        mimc_file.write_text(gen_mimc_circom(depth), encoding="utf-8")
        poseidon_file.write_text(gen_poseidon_circom(depth), encoding="utf-8")

        print(f"[INFO] Generated circuits for depth = {depth}")

    print(f"\n[DONE] Files saved to: {OUT_DIR.resolve()}")


# ------------------------------------------------------------------
# Script Entry Point
# ------------------------------------------------------------------
if __name__ == "__main__":
    main()
