# -*- coding:utf-8 -*-
__author__ = "arkenstone"

import argparse
import os
import scipy.io
import logging
import numpy as np
import pandas as pd
from txt2xml import writeXml
from scipy.ndimage.measurements import find_objects
from functools import partial


paperdoll_mat = '/home/arkenstone/Downloads/apparel_dataset/paperdoll/data/paperdoll_dataset.mat'
# fashionista_mat = '/home/arkenstone/Downloads/apparel_dataset/paperdoll/data/fashionista_v0.2.mat'
fashion_root_dir = '/home/arkenstone/Downloads/apparel_dataset/paperdoll/data/fashionista'
fashion_labels = fashion_root_dir + '/anno/labels.csv'
fashion_pixel_label_dir = fashion_root_dir + '/img_pixel'
fashion_url = fashion_root_dir + '/anno/img_urls.csv'

# set logging format
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s %(name)s - %(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def retrieve_paperdoll_info(outdir, outfile="img_anno.txt", return_info=False):
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    mat = scipy.io.loadmat(paperdoll_mat)
    # label list
    labels = np.asarray([item[0] for item in mat["labels"][0]])
    # restore image id, url, and tags into array
    img_count = len(mat["samples"][0])
    samples = np.array([])
    if os.path.isfile(outdir+"/"+outfile):
        logger.warning("Annotation file is exists! If reinitialize one, delete if manually first!")
        return
    with open(outdir+"/"+outfile, mode="wb") as f:
        f.write("id,url,tags\n")
        for index in range(img_count):
            # img unique id (list)
            id = mat["samples"][0][index][0].flatten()[0]
            # img download url (list)
            url = mat["samples"][0][index][1][0]
            # tags (list)
            tags_ids = mat["samples"][0][index][3][0].tolist()
            tags = [labels[i-1] for i in tags_ids]
            samples = np.append(samples, np.array([[id], [url], tags]))
            line = "{},{},{}\n".format(id, url, " ".join(tags))
            f.write(line)
        f.close()
    samples = samples.reshape(img_count, 3)
    if return_info:
        return samples
    else:
        return


def divide_shoe_proposal(prop, shoe_label_index, xmin=None, ymin=None):
    # input shoe proposal pixel matrix return coordinate list of each shoe
    prop_width, prop_height = prop.shape[1], prop.shape[0]
    if not xmin:
        xmin, ymin = 0, 0
    # check vertical divide line
    vertical_line = False
    for i in range(prop_width):
        if not (shoe_label_index in set(prop[:, i])):
            shoe_prop1 = prop[:, :i]
            shoe_prop2 = prop[:, i:]
            xmin_new = xmin + i
            ymin_new = ymin
            vertical_line = True
            break
    # check horizontal divide line
    if not vertical_line:
        horizontal_line = False
        for i in range(prop_height):
            if not (shoe_label_index in set(prop[i])):
                shoe_prop1 = prop[:i]
                shoe_prop2 = prop[i:]
                ymin_new = ymin + i
                xmin_new = xmin
                horizontal_line = True
                break
        if not horizontal_line:
            logger.warning("Only one shoe marked or two shoes are overlapped! Stop separating!")
            return [xmin, ymin, xmin+prop_width, ymin+prop_height]
    shoe_loc1 = find_objects(shoe_prop1)
    xmin1 = xmin + shoe_loc1[shoe_label_index-1][0].start
    xmax1 = xmin + shoe_loc1[shoe_label_index-1][0].stop - 1
    ymin1 = ymin + shoe_loc1[shoe_label_index-1][1].start
    ymax1 = ymin + shoe_loc1[shoe_label_index-1][1].stop - 1
    shoe_loc2 = find_objects(shoe_prop2)
    xmin2 = xmin_new + shoe_loc2[shoe_label_index-1][0].start
    xmax2 = xmin_new + shoe_loc2[shoe_label_index-1][0].stop - 1
    ymin2 = ymin_new + shoe_loc2[shoe_label_index-1][1].start
    ymax2 = ymin_new + shoe_loc2[shoe_label_index-1][1].stop - 1
    return [xmin1, ymin1, xmax1, ymax1, xmin2, ymin2, xmax2, ymax2]


def fashionista2VOC_format(pixel_file, outdir='.', prefix='fashionista_'):
    img_index = os.path.splitext(os.path.basename(pixel_file))[0]
    outfile = outdir + '/' + prefix + str(img_index) + '.xml'
    img_name = prefix + str(img_index) + '.jpg'
    # skip existing file
    if os.path.isfile(outfile):
        return
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    # load labels
    df_labels = pd.read_csv(fashion_labels)
    labels = df_labels["label"].tolist()
    # load image pixel labels
    if os.path.isfile(pixel_file):
        pixels = np.asarray(pd.read_csv(pixel_file))
        width = pixels.shape[1]
        height = pixels.shape[0]
        object_locs = find_objects(pixels)  # return slice object
        object_coord = []
        for index, loc in enumerate(object_locs):
            if not loc:
                continue
            object_prop = pixels[loc]
            prop_label_index = index + 1
            ymin = loc[0].start
            ymax = loc[0].stop - 1
            xmin = loc[1].start
            xmax = loc[1].stop - 1
            # count labels and use most one as proposal label
            # remove null label, skin and hair
            # label_list = [i for i in object_prop.flatten().tolist()
            #               if labels[i] != 'null' and labels[i] != 'skin' and labels != 'hair']
            # prop_label_index = max(set(label_list), key=label_list.count)
            # consider shoe label separately for its isolated two parts
            if labels[prop_label_index] == 'shoes':
                # divide shoe proposal by null block
                coord = divide_shoe_proposal(object_prop, prop_label_index, xmin, ymin)
                if len(coord) == 4:
                    coord.insert(0, 'shoes')
                else:
                    coord.insert(0, 'shoes')
                    coord.insert(5, 'shoes')
            else:
                coord = [labels[prop_label_index], xmin, ymin, xmax, ymax]
            object_coord += coord
        # write to xml
        writeXml(outdir, img_name, width, height, object_coord, outfile)


def download_img(outdir, processes=10, anno_file=None, urls=[], ids=[],
                 id_header="id", url_header="url", img_type=".jpg", prefix='fashionista_'):
    from pathos.multiprocessing import ProcessingPool as Pool
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    # ir urls is specified, use it first
    import urllib2

    def _download_img(url, outfile, wait_time=5):
        if os.path.isfile(outfile):
            return
        # add header
        hdr = {'User-Agent': 'Mozilla/5.0'}
        logger.info("Downloading: {} ...".format(url))
        request = urllib2.Request(url, headers=hdr)
        try:
            response = urllib2.urlopen(request, timeout=wait_time).read()
        except urllib2.HTTPError, e:
            logger.error("Downloading Error: HTML page not found!\n{}", e.message)
            return
        # skip existing file
        if not len(response):
            logger.warning("Timeout: {}".format(url))
        else:
            logger.info("Done: {}".format(url))
        with open(outfile, "wb") as of:
            of.write(response)

    if not (anno_file or len(urls)):
        logger.error("Annotation file or urls must be provided!")
        exit(-1)
    if not len(urls):
        try:
            df = pd.read_csv(anno_file)
            urls = df[url_header].tolist()
        except:
            logger.error("anno_file is not .csv type or 'url' is not in its header!")
            exit(-1)
    if not len(ids):
        ids = df[id_header].tolist()
    outfiles = [outdir + "/" + prefix + str(i) + img_type for i in ids]
    pool = Pool(processes=processes)
    pool.map(_download_img, urls, outfiles)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose mode')
    parser.add_argument('--outdir', '-o', type=str, required=True)
    parser.add_argument('--data', type=str, choices=['paperdoll', 'fashionista'])
    args = parser.parse_args()
    if args.data == "paperdoll":
        samples = retrieve_paperdoll_info(args.outdir, return_info=True)
        img_dir = "paperdoll/img"
        if len(samples):
            urls = [i[0] for i in samples[:, 1]]
            ids = [i[0] for i in samples[:, 0]]
            download_img(img_dir, urls=urls, ids=ids)
        else:
            download_img(img_dir, anno_file="paperdoll/img_anno.txt")
    elif args.data == "fashionista":
        fashion_img_dir = args.outdir + '/JPEGImages'
        fashion_anno_dir = args.outdir + '/Annotations'
        # fashion_layouts_dir = args.outdir + '/ImageSets'
        # generate xml annotation file
        files = os.listdir(fashion_pixel_label_dir)
        img_pixels = [fashion_pixel_label_dir+"/"+filename for filename in files]
        # pool2 = Pool(processes=10)
        # partial_fashionista2VOC_format = partial(fashionista2VOC_format, outdir=fashion_anno_dir)
        # pool2 = multiprocessing.Pool(processes=10)
        # pool2.map(partial_fashionista2VOC_format, img_pixels)
        for pixel_file in img_pixels:
            fashionista2VOC_format(pixel_file, outdir=fashion_anno_dir)
        logger.info("Generating xml annotation file done!")
        # generate trainval file
        # ----------------------
        # download imgs
        df_url = pd.read_csv(fashion_url)
        index = df_url['index'].tolist()
        urls = df_url['url'].tolist()
        download_img(fashion_img_dir, urls=urls, ids=index, prefix='fashionista_')
    else:
        logger.info("Only paperdoll or fashionista dataset is allowed now!")








