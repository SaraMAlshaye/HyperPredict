"""Download the official NHANES 2021-2023 files into data/raw/.

Files are saved unchanged (SAS transport .xpt). Existing files are skipped unless
--force is given. Each file is checked by opening it and confirming SEQN exists.
"""
import argparse
import sys
import urllib.request

import pandas as pd

from nhanes_config import BASE_URL, KEEP_COLUMNS, NHANES_FILES, RAW_DIR


def download(name: str, force: bool) -> bool:
    path = RAW_DIR / f"{name}.xpt"
    url = f"{BASE_URL}/{name}.xpt"
    if path.exists() and not force:
        print(f"[skip] {path.name} already exists")
    else:
        print(f"[get ] {url}")
        tmp = path.with_suffix(".part")
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "HyperPredict/1.0"})
            with urllib.request.urlopen(request, timeout=120) as response, open(tmp, "wb") as out:
                out.write(response.read())
            tmp.replace(path)
        except Exception as exc:  # network or HTTP failure
            tmp.unlink(missing_ok=True)
            print(f"[FAIL] {name}: {exc}")
            return False

    try:
        df = pd.read_sas(path, format="xport")
    except Exception as exc:
        print(f"[FAIL] {name}: file could not be read as SAS XPORT ({exc})")
        return False
    missing = [c for c in KEEP_COLUMNS[name] if c not in df.columns]
    if missing:
        print(f"[FAIL] {name}: expected columns not found: {missing}")
        return False
    print(f"[ ok ] {name}: {len(df):,} rows x {df.shape[1]} columns "
          f"({NHANES_FILES[name]}); codebook {BASE_URL}/{name}.htm")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="re-download existing files")
    args = parser.parse_args()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    failed = [name for name in NHANES_FILES if not download(name, args.force)]
    if failed:
        sys.exit(f"Download/verification failed for: {failed}")
    print("All NHANES files downloaded and verified.")


if __name__ == "__main__":
    main()
