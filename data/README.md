# Local dataset

The database and its CSV source files are distributed with the official ESILV
student kit and intentionally excluded from this public repository.

Copy these four files from `kit-td1/data/` into this directory before running
the scripts:

- `boutique.sqlite`
- `product.csv`
- `customers.csv`
- `orders.csv`

`manifest.json` is committed so `python verify-data.py` can verify the exact
SHA-256 fingerprints after the local files have been copied. Do not replace or
edit the distributed database.

