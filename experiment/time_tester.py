import csv
import json
import shutil
import subprocess
import time
import traceback
from pathlib import Path


# ------------------------------------------------------------------
# Project Path Configuration
# ------------------------------------------------------------------
ROOT = Path(".").resolve()
CIRCUIT_DIR = ROOT / "circuits"
INPUT_DIR = ROOT / "merkle_inputs"
RESULT_DIR = ROOT / "results"
BUILD_DIR = ROOT / "build"

# Ensure required output directories exist.
RESULT_DIR.mkdir(parents=True, exist_ok=True)
BUILD_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------
# Benchmark Scope Configuration
# ------------------------------------------------------------------
# Full benchmark example:
# METHODS = ["plain", "mimc", "poseidon"]
# LEVELS = list(range(1, 21))

# Current benchmark target configuration.
METHODS = ["poseidon"]
LEVELS = [6]

# Powers of Tau file required by Groth16 setup.
PTAU = ROOT / "pot12_final.ptau"


# ------------------------------------------------------------------
# External Executable Paths
# ------------------------------------------------------------------
# These are resolved dynamically in main().
CIRCOM_EXE = None
SNARKJS_EXE = None
NODE_EXE = None


# ==================================================================
# Command Execution Helper
# ==================================================================

def run_cmd(cmd, cwd=None, step_name: str = ""):
    """
    Execute a subprocess command and collect detailed runtime metadata.

    Parameters
    ----------
    cmd : list
        Command and arguments to execute
    cwd : Path or None, optional
        Working directory for the subprocess
    step_name : str, optional
        Human-readable label for the current benchmark stage

    Returns
    -------
    dict
        Dictionary containing command string, return code, stdout,
        stderr, and elapsed time
    """

    # Small delay for clearer console separation during benchmarking.
    print("[WAIT] sleeping 1 second before command...")
    time.sleep(1)

    print("\n" + "=" * 100)
    if step_name:
        print(f"[STEP] {step_name}")
    print("[CMD ]", " ".join(str(x) for x in cmd))
    if cwd is not None:
        print("[CWD ]", cwd)

    start = time.perf_counter()

    proc = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )

    end = time.perf_counter()

    print("[CODE]", proc.returncode)

    if proc.stdout:
        print("[STDOUT]")
        print(proc.stdout)

    if proc.stderr:
        print("[STDERR]")
        print(proc.stderr)

    print(f"[TIME] {end - start:.6f}s")
    print("=" * 100)

    return {
        "cmd": " ".join(str(x) for x in cmd),
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "elapsed": end - start,
    }


# ==================================================================
# R1CS Metadata Extraction
# ==================================================================

def extract_r1cs_info(text: str):
    """
    Extract key R1CS summary lines from snarkjs output.

    Expected fields include:
    - constraints
    - wires
    - private inputs
    - public inputs
    - labels

    Parameters
    ----------
    text : str
        Raw stdout text from `snarkjs r1cs info`

    Returns
    -------
    dict
        Dictionary containing extracted summary strings
    """

    info = {
        "constraints": None,
        "wires": None,
        "private_inputs": None,
        "public_inputs": None,
        "labels": None,
    }

    for raw in text.splitlines():
        line = raw.strip()
        lower = line.lower()

        if "constraints" in lower and info["constraints"] is None:
            info["constraints"] = line
        elif "wires" in lower and info["wires"] is None:
            info["wires"] = line
        elif "private inputs" in lower and info["private_inputs"] is None:
            info["private_inputs"] = line
        elif "public inputs" in lower and info["public_inputs"] is None:
            info["public_inputs"] = line
        elif "labels" in lower and info["labels"] is None:
            info["labels"] = line

    return info


# ==================================================================
# File Utility Helpers
# ==================================================================

def file_size_bytes(path: Path):
    """
    Return file size in bytes if the file exists.

    Parameters
    ----------
    path : Path
        Target file path

    Returns
    -------
    int or None
        File size in bytes, or None if the file does not exist
    """
    return path.stat().st_size if path.exists() else None



def ensure_exists(path: Path, desc: str) -> None:
    """
    Validate that a required file or directory exists.

    Parameters
    ----------
    path : Path
        Path to validate
    desc : str
        Human-readable description of the required resource

    Raises
    ------
    FileNotFoundError
        If the required path does not exist
    """
    if not path.exists():
        raise FileNotFoundError(f"Missing {desc}: {path}")



