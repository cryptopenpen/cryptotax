# cryptotax

## WARNING: WORK IN PROGRESS, need test, test, test and re-test

Generateur de cession d'actif numerique pour la declaration d'impots sur le revenue français (CERFA 2086) sur différents exchange

note: les calcul intermediaire sont fait en USD mais l'output est en euro

Exchange supporté:
* Etoro (~OK et a priori terminé, juste besoin de plus de gens qui test)
* Binance (BETA)
   * need more test/retour
   * probleme de somme negative (arrondi ? digit limit d'export binance ?)

* Coinbase (TODO)
* Crypto.com (TODO)


### Particularité:
* Etoro:
  * relevé de compte depuis https://accountstat.etoro.com/ (important, il faut TOUT extraire, pas que l'année imposable)
  * l'exchange étant mixte crypto/action, seul les crypto sont importé
  * les transfers de crypto sont considéré comme une vente (pas de support donc...)  
* Binance
  * relevé complet depuis https://www.binance.com/fr/my/wallet/history/deposit-crypto (important, il faut TOUT extraire, pas que l'année imposable)
  * seul le compte spot est pris en compte (cela inclue le earning, mais pas le margin, futur etc...)
  * seul l'EURO est supporté comme cashin/cashout  
  * les transfert entrant de crypto sont compris comme une augmentation de valeur du portefeuille
  * les transfert sortant de crypto sont compris comme une diminution de valeur du portefeuille

### Fonctionnement

Etant donnée que binance est utilisé pour connaitre le prix d'un asset, un compte binance est necessaire quelque soit l'exchange chargé !

En cas d'asset inconnu, ajouter une translation dans le dictionnaire ASSET_RENAME ou ajotuer l'entrée a la main dans la table de cache 

arguments:
* `--config {yaml file}` charge le fichier de configuration (voir config.sample.yaml) 
* `--boot`                (re)créé la structure de BDD necessaire
* `--exchange {ETORO,BINANCE,COINBASE,CRYPTOCO}` specifie l'exchange courant
* `--load`  charge le relevé de compte de l'exchange
* `-i INF, --inf INF`     fichier de relevé de compte
* `-c, --cc`              essaie de regrouper les ventes de meme actifs dans la meme minute
* `--clean` supprime les donnée importé pour l'exchange
* `--generate` genere la liste des cession pour le CERFA 2086 ainsi que la plus/moins value global
* `-o OUTF, --outf OUTF`  fichier de sortie
* `-b BEGIN, --begin BEGIN` date de debut de l'année d'imposition (format 2020-01-01-00-00-00)
* `-e END, --end END`  date de fin de l'année d'imposition (format 2020-01-01-00-00-00)


Exemple de fontionnement
* créer un virtualenv (python 3.6+) et installer les requirements
* lancer le docker compose fourni (attention au port, modifier le config.py en consequence)
* `python src/main.py --config config.yaml --boot`
* `python src/main.py --config config.yaml --exchange ETORO --clean`
* `python src/main.py --config config.yaml --exchange ETORO --load --cc --inf eToroAccountStatement_01-01-2019_12-04-2021.xlsx`
* `python src/main.py --config config.yaml --generate --outf decla.csv --begin 2020-01-01-00-00-00 --end 2020-12-31-23-59-59`


### CURRENT DEV (branch: develop):

    * test more with various inputs
    * little refactoring on disposal calculus
    * add "instant 0" / "balance 0" validation (avoid selling asset created ex-nihilo....)
    * add replay/idempotency support

### CURRENT LIMITATION

    * no support for interexchange/wallet movement (ex: buy on coinbase, send to binance then sell)  

### NEXT: 

    * add coinbase implementation
    * add cryptoco implementation
    * add interexchange transfert support
    * add sqlite support (no need for external db with compose)
        * i don't like it because it makes debug/profiling harder for me
        * but it is easier to handle for not-dev people...


Vous voulez m'aider/remercier/encourager ou vous savez tout simplement pas quoi faire de vos crypto ?

Voici mes adresses de wallet public ;) :

* bitcoin: `1DqSdywm8j2Q4WCya3TmWMGWMK2To1R3RF`
* ethereum: `0xc76955475cb6b839ac45460f05812bec40266dd7`
* binance coin (BEP2): `bnb136ns6lfw4zs5hg4n85vdthaad7hq5m4gtkgf23` memo: `108102908`
* xrp: `rEb8TK3gBgk5auZkwc6sHnwrGVJH8DuaLh` tag: `106481737`
* maiar: `@penpen`
* egld: `erd1a2vpl2kawxdlm6sumymtglsp98vgawm5uphksvkjvrtc2uuu0uss2nyc7t`

