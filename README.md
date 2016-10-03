# clouseau
> Tool to find out some clues after crashes in using data from Socorro, Bugzilla and mercurial.

[![Build Status](https://api.travis-ci.org/mozilla/clouseau.svg?branch=master)](https://travis-ci.org/mozilla/clouseau)
[![codecov.io](https://img.shields.io/codecov/c/github/mozilla/clouseau/master.svg)](https://codecov.io/github/mozilla/clouseau?branch=master)

## Setup

Install the prerequisites via `pip`:
```sh
sudo pip install -r requirements.txt
```

## Usage

### stats
> Get crash rates for a given channel.

```sh
python -m clouseau.stats -s 2016-05-01 -e 2016-05-07 -c beta -f csv -o /tmp/fx_beta_data.csv
```

### DLL & Addon versions
> Get versions of DLLs and addons for a set of crashes.

```sh
python -m clouseau.dll_addon_versions -S "JS::Heap<T>::~Heap<T>" -m "roboform.dll" -a "{22119944-ED35-4ab1-910B-E619EA06A115}" -V 47.0 47.0.1 48.0 48.0.1 48.0.2
```

### Graphics critical errors
> Get frequency of the different possible graphics critical errors.

```sh
python -m clouseau.gfx_critical_errors -c release
```

For a particular signature:
```sh
python -m clouseau.gfx_critical_errors -S "nvd3dum.dll | CD3DDDIDX10::Colorfill" -c release
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
