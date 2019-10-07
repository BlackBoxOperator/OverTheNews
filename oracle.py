#!/usr/bin/env python3.6
# coding: utf-8

from tqdm import *
import numpy as np
import time, jieba, os, json, csv, re, sys

from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
import joblib

from gensim import corpora
from gensim.models import Phrases
from gensim.models import Word2Vec

#from scipy import sparse
#from scipy.sparse import csr_matrix
from auxiliary.bm25 import BM25Transformer
from logger import EpochLogger

###########################
#  modifiable parameters  #
###########################

#size = '10w_'
size = '60w_' # corpus size
retrieve_size = 300
#retrieve_size = 500 # for pagen.py
queryFile = os.path.join('QS_final.csv') # may use QS_2.csv latter
#queryFile = os.path.join('spec.csv') # may use QS_2.csv latter

w2vFile = 'news_d200_e100'
#2vFile = '200w_wiki_60w'
#w2vFile = '200w_wiki_60w_80w'

###########################

dictFile = os.path.join('auxiliary', 'dict.txt')
stopwordFile = os.path.join('auxiliary', 'stopword.txt')

outputFile = os.path.join('submit.csv')

tokenFile = os.path.join('corpus', size + 'token.txt')
tokeyFile = os.path.join('corpus', size + 'tokey.txt')
titleFile = os.path.join('corpus', size + 'title.txt')

w2vPath = os.path.join('w2v', w2vFile + '.w2v')

bm25Cache = os.path.join('cache', size + 'bm25.pkl')
docBM25Cache = os.path.join('cache', size + 'doc_bm25.pkl')
vectorizerCache = os.path.join('cache', size + 'vectorizer.pkl')
docW2VCache = os.path.join('cache', size + w2vFile + '_doc_w2v.pkl')
caches = [bm25Cache, docBM25Cache, vectorizerCache, docW2VCache]

jieba.load_userdict(dictFile)
cut_method = jieba.cut_for_search

def retain_chinese(line):
    return re.compile(r"[^\u4e00-\u9fa5]").sub('', line).replace('臺', '台')

def get_screen_len(line):
    chlen = len(retain_chinese(line))
    return (len(line) - chlen) + chlen * 2

