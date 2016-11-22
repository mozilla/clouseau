#!/bin/sh

cd $1/hg/mozilla-$2.hg
hg pull -u
hg --config extensions.hgmo=$1/hg/version-control-tools.hg/hgext/hgmo serve --hgmo &
pid=$!

cd $1/git/clouseau
python -m clouseau.guiltypatches -d $3 -o $4 -c $5 -t $6 -l

kill $pid
