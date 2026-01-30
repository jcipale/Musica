#!/opt/Musica/venv/bin/python

"""
musica_db_export.py
Export recordings to CSV or plain text.
Translated from musica_db_export.csh
"""

import os
import sys
import subprocess
from pathlib import Path


def error(msg, code=1):
    print(msg)
    sys.exit(code)


def load_config(path):
    """
    Load KEY=value pairs from musica.conf.
    Values are treated literally and exported to os.environ.
    """
    config = {}
    with path.open("r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            config[key] = val
            os.environ[key] = val
    return config


def main():
    # script_dir and base_dir
    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent

    # load config
    config_path = base_dir / "config" / "musica.conf"
    if not config_path.is_file():
        error(f"Error: config missing: {config_path}")

    config = load_config(config_path)

    # run environment verification
    verify_script = base_dir / "bin" / "musica_verify_env.py"
    if not verify_script.is_file():
        error("Environment verification script not found.")

    result = subprocess.run(
        [sys.executable, str(verify_script)],
        check=False
    )
    if result.returncode != 0:
        error("Environment verification failed.")

    # output path
    if len(sys.argv) >= 2 and sys.argv[1]:
        outpath = Path(sys.argv[1])
    else:
        outpath = Path(config["MUSICA_EXPORT_DIR"]) / config["MUSICA_DEFAULT_EXPORT"]

    # format selection
    fmt = "csv"
    if len(sys.argv) >= 3 and sys.argv[2]:
        fmt = sys.argv[2]

    db_type = config.get("MUSICA_DB_TYPE")
    db_name = config.get("MUSICA_DB_NAME")
    db_user = config.get("MUSICA_DB_USER", "")
    db_pass = config.get("MUSICA_DB_PASS", "")

    if not db_type or not db_name:
        error("Database configuration incomplete.")

    # build DB client command
    if db_pass == "":
        base_cmd = ["sudo", db_type, "-D", db_name, "-e"]
    else:
        base_cmd = [
            db_type,
            "-u", db_user,
            f"-p{db_pass}",
            "-D", db_name,
            "-e",
        ]

    try:
        with outpath.open("w", newline="") as outfile:
            if fmt == "csv":
                # tab-separated output -> convert to CSV
                sql = (
                    "SELECT artist,title,orchestra,conductor,year,genre,"
                    "format,label,catalog_number,reissue,mode,dbx "
                    "FROM recordings ORDER BY year,artist;"
                )
                proc = subprocess.Popen(
                    base_cmd + [sql],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = proc.communicate()

                if proc.returncode != 0:
                    sys.stderr.write(stderr)
                    error("Export failed.")

                for line in stdout.splitlines():
                    outfile.write(line.replace("\t", ",") + "\n")
            else:
                sql = "SELECT * FROM recordings ORDER BY year,artist;"
                proc = subprocess.run(
                    base_cmd + [sql],
                    stdout=outfile
                )
                if proc.returncode != 0:
                    error("Export failed.")

    except Exception as e:
        error(f"Export failed: {e}")

    print(f"Export saved to: {outpath}")
    sys.exit(0)


if __name__ == "__main__":
    main()

