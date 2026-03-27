pragma circom 2.1.6;

include "circomlib/poseidon.circom";
// include "https://github.com/0xPARC/circom-secp256k1/blob/master/circuits/bigint.circom";

template Example () {
    signal input a;
    signal output c;

    component hash = Poseidon(1);
    hash.inputs[0] <== a;
    c <== hash.out;

    log("hash", hash.out);
}

component main = Example();

/* INPUT = {
    "a": "5"
} */