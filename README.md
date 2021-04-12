# cryptotax

## WORK IN PROGRESS, need test, test, test and re-test

Generateur de cession d'actif numerique pour la declaration d'impots sur le revenue français (CERFA 2086) sur différents exchange

Exchange supporté:
* Etoro (OK)
* Binance (WIP)
* Coinbase (TODO)
* Crypto.com (TODO)

arguments:
* `--boot`                (re)créé la structure de BDD necessaire
* `--load {ETORO,BINANCE,COINBASE,CRYPTOCO}` charge le relevé de compte de l'exchange
* `-i INF, --inf INF`     fichier de relevé de compte
* `-c, --cc`              essaie de regrouper les ventes de meme actifs dans la meme minute
* `--clean {ETORO,BINANCE,COINBASE,CRYPTOCO}` supprime les donnée importé pour l'exchange
* `--generate` genere la liste des cession pour le CERFA 2086 ainsi que la plus/moins value global
* `-o OUTF, --outf OUTF`  fichier de sortie
* `-b BEGIN, --begin BEGIN` date de debut de l'année d'imposition (format 2020-01-01-00-00-00)
* `-e END, --end END`  date de fin de l'année d'imposition (format 2020-01-01-00-00-00)

Note sur le relevé de compte

Pour le moment, les transfert entrant sont considéré comme des achats et les transfert sortant sont ignoré en ce qui concerne la vente

* Etoro: relevé de compte depuis https://accountstat.etoro.com/ (important, il faut TOUT extraire, pas que l'année imposable)
* Binance: historique des trade depuis https://www.binance.com/fr/my/orders/exchange/usertrade (important, il faut TOUT extraire, pas que l'année imposable)
*


Exemple de fontionnement
* créer un virtualenv (python 3.6+) et installer les requirements
* lancer le docker compose fourni (attention au port, modifier le config.py en consequence)
* `python src/main.py --boot`
* `python src/main.py --clean ETORO`
* `python src/main.py --load ETORO --cc --inf eToroAccountStatement_01-01-2019_12-04-2021.xlsx`
* `python src/main.py --generate --outf decla.csv --begin 2020-01-01-00-00-00 --end 2020-12-31-23-59-59`


### CURRENT DEV (branch: develop):

    * test more with various inputs
    * little refactoring on disposal calculus
    * switch coingecko to binance for price guessing when binance active
    * finalize binance implementation
    * support mixing exchange declaration
    * add "instant 0" / "balance 0" validation (avoid selling asset created ex-nihilo....)
    * add replay/idempotency support
    * add correct rounding

### CURRENT LIMITATION

    * no support for interexchange/wallet movement (ex: buy on coinbase, send to binance then sell)  

### NEXT: 

    * add coinbase implementation
    * add cryptoco implementation
    * add sqlite support (no need for external db with compose)
        * i don't like it because it makes debug/profiling harder for me
        * but it is easier to handle for not-dev people...


### Particularité:
* Concernant, l'exchange étant mixte crypto/action, seul les crypto sont importés  

Vous voulez m'aider/remercier/encourager ou vous savez tout simplement pas quoi faire de vos crypto ?

Voici mes adresses de wallet public ;) :

* bitcoin: `1DqSdywm8j2Q4WCya3TmWMGWMK2To1R3RF`
* ethereum: `0xc76955475cb6b839ac45460f05812bec40266dd7`
* binance coin (BEP2): `bnb136ns6lfw4zs5hg4n85vdthaad7hq5m4gtkgf23` memo: `108102908`
* xrp: `rEb8TK3gBgk5auZkwc6sHnwrGVJH8DuaLh` tag: `106481737`
* maiar: `@penpen`
* egld: `erd1a2vpl2kawxdlm6sumymtglsp98vgawm5uphksvkjvrtc2uuu0uss2nyc7t`

