import datetime
import logging

from binance.client import Client
from pycoingecko import CoinGeckoAPI
from sqlalchemy import text
from sqlalchemy.engine import Connection
from tenacity import retry, wait_fixed, stop_after_attempt, before_log

from database import BOOT_DB_REQUEST

logger = logging.getLogger("main")

class CurrencyExtractor:

    def __init__(self, connection: Connection, binance_client: Client):
        self.connection = connection
        self.binance_client = binance_client
        self.local_gecko_cache = {}

    def get_gecko_token_name(self, token_name):
        if token_name in self.local_gecko_cache.keys():
            return self.local_gecko_cache[token_name]

        with self.connection.begin() as conn:
            sql = "SELECT * FROM asset_gecko_convert WHERE token_name like %s"
            args = [token_name]

            result = conn.execute(sql, args).mappings().fetchone()

            if result:
                self.local_gecko_cache[token_name] = result["gecko_name"]
                return self.local_gecko_cache[token_name]

        return token_name

    def get_asset_price(self, asset: str, timestamp: datetime, scope="GECKO"):
        if asset.upper() in ["USD", "USDT"]:
            return 1.0

        key = "{}-{}-{}".format(timestamp.strftime("%Y-%m-%d-%H-%M"), scope, asset)

        with self.connection.begin() as conn:
            sql = "SELECT price FROM asset_price_cache WHERE `key` = %s"
            args = [key]

            result = conn.execute(sql, args).mappings().fetchone()

            if result:
                return result["price"]
            else:
                if scope == "GECKO":
                    price = self.query_coingecko_asset_price(asset, timestamp)
                elif scope == "BINANCE":
                    price = self.query_binance_asset_price(asset, timestamp)

                sql = "INSERT INTO asset_price_cache (`key`, price)" \
                      "                       VALUES (%s,  %s   )"
                conn.execute(sql, [key, price])

                return price

    # TODO: coingecko api is limit rated... use binance api instead
    @retry(stop=stop_after_attempt(10), wait=wait_fixed(2), reraise=True)
    def query_coingecko_asset_price(self, asset: str, timestamp: datetime, fiat: str = "usd"):
        asset = self.get_gecko_token_name(asset)
        logger.debug("Requesting price of {} at {}".format(asset, timestamp))

        if asset == "euro":
            return self.query_coingecko_asset_price("tether", timestamp, fiat="eur")
        else:
            cg = CoinGeckoAPI()
            data = cg.get_coin_history_by_id(asset, timestamp.strftime("%d-%m-%Y %H:%M:%S"), localization='false')
            price = data["market_data"]["current_price"][fiat]
            logger.debug("{} is {} at {}".format(asset, price, timestamp))
            return float(price)

    def query_binance_asset_price(self, asset: str, timestamp: datetime, delta_minutes=10):
        asset = asset.upper()+"USDT"
        logger.debug("Requesting price of {} at {}".format(asset, timestamp))
        start_date = timestamp
        end_date = start_date + datetime.timedelta(minutes=delta_minutes)

        klines = self.binance_client.get_historical_klines(asset,
                                                       Client.KLINE_INTERVAL_3MINUTE,
                                                       str(start_date.timestamp()),
                                                       str(end_date.timestamp()))
        if not klines:
            raise Exception("Unable to guess price from {} at {}".format(asset, timestamp))

        return float(float(klines[0][1])+float(klines[0][2])+float(klines[0][3])+float(klines[0][4]))/4


def boot_db(dialect: str, engine: Connection):
    with engine.begin() as conn:
        creation_steps = BOOT_DB_REQUEST[dialect]

        for step in creation_steps:
            conn.execute(step)
