#!/bin/bash

# download_from_gdrive <FILE_ID> <OUTPUT_FILENAME>
download_from_gdrive() {
    file_id=$1
    file_name=$2 # first stage to get the warning html
    curl -c /tmp/cookies \
    "https://drive.google.com/uc?export=download&id=$file_id" > \
    /tmp/intermezzo.html
    # second stage to extract the download link from html above
    download_link=$(cat /tmp/intermezzo.html | \
    grep -Po 'uc-download-link" [^>]* href="\K[^"]*' | \
    sed 's/\&amp;/\&/g')
    curl -L -b /tmp/cookies \
    "https://drive.google.com$download_link" > $file_name
}

down_small() {
    file_id=$1
    file_name=$2
    if [ ! -f $file_name ];then
        wget --no-check-certificate \
            "https://drive.google.com/uc?export=download&id=${file_id}" \
            -O $file_name
    fi
}

down_large() {
    file_id=$1
    file_name=$2
    if [ ! -f $file_name ];then
        download_from_gdrive $file_id $file_name
    fi
}

# download corpus files
down_small 1avkR7mu2mMnIcynhqEGc0ftnMFfBwHDA corpus/60w_title.txt
down_large 1VwjLCVfByaO5ywBFg_nmjp9RlJBRevCk corpus/60w_token.txt
down_small 1Eveuc2Yd12ehBmM-pmNde4ij1IUXDRMF corpus/60w_tokey.txt

# download word2vector models
down_small 1oJZGdpu2Mm-Ga13H_5qxJeZ-nsHjn-NM w2v/news_d200_e100.w2v
down_large 11h5ZFbVAsqd41YnmM11TSZia1Sz563WM w2v/news_d200_e100.w2v.trainables.syn1neg.npy
down_large 1_GGMH8AuX-UNwiT6mJpF_h-S4YxxztuQ w2v/news_d200_e100.w2v.wv.vectors.npy

# install python requirements
pip3.6 install -r requirements.txt
python3.6 oracle.py
python3.6 plugin/patcher.py submit.csv plugin/patcher.py
