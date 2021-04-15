from sqlalchemy.engine import Connection

from exchange.binance import BinanceTaxExtractor
from exchange.etoro import EtoroTaxExtractor
from utils import CurrencyExtractor

SUPPORTED_EXCHANGES = {"ETORO": EtoroTaxExtractor,
                       "BINANCE": BinanceTaxExtractor}


class TaxExtractor:

    @staticmethod
    def get_extractor(exchange: str, engine: Connection, currency_extractor: CurrencyExtractor):
        if exchange not in SUPPORTED_EXCHANGES:
            raise Exception("Unsupported exchange: {}".format(exchange))

        return SUPPORTED_EXCHANGES[exchange](engine, currency_extractor)
