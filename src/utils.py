import datetime
import logging

from pycoingecko import CoinGeckoAPI
from sqlalchemy import text
from sqlalchemy.engine import Connection
from tenacity import retry, wait_fixed, stop_after_attempt, before_log

from database import BOOT_DB_REQUEST

logger = logging.getLogger("main")

GECKO_CONVERT = {"BNB": "binancecoin"}


class CurrencyExtractor:

    def __init__(self, connection: Connection):
        self.connection = connection

    def get_asset_price(self, asset: str, timestamp: datetime):
        if asset.upper() in GECKO_CONVERT:
            asset = GECKO_CONVERT[asset.upper()].lower()

        key = "{}-{}".format(timestamp.strftime("%Y-%m-%d-%H-%M"), asset)

        with self.connection.begin() as conn:
            sql = "SELECT price FROM asset_price_cache WHERE `key` = %s"
            args = [key]

            result = conn.execute(sql, args).mappings().fetchone()

            if result:
                return result["price"]
            else:
                if asset == "euro":
                    price = self.query_coingecko_asset_price("tether", timestamp, fiat="eur")
                else:
                    price = self.query_coingecko_asset_price(asset, timestamp)

                sql = "INSERT INTO asset_price_cache (`key`, price)" \
                      "                       VALUES (%s,  %s   )"
                conn.execute(sql, [key, price])

                return price

    # TODO: coingecko api is limit rated... use binance api instead
    @retry(stop=stop_after_attempt(20), wait=wait_fixed(5), reraise=True)
    def query_coingecko_asset_price(self, asset: str, timestamp: datetime, fiat: str = "usd"):
        cg = CoinGeckoAPI()
        data = cg.get_coin_history_by_id(asset, timestamp.strftime("%d-%m-%Y %H:%M:%S"), localization='false')
        price = data["market_data"]["current_price"][fiat]
        logger.debug("{} is {} at {}".format(asset, price, timestamp))
        return price


def boot_db(dialect: str, engine: Connection):
    with engine.begin() as conn:
        creation_steps = BOOT_DB_REQUEST[dialect]

        for step in creation_steps:
            conn.execute(step)
