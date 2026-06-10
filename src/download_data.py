from pathlib import Path
from urllib.request import urlretrieve


DATA_URL = (
    "http://www.minethatdata.com/"
    "Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv"
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "hillstrom_email.csv"


def main() -> None:
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    if RAW_PATH.exists() and RAW_PATH.stat().st_size > 0:
        print(f"Already exists: {RAW_PATH}")
        return

    print(f"Downloading Hillstrom dataset from {DATA_URL}")
    urlretrieve(DATA_URL, RAW_PATH)
    print(f"Saved to {RAW_PATH}")


if __name__ == "__main__":
    main()
