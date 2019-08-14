# -*- coding:utf-8 -*-
import json
import os
import re
import urllib.request
from PIL import Image
import colorsys
import math
import time
from functools import cmp_to_key
from sklearn.cluster import KMeans
from collections import Counter
import cv2  # for resizing image
from colorthief import ColorThief

from colormath.color_diff import delta_e_cie1976


def merge_image(l):
    # 拼接头像
    numPic = len(l)
    print(numPic)

    numrow = 12
    numcol = 12  # 向下取整
    toImage = Image.new('RGBA', (59 * numrow, 33 * numcol))  # 先生成头像集模板

    x = 0  # 小头像拼接时的左上角横坐标
    y = 0  # 小头像拼接时的左上角纵坐标

    for index, i in enumerate(l):
        try:
            # 打开图片
            img = Image.open(i)
        except IOError:
            print(u'Error: 没有找到文件或读取文件失败')
        else:
            # 缩小图片
            img = img.resize((59, 33), Image.ANTIALIAS)
            # 拼接图片
            toImage.paste(img, (x * 59, y * 33))
            x += 1
            if x == numrow:
                x = 0
                y += 1

    print()
    toImage.save('./sort_heros' + str(int(time.time())) + ".png")


def hex_to_rgb(value):
    value = value.lstrip('0x')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


def rgb_to_hex(rgb):
    return '0x%02x%02x%02x%02x' % rgb


def get_color_img(color_list):
    numPic = len(color_list)
    print(numPic)

    numrow = 12
    numcol = 12
    toImage = Image.new('RGB', (59 * numrow, 33 * numcol))

    x = 0
    y = 0

    for index, i in enumerate(color_list):
        try:
            lst = list(i)
            lst.pop(len(lst) - 1)
            t = tuple(lst)
            img = Image.new('RGBA', (59, 33), t)
        except IOError:
            print(u'Error: 没有找到文件或读取文件失败')
        else:
            # 缩小图片
            img = img.resize((59, 33), Image.ANTIALIAS)
            # 拼接图片
            toImage.paste(img, (x * 59, y * 33))
            x += 1
            if x == numrow:
                x = 0
                y += 1

    toImage.save('./colors_' + str(int(time.time())) + ".png")


def compute_average_image_color(p):
    img = Image.open(p)
    img = img.convert('RGBA')
    width, height = img.size

    r_total = 0
    g_total = 0
    b_total = 0

    count = 0
    for x in range(0, width):
        for y in range(0, height):
            r, g, b, a = img.getpixel((x, y))
            r_total += r
            g_total += g
            b_total += b
            count += 1

    return (int(r_total / count), int(g_total / count), int(b_total / count), a)


def get_dominant_color(image_path):
    # 颜色模式转换，以便输出rgb颜色值
    image = Image.open(image_path)
    image = image.convert('RGBA')

    # 生成缩略图，减少计算量，减小cpu压力
    image.thumbnail((200, 200))

    max_score = 0
    dominant_color = 0

    for count, (r, g, b, a) in image.getcolors(image.size[0] * image.size[1]):
        # 跳过纯黑色
        if a == 0:
            continue

        saturation = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)[1]

        y = min(abs(r * 2104 + g * 4130 + b * 802 + 4096 + 131072) >> 13, 235)

        y = (y - 16.0) / (235 - 16)
        #
        # 忽略高亮色
        if y > 0.9:
            continue

        # Calculate the score, preferring highly saturated colors.
        # Add 0.1 to the saturation so we don't completely ignore grayscale
        # colors by multiplying the count by zero, but still give them a low
        # weight.
        score = (saturation + 0.1) * count

        if score > max_score:
            max_score = score
            dominant_color = (r, g, b, a)

    return dominant_color