def append_json(results, out_file: Path) -> None:
    """
    Write the full benchmark result list to a JSON file.

    Parameters
    ----------
    results : list
        Benchmark result records
    out_file : Path
        Output JSON file path
    """
    out_file.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )



def write_csv(results, out_file: Path) -> None:
    """
    Write benchmark results to a CSV file.

    Parameters
    ----------
    results : list
        Benchmark result records
    out_file : Path
        Output CSV file path
    """

    fieldnames = [
        "method", "level", "depth",
        "compile_ok", "compile_time",
        "witness_ok", "witness_time",
        "setup_ok", "setup_time",
        "contribute_ok", "contribute_time",
        "prove_ok", "prove_time",
        "verify_ok", "verify_time",
        "constraints", "wires", "private_inputs", "public_inputs", "labels",
        "r1cs_size", "wasm_size", "zkey_size", "proof_size", "sym_size",
        "verify_stdout",
        "error_stage", "exception",
    ]

    with out_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for r in results:
            row = {
                "method": r.get("method"),
                "level": r.get("level"),
                "depth": r.get("depth"),
                "compile_ok": r.get("compile_ok"),
                "compile_time": r.get("compile_time"),
                "witness_ok": r.get("witness_ok"),
                "witness_time": r.get("witness_time"),
                "setup_ok": r.get("setup_ok"),
                "setup_time": r.get("setup_time"),
                "contribute_ok": r.get("contribute_ok"),
                "contribute_time": r.get("contribute_time"),
                "prove_ok": r.get("prove_ok"),
                "prove_time": r.get("prove_time"),
                "verify_ok": r.get("verify_ok"),
                "verify_time": r.get("verify_time"),
                "constraints": (r.get("r1cs_info") or {}).get("constraints"),
                "wires": (r.get("r1cs_info") or {}).get("wires"),
                "private_inputs": (r.get("r1cs_info") or {}).get("private_inputs"),
                "public_inputs": (r.get("r1cs_info") or {}).get("public_inputs"),
                "labels": (r.get("r1cs_info") or {}).get("labels"),
                "r1cs_size": r.get("r1cs_size"),
                "wasm_size": r.get("wasm_size"),
                "zkey_size": r.get("zkey_size"),
                "proof_size": r.get("proof_size"),
                "sym_size": r.get("sym_size"),
                "verify_stdout": r.get("verify_stdout"),
                "error_stage": r.get("error_stage"),
                "exception": r.get("exception"),
            }
            writer.writerow(row)


# ==================================================================
# Single Benchmark Task
# ==================================================================

