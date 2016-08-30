# clouseau
> Tool to find out some clues after crashes in using data from Socorro, Bugzilla and mercurial 

[![Build Status](https://api.travis-ci.org/mozilla/clouseau.svg?branch=master)](https://travis-ci.org/mozilla/clouseau)
[![codecov.io](https://img.shields.io/codecov/c/github/mozilla/clouseau/master.svg)](https://codecov.io/github/mozilla/clouseau?branch=master)

## Setup

Install the prerequisites via `pip`:
```sh
sudo pip install -r requirements.txt
```

## Usage

### stats
> Get crash rates for a given channel

```sh
python -m clouseau.stats -s 2016-05-01 -e 2016-05-07 -c beta -f csv -o /tmp/fx_beta_data.csv
```

## Running tests

Install test prerequisites via `pip`:
```sh
sudo pip install -r test-requirements.txt
```

Run tests:
```sh
coverage run --source=clouseau -m unittest discover tests/
```

## Credentials

Copy the file config.ini-TEMPLATE into config.ini and fill the token entries.
