pragma circom 2.1.6;

include "circomlib/mimc.circom";

/**
 * Merkle inclusion proof using MultiMiMC7([left, right])
 * depth = 0 means root == leaf
 */
template MerkleProof(DEPTH) {
    signal input root;
    signal input leaf;

    leaf === root;

    log("hash value", leaf);
    log("root value ", root);
}

component main { public [root] } = MerkleProof(0);
