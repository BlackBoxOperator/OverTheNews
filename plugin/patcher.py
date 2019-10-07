#!/usr/bin/env python3.6
import csv, sys

def enbuff(qry_idx, news_idcs, plug):
    length = len(news_idcs)
    plug = [r for r in plug if r[0] == qry_idx]
    posl = [r[3] for r in plug if int(r[2]) > 0]
    negl = [r[3] for r in plug if int(r[2]) == 0]
    extl = [r[3] for r in plug if int(r[2]) < 0]
    if plug[1] == 'r': posl, negl = negl, posl
    poss, negs = set(posl), set(negl)
    canl = [idx for idx in news_idcs if idx not in negs and idx not in poss]
    extl = [e for e in extl if e not in poss and e not in negs and e not in canl]
    buffed_news_idcs = (posl + canl + extl)[:length]
    if len(buffed_news_idcs) < length:
        print("not enough candidates in", qry_idx), exit(0)
    return [qry_idx, *buffed_news_idcs]


origin = csv.reader(open(sys.argv[1], encoding="UTF-8"))
plugin = list(csv.reader(open(sys.argv[2], encoding="UTF-8")))
buffed = csv.writer(open("submit_patched.csv", "w", encoding="UTF-8"))

plugin_idcs = set(r[0] for r in plugin)

buffed.writerow(next(origin))

for row in origin:
    query_idx, *news_idcs = row
    if query_idx in plugin_idcs:
        buffed.writerow(enbuff(query_idx, news_idcs, plugin))
    else:
        buffed.writerow(row)

print("記得換 r, s")
