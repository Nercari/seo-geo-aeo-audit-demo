#!/usr/bin/env bash
# Sends every page to the public Schema.org validator and counts objects/errors.
cd "$(dirname "$0")/.."; mkdir -p measurements/schema
for v in before after; do for f in demo/site_$v/*.html; do n=$(basename $f .html)
 curl -s -m 30 -X POST https://validator.schema.org/validate --data-urlencode "html@$f" | tail -c +5 > measurements/schema/$v-$n.json; done; done
python3 - <<'P'
import json,glob,collections
tot=collections.defaultdict(lambda:[0,0,set()])
def walk(o,a):
    if isinstance(o,dict):
        a[1]+=len(o.get("errors",[]) or [])
        for t in o.get("types",[]) or []: a[2].add(t.get("value"))
        for v in o.values(): walk(v,a)
    elif isinstance(o,list):
        for v in o: walk(v,a)
for f in sorted(glob.glob("measurements/schema/*.json")):
    v=f.split("/")[-1].split("-")[0]; d=json.loads(open(f).read())
    tot[v][0]+=d.get("numObjects",0); walk(d.get("tripleGroups",[]),tot[v])
for v in ("before","after"): print(f"{v}: {tot[v][0]} schema objects, {tot[v][1]} errors, types={sorted(tot[v][2])}")
P
