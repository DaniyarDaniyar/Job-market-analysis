"""Reproducible command-line entry points and interactive console menu."""
import argparse
import json
import sys
from pathlib import Path
from .ingest import build_database
from .analytics import generate_analysis
from .downloader import download_data

def main():
    parser=argparse.ArgumentParser(description='Job Market Skills Analytics · topic 14')
    sub=parser.add_subparsers(dest='command')
    sub.add_parser('download',help='Download real Kaggle dataset version 13')
    ingest=sub.add_parser('ingest',help='Clean CSV into SQLite and Parquet')
    ingest.add_argument('--input',default='data/raw/linkedin/postings.csv')
    ingest.add_argument('--output',default='data/processed')
    ingest.add_argument('--chunksize',type=int,default=10000)
    analyze=sub.add_parser('analyze',help='Run EDA, SQL, forecasts and charts')
    analyze.add_argument('--data',default='data/processed')
    analyze.add_argument('--output',default='reports')
    sub.add_parser('demo',help='Build small real-data demo; does not overwrite submitted full-data reports')
    sub.add_parser('menu',help='Interactive console menu')
    args=parser.parse_args()
    try:
        if args.command=='download':
            print(download_data())
        elif args.command=='ingest':
            print(json.dumps(build_database(args.input,args.output,args.chunksize),indent=2))
        elif args.command=='analyze':
            print(json.dumps(generate_analysis(args.data,args.output),indent=2))
        elif args.command=='demo':
            build_database('data/sample/postings.csv','data/demo')
            generate_analysis('data/demo','data/demo/reports')
            print('Demo ready. Run: JOBMARKET_DATA_DIR=data/demo streamlit run app.py')
        elif args.command=='menu':
            menu()
        else:
            parser.print_help()
    except (OSError,ValueError) as error:
        print(f'Error: {error}',file=sys.stderr)
        return 1
    return 0

def menu():
    while True:
        print('\n1 — Load real-data sample\n2 — Show full-run summary\n3 — Dashboard instructions\n0 — Exit')
        choice=input('Select: ').strip()
        if choice=='0':
            break
        elif choice=='1':
            build_database('data/sample/postings.csv','data/demo')
            print('Sample loaded to data/demo')
        elif choice=='2':
            try:
                print(Path('reports/summary.json').read_text())
            except FileNotFoundError:
                print('Run python -m jobmarket analyze first.')
        elif choice=='3':
            print('JOBMARKET_DATA_DIR=data/demo streamlit run app.py')
        else:
            print('Enter 0, 1, 2 or 3.')

if __name__=='__main__':
    raise SystemExit(main())
