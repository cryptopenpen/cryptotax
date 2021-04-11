import argparse
import logging
from datetime import datetime

from exchange.etoro import EtoroTaxExtractor, read_account_statement
from reporter import TaxReporter, dump_to_csv
from utils import boot_db
from sqlalchemy import create_engine

logging.basicConfig(format='%(asctime)s %(message)s')

logger = logging.getLogger("main")
logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inf", type=str, help="etoro account statement", required=True)
    parser.add_argument("-o", "--outf", type=str, help="csv of disposal summary", required=True)
    parser.add_argument("-b", "--begin", type=str, help="begin date of tax year", required=True)
    parser.add_argument("-e", "--end", type=str, help="end date of tax year", required=True)
    parser.add_argument("-c", "--cc", action="store_true", help="try compact sale within same minute timestamp", required=False)
    args = parser.parse_args()

    input_filename = args.inf
    output_filename = args.outf
    try_compact = args.cc
    begin_date = args.begin
    end_date = args.end

    engine = create_engine("mysql+pymysql://root:1234cryptotax1234@localhost:3307/tax_reporter?charset=utf8mb4")

    boot_db("mysql+pymysql", engine)

    all_pos, closed_pos = read_account_statement(input_filename)
    accountstat = EtoroTaxExtractor(all_pos, closed_pos, engine)
    #accountstat.clean_all_history()
    accountstat.extract_purchase_history()
    accountstat.extract_sale_history()
    accountstat.consolidate_history()
    accountstat.generate_purchase_operation_history()
    accountstat.generate_sale_operation_history(try_compact=try_compact)

    report = TaxReporter(engine)
    tax_report = report.generate_tax_disposal_history(begin_date=datetime.strptime(begin_date, "%Y-%m-%d-%H-%M-%S"),
                                                      end_date=datetime.strptime(end_date, "%Y-%m-%d-%H-%M-%S"),
                                                      compacted=try_compact)

    dump_to_csv(tax_report, output_filename)