def benchmark_one(method: str, level: int):
    """
    Benchmark one circuit / input pair through the full Groth16 pipeline.

    Parameters
    ----------
    method : str
        Circuit family name, e.g. plain / mimc / poseidon
    level : int
        Merkle tree level used to derive circuit depth and input file

    Returns
    -------
    dict
        Full benchmark result record
    """

    depth = level - 1
    circuit_name = f"{method}_depth_{depth}"

    circom_file = CIRCUIT_DIR / f"{circuit_name}.circom"
    input_file = INPUT_DIR / method / f"input_level_{level}.json"

    ensure_exists(circom_file, "circom file")
    ensure_exists(input_file, "input file")
    ensure_exists(PTAU, "ptau file")

    # Create a clean build directory for this benchmark target.
    workdir = BUILD_DIR / circuit_name
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True, exist_ok=True)

    result = {
        "method": method,
        "level": level,
        "depth": depth,
        "circuit": str(circom_file),
        "input": str(input_file),
    }

    # --------------------------------------------------------------
    # 1) Circuit Compilation
    # --------------------------------------------------------------
    compile_res = run_cmd(
        [
            CIRCOM_EXE,
            str(circom_file),
            "--r1cs",
            "--wasm",
            "--sym",
            "-l",
            str(ROOT / "node_modules"),
            "-o",
            str(workdir),
        ],
        step_name=f"{circuit_name} :: compile",
    )

    result["compile_time"] = compile_res["elapsed"]
    result["compile_ok"] = (compile_res["returncode"] == 0)
    result["compile_stdout"] = compile_res["stdout"]
    result["compile_stderr"] = compile_res["stderr"]

    if not result["compile_ok"]:
        result["error_stage"] = "compile"
        return result

    # Expected compilation outputs.
    r1cs_file = workdir / f"{circuit_name}.r1cs"
    sym_file = workdir / f"{circuit_name}.sym"
    js_dir = workdir / f"{circuit_name}_js"
    wasm_file = js_dir / f"{circuit_name}.wasm"
    witness_file = workdir / "witness.wtns"
    zkey_0 = workdir / f"{circuit_name}_0000.zkey"
    zkey_final = workdir / f"{circuit_name}_final.zkey"
    proof_file = workdir / "proof.json"
    public_file = workdir / "public.json"
    vkey_file = workdir / "verification_key.json"

    ensure_exists(r1cs_file, "compiled r1cs file")
    ensure_exists(wasm_file, "compiled wasm file")
    ensure_exists(js_dir / "generate_witness.js", "generate_witness.js")

    # --------------------------------------------------------------
    # 2) R1CS Information Extraction
    # --------------------------------------------------------------
    r1cs_info_res = run_cmd(
        [SNARKJS_EXE, "r1cs", "info", str(r1cs_file)],
        step_name=f"{circuit_name} :: r1cs info",
    )

    result["r1cs_info_ok"] = (r1cs_info_res["returncode"] == 0)
    result["r1cs_info"] = extract_r1cs_info(r1cs_info_res["stdout"])
    result["r1cs_info_stdout"] = r1cs_info_res["stdout"]
    result["r1cs_info_stderr"] = r1cs_info_res["stderr"]

    if not result["r1cs_info_ok"]:
        result["error_stage"] = "r1cs_info"
        return result

    # --------------------------------------------------------------
    # 3) Witness Generation
    # --------------------------------------------------------------
    witness_res = run_cmd(
        [
            NODE_EXE,
            str(js_dir / "generate_witness.js"),
            str(wasm_file),
            str(input_file),
            str(witness_file),
        ],
        step_name=f"{circuit_name} :: witness",
    )

    result["witness_time"] = witness_res["elapsed"]
    result["witness_ok"] = (witness_res["returncode"] == 0)
    result["witness_stdout"] = witness_res["stdout"]
    result["witness_stderr"] = witness_res["stderr"]

    if not result["witness_ok"]:
        result["error_stage"] = "witness"
        return result

    # --------------------------------------------------------------
    # 4) Groth16 Setup
    # --------------------------------------------------------------
    setup_res = run_cmd(
        [
            SNARKJS_EXE, "groth16", "setup",
            str(r1cs_file),
            str(PTAU),
            str(zkey_0),
        ],
        step_name=f"{circuit_name} :: setup",
    )

    result["setup_time"] = setup_res["elapsed"]
    result["setup_ok"] = (setup_res["returncode"] == 0)
    result["setup_stdout"] = setup_res["stdout"]
    result["setup_stderr"] = setup_res["stderr"]

    if not result["setup_ok"]:
        result["error_stage"] = "setup"
        return result

    # --------------------------------------------------------------
    # 5) zkey Contribution
    # --------------------------------------------------------------
    contribute_res = run_cmd(
        [
            SNARKJS_EXE, "zkey", "contribute",
            str(zkey_0),
            str(zkey_final),
            "--name=bench",
            "-e=random",
        ],
        step_name=f"{circuit_name} :: contribute",
    )

    result["contribute_time"] = contribute_res["elapsed"]
    result["contribute_ok"] = (contribute_res["returncode"] == 0)
    result["contribute_stdout"] = contribute_res["stdout"]
    result["contribute_stderr"] = contribute_res["stderr"]

    if not result["contribute_ok"]:
        result["error_stage"] = "contribute"
        return result

    # --------------------------------------------------------------
    # 6) Proof Generation
    # --------------------------------------------------------------
    prove_res = run_cmd(
        [
            SNARKJS_EXE, "groth16", "prove",
            str(zkey_final),
            str(witness_file),
            str(proof_file),
            str(public_file),
        ],
        step_name=f"{circuit_name} :: prove",
    )

    result["prove_time"] = prove_res["elapsed"]
    result["prove_ok"] = (prove_res["returncode"] == 0)
    result["prove_stdout"] = prove_res["stdout"]
    result["prove_stderr"] = prove_res["stderr"]

    if not result["prove_ok"]:
        result["error_stage"] = "prove"
        return result

    # --------------------------------------------------------------
    # 7) Verification Key Export
    # --------------------------------------------------------------
    vkey_res = run_cmd(
        [
            SNARKJS_EXE, "zkey", "export", "verificationkey",
            str(zkey_final),
            str(vkey_file),
        ],
        step_name=f"{circuit_name} :: export verification key",
    )

    result["vkey_ok"] = (vkey_res["returncode"] == 0)
    result["vkey_stdout"] = vkey_res["stdout"]
    result["vkey_stderr"] = vkey_res["stderr"]

    if not result["vkey_ok"]:
        result["error_stage"] = "export_vkey"
        return result

    # --------------------------------------------------------------
    # 8) Proof Verification
    # --------------------------------------------------------------
    verify_res = run_cmd(
        [
            SNARKJS_EXE, "groth16", "verify",
            str(vkey_file),
            str(public_file),
            str(proof_file),
        ],
        step_name=f"{circuit_name} :: verify",
    )

    result["verify_time"] = verify_res["elapsed"]
    result["verify_ok"] = (verify_res["returncode"] == 0)
    result["verify_stdout"] = verify_res["stdout"]
    result["verify_stderr"] = verify_res["stderr"]

    if not result["verify_ok"]:
        result["error_stage"] = "verify"
        return result

    # Benchmark completed successfully.
    result["error_stage"] = None

    # Collect artifact sizes for later analysis.
    result["r1cs_size"] = file_size_bytes(r1cs_file)
    result["wasm_size"] = file_size_bytes(wasm_file)
    result["zkey_size"] = file_size_bytes(zkey_final)
    result["proof_size"] = file_size_bytes(proof_file)
    result["sym_size"] = file_size_bytes(sym_file)

    return result