if __name__ == '__main__':

    stopwords = open(stopwordFile, 'r', encoding="UTF-8").read().split()
    queries = dict([row for row in csv.reader(open(queryFile, 'r', encoding="UTF-8"))][1:])

    trim = lambda f: [t.strip() for t in f if t.strip()]
    tokey = trim(open(tokeyFile, encoding="UTF-8").read().split('\n'))

    print("loading w2v model...", end='')
    sys.stdout.flush()
    model = Word2Vec.load(w2vPath)
    print("ok")

    if all([os.path.isfile(cache) for cache in caches]):
        print("loading bm25Cache...", end='');
        sys.stdout.flush()
        bm25 = joblib.load(bm25Cache)
        print("ok")
        print("loading docBM25Cache...", end='')
        sys.stdout.flush()
        doc_bm25 = joblib.load(docBM25Cache)
        print("ok")
        print("loading vectorizerCache...", end='')
        sys.stdout.flush()
        vectorizer = joblib.load(vectorizerCache)
        print("ok")
        print("loading docW2VCache...", end='')
        sys.stdout.flush()
        docWv = joblib.load(docW2VCache)
        print("ok")

    else:

        token = trim(open(tokenFile, encoding="UTF-8").read().split('\n'))

        titles = dict(zip(tokey, open(titleFile, encoding="UTF-8").read().split('\n')))

        # append title to doc
        print("\nappending title to document...\n")

        title_weight = 2
        for i, key in enumerate(tqdm(tokey)):
            title = retain_chinese(titles.get(key, '')).strip()
            if title and title != "Non":
                title_token = ' {}'.format(' '.join([w for w
                    in cut_method(title) if w not in stopwords])) * title_weight
                token[i] += title_token

        if len(token) != len(tokey):
            print('token len sould equal to tokey len')
            exit(0)

        bm25 = BM25Transformer()
        vectorizer = TfidfVectorizer()

        print("\nbuilding corpus vector space...\n")

        doc_tf = vectorizer.fit_transform(tqdm(token))

        print("fitting bm25...", end='');
        sys.stdout.flush()
        bm25.fit(doc_tf)
        print("transforming...", end='');
        doc_bm25 = bm25.transform(doc_tf)
        print("ok")

        print("saving bm25Cache...", end='');
        sys.stdout.flush()
        joblib.dump(bm25, bm25Cache)
        print("ok")
        print("saving docBM25Cache...", end='');
        sys.stdout.flush()
        joblib.dump(doc_bm25, docBM25Cache)
        print("ok")
        print("saving vectorizerCache...", end='');
        sys.stdout.flush()
        joblib.dump(vectorizer, vectorizerCache)
        print("ok")

        print('\ncorpus vector space - ok\n')

        docsTokens = [t.split() for t in token]

        print("making document word vector")

        docWv = np.array([np.sum(model.wv[[t for t in docsTokens[i] if t in model.wv]], axis=0) \
                            for i in tqdm(range(len(docsTokens)))])

        print("saving docW2VCache...", end='');
        sys.stdout.flush()
        joblib.dump(docWv, docW2VCache)
        print("ok")

        #scores = np.zeros((len(queries),len(docsTokens)))

    with open(outputFile, 'w', newline='', encoding="UTF-8") as csvfile:
        writer = csv.writer(csvfile)
        headers = ['Query_Index'] + ['Rank_{:03d}'.format(i) for i in range(1, retrieve_size + 1)]
        writer.writerow(headers)

        for idx, q_id in enumerate(tqdm(queries)):


            query = ' '.join([w for w in cut_method(queries[q_id].replace('臺', '台'))
                                if w not in stopwords])

            # tricky extension
            if '中國學生' in queries[q_id]:
                query += ' 陸生 中生 大陸 學生'
            if '證所' in queries[q_id]:
                query += ' 證交稅 證交'
            if 'ubike' in queries[q_id]:
                query += ' 腳踏車 YouBike' * 5
            if 'Uber' in queries[q_id]:
                query += ' 計程車 Uber Ubr' * 10
            if 'HIV' in queries[q_id]:
                query += ' 愛滋病 愛滋 健保卡 健保 註記 登記' * 20


            qryTokens = [tok for tok in query.split() if tok in model.wv]
            qryWv = np.sum(model.wv[qryTokens], axis=0)

            #scores[idx] = model.wv.cosine_similarities(qryWv, docWv)
            scores = model.wv.cosine_similarities(qryWv, docWv)

            stages = [20, 40, 60, 80, 100]

            init_bar = '[ stage 0/{} ] Query{}: {}'.format(len(stages), idx + 1, query)
            print(init_bar)
            qry_tf = vectorizer.transform([query])
            qry_bm25 = bm25.transform(qry_tf)

            sims = cosine_similarity(qry_bm25, doc_bm25)[0]
            sims += scores
            ranks = [(t, v) for (v, t) in zip(sims, tokey)]
            ranks.sort(key=lambda e: e[-1], reverse=True)

            for stage, fb_n in enumerate(stages):

                print("\033[F[ stage {}/{} ]".format(stage + 1, len(stages)))

                # relavance feedback stage 1
                qry_bm25 = qry_bm25 + \
                        np.sum(doc_bm25[tokey.index(ranks[i][0])] * 0.1 for i in range(fb_n))
                        #np.sum(doc_bm25[tokey.index(ranks[i][0])] * 0.5 for i in range(fb_n))
                        #np.sum(np.fromiter(doc_bm25[tokey.index(ranks[i][0])] * 0.5 for i in range(fb_n))) # for 3.7

                sims = cosine_similarity(qry_bm25, doc_bm25)[0]
                sims += scores
                ranks = [(t, v) for (v, t) in zip(sims, tokey)]
                ranks.sort(key=lambda e: e[-1], reverse=True)

            entry = [q_id] + [e[0] for e in ranks[:retrieve_size]]
            #entry = [queries[q_id]] + [e[0] for e in ranks[:retrieve_size]] # for pagen.py
            writer.writerow(entry)

            print("\033[F" + ' ' * get_screen_len(init_bar))
            print("\033[F" * 3)
