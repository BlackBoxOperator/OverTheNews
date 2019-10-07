#!/usr/bin/env python3.6
import sys, csv
from difflib import SequenceMatcher
from pprint import pprint

try:
    queryFile = sys.argv[1]
except Exception as e:
    print("give me queryFile")
    exit(1)

try:
    extFile = sys.argv[2]
except Exception as e:
    print("give me extFile")
    exit(1)


queries = dict([row for row in csv.reader(open(queryFile, 'r', encoding="UTF-8"))][1:])

TDQS = open("TDQS.txt", encoding="UTF-8").read().split()

mapping = dict()

for idx in queries:
    for tdq in TDQS:
        sim = SequenceMatcher(None, queries[idx], tdq).ratio()
        if sim > 0.5:
            print(idx, queries[idx], tdq, sim)
            mapping[tdq] = idx

tdFile = "NTD.csv" # mod here
td = [row for row in csv.reader(open(tdFile, 'r', encoding="UTF-8"))][1:]

patch_list = dict()

patchFile = 'new.patch'
for row in td:
    if row[0] in mapping:
        patch_list.setdefault(mapping[row[0]], []).append((row[-2], row[-1]))

ext = dict([(row[0], row[1:]) for row in csv.reader(open(extFile, 'r', encoding="UTF-8"))][1:])
for query_string in mapping:
    for query in ext:
        if query == query_string:
            exist = [news for news, score in patch_list[mapping[query]]]
            for news in ext[query]:
                if news not in exist:
                    patch_list[mapping[query]].append((news, -1))

with open(patchFile, 'w', newline='', encoding="UTF-8") as csvfile:
    writer = csv.writer(csvfile)
    for idx in patch_list:
        for news, score in patch_list[idx]:
            writer.writerow([idx, 's', score, news])

print("記得換 r, s")
