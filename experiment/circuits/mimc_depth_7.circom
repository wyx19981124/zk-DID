pragma circom 2.1.6;

include "mimc.circom";

/**
 * Merkle inclusion proof using MultiMiMC7([left, right])
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

        // If pathIndices[i] = 0:
        //   left  = hash[i],         right = pathElements[i]
        // If pathIndices[i] = 1:
        //   left  = pathElements[i], right = hash[i]
        left[i]  <== hash[i] + pathIndices[i] * (pathElements[i] - hash[i]);
        right[i] <== pathElements[i] + pathIndices[i] * (hash[i] - pathElements[i]);

        // MultiMiMC7 with 2 inputs
        H[i] = MultiMiMC7(2, 91);
        H[i].in[0] <== left[i];
        H[i].in[1] <== right[i];
        H[i].k <== 0;

        hash[i + 1] <== H[i].out;
    }

    // Final check
    hash[DEPTH] === root;
    log("hash value", hash[DEPTH]);
    log("root value ", root);
}

component main { public [root] } = MerkleProof(7);
