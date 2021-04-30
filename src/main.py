import argparse
import logging
import sys

import yaml
from datetime import datetime

from utils import CurrencyExtractor

from binance.client import Client

from exchange.common import TaxExtractor
from reporter import TaxReporter, dump_to_csv
from utils import boot_db
from sqlalchemy import create_engine

logging.basicConfig(format='%(asctime)s %(message)s')

logger = logging.getLogger("main")
logger.setLevel(logging.DEBUG)


def load_configuration(filename):
    with open(filename) as file:
        return yaml.load(file, Loader=yaml.FullLoader)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--config", type=str, help="yaml config file", required=True)
    parser.add_argument("--exchange", type=str, help="selected exchange", required=not ("--generate" not in sys.argv or "--boot" not in sys.argv), choices=TaxExtractor.get_supported_exchange().keys())

    parser.add_argument("--boot", action="store_true", help="create intial database structure", required=False)

    parser.add_argument("--load", action="store_true", help="load exchange data", required=False, )
    parser.add_argument("-i", "--inf", type=str, help="exchange account statement", required="--load" in sys.argv)
    parser.add_argument("-c", "--cc", action="store_true", help="try compact sale within same minute timestamp", required=False)

    parser.add_argument("--clean", action="store_true", help="clean loaded exchange data", required=False)

    parser.add_argument("--generate", action="store_true", help="generate disposal summary", required=False)
    parser.add_argument("-o", "--outf", type=str, help="csv of disposal summary", required="--generate" in sys.argv)
    parser.add_argument("-b", "--begin", type=str, help="begin date of tax year", required="--generate" in sys.argv)
    parser.add_argument("-e", "--end", type=str, help="end date of tax year", required="--generate" in sys.argv)

    args = parser.parse_args()

    config_file = args.config
    exchange = args.exchange
    execute_boot = args.boot
    execute_load = args.load
    execute_clean = args.clean
    execute_generate = args.generate

    input_filename = args.inf
    output_filename = args.outf
    try_compact = args.cc
    begin_date = args.begin
    end_date = args.end

    config = load_configuration(config_file)

    engine = create_engine(config["database"]["database_uri"])
    binance_client = Client(config["binance"]["key"], config["binance"]["secret"])
    currency_extractor = CurrencyExtractor(engine, binance_client)

    if execute_boot:
        boot_db(config["database"]["database_dialect"], engine)

    if execute_clean:
        extractor = TaxExtractor.get_extractor(exchange, engine, currency_extractor)
        extractor.clean_all_history()

    if execute_load:
        extractor = TaxExtractor.get_extractor(exchange, engine, currency_extractor)
        extractor.load_account_statement(input_filename)
        extractor.process_load()
        extractor.generate_purchase_operation_history()
        extractor.generate_sale_operation_history(try_compact=try_compact)

    if execute_generate:
        report = TaxReporter(engine, currency_extractor)
        tax_report = report.generate_tax_disposal_history(begin_date=datetime.strptime(begin_date, "%Y-%m-%d-%H-%M-%S"),
                                                          end_date=datetime.strptime(end_date, "%Y-%m-%d-%H-%M-%S"),
                                                          compacted=try_compact)

        dump_to_csv(tax_report, output_filename)












