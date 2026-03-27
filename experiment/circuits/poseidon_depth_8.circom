pragma circom 2.1.6;

include "poseidon.circom";

/**
 * Merkle inclusion proof using Poseidon(2)
 * Public:  root
 * Private: leaf, pathElements[DEPTH], pathIndices[DEPTH]
 * b_i = 0 => current is left ;  b_i = 1 => current is right
 */
template MerkleProof(DEPTH) {
    // Public
    signal input root;

    // Private
    signal input leaf;
    signal input pathElements[DEPTH];
    signal input pathIndices[DEPTH];

    // Predeclare signals
    signal hash[DEPTH + 1];
    signal left[DEPTH];
    signal right[DEPTH];
    component H[DEPTH];

    // Initialize
    hash[0] <== leaf;

    for (var i = 0; i < DEPTH; i++) {
        // Boolean constraint for direction bit
        pathIndices[i] * (pathIndices[i] - 1) === 0;

        left[i]  <== hash[i] + pathIndices[i] * (pathElements[i] - hash[i]);
        right[i] <== pathElements[i] + pathIndices[i] * (hash[i] - pathElements[i]);

        // Poseidon(2)
        H[i] = Poseidon(2);
        H[i].inputs[0] <== left[i];
        H[i].inputs[1] <== right[i];

        hash[i + 1] <== H[i].out;
    }

    // Final check
    hash[DEPTH] === root;
    log("hash value", hash[DEPTH]);
    log("root value ", root);
}

component main { public [root] } = MerkleProof(8);
