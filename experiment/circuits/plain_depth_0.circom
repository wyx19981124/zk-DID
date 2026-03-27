pragma circom 2.1.6;

/**
 * Merkle inclusion proof using plain addition
 * depth = 0 means root == leaf
 */
template MerkleProofPlain(DEPTH) {
    signal input root;
    signal input leaf;

    leaf === root;

    log("hash value", leaf);
    log("root value ", root);
}

component main { public [root] } = MerkleProofPlain(0);
