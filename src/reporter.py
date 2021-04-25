import csv
import logging
from datetime import datetime
from decimal import Decimal
from typing import List

from sqlalchemy.engine import Connection

from exchange.common import AbstractExchangeExtractor, TaxExtractor
from utils import CurrencyExtractor

logger = logging.getLogger("main")

header = ["disposal_datetime",
          "current_portfolio_value",
          "disposal_price",
          "current_total_purchase",
          "current_previous_disposed_purchase",
          "current_balanced_purchase",
          "profit_and_loss"]
white_row = [""*7]


# replace shitty version
def real_round(value: Decimal, digit: int = 2):
    return Decimal(str(round(value, digit)))


def dump_to_csv(tax_report, output):
    with open(output, 'w', newline='') as csvfile:
        disposal_writer = csv.writer(csvfile, delimiter=';')

        disposal_writer.writerow(header)

        disposals = tax_report["disposals"]
        for disposal in disposals:
            disposal_writer.writerow([disposal["disposal_datetime"],
                                      disposal["current_portfolio_value"],
                                      disposal["disposal_price"],
                                      disposal["current_total_purchase"],
                                      disposal["current_previous_disposed_purchase"],
                                      disposal["current_balanced_purchase"],
                                      disposal["profit_and_loss"]])

        disposal_writer.writerow(white_row)

        disposal_writer.writerow(["creation_date", tax_report["creation_date"] ])
        disposal_writer.writerow(["begin_date", tax_report["begin_date"] ])
        disposal_writer.writerow(["end_date", tax_report["end_date"] ])
        disposal_writer.writerow(["compacted", tax_report["compacted"] ])
        disposal_writer.writerow(["global_pnl", tax_report["global_pnl"] ])


class TaxReporter:
    def __init__(self, connection: Connection, currency_extractor: CurrencyExtractor):
        self.connection = connection
        self.currency_extractor = currency_extractor
        self.all_extractor = [cls(self.connection, self.currency_extractor) for cls in TaxExtractor.get_supported_exchange().values()]

    def get_sale_operations(self, begin_date: datetime, end_date: datetime):
        with self.connection.connect() as conn:
            sql = "SELECT * FROM sale_operation_history WHERE sale_datetime >= %s AND sale_datetime <= %s ORDER BY sale_datetime ASC"
            args = [begin_date, end_date]

            result = conn.execute(sql, args).mappings().all()
            return result

    def get_portfolio_value(self, timestamp: datetime):
        portfolio_value = 0.0

        for extractor in self.all_extractor:
            portfolio_value += extractor.get_portfolio_value(timestamp)
        return portfolio_value

    def get_all_purchase_value(self, timestamp: datetime):
        with self.connection.connect() as conn:
            sql = "SELECT SUM(amount_price_euro) FROM purchase_operation_history WHERE purchase_datetime <= %s"
            args = [timestamp]
            result = conn.execute(sql, args).mappings().fetchone()

            return result["SUM(amount_price_euro)"] if result["SUM(amount_price_euro)"] else 0.0

    def generate_tax_disposal_history(self, begin_date: datetime, end_date: datetime, compacted: bool = False):
        logger.info("Generate tax disposal history")
        sale_operations = self.get_sale_operations(begin_date, end_date)

        all_disposals = []
        global_pnl = 0

        for sale in sale_operations:
            disposal = {}

            sale_datetime = sale["sale_datetime"]
            current_portfolio_value = self.get_portfolio_value(sale_datetime)

            disposal["disposal_datetime"] = sale_datetime
            disposal["current_portfolio_value"] = real_round(Decimal(current_portfolio_value))
            disposal["disposal_price"] = real_round(Decimal(sale["amount_price_euro"]))

            all_cash_in = self.get_all_purchase_value(sale_datetime)
            disposal["current_total_purchase"] = real_round(Decimal(all_cash_in))

            if all_disposals:
                previous_disposal = all_disposals[-1]
                current_previous_disposed_purchase = previous_disposal["current_balanced_purchase"] * previous_disposal["disposal_price"] / previous_disposal["current_portfolio_value"]
                disposal["current_previous_disposed_purchase"] = real_round(Decimal(current_previous_disposed_purchase + previous_disposal["current_previous_disposed_purchase"]))
            else:
                disposal["current_previous_disposed_purchase"] = 0

            disposal["current_balanced_purchase"] = real_round(Decimal(disposal["current_total_purchase"] - disposal["current_previous_disposed_purchase"]))
            disposal["profit_and_loss"] = real_round(Decimal(disposal["disposal_price"] - (disposal["current_balanced_purchase"] * disposal["disposal_price"] / disposal["current_portfolio_value"])))

            global_pnl += real_round(Decimal(disposal["profit_and_loss"]))

            all_disposals.append(disposal)

        tax_report = self.save_declaration(begin_date, end_date, all_disposals, compacted, global_pnl)

        return tax_report

    def save_declaration(self, begin_date: datetime, end_date: datetime, all_disposals: List, compacted: bool, global_pnl: float):
        tax_report = {"creation_date": datetime.utcnow(),
                      "begin_date": begin_date,
                      "end_date": end_date,
                      "disposals": all_disposals,
                      "compacted": compacted,
                      "global_pnl": global_pnl}

        with self.connection.begin() as conn:
            sql = "INSERT INTO tax_report (creation_date, begin_date, end_date, compacted, global_pnl)" \
                  "                VALUES (%s,            %s,         %s,       %s,        %s        )"
            result = conn.execute(sql, [tax_report["creation_date"],
                                        tax_report["begin_date"],
                                        tax_report["end_date"],
                                        tax_report["compacted"],
                                        tax_report["global_pnl"]])
            tax_report["id"] = result.lastrowid

            for disposal in all_disposals:
                    sql = "INSERT INTO tax_disposal_history (disposal_datetime, current_portfolio_value, disposal_price, current_total_purchase, current_previous_disposed_purchase, current_balanced_purchase, profit_and_loss, tax_report_id)" \
                          "                          VALUES (%s,                %s,                      %s,             %s,                     %s,                                  %s,                        %s,              %s           )"
                    conn.execute(sql, [disposal["disposal_datetime"],
                                         disposal["current_portfolio_value"],
                                         disposal["disposal_price"],
                                         disposal["current_total_purchase"],
                                         disposal["current_previous_disposed_purchase"],
                                         disposal["current_balanced_purchase"],
                                         disposal["profit_and_loss"],
                                         tax_report["id"]])

        return tax_report




