import csv
import logging
from datetime import datetime

from sqlalchemy.engine import Connection

from exchange.common import AbstractExchangeExtractor
from utils import CurrencyExtractor

logger = logging.getLogger("main")


class CoinbaseTaxExtractor(AbstractExchangeExtractor):

    PLATFORM = "COINBASE"

    def __init__(self, connection: Connection, currency_extractor: CurrencyExtractor):
        super(CoinbaseTaxExtractor, self).__init__(connection, currency_extractor)

    def clean_all_history(self):
        super(CoinbaseTaxExtractor, self).clean_all_history()

        with self.connection.begin() as conn:
            sql = "DELETE FROM `coinbase_raw_operations`;"
            conn.execute(sql, [])
            sql = "DELETE FROM `coinbase_fiat_history`;"
            conn.execute(sql, [])
            sql = "DELETE FROM `coinbase_crypto_history`;"
            conn.execute(sql, [])

    def load_account_statement(self, filepath):
        sql = "INSERT INTO `coinbase_raw_operations` (`operation_datetime`, `operation`, `coin`, `quantity`, `spot_price`, `amount_price`, `note`)" \
              "                               VALUES (%s,                   %s,          %s,     %s,         %s,           %s,             %s    )"

        with open(filepath) as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            header_found = False

            with self.connection.begin() as conn:

                for row in reader:
                    if row and row[0] == "Timestamp":
                        header_found = True
                        continue
                    elif not header_found:
                        continue

                    conn.execute(sql, [datetime.strptime(row[0], "%Y-%m-%dT%H:%M:%SZ"),
                                       row[1].upper(),
                                       row[2],
                                       float(row[3]),
                                       float(row[4]),
                                       float(row[5]) if row[5] else 0.0,
                                       row[8]])

    def process_load(self):
        self.extract_fiat_history()
        self.extract_crypto_history()
        self.consolidate_history()

    def extract_fiat_history(self):
        sqli = "INSERT INTO coinbase_fiat_history(operation_datetime, asset, amount, operation)" \
               "                          VALUES (%s,                 %s,    %s,     %s       )"
        with self.connection.begin() as conn:
            sql = "SELECT * FROM `coinbase_raw_operations` WHERE operation = %s;"
            result = conn.execute(sql, ["BUY"]).mappings().all()

            for res in result:
                note = res["note"]
                fiat = note.split(" ")[-1]
                conn.execute(sqli, [res["operation_datetime"],
                                    fiat,
                                    res["amount_price"],
                                    "BUY"])

            sql = "SELECT * FROM `coinbase_raw_operations` WHERE operation = %s;"
            result = conn.execute(sql, ["SELL"]).mappings().all()

            for res in result:
                note = res["note"]
                fiat = note.split(" ")[-1]
                conn.execute(sqli, [res["operation_datetime"],
                                    fiat,
                                    res["amount_price"],
                                    "SELL"])

    def extract_crypto_history(self):
        sqli = "INSERT INTO coinbase_crypto_history(operation_datetime, asset, amount_asset, operation)" \
               "                           VALUES (%s,                 %s,    %s,           %s       )"

        with self.connection.begin() as conn:
            # search for buy crypto (with fiat)
            sql = "SELECT * FROM `coinbase_raw_operations` WHERE operation = %s;"
            result = conn.execute(sql, ["Buy"]).mappings().all()

            for res in result:
                conn.execute(sqli, [res["operation_datetime"],
                                    res["coin"],
                                    res["quantity"],
                                    "BUY"])

            # search for sell crypto (with fiat)
            sql = "SELECT * FROM `coinbase_raw_operations` WHERE operation = %s;"
            result = conn.execute(sql, ["Sell"]).mappings().all()
            for res in result:
                conn.execute(sqli, [res["operation_datetime"],
                                    res["coin"],
                                    -float(res["quantity"]),
                                    "SELL"])


            # search for deposit (transfert)
            sql = "SELECT * FROM `coinbase_raw_operations` WHERE operation = %s;"
            result = conn.execute(sql, ["Receive"]).mappings().all()

            for res in result:
                conn.execute(sqli, [res["operation_datetime"],
                                    res["coin"],
                                    res["quantity"],
                                    "BUY"])

            # search for widrawth (transfert)
            sql = "SELECT * FROM `coinbase_raw_operations` WHERE operation = %s;"
            result = conn.execute(sql, ["Send"]).mappings().all()
            for res in result:
                conn.execute(sqli, [res["operation_datetime"],
                                    res["coin"],
                                    -float(res["quantity"]),
                                    "SELL"])
                                    
            # search for CONVERT
            sql = "SELECT * FROM `coinbase_raw_operations` WHERE operation = %s;"
            result = conn.execute(sql, ["Convert"]).mappings().all()

            for res in result:
                note = res["note"]
                note_tokens = note.split(" ")
                new_coin = note_tokens[-1]
                new_amount = float(note_tokens[-2].replace(",","."))
                conn.execute(sqli, [res["operation_datetime"],
                                    res["coin"],
                                    -float(res["quantity"]),
                                    "SELL"])
                conn.execute(sqli, [res["operation_datetime"],
                                    new_coin,
                                    new_amount,
                                    "BUY"])


            # Distribution: used (crypto free-buy/airdrop)
            sql = "SELECT * FROM `coinbase_raw_operations` WHERE operation = %s;"
            result = conn.execute(sql, ["Coinbase Earn"]).mappings().all()
            for res in result:
                conn.execute(sqli, [res["operation_datetime"],
                                    res["coin"],
                                    res["quantity"],
                                    "BUY"])

    def consolidate_history(self):
        pass

    def get_all_fiat_deposit(self):
        with self.connection.connect() as conn:
            sql = "SELECT * FROM coinbase_fiat_history where operation = %s"
            args = ["BUY"]

            result = conn.execute(sql, args).mappings().all()
            return result

    def get_all_fiat_withdraw(self):
        with self.connection.connect() as conn:
            sql = "SELECT * FROM coinbase_fiat_history where operation = %s"
            args = ["SELL"]

            result = conn.execute(sql, args).mappings().all()
            return result

    def generate_purchase_operation_history(self):
        logger.info("Generate coinbase purchase operation history")
        all_open_positions = self.get_all_fiat_deposit()

        for open_position in all_open_positions:
            euro_price = self.currency_extractor.get_asset_price("euro", open_position["operation_datetime"])
            purchase_operation = {
                "purchase_datetime": open_position["operation_datetime"],
                "asset": open_position["asset"],
                "amount_asset": open_position["amount"],
                "amount_price_usd": open_position["amount"]/euro_price,  # warn: price is already in euro, get dollar instead
                "amount_price_euro": open_position["amount"],
                "current_asset_price_usd": open_position["amount"]/euro_price,  # warn: price is already in euro, get dollar instead
                "current_asset_price_euro": open_position["amount"],
            }

            self.save_purchase_operation(purchase_operation)

    def generate_sale_operation_history(self, try_compact: bool = False):
        logger.info("Generate coinbase sale operation history (compact is {})".format(try_compact))
        all_close_positions = self.get_all_fiat_withdraw()

        for close_position in all_close_positions:
            euro_price = self.currency_extractor.get_asset_price("euro", close_position["operation_datetime"])
            amount = abs(close_position["amount"])
            sale_operation = {
                "sale_datetime": close_position["operation_datetime"],
                "asset": close_position["asset"],
                "amount_asset": amount,
                "amount_price_usd": amount/euro_price,  # warn: price is already in euro, get dollar instead
                "amount_price_euro": amount,
                "current_asset_price_usd": amount/euro_price,  # warn: price is already in euro, get dollar instead
                "current_asset_price_euro": amount,
            }

            self.save_sale_operation(sale_operation)

    def get_portfolio_value(self, timestamp: datetime):
        portfolio_value = 0.0
        with self.connection.connect() as conn:
            sql = "select sum(amount_asset) as amount, asset from coinbase_crypto_history where operation_datetime <= %s group by asset"
            args = [timestamp]

            result = conn.execute(sql, args).mappings().all()

            for res in result:
                amount = res["amount"]
                asset = res["asset"].lower()

                if amount <= 0.0:
                    continue

                price = self.currency_extractor.get_asset_price(asset, timestamp, scope="GECKO")

                euro_price = self.currency_extractor.get_asset_price("euro", timestamp)
                portfolio_value += price * amount * euro_price

        return portfolio_value
