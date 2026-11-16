"""Download the publicly accessible Kaggle dataset, version 13."""
from pathlib import Path
import json
import zipfile
import requests
from .ingest import sha256_file

URL='https://www.kaggle.com/api/v1/datasets/download/arshkon/linkedin-job-postings?datasetVersionNumber=13'

def download_data(destination='data/raw/linkedin'):
    destination=Path(destination); destination.mkdir(parents=True,exist_ok=True)
    archive=destination.parent/'linkedin-v13.zip'
    partial=archive.with_suffix('.part')
    try:
        with requests.get(URL,stream=True,timeout=(30,120)) as response:
            response.raise_for_status()
            with partial.open('wb') as f:
                for block in response.iter_content(1024*1024):
                    f.write(block)
        if not zipfile.is_zipfile(partial):
            raise ValueError('Kaggle did not return a ZIP. Download version 13 manually from the dataset page.')
        partial.replace(archive)
        with zipfile.ZipFile(archive) as z:
            # Select one known file, avoiding archive path traversal and unnecessary files.
            with z.open('postings.csv') as source, (destination/'postings.csv').open('wb') as out:
                import shutil
                shutil.copyfileobj(source,out)
        manifest={'url':URL,'version':13,'license':'CC BY-SA 4.0','archive_sha256':sha256_file(archive),
                  'postings_sha256':sha256_file(destination/'postings.csv')}
        (destination/'download_manifest.json').write_text(json.dumps(manifest,indent=2))
    finally:
        partial.unlink(missing_ok=True)
    return destination/'postings.csv'
