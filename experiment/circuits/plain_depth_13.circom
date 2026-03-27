pragma circom 2.1.6;

/**
 * Merkle inclusion proof using plain addition
 * Public:  root
 * Private: leaf, pathElements[DEPTH], pathIndices[DEPTH]
 * b_i = 0 => current is left ;  b_i = 1 => current is right
 *
 * Parent rule:
 *   parent = left + right
 */
template MerkleProofPlain(DEPTH) {
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

    // Initialize
    hash[0] <== leaf;

    for (var i = 0; i < DEPTH; i++) {
        // pathIndices[i] must be boolean
        pathIndices[i] * (pathIndices[i] - 1) === 0;

        // b_i = 0 => current hash is left, sibling is right
        // b_i = 1 => sibling is left, current hash is right
        left[i]  <== hash[i] + pathIndices[i] * (pathElements[i] - hash[i]);
        right[i] <== pathElements[i] + pathIndices[i] * (hash[i] - pathElements[i]);

        // Plain parent computation: parent = left + right
        hash[i + 1] <== left[i] + right[i];
    }

    // Final check
    hash[DEPTH] === root;

    log("hash value", hash[DEPTH]);
    log("root value ", root);
}

component main { public [root] } = MerkleProofPlain(13);
