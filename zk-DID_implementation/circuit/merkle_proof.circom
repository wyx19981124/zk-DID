pragma circom 2.1.6;

include "circomlib/poseidon.circom";

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

    // Predeclare signals (cannot declare inside loops)
    signal hash[DEPTH + 1];
    signal left[DEPTH];
    signal right[DEPTH];
    component H[DEPTH];

    // Initialize
    hash[0] <== leaf;

    for (var i = 0; i < DEPTH; i++) {
        // Boolean constraint for direction bit
        pathIndices[i] * (pathIndices[i] - 1) === 0;

        // ---- Fixed version: only one multiplication per line ----
        left[i]  <== hash[i] + pathIndices[i] * (pathElements[i] - hash[i]);
        right[i] <== pathElements[i] + pathIndices[i] * (hash[i] - pathElements[i]);

        // Poseidon(2)
        H[i] = Poseidon(2);
        H[i].inputs[0] <== left[i];
        H[i].inputs[1] <== right[i];

        hash[i + 1] <== H[i].out;
    }

    // Final check: computed root must match public root
    hash[DEPTH] === root;
    log("hash value", hash[DEPTH]);
    log("root value ", root);
}

component main { public [ root ] } = MerkleProof(2);

/*INPUT = {
  "root": "14584785055382556326210907033282734502682828261159016163821002652096312610514",
  "leaf": "4267533774488295900887461483015112262021273608761099826938271132511348470966",
  "pathElements": [
    "17969335243827093337266579217235383262796757007750104556615141505252572255932",
    "511423173011514445354949820059241663608825072739744632506386229195935024324"
  ],
  "pathIndices": [0, 0]
} */