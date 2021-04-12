import logging
from datetime import datetime
from typing import List

from openpyxl import load_workbook
from pycoingecko import CoinGeckoAPI
from sqlalchemy.engine import Connection

from utils import query_coingecko_asset_price

CRYPTO_PAIR = {
    "BITCOIN": "BTC/USD",
    "ETHEREUM": "ETH/USD",
    "LITECOIN": "LTC/USD",
    "TRON": "TRX/USD",
    "CARDANO": "ADA/USD",
    "NEO": "NEO/USD",
    "STELLAR": "XLM/USD",
    "TEZOS": "XTZ/USD",
    "MIOTA": "IOTA/USD",
    "RIPPLE": "XRP/USD",
    "DASH": "DASH/USD",
    "BNB": "BNB/USD",
}

PAIR_CRYPTO = {v: k for k,v in CRYPTO_PAIR.items()}

GECKO_CONVERT = {"BNB": "binancecoin"}

FIELD_NAME_TYPE = 2
FIELD_TYPE_OPEN_POSITION = "Open Position"

FIELD_NAME_DETAILS = 3

FIELD_NAME_ACTION = 1

logger = logging.getLogger("main")


class EtoroTaxExtractor:

    PLATFORM = "ETORO"

    def __init__(self, connection: Connection):
        self.connection = connection
        self.all_position_operations = None
        self.closed_positions = None

    def load_account_statement(self, filepath):
        wb = load_workbook(filename = filepath)

        transactions_report = wb["Transactions Report"]
        closed_positions = wb["Closed Positions"]

        self.all_position_operations = transactions_report
        self.closed_positions = closed_positions

    def clean_all_history(self):
        with self.connection.begin() as conn:
            sql = "DELETE FROM `etoro_open_positions`;"
            conn.execute(sql, [])
            sql = "DELETE FROM `etoro_close_positions`;"
            conn.execute(sql, [])
            sql = "DELETE FROM `purchase_operation_history` WHERE EXCHANGE = %s;"
            conn.execute(sql, [self.PLATFORM])
            sql = "DELETE FROM `sale_operation_history` WHERE EXCHANGE = %s;"
            conn.execute(sql, [self.PLATFORM])

    def extract_purchase_history(self):
        with self.connection.begin() as conn:

            for row in self.all_position_operations.rows:
                # skip anything other than "Open Positions"
                if not row[FIELD_NAME_TYPE].internal_value == FIELD_TYPE_OPEN_POSITION:
                    continue

                # skip not crypto
                if row[FIELD_NAME_DETAILS].internal_value.upper() not in CRYPTO_PAIR.values():
                    continue

                position = {
                    "position_id": row[4].internal_value,
                    "open_datetime": datetime.fromisoformat(row[0].internal_value),
                    "asset": row[3].internal_value,
                    "amount_asset": None,
                    "amount_price": float(row[5].internal_value),
                    "current_asset_price": None
                }

                sql = "INSERT INTO etoro_open_positions (position_id, open_datetime, asset, amount_price)" \
                      "                          VALUES (%s,          %s,            %s,    %s          )"
                conn.execute(sql, [position["position_id"],
                                   position["open_datetime"],
                                   position["asset"],
                                   position["amount_price"]])

    def extract_sale_history(self):
        supported_action = ["BUY "+asset for asset in CRYPTO_PAIR]

        with self.connection.begin() as conn:

            for row in self.closed_positions.rows:
                # skip not crypto
                if row[FIELD_NAME_ACTION].internal_value.upper() not in supported_action:
                    continue

                position = {
                    "position_id": row[0].internal_value,
                    "close_datetime": datetime.strptime(row[10].internal_value, "%d/%m/%Y %H:%M"),
                    "profit_price": float(row[8].internal_value.replace(",", ".")),
                    "open_asset_price": float(row[5].internal_value.replace(",", ".")),
                    "current_asset_price": float(row[6].internal_value.replace(",", ".")),
                    "amount_asset": float(row[4].internal_value.replace(",", ".")),
                    "amount_price": float(row[3].internal_value.replace(",", ".")),
                }

                sql = "INSERT INTO etoro_close_positions (position_id, close_datetime, asset, amount_asset, amount_price, current_asset_price, profit_price, open_asset_price)" \
                      "                           VALUES (%s,          %s,             %s,    %s,           %s,           %s,                  %s,           %s              )"
                conn.execute(sql, [position["position_id"],
                                   position["close_datetime"],
                                   row[FIELD_NAME_ACTION].internal_value[4:].lower(),
                                   position["amount_asset"],
                                   position["amount_price"],
                                   position["current_asset_price"],
                                   position["profit_price"],
                                   position["open_asset_price"]])

    def get_all_open_positions(self):
        with self.connection.connect() as conn:
            sql = "SELECT * FROM etoro_open_positions"
            args = []

            result = conn.execute(sql, args).mappings().all()
            return result

    def get_all_close_positions(self):
        with self.connection.connect() as conn:
            sql = "SELECT * FROM etoro_close_positions"
            args = []

            result = conn.execute(sql, args).mappings().all()

            return result

    def get_close_position(self, position_id: str):
        with self.connection.connect() as conn:
            sql = "SELECT * FROM etoro_close_positions WHERE position_id = %s"
            args = [position_id]

            result = conn.execute(sql, args).mappings().fetchone()

            return result

    def save_open_position(self, open_position):
        with self.connection.begin() as conn:
            sql = "UPDATE etoro_open_positions " \
                  "SET " \
                  " asset = %s, " \
                  " amount_asset = %s, " \
                  " amount_price = %s, " \
                  " current_asset_price = %s " \
                  "WHERE " \
                  " position_id = %s"
            conn.execute(sql, [open_position["asset"],
                               open_position["amount_asset"],
                               open_position["amount_price"],
                               open_position["current_asset_price"],
                               open_position["position_id"]])

    def consolidate_history(self):
        all_open_positions = self.get_all_open_positions()

        for open_position in all_open_positions:
            close_position = self.get_close_position(open_position["position_id"])

            position = dict(open_position)
            position["asset"] = PAIR_CRYPTO[position["asset"].upper()].lower()
            if close_position:
                position["amount_asset"] = close_position["amount_asset"]
                position["current_asset_price"] = close_position["open_asset_price"]
            else:
                logger.warning("Unknown price {}....".format(position))
                current_asset_price = self.get_asset_price(position["asset"], position["open_datetime"])
                position["amount_asset"] = position["amount_price"]/current_asset_price
                position["current_asset_price"] = current_asset_price

            self.save_open_position(position)

    def save_purchase_operation(self, purchase_operation):
        with self.connection.begin() as conn:
            sql = "INSERT INTO purchase_operation_history (purchase_datetime, asset, amount_asset, amount_price, current_asset_price, exchange)" \
                        "                          VALUES (%s,                %s,    %s,           %s,           %s                 , %s      )"
            conn.execute(sql, [purchase_operation["purchase_datetime"],
                               purchase_operation["asset"],
                               purchase_operation["amount_asset"],
                               purchase_operation["amount_price"],
                               purchase_operation["current_asset_price"],
                               self.PLATFORM])

    def save_sale_operation(self, sale_operation):
        with self.connection.begin() as conn:
            sql = "INSERT INTO sale_operation_history (sale_datetime, asset, amount_asset, amount_price, current_asset_price, exchange)" \
                  "                            VALUES (%s,            %s,    %s,           %s,           %s                 , %s      )"
            conn.execute(sql, [sale_operation["sale_datetime"],
                               sale_operation["asset"],
                               sale_operation["amount_asset"],
                               sale_operation["amount_price"],
                               sale_operation["current_asset_price"],
                               self.PLATFORM])

    def generate_purchase_operation_history(self):
        all_open_positions = self.get_all_open_positions()

        for open_position in all_open_positions:
            purchase_operation = {
                "purchase_datetime": open_position["open_datetime"],
                "asset": open_position["asset"],
                "amount_asset": open_position["amount_asset"],
                "amount_price": open_position["amount_price"],
                "current_asset_price": open_position["current_asset_price"],
            }

            self.save_purchase_operation(purchase_operation)


    def generate_sale_operation_history(self, try_compact: bool = False):
        all_close_positions = self.get_all_close_positions()

        if try_compact:
            compacted_sale_op = {}
            for close_op in all_close_positions:
                key = close_op["close_datetime"].strftime("%d-%m-%Y-%H-%M")+"-"+close_op["asset"]

                if key in compacted_sale_op.keys():
                    compacted_sale_op[key]["amount_asset"] += close_op["amount_asset"]
                    compacted_sale_op[key]["amount_price"] += close_op["amount_price"] + close_op["profit_price"]
                else:
                    compacted_sale_op[key] = {
                        "sale_datetime": close_op["close_datetime"],
                        "asset": close_op["asset"],
                        "amount_asset": close_op["amount_asset"],
                        "amount_price": close_op["amount_price"] + close_op["profit_price"],
                        "current_asset_price": close_op["current_asset_price"],
                    }

            for op in compacted_sale_op.values():
                self.save_sale_operation(op)
        else:
            for close_position in all_close_positions:
                sale_operation = {
                    "sale_datetime": close_position["close_datetime"],
                    "asset": close_position["asset"],
                    "amount_asset": close_position["amount_asset"],
                    "amount_price": close_position["amount_price"] + close_position["profit_price"],
                    "current_asset_price": close_position["current_asset_price"],
                }

                self.save_sale_operation(sale_operation)

    def get_asset_price(self, asset: str, timestamp: datetime):
        if asset.upper() in GECKO_CONVERT:
            asset = GECKO_CONVERT[asset.upper()].lower()

        return query_coingecko_asset_price(asset, timestamp)

