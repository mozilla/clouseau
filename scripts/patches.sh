#!/bin/sh

cd ~/dev/mozilla/mozilla-$1.hg
hg pull -u
hg --config extensions.hgmo=~/dev/mozilla/version-control-tools.hg/hgext/hgmo serve --hgmo &
pid=$!

cd ~/split/clouseau.git.pr
python -m clouseau.guiltypatches -d $2 -o $3 -c $4 -p $5 -t $6 

kill $pid
