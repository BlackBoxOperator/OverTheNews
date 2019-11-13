#!/bin/bash

if grep Arch /etc/os-release;then
    INSTALL="sudo pacman -S "
elif grep Ubuntu /etc/os-release;then
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

down(){
    case $1 in
        "large") download_from_gdrive $2 $3 ;;
        "small") wget --no-check-certificate \
            "https://drive.google.com/uc?export=download&id=$2" -O $3 ;;
        *)  echo 'invalid option'; exit ;;
    esac
}

# download corpus files
down small 1avkR7mu2mMnIcynhqEGc0ftnMFfBwHDA corpus/60w_title.txt
down large 1VwjLCVfByaO5ywBFg_nmjp9RlJBRevCk corpus/60w_token.txt
down small 1Eveuc2Yd12ehBmM-pmNde4ij1IUXDRMF corpus/60w_tokey.txt

# download word2vector models
down small 1oJZGdpu2Mm-Ga13H_5qxJeZ-nsHjn-NM w2v/news_d200_e100.w2v
down large 11h5ZFbVAsqd41YnmM11TSZia1Sz563WM w2v/news_d200_e100.w2v.trainables.syn1neg.npy
down large 1_GGMH8AuX-UNwiT6mJpF_h-S4YxxztuQ w2v/news_d200_e100.w2v.wv.vectors.npy

# install python requirements
pip3.6 install -r requirements.txt

# run the model and patch
python3.6 oracle.py
python3.6 plugin/patcher.py submit.csv plugin/final.patch

echo "submit_patched.csv is the final result!"
