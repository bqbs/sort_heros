# -*- coding:utf-8 -*-
import json
import os
import re
import time
import urllib.request

import math
from PIL import Image
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from colormath.color_objects import sRGBColor, LabColor
from colorthief import ColorThief

row_num = 12
col_num = 12


def merge_image(image_list):
    # 拼接头像
    image_size = len(image_list)
    print(image_size)

    # 先生成头像集模板
    target_img = Image.new('RGBA', (59 * row_num, 33 * col_num))

    x = 0
    y = 0

    for index, i in enumerate(image_list):
        try:
            # 打开图片
            img = Image.open(i)
        except IOError:
            print(u'Error: 没有找到文件或读取文件失败')
        else:
            # 缩小图片
            img = img.resize((59, 33), Image.ANTIALIAS)
            # 拼接图片
            target_img.paste(img, (x * 59, y * 33))
            x += 1
            if x == row_num:
                x = 0
                y += 1

    print()
    target_img.save('./sort_heros' + str(int(time.time())) + ".png")


def hex_to_rgb(value):
    value = value.lstrip('0x')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


def rgb_to_hex(rgb):
    return '0x%02x%02x%02x%02x' % rgb


def gen_dominant_color_img(color_list):
    color_size = len(color_list)
    print(color_size)

    target_image = Image.new('RGB', (59 * row_num, 33 * col_num))

    x = 0
    y = 0

    for index, color in enumerate(color_list):
        try:
            lst = list(color)
            t = tuple(lst)
            img = Image.new('RGBA', (59, 33), t)
        except IOError:
            print(u'Error: 没有找到文件或读取文件失败')
        else:
            # 缩小图片
            img = img.resize((59, 33), Image.ANTIALIAS)
            # 拼接图片
            target_image.paste(img, (x * 59, y * 33))
            x += 1
            if x == row_num:
                x = 0
                y += 1

    target_image.save('./colors_' + str(int(time.time())) + ".png")


def get_dominant_color_by_color_thief(image_path):
    color_thief = ColorThief(image_path)
    # get the dominant color
    dominant_color = color_thief.get_color(quality=6)
    l = list(dominant_color)
    return tuple(l)


def get_all_hero_img():
    """
    获取英雄头像

    :return:
    """
    try:
        img_list = []
        f = open('./dota2_heros.json')
        heros_json = json.load(f)
        for d in heros_json['data']:
            # print(d)
            file_path = './images/%s' % re.search(r'[a-zA-Z._]+png', d['img'], re.M | re.I).group()
            img_list.append(file_path)
            if not os.path.exists(file_path):
                urllib.request.urlretrieve(d['img'], filename=file_path)

        return img_list
    except Exception as e:
        print(e)
        return []


def colour_distance(rgb_1, rgb_2):
    """
    欧式距离计算方法


    :param rgb_1: rgb颜色值
    :param rgb_2: rgb颜色值
    :return:
    """
    R_1, G_1, B_1 = rgb_1
    R_2, G_2, B_2 = rgb_2
    rmean = (R_1 + R_2) / 2
    R = R_1 - R_2
    G = G_1 - G_2
    B = B_1 - B_2
    return math.sqrt((2 + rmean / 256) * (R ** 2) + 4 * (G ** 2) + (2 + (255 - rmean) / 256) * (B ** 2))


def sort_hero_by_color():
    global base_color = convert_color(sRGBColor(0,0,0), LabColor, target_illuminant='d50')
    img_list = get_all_hero_img()
    obj_list = []
    for index, img in enumerate(img_list):
        dominant_color = get_dominant_color_by_color_thief(img)
        rgb = sRGBColor(dominant_color[0], dominant_color[1], dominant_color[2])
        # if index == 0:
        #    base_color = convert_color(rgb, LabColor, target_illuminant='d50')

        target_color = convert_color(rgb, LabColor, target_illuminant='d50')
        delta_e = delta_e_cie2000(target_color, base_color, Kh=2)
        c = (img, dominant_color, delta_e)
        # print(index, c)

        # 通过欧氏距离
        # distance = colour_distance(dominant_color, (0, 0, 0))
        # c = (img, dominant_color, distance)

        obj_list.append(c)

    obj_list = sorted(obj_list, key=lambda obj: obj[2])
    i_list = []
    c_list = []
    for obj in obj_list:
        print(obj)
        i_list.append(obj[0])
        c_list.append(obj[1])

    merge_image(i_list)
    gen_dominant_color_img(c_list)


if __name__ == '__main__':
    sort_hero_by_color()
