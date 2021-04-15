from sqlalchemy.engine import Connection


class BinanceTaxExtractor:

    PLATFORM = "BINANCE"

    def __init__(self, connection: Connection):
        self.connection = connection

    def clean_all_history(self):
        with self.connection.begin() as conn:
            sql = "DELETE FROM `binance_open_positions`;"
            conn.execute(sql, [])
            sql = "DELETE FROM `binance_close_positions`;"
            conn.execute(sql, [])
            sql = "DELETE FROM `purchase_operation_history` WHERE EXCHANGE = %s;"
            conn.execute(sql, [self.PLATFORM])
            sql = "DELETE FROM `sale_operation_history` WHERE EXCHANGE = %s;"
            conn.execute(sql, [self.PLATFORM])


