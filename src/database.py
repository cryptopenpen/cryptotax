BOOT_DB_REQUEST = {
    "mysql": ["""
CREATE TABLE IF NOT EXISTS `asset_price_cache` (
  `key` varchar(256) NOT NULL,
  `price` float NOT NULL,
  UNIQUE KEY `key` (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""","""
CREATE TABLE IF NOT EXISTS `asset_gecko_convert` (
  `token_name` varchar(256) NOT NULL,
  `gecko_name` varchar(256) NOT NULL,
  UNIQUE KEY `token_name` (`token_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""","""
DROP TABLE IF EXISTS `binance_crypto_history`;
CREATE TABLE `binance_crypto_history` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `operation_datetime` datetime NOT NULL,
  `asset` varchar(256) NOT NULL,
  `amount_asset` float NOT NULL,
  `operation` varchar(256) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""","""
DROP TABLE IF EXISTS `binance_fiat_history`;
CREATE TABLE `binance_fiat_history` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `operation_datetime` datetime NOT NULL,
  `asset` varchar(256) NOT NULL,
  `amount` float NOT NULL,
  `operation` varchar(256) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""","""
DROP TABLE IF EXISTS `binance_raw_operations`;
CREATE TABLE `binance_raw_operations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `operation_datetime` datetime NOT NULL,
  `account` varchar(256) NOT NULL,
  `operation` varchar(256) NOT NULL,
  `coin` varchar(256) NOT NULL,
  `change` float NOT NULL,
  `remark` varchar(256) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `coin` (`coin`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""","""
DROP TABLE IF EXISTS `coinbase_raw_operations`;
CREATE TABLE `coinbase_raw_operations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `operation_datetime` datetime NOT NULL,
  `operation` varchar(256) NOT NULL,
  `coin` varchar(256) NOT NULL,
  `quantity` float NOT NULL,
  `spot_price` float NOT NULL,
  `amount_price` float NOT NULL,
  `note` text NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""","""
DROP TABLE IF EXISTS `etoro_close_positions`;
CREATE TABLE `etoro_close_positions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `position_id` varchar(256) NOT NULL,
  `close_datetime` datetime NOT NULL,
  `asset` varchar(256) NOT NULL,
  `amount_asset` float NOT NULL,
  `amount_price` float NOT NULL,
  `current_asset_price` float NOT NULL,
  `profit_price` float NOT NULL,
  `open_asset_price` float NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""","""
DROP TABLE IF EXISTS `etoro_open_positions`;
CREATE TABLE `etoro_open_positions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `position_id` varchar(256) NOT NULL,
  `open_datetime` datetime NOT NULL,
  `asset` varchar(256) NOT NULL,
  `amount_asset` float DEFAULT NULL,
  `amount_price` float DEFAULT NULL,
  `current_asset_price` float DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `position_id` (`position_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""","""
DROP TABLE IF EXISTS `purchase_operation_history`;
CREATE TABLE `purchase_operation_history` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `purchase_datetime` datetime NOT NULL,
  `asset` varchar(256) NOT NULL,
  `amount_asset` float NOT NULL,
  `amount_price_usd` float NOT NULL,
  `amount_price_euro` float NOT NULL,
  `current_asset_price_usd` float NOT NULL,
  `current_asset_price_euro` float NOT NULL,
  `exchange` varchar(256) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""","""
DROP TABLE IF EXISTS `sale_operation_history`;
CREATE TABLE `sale_operation_history` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sale_datetime` datetime NOT NULL,
  `asset` varchar(256) NOT NULL,
  `amount_asset` float NOT NULL,
  `amount_price_usd` float NOT NULL,
  `amount_price_euro` float NOT NULL,
  `current_asset_price_usd` float NOT NULL,
  `current_asset_price_euro` float NOT NULL,
  `exchange` varchar(256) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""","""
DROP TABLE IF EXISTS `tax_disposal_history`;
CREATE TABLE `tax_disposal_history` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `disposal_datetime` datetime NOT NULL,
  `current_portfolio_value` float NOT NULL,
  `disposal_price` float NOT NULL,
  `current_total_purchase` float NOT NULL,
  `current_previous_disposed_purchase` float NOT NULL,
  `current_balanced_purchase` float NOT NULL,
  `profit_and_loss` float NOT NULL,
  `tax_report_id` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""","""
DROP TABLE IF EXISTS `tax_report`;
CREATE TABLE `tax_report` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `creation_date` datetime NOT NULL,
  `begin_date` datetime DEFAULT NULL,
  `end_date` datetime DEFAULT NULL,
  `compacted` tinyint(1) NOT NULL,
  `global_pnl` float NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""]
}
