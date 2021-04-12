import datetime
import logging

from pycoingecko import CoinGeckoAPI
from sqlalchemy import text
from sqlalchemy.engine import Connection
from tenacity import retry, wait_fixed

from database import BOOT_DB_REQUEST

logger = logging.getLogger("main")


# TODO: coingecko api is limit rated... use binance api instead
@retry(wait=wait_fixed(2))
def query_coingecko_asset_price(asset: str, timestamp: datetime):
    cg = CoinGeckoAPI()
    data = cg.get_coin_history_by_id(asset, timestamp.strftime("%d-%m-%Y %H:%M:%S"), localization='false')
    price = data["market_data"]["current_price"]["usd"]
    logger.debug("{} is {} at {}".format(asset, price, timestamp))
    return price


def boot_db(dialect: str, engine: Connection):
    with engine.begin() as conn:
        creation_steps = BOOT_DB_REQUEST[dialect]

        for step in creation_steps:
            conn.execute(step)

