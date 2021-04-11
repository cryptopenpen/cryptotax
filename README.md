# cryptotax

## THIS IS A WORK IN PROGRESS, SEVERAL TESTS ARE STILL REQUIRED

french tax declaration generator for various exchange in order to fill 2086 report

* `--inf is input file (etoro report)`
* `--outf is output file (csv report of disposal declaration)`
* `--cc is option for trying close position compaction`
* `--begin is begin date of year of declaration`
* `--end is end date of year of declaration`

example of running:
* run compose file for mariadb service (tune file if needed, beware of 3307 port)
* install requirements (pip)  
* run main script
 
`python src/main.py --inf etoro_account_statement.xlsx --outf report.csv --cc --begin 2020-01-01-00-00-00 --end 2020-12-31-23-59-59`

If problems, try locate failing step in main.py and tune directly in database

### CURRENT DEV (branch: develop):

    * test more with various inputs
    * add real config file
    * switch coingecko to binance for price guessing when binance active
    * add command step process support
    * finalize binance implementation
    * add support for sqlite3 (get ride of docker mariadb)
    * support mixing exchange 


### NEXT: 

    * add coinbase implementation
    * add cryptoco implementation


### Exchange inforamtions:
* for 2086 filling, we only need crypto asset, legacy stocks are filtered if any (like ETORO)  

You want to help/thank/encourage me or you don't known what to do with your crypto ?

here are my wallets ;) :

* bitcoin: `1DqSdywm8j2Q4WCya3TmWMGWMK2To1R3RF`
* ethereum: `0xc76955475cb6b839ac45460f05812bec40266dd7`
* binance coin (BEP2): `bnb136ns6lfw4zs5hg4n85vdthaad7hq5m4gtkgf23` memo: `108102908`
* xrp: `rEb8TK3gBgk5auZkwc6sHnwrGVJH8DuaLh` tag: `106481737`