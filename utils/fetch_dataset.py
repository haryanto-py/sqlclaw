from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

from kaggle.api.kaggle_api_extended import KaggleApi

OLIST_DATASET_ID = "olistbr/brazilian-ecommerce"


def download_dataset(dataset_id: str = OLIST_DATASET_ID, output_path: str = "./data") -> Path:
    """
    Authenticates with Kaggle and downloads a dataset, unzipping it into output_path.

    Args:
        dataset_id: Kaggle dataset identifier in the form "owner/dataset-name".
        output_path: Local directory to download and unzip files into.

    Returns:
        Path to the output directory.
    """
    dest = Path(output_path)
    dest.mkdir(parents=True, exist_ok=True)

    api = KaggleApi()
    api.authenticate()

    print(f"Downloading dataset '{dataset_id}' to '{dest}' ...")
    api.dataset_download_files(dataset_id, path=str(dest), unzip=True)
    print("Download complete.")

    csv_files = list(dest.glob("*.csv"))
    print(f"Files available: {[f.name for f in csv_files]}")

    return dest


if __name__ == "__main__":
    download_dataset()
