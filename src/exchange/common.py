from sqlalchemy.engine import Connection

from exchange.etoro import EtoroTaxExtractor

SUPPORTED_EXCHANGES = {"ETORO": EtoroTaxExtractor}


class TaxExtractor:

    @staticmethod
    def get_extractor(exchange: str, engine: Connection):
        if exchange not in SUPPORTED_EXCHANGES:
            raise Exception("Unsupported exchange: {}".format(exchange))

        return SUPPORTED_EXCHANGES[exchange](engine)
