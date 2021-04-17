import datetime
import logging

from binance.client import Client
from pycoingecko import CoinGeckoAPI
from sqlalchemy import text
from sqlalchemy.engine import Connection
from tenacity import retry, wait_fixed, stop_after_attempt, before_log

from database import BOOT_DB_REQUEST

logger = logging.getLogger("main")

ASSET_RENAME = {"BTC": "bitcoin",
                "XLM": "stellar",
                "ADA": "cardano",
                "EUR": "euro"}

class CurrencyExtractor:

    def __init__(self, connection: Connection, binance_client: Client):
        self.connection = connection
        self.binance_client = binance_client

    def get_asset_price(self, asset: str, timestamp: datetime):
        key = "{}-{}".format(timestamp.strftime("%Y-%m-%d-%H-%M"), asset)

        with self.connection.begin() as conn:
            sql = "SELECT price FROM asset_price_cache WHERE `key` = %s"
            args = [key]

            result = conn.execute(sql, args).mappings().fetchone()

            if result:
                return result["price"]
            else:
                try:
                    price = self.query_binance_asset_price(asset.upper()+"USDT", timestamp)
                except:
                    price = self.query_coingecko_asset_price(ASSET_RENAME[asset.upper()] if asset.upper() in ASSET_RENAME.keys() else asset.lower(), timestamp)

                sql = "INSERT INTO asset_price_cache (`key`, price)" \
                      "                       VALUES (%s,  %s   )"
                conn.execute(sql, [key, price])

                return price

    # TODO: coingecko api is limit rated... use binance api instead
    @retry(stop=stop_after_attempt(20), wait=wait_fixed(5), reraise=True)
    def query_coingecko_asset_price(self, asset: str, timestamp: datetime, fiat: str = "usd"):
        if asset.upper() in ["EURO", "EUR"]:
            asset = "tether"
            fiat = "eur"

        logger.debug("Query for price of {} at {}".format(asset, timestamp))
        cg = CoinGeckoAPI()
        data = cg.get_coin_history_by_id(asset, timestamp.strftime("%d-%m-%Y %H:%M:%S"), localization='false')
        price = data["market_data"]["current_price"][fiat]
        logger.debug("{} is {} at {}".format(asset, price, timestamp))
        if asset.upper() in ["EURO", "EUR"]:
            price = 1.0/float(price)
        return price

    def query_binance_asset_price(self, asset: str, timestamp: datetime, delta_minutes=10):
        logger.debug("Query for price of {} at {}".format(asset, timestamp))
        start_date = timestamp
        end_date = start_date + datetime.timedelta(minutes=delta_minutes)

        klines = self.binance_client.get_historical_klines(asset,
                                                       Client.KLINE_INTERVAL_3MINUTE,
                                                       str(start_date.timestamp()),
                                                       str(end_date.timestamp()))
        if not klines:
            raise Exception("Unable to guess price from {} at {}".format(asset, timestamp))

        price = (float(klines[0][1])+float(klines[0][2])+float(klines[0][3])+float(klines[0][4]))/4.0
        logger.debug("{} is {} at {}".format(asset, price, timestamp))
        return price


def boot_db(dialect: str, engine: Connection):
    with engine.begin() as conn:
        creation_steps = BOOT_DB_REQUEST[dialect]

        for step in creation_steps:
            conn.execute(step)
