# zk-DID
A novel IoT identity management system leveraging zero-knowledge membership proofs to enable dynamic identifiers.

## Overview

This repository contains the implementation and experimental evaluation
of the zk-DID scheme proposed in our work. It is organized into two main
parts:

-   **zk-DID implementation**
-   **Experiment reproduction**

The repository is designed to both demonstrate the core functionality of
zk-DID and allow users to reproduce the experimental results reported in
the paper.

------------------------------------------------------------------------

## Repository Structure

The repository contains two main folders:

-   `zk-DID_implementation/`
-   `experiment/`

------------------------------------------------------------------------

## zk-DID Implementation

The `zk-DID_implementation/` folder provides the core implementation of
the zk-DID framework. It includes:

-   **`circuit/`**\
    Contains the zero-knowledge proof (ZKP) circuits used in zk-DID.

-   **`owner/`**\
    Implements operations performed by the **resource owner**, such as
    identity generation and credential-related processes.

-   **`subject/`**\
    Implements operations performed by the **user (subject)**, including
    authentication and proof generation.

------------------------------------------------------------------------

## Experiment

The `experiment/` folder is designed to reproduce the experimental
results presented in our paper.

### Circuit Compiler

    experiment/circuit_compiler.py

This script generates ZKP circuits under different configurations:

-   Merkle tree depth: **1 to 20**
-   Hash functions:
    -   MiMC
    -   Poseidon
    -   Plain addition

Generated circuits are saved in:

    experiment/circuits/

------------------------------------------------------------------------

### Input Generator

    experiment/input_generator.py

This script simulates inputs required for the generated circuits:

-   Supports Merkle tree depths from **1 to 20**
-   Supports multiple hash algorithms:
    -   MiMC
    -   Poseidon
    -   Plain addition

Generated inputs are stored in:

    experiment/merkle_inputs/

------------------------------------------------------------------------

### Benchmark Tester

    experiment/time_tester.py

This script executes benchmarking experiments and evaluates:

-   Execution time at each stage
-   Space (memory/storage) performance

Benchmark results are saved in:

    experiment/execution_result/

------------------------------------------------------------------------

## Installation

Install dependencies using:

``` bash
pip install -r requirements.txt
```

------------------------------------------------------------------------

## How to Use

### 1. Generate Circuits

``` bash
python experiment/circuit_compiler.py
```

------------------------------------------------------------------------

### 2. Generate Inputs

``` bash
python experiment/input_generator.py
```

------------------------------------------------------------------------

### 3. Run Benchmark

``` bash
python experiment/time_tester.py
```

------------------------------------------------------------------------

### 4. Run zk-DID Implementation

The zk-DID workflow involves interactions between the resource owner and
the user (subject). Follow the steps below:

(1)  **Deploy Smart Contract (Owner side)**

``` bash
python zk-DID_implementation/owner/contract_deploy.py
```

(2)  **Generate Name List (User side)**

``` bash
python zk-DID_implementation/subject/creater.py
```

(3)  **Generate Token (User side)**

``` bash
python zk-DID_implementation/subject/prover.py
```

(4)  **Token Verification / Operation (Owner side)**

``` bash
python zk-DID_implementation/owner/token_operation.py
```

(5)  **Claim Record Entries (User side)**

``` bash
python zk-DID_implementation/subject/retrieval.py
```

------------------------------------------------------------------------

## Notes

-   Follow the order: circuit → input → benchmark
-   The Merkle tree contract needs to be manually deployed on-chain by the tester before running step 4(2).
-   Results may vary depending on hardware
-   You need to generate a new "powers of tau" ceremony using `snarkjs`. Place the generated `pot12_final.ptau` file into the `experiment/` directory before running the experiments. (The process can be referenced from: https://docs.circom.io/getting-started/proving-circuits/)