def get_accent_color(path):
    im = Image.open(path)
    if im.mode != "RGB":
        im = im.convert('RGB')
    delta_h = 0.3
    avg_h = sum(t[0] for t in
                [colorsys.rgb_to_hsv(*im.getpixel((x, y))) for x in range(im.size[0]) for y in range(im.size[1])]) / (
                im.size[0] * im.size[1])
    beyond = filter(lambda x: abs(colorsys.rgb_to_hsv(*x)[0] - avg_h) > delta_h,
                    [im.getpixel((x, y)) for x in range(im.size[0]) for y in range(im.size[1])])
    if len(list(beyond)) > 0:
        r = sum(e[0] for e in beyond) / len(list(beyond))
        g = sum(e[1] for e in beyond) / len(list(beyond))
        b = sum(e[2] for e in beyond) / len(list(beyond))
        for i in range(im.size[0] / 2):
            for j in range(im.size[1] / 10):
                im.putpixel((i, j), (r, g, b))
        im.save('res' + path)
        return (r, g, b)
    return (0, 0, 0)


def get_dominant_color_new(image_path, k=4, image_processing_size=None):
    """
    takes an image as input
    returns the dominant color of the image as a list

    dominant color is found by running k means on the
    pixels & returning the centroid of the largest cluster

    processing time is sped up by working with a smaller image;
    this resizing can be done with the image_processing_size param
    which takes a tuple of image dims as input

    >>> get_dominant_color(my_image, k=4, image_processing_size = (25, 25))
    [56.2423442, 34.0834233, 70.1234123]
    """
    # resize image if new dims provided
    image = cv2.imread(image_path)
    # image = image.convert('RGBA')

    if image_processing_size is not None:
        image = cv2.resize(image, image_processing_size,
                           interpolation=cv2.INTER_AREA)

    # reshape the image to be a list of pixels
    image = image.reshape((image.shape[0] * image.shape[1], 3))

    # cluster and assign labels to the pixels
    clt = KMeans(n_clusters=k)
    labels = clt.fit_predict(image)

    # count labels to find most popular
    label_counts = Counter(labels)

    # subset out most popular centroid
    dominant_color = clt.cluster_centers_[label_counts.most_common(1)[0][0]]

    return list(dominant_color)[0]


def get_dominant_color_3(image_path):
    color_thief = ColorThief(image_path)
    # get the dominant color
    dominant_color = color_thief.get_color(quality=6)
    l = list(dominant_color)

    print(l)
    l.append(0)
    print(l)
    print(tuple(l))
    return tuple(l)


def get_all_hero_img():
    try:
        img_list = []
        f = open('./sort_hero.json')
        heros_json = json.load(f)
        for d in heros_json['data']:
            # print(d)
            file_path = './images/%s' % re.search(r'[a-zA-Z\.\_]+png', d['img'], re.M | re.I).group()
            img_list.append(file_path)
            if not os.path.exists(file_path):
                urllib.request.urlretrieve(d['img'], filename=file_path)

        return img_list
    except Exception as e:
        print(e)
        return []


def color_sort(a):
    try:
        i = int(rgb_to_hex(a[1]), 16)
        print(i)
        return i

    except Exception as e:
        print(e)


def distance(c1, c2):
    (r1, g1, b1, a1) = c1
    (r2, g2, b2, a2) = c2
    return math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)


def ColourDistance(rgb_1, rgb_2):
    R_1, G_1, B_1, A_1 = rgb_1
    R_2, G_2, B_2, A_2 = rgb_2
    rmean = (R_1 + R_2) / 2
    R = R_1 - R_2
    G = G_1 - G_2
    B = B_1 - B_2
    return math.sqrt((2 + rmean / 256) * (R ** 2) + 4 * (G ** 2) + (2 + (255 - rmean) / 256) * (B ** 2))


def sort_hero_by_color():
    img_list = get_all_hero_img()
    color_list = []
    for img in img_list:
        t = get_dominant_color_3(img)
        print(img, t)
        # d = distance(t, (0, 0, 0, 0))
        d = ColourDistance(t, (127, 127, 127, 127))
        c = (img, t, d)
        color_list.append(c)

    color_list = sorted(color_list, key=lambda c: c[1])
    i_list = []
    c_list = []
    for color in color_list:
        i_list.append(color[0])
        c_list.append(color[1])

    merge_image(i_list)
    get_color_img(c_list)


if __name__ == '__main__':
    sort_hero_by_color()
