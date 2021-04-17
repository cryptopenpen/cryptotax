import logging
from datetime import datetime

from sqlalchemy.engine import Connection

from utils import CurrencyExtractor

logger = logging.getLogger("main")


class TaxExtractor:

    @staticmethod
    def get_supported_exchange():
        from exchange.binance import BinanceTaxExtractor
        from exchange.etoro import EtoroTaxExtractor

        return {"ETORO": EtoroTaxExtractor,
                "BINANCE": BinanceTaxExtractor}

    @staticmethod
    def get_extractor(exchange: str, engine: Connection, currency_extractor: CurrencyExtractor):
        extractors = TaxExtractor.get_supported_exchange()
        if exchange not in extractors:
            raise Exception("Unsupported exchange: {}".format(exchange))

        return extractors[exchange](engine, currency_extractor)


class AbstractExchangeExtractor:

    PLATFORM = "NONE"

    def __init__(self, connection: Connection, currency_extractor: CurrencyExtractor):
        self.connection = connection
        self.currency_extractor = currency_extractor

    def clean_all_history(self):
        logger.info("Delete all {} history".format(self.PLATFORM))
        with self.connection.begin() as conn:
            sql = "DELETE FROM `purchase_operation_history` WHERE EXCHANGE = %s;"
            conn.execute(sql, [self.PLATFORM])
            sql = "DELETE FROM `sale_operation_history` WHERE EXCHANGE = %s;"
            conn.execute(sql, [self.PLATFORM])

    def load_account_statement(self, filepath):
        pass

    def process_load(self):
        pass

    def save_purchase_operation(self, purchase_operation):
        with self.connection.begin() as conn:
            sql = "INSERT INTO purchase_operation_history (purchase_datetime, asset, amount_asset, amount_price_usd," \
                  "                                        amount_price_euro, current_asset_price_usd," \
                  "                                        current_asset_price_euro, exchange)" \
                  "                                VALUES (%s,                %s,    %s,           %s," \
                  "                                        %s,                %s," \
                  "                                        %s,                       %s      )"
            conn.execute(sql, [purchase_operation["purchase_datetime"],
                               purchase_operation["asset"],
                               purchase_operation["amount_asset"],
                               purchase_operation["amount_price_usd"],
                               purchase_operation["amount_price_euro"],
                               purchase_operation["current_asset_price_usd"],
                               purchase_operation["current_asset_price_euro"],
                               self.PLATFORM])

    def save_sale_operation(self, sale_operation):
        with self.connection.begin() as conn:
            sql = "INSERT INTO sale_operation_history (sale_datetime, asset, amount_asset, amount_price_usd, amount_price_euro, current_asset_price_usd, current_asset_price_euro, exchange)" \
                  "                            VALUES (%s,            %s,    %s,           %s,               %s,                %s,                      %s,                       %s      )"
            conn.execute(sql, [sale_operation["sale_datetime"],
                               sale_operation["asset"],
                               sale_operation["amount_asset"],
                               sale_operation["amount_price_usd"],
                               sale_operation["amount_price_euro"],
                               sale_operation["current_asset_price_usd"],
                               sale_operation["current_asset_price_euro"],
                               self.PLATFORM])

    def generate_purchase_operation_history(self):
        pass

    def generate_sale_operation_history(self, try_compact: bool = False):
        pass

    def get_portfolio_value(self, timestamp: datetime):
        raise Exception("not implemented")
