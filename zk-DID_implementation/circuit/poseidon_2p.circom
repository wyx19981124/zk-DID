pragma circom 2.1.6;

include "circomlib/poseidon.circom";
// include "https://github.com/0xPARC/circom-secp256k1/blob/master/circuits/bigint.circom";

template Example () {
    signal input a;
    signal input b;
    signal output c;

    component hash = Poseidon(2);
    hash.inputs[0] <== a;
    hash.inputs[1] <== b;
    c <== hash.out;
    log("hash", hash.out);
}

component main = Example();

/* INPUT = {
    "a": "5",
    "b": "77"
} */