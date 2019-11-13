#!/bin/bash

if grep Arch /etc/os-release > /dev/null;then
    INSTALL="sudo pacman -S "
elif grep Ubuntu /etc/os-release > /dev/null;then
    INSTALL="sudo apt install "
fi

check_cmd(){
    cmd=$1
    install=$2
    if ! type "$cmd" > /dev/null 2>&1; then
        if [ -z "$INSTALL" ];then
            echo "please install $cmd"; exit
        fi
        echo -ne "\ninstalling $cmd...\n\n"
        eval "$install"
    fi
}

check_cmd curl "$INSTALL curl"
check_cmd wget "$INSTALL wget"
check_cmd python3.6 \
    "if grep Arch /etc/os-release;then
        yay -S python36
    else
        $INSTALL python3.6
    fi"
check_cmd pip3.6 "curl https://bootstrap.pypa.io/get-pip.py | sudo python3.6"

download_from_gdrive() {
    file_id=$1
    file_name=$2 # first stage to get the warning html
    if [ ! -f $file_name ];then
        curl -L -o $file_name -c /tmp/cookies \
        "https://drive.google.com/uc?export=download&id=$file_id"
        if grep "Virus scan warning" $file_name > /dev/null;then
            # second stage to extract the download link from html above
            download_link=$(cat $file_name | \
            grep -Po 'uc-download-link" [^>]* href="\K[^"]*' | \
            sed 's/\&amp;/\&/g')
            curl -L -b /tmp/cookies \
            "https://drive.google.com$download_link" > $file_name
        fi
    fi
}

# download corpus files
download_from_gdrive 1avkR7mu2mMnIcynhqEGc0ftnMFfBwHDA corpus/60w_title.txt
download_from_gdrive 1VwjLCVfByaO5ywBFg_nmjp9RlJBRevCk corpus/60w_token.txt
download_from_gdrive 1Eveuc2Yd12ehBmM-pmNde4ij1IUXDRMF corpus/60w_tokey.txt

# download word2vector models
download_from_gdrive 1oJZGdpu2Mm-Ga13H_5qxJeZ-nsHjn-NM w2v/news_d200_e100.w2v
download_from_gdrive 11h5ZFbVAsqd41YnmM11TSZia1Sz563WM w2v/news_d200_e100.w2v.trainables.syn1neg.npy
download_from_gdrive 1_GGMH8AuX-UNwiT6mJpF_h-S4YxxztuQ w2v/news_d200_e100.w2v.wv.vectors.npy

# install python requirements
pip3.6 install -r requirements.txt

# run the model and patch
python3.6 oracle.py
python3.6 plugin/patcher.py submit.csv plugin/final.patch

echo "submit_patched.csv is the final result!"
