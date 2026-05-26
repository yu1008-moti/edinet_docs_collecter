import csv
import requests
import pandas as pd
import os
from typing import Dict, Generator, List
import datetime as dt
from dateutil.relativedelta import relativedelta
import time
from pathlib import Path

ENDPOINT_TO_COLLECT_DOCSLIST = 'https://api.edinet-fsa.go.jp/api/v2/documents.json'
TYPE_TO_COLLECT_DOCSLIST = 2

ENDPOINT_TO_DOWNLOAD_DOC = 'https://api.edinet-fsa.go.jp/api/v2/documents'
TYPE_TO_DOWNLOAD_DOC = 5

def _get_api_key():
    api_key = os.getenv('API_KEY_EDINET')
    return api_key

def _get_edinet_url(cfg):
    api_key = _get_api_key()
    cfg_date  = dt.datetime(cfg['date']['year'], cfg['date']['month'], cfg['date']['day']).strftime('%Y-%m-%d') if 'date' in cfg else None
    cfg_docID = cfg['docID'] if 'docID' in cfg else None
    cfg_type  = cfg['type']
    cfg_endp  = cfg['endpoint']

    if cfg_date:
        url = f'{cfg_endp}?date={cfg_date}&type={cfg_type}&Subscription-Key={api_key}'
    else:
        url = f'{cfg_endp}/{cfg_docID}?type={cfg_type}&Subscription-Key={api_key}'

    return url

def _iter_download_DocsList(date: dt.datetime) -> Dict:

    cfg = {
        'date' : {
            'year'  : date.year,
            'month' : date.month,
            'day'   : date.day
        },
        'type' : TYPE_TO_COLLECT_DOCSLIST,
        'endpoint' : ENDPOINT_TO_COLLECT_DOCSLIST
    }

    url = _get_edinet_url(cfg)
    res = requests.get(url).json()

    return res

def _download_DocsList() -> Generator[Dict, None, None]:
    time_range = {
        'start' : dt.datetime.now(tz=dt.timezone.utc) - relativedelta(years=10),
        'end'   : dt.datetime.now(tz=dt.timezone.utc)
    }

    for date in pd.date_range(start=time_range['start'], end=time_range['end']).to_list():
        time.sleep(10)  # Sleep for 1 second to avoid overwhelming the API
        res = _iter_download_DocsList(date)
        yield res

def get_DocsList() -> None:
    docsList: Dict[str, List] = {}
    for res in _download_DocsList():
        date = res['metadata']['parameter']['date']
        sequences:List[Dict] = res['results'] # sequence of documents list
        for seq in sequences: # sequence of documents list
            for key, value in seq.items(): # key: document component name, value: the content of the document component
                if key not in docsList:
                    docsList[key] = [value]
                else:
                    docsList[key].append(value)
        df_docsList = pd.DataFrame.from_dict(docsList)
        df_docsList.to_csv(f'./docsList/{date}.csv', index=False)
        docsList = {} # Clear the docsList for the next date's data

    return

def _check_file_contents(file_path: str) -> bool:
    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

        if len(rows) <= 1:
            return True
        return False

def _load_query_csv(date_from: dt.datetime) -> Generator[pd.DataFrame, None, None]:
    for path in Path('./docsList').glob('*.csv'):
        date = path.stem  # Extract date from filename (e.g., '2024-06-01.csv' -> '2024-06-01')
        if dt.datetime.strptime(date, '%Y-%m-%d') < date_from:
            continue
        if _check_file_contents(path): 
            print(f"Skipping empty or header-only CSV file: {date}")
            continue # Skip empty or header-only CSV files
        df = pd.read_csv(path, usecols=['docID', 'edinetCode', 'filerName', 'docDescription', 'csvFlag'])
        extracted_df = df[df['csvFlag'] == 1]
        extracted_df['date'] = date  # Add date column to the extracted DataFrame
        yield extracted_df

def _iter_download_doc(doc_id: str) -> requests.Response:

    cfg = {
        'docID' : doc_id,
        'type'  : TYPE_TO_DOWNLOAD_DOC,
        'endpoint' : ENDPOINT_TO_DOWNLOAD_DOC
    }

    url = _get_edinet_url(cfg)
    res = requests.get(url)

    return res

def get_doc(date_from: dt.datetime) -> None:
    date_from=dt.datetime.strptime(date_from, '%Y-%m-%d')
    for extracted_df in _load_query_csv(date_from=date_from):
        for _, row in extracted_df.iterrows():
            doc_id = row['docID']
            edinet_code = row['edinetCode']
            filter_name = row['filerName']
            doc_description = row['docDescription'].replace('/', '-')  # Replace '/' with '_' to avoid issues in filenames
            date = row['date']

            time.sleep(10)  # Sleep for 10 second to avoid overwhelming the API
            res = _iter_download_doc(doc_id)
            open_path = f'./downloaded_docs/{date}_{doc_id}_{edinet_code}_{filter_name}_{doc_description}.zip'
            print(f"\rsave document: {open_path[:50]}...", end="")
            with open(open_path, 'wb') as f:
                f.write(res.content)
    
    return