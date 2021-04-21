import csv
import logging
from datetime import datetime

from sqlalchemy.engine import Connection

from exchange.common import AbstractExchangeExtractor
from utils import CurrencyExtractor

logger = logging.getLogger("main")


class BinanceTaxExtractor(AbstractExchangeExtractor):

    PLATFORM = "BINANCE"

    def __init__(self, connection: Connection, currency_extractor: CurrencyExtractor):
        super(BinanceTaxExtractor, self).__init__(connection, currency_extractor)

    def clean_all_history(self):
        super(BinanceTaxExtractor, self).clean_all_history()
        
        with self.connection.begin() as conn:
            sql = "DELETE FROM `binance_raw_operations`;"
            conn.execute(sql, [])
            sql = "DELETE FROM `binance_fiat_history`;"
            conn.execute(sql, [])
            sql = "DELETE FROM `binance_crypto_history`;"
            conn.execute(sql, [])

    def load_account_statement(self, filepath):
        with open(filepath) as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            with self.connection.begin() as conn:

                sql = "INSERT INTO binance_raw_operations (`operation_datetime`, `account`, `operation`, `coin`, `change`, `remark`)" \
                      "                            VALUES (%s,                   %s,        %s,          %s,     %s,       %s      )"

                for row in reader:
                    if row[0] == "UTC_Time":
                        continue

                    conn.execute(sql, [datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S"),
                                       row[1],
                                       row[2],
                                       row[3],
                                       float(row[4]),
                                       row[5]])

    def process_load(self):
        """
        Deposit: used (fiat deposit, crypt transfer)
        Transaction Related: used (fiat deposit to crypto)
        Sell: used (crypto sell)
        Buy: used (crypto buy)
        Fee: used (crypto sell-like)
        Withdraw: used (fiat withdraw, crypt withdraw)
        Small assets exchange BNB: used (crypto sell/buy)
        Savings purchase (ignored)
        Savings Principal redemption (ignored)
        transfer_out (ignored)
        transfer_in (ignored)
        POS savings purchase (ignored)
        Savings Interest: used (crypto free-buy)
        POS savings interest: used (crypto free-buy)
        Launchpool Interest: used (crypto free-buy)
        POS savings redemption (ignored)
        Super BNB Mining: used (crypto free-buy)
        Distribution: used (crypto free-buy/airdrop)
        """
        self.extract_fiat_history()
        self.extract_crypto_history()
        self.consolidate_history()

    def extract_fiat_history(self):
        sqli = "INSERT INTO binance_fiat_history(operation_datetime, asset, amount, operation)" \
               "                          VALUES (%s,                 %s,    %s,     %s       )"
        with self.connection.begin() as conn:
            sql = "SELECT * FROM `binance_raw_operations` WHERE operation = %s AND coin = %s AND account = %s;"
            result = conn.execute(sql, ["Deposit", "EUR", "Spot"]).mappings().all()

            for res in result:
                conn.execute(sqli, [res["operation_datetime"],
                                    "EUR",
                                    res["change"],
                                    "DEPOSIT"])

            sql = "SELECT * FROM `binance_raw_operations` WHERE operation = %s AND coin = %s AND account = %s;"
            result = conn.execute(sql, ["Withdraw", "EUR", "Spot"]).mappings().all()

            for res in result:
                conn.execute(sqli, [res["operation_datetime"],
                                    "EUR",
                                    res["change"],
                                    "WITHDRAW"])

    def extract_crypto_history(self):
        sqli = "INSERT INTO binance_crypto_history(operation_datetime, asset, amount_asset, operation)" \
               "                           VALUES (%s,                 %s,    %s,           %s       )"

        with self.connection.begin() as conn:
            # search for deposit with crypto
            sql = "SELECT * FROM `binance_raw_operations` WHERE operation = %s AND coin != %s AND account = %s;"
            result = conn.execute(sql, ["Deposit", "EUR", "Spot"]).mappings().all()

            for res in result:
                conn.execute(sqli, [res["operation_datetime"],
                                    res["coin"],
                                    res["change"],
                                    "BUY"])

            # search for widrawth with crypto
            sql = "SELECT * FROM `binance_raw_operations` WHERE operation = %s AND coin != %s AND account = %s;"
            result = conn.execute(sql, ["Withdraw", "EUR", "Spot"]).mappings().all()
            for res in result:
                conn.execute(sqli, [res["operation_datetime"],
                                    res["coin"],
                                    res["change"],
                                    "SELL"])

            # search for buy/sell with crypto
            sql = "SELECT * FROM `binance_raw_operations` WHERE operation = %s AND coin != %s AND account = %s;"
            result = conn.execute(sql, ["Buy", "EUR", "Spot"]).mappings().all()
            for res in result:
                conn.execute(sqli, [res["operation_datetime"],
                                    res["coin"],
                                    res["change"],
                                    "BUY"])

            # search for buy/sell with crypto
            sql = "SELECT * FROM `binance_raw_operations` WHERE operation = %s AND coin != %s AND account = %s;"
            result = conn.execute(sql, ["Sell", "EUR", "Spot"]).mappings().all()
            for res in result:
                conn.execute(sqli, [res["operation_datetime"],
                                    res["coin"],
                                    res["change"],
                                    "SELL"])

            # search for fee
            sql = "SELECT * FROM `binance_raw_operations` WHERE operation = %s AND coin != %s AND account = %s;"
            result = conn.execute(sql, ["Fee", "EUR", "Spot"]).mappings().all()
            for res in result:
                conn.execute(sqli, [res["operation_datetime"],
                                    res["coin"],
                                    res["change"],
                                    "SELL"])

            # search for bnb convert
            sql = "SELECT * FROM `binance_raw_operations` WHERE operation = %s AND coin != %s AND account = %s;"
            result = conn.execute(sql, ["Small assets exchange BNB", "EUR", "Spot"]).mappings().all()
            for res in result:
                conn.execute(sqli, [res["operation_datetime"],
                                    res["coin"],
                                    res["change"],
                                    "BUY"])

            # Savings Interest: used (crypto free-buy)
            sql = "SELECT * FROM `binance_raw_operations` WHERE operation = %s AND coin != %s AND account = %s;"
            result = conn.execute(sql, ["Savings Interest", "EUR", "Spot"]).mappings().all()
            for res in result:
                conn.execute(sqli, [res["operation_datetime"],
                                    res["coin"],
                                    res["change"],
                                    "BUY"])

            # POS savings interest: used (crypto free-buy)
            sql = "SELECT * FROM `binance_raw_operations` WHERE operation = %s AND coin != %s AND account = %s;"
            result = conn.execute(sql, ["POS savings interest", "EUR", "Spot"]).mappings().all()
            for res in result:
                conn.execute(sqli, [res["operation_datetime"],
                                    res["coin"],
                                    res["change"],
                                    "BUY"])

            # Launchpool Interest: used (crypto free-buy)
            sql = "SELECT * FROM `binance_raw_operations` WHERE operation = %s AND coin != %s AND account = %s;"
            result = conn.execute(sql, ["Launchpool Interest", "EUR", "Spot"]).mappings().all()
            for res in result:
                conn.execute(sqli, [res["operation_datetime"],
                                    res["coin"],
                                    res["change"],
                                    "BUY"])

            # Super BNB Mining: used (crypto free-buy)
            sql = "SELECT * FROM `binance_raw_operations` WHERE operation = %s AND coin != %s AND account = %s;"
            result = conn.execute(sql, ["Super BNB Mining", "EUR", "Spot"]).mappings().all()
            for res in result:
                conn.execute(sqli, [res["operation_datetime"],
                                    res["coin"],
                                    res["change"],
                                    "BUY"])

            # Distribution: used (crypto free-buy/airdrop)
            sql = "SELECT * FROM `binance_raw_operations` WHERE operation = %s AND coin != %s AND account = %s;"
            result = conn.execute(sql, ["Distribution", "EUR", "Spot"]).mappings().all()
            for res in result:
                conn.execute(sqli, [res["operation_datetime"],
                                    res["coin"],
                                    res["change"],
                                    "BUY"])

    def consolidate_history(self):
        # corrige les sommes negatives ?
        pass

    def get_all_fiat_deposit(self):
        with self.connection.connect() as conn:
            sql = "SELECT * FROM binance_fiat_history where operation = %s"
            args = ["DEPOSIT"]

            result = conn.execute(sql, args).mappings().all()
            return result

    def get_all_fiat_withdraw(self):
        with self.connection.connect() as conn:
            sql = "SELECT * FROM binance_fiat_history where operation = %s"
            args = ["WITHDRAW"]

            result = conn.execute(sql, args).mappings().all()
            return result

    def generate_purchase_operation_history(self):
        logger.info("Generate binance purchase operation history")
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
        logger.info("Generate binance sale operation history (compact is {})".format(try_compact))
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
            sql = "select sum(amount_asset) as amount, asset from binance_crypto_history where operation_datetime < %s and exchange = %s group by asset"
            args = [timestamp, self.PLATFORM]

            result = conn.execute(sql, args).mappings().all()

            for res in result:
                amount = res["amount"]
                asset = res["asset"].lower()

                if amount <= 0.0:
                    continue

                price = self.currency_extractor.get_asset_price(asset, timestamp, scope="BINANCE")
                euro_price = self.currency_extractor.get_asset_price("euro", timestamp)
                portfolio_value += price * amount * euro_price

        return portfolio_value
