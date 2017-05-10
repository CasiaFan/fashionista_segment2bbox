## Format fashionista dataset to VOC type <br>

This project aims to make data in fashionista dataset satisfy VOC standard, where pixel-wise segmentation label to ground-truth bounding box. <br>

When getting these fashion item detection training samples, we could easily fine-tune model like ImageNet and CaffeNet to a powerful detector and classifier in fashion item recognition field! <br>

### Usage:
  **1).** This project is based on work by Kota Yamaguchi et.al ([look here](http://vision.is.tohoku.ac.jp/~kyamagu/research/paperdoll/) or [fork github](https://github.com/kyamagu/paperdoll)).
  So you need to clone this project:<br>
  ```shell
  $ git clone https://github.com/kyamagu/paperdoll.git
  ```

  **2).** Run `matlab` and navigate to paperdoll project root directory, then run `make` to compile necessary binaries.

  **3).** Download [fashionista](http://vision.is.tohoku.ac.jp/~kyamagu/research/paperdoll/fashionista-v0.2.1.tgz) dataset to `./data` directory.

  **4).** Put img_labeled_pixel_and_anno.m into `./data` directory and run it in matlab (check it before using in case you don't want to use the default directories)

  **5).** Put `__init__.py`, `mat2voc_format.py`, `txt2xml.py`, `conversion.sh` scripts into `./data` directory and simply run conversion.sh.
  But for better debugging and personal preference, I suggest you to check these scripts first.

### Requirements:
These scripts are mainly written in python, so the following packages are required for normal using.
- scipy
- numpy
- pandas
- urllib2

### File Tree:
Here is the file tree if you run scripts in default. <br>
```shell
paperdoll/ ___ lib/
            |_ log/
            |_ ...
            |_ make.m
            |_ data/ ___ fashionista_v0.2.mat
                      |_ img_labeled_pixel_and_anno.m**
                      |_ __init__.py
                      |_ conversion.sh
                      |_ mat2voc_format.py
                      |_ txt2xml.py
                      |_ fashionista/ ___ anno/ ___ fashionista.train.list.csv
                                       |         |_ img_urls.csv
                                       |         |_ labels.csv
                                       |
                                       |_ img_pixel/ ___ xx.csv  # image labels in pixel grain
                                       |_ Annotations/ ___ fashionista_xx.xml
                                       |_ JPEGImages/ ___ fashionista_xx.jpg
```