# ==================================================================
# Main Execution Entry
# ==================================================================

def main() -> None:
    """
    Resolve dependencies, execute all benchmark targets, and export
    aggregated results.
    """

    global CIRCOM_EXE, SNARKJS_EXE, NODE_EXE

    # Resolve required command-line tools from the current environment.
    CIRCOM_EXE = shutil.which("circom")
    SNARKJS_EXE = shutil.which("snarkjs")
    NODE_EXE = shutil.which("node")

    print(f"[CHECK] circom : {CIRCOM_EXE}")
    print(f"[CHECK] snarkjs: {SNARKJS_EXE}")
    print(f"[CHECK] node   : {NODE_EXE}")
    print(f"[CHECK] PTAU   : {PTAU} -> {PTAU.exists()}")
    print(f"[CHECK] node_modules exists: {(ROOT / 'node_modules').exists()}")

    if CIRCOM_EXE is None:
        raise EnvironmentError("Command not found: circom")
    if SNARKJS_EXE is None:
        raise EnvironmentError("Command not found: snarkjs")
    if NODE_EXE is None:
        raise EnvironmentError("Command not found: node")

    all_results = []
    json_out = RESULT_DIR / "benchmark_results.json"
    csv_out = RESULT_DIR / "benchmark_results.csv"

    total = len(METHODS) * len(LEVELS)
    index = 0

    for method in METHODS:
        for level in LEVELS:
            index += 1
            print(f"\n[{index}/{total}] method={method}, level={level}, depth={level - 1}")

            try:
                res = benchmark_one(method, level)
            except Exception as e:
                # Preserve failure information in the result set so that
                # the whole benchmark process can continue.
                res = {
                    "method": method,
                    "level": level,
                    "depth": level - 1,
                    "compile_ok": False,
                    "witness_ok": False,
                    "setup_ok": False,
                    "contribute_ok": False,
                    "prove_ok": False,
                    "verify_ok": False,
                    "error_stage": "exception",
                    "exception": str(e),
                    "traceback": traceback.format_exc(),
                }
                print("[EXCEPTION]", e)
                print("[TRACEBACK]")
                print(traceback.format_exc())

            all_results.append(res)

            # Persist intermediate results after each benchmark target.
            # This helps preserve data even if a later run crashes.
            append_json(all_results, json_out)
            write_csv(all_results, csv_out)

            status = "OK" if res.get("verify_ok") else f"FAIL at {res.get('error_stage')}"
            print(status)

    print("\nDone.")
    print(f"JSON: {json_out}")
    print(f"CSV : {csv_out}")


# ------------------------------------------------------------------
# Script Entry Point
# ------------------------------------------------------------------
if __name__ == "__main__":
    main()
