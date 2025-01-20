#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：zx_2
@File    ：0_4_s2vec.py
@IDE     ：PyCharm
@Author  ：Logan
@Date    ：2023/12/2 上午7:59
"""

from transformers import RobertaTokenizer, RobertaModel
from tqdm import tqdm
import torch
import os
import numpy as np
import json
import argparse


def parameter_parser():
    parser = argparse.ArgumentParser(description='embed stage_1')
    # history_save_path
    parser.add_argument('--index', help="Please give a data_path", type=str)
    return parser.parse_args()


def load_data(filename):
    """
    数据的输入
    :param filename:
    :return:
    """
    with open(filename, encoding='utf-8') as f:
        data = json.load(f)

    data = [(c, '\n'.join(list(t.values()))) for c, t in data.items()]
    return data


def doc_trans_1(tokenizer, file_path, output_path):
    print('模型载入成功')
    # 载入数据
    data = load_data(file_path)
    # 将data分为4个部分
    print('数据载入成功')
    id_320, token_ids_320 = [], []
    id_384, token_ids_384 = [], []
    id_448, token_ids_448 = [], []
    id_512, token_ids_512 = [], []

    for index, text in tqdm(data):
        token_ids = tokenizer(text, truncation=True, max_length=512)['input_ids']
        if len(token_ids) <= 320:
            id_320.append(index)
            token_ids_320.append(token_ids)
        elif len(token_ids) <= 384:
            id_384.append(index)
            token_ids_384.append(token_ids)
        elif len(token_ids) <= 448:
            id_448.append(index)
            token_ids_448.append(token_ids)
        else:
            id_512.append(index)
            token_ids_512.append(token_ids)

    print(len(token_ids_320))
    print(len(token_ids_384))
    print(len(token_ids_448))
    print(len(token_ids_512))

    if not os.path.exists(output_path):
        os.mkdir(output_path)

    with open(output_path + '/id_320.json', 'w') as f:
        json.dump(id_320, f)
    with open(output_path + '/token_ids_320.json', 'w') as f:
        json.dump(token_ids_320, f)
    with open(output_path + '/id_384.json', 'w') as f:
        json.dump(id_384, f)
    with open(output_path + '/token_ids_384.json', 'w') as f:
        json.dump(token_ids_384, f)
    with open(output_path + '/id_448.json', 'w') as f:
        json.dump(id_448, f)
    with open(output_path + '/token_ids_448.json', 'w') as f:
        json.dump(token_ids_448, f)
    with open(output_path + '/id_512.json', 'w') as f:
        json.dump(id_512, f)
    with open(output_path + '/token_ids_512.json', 'w') as f:
        json.dump(token_ids_512, f)


def doc_trans_2(model, output_path, length, batch_size, device):
    print('length', length, 'batch_size', batch_size)
    with open(output_path + '/token_ids_{}.json'.format(length), 'r') as f:
        token_ids_list = json.load(f)
    attention_mask_list = [[1] * len(token_ids) for token_ids in token_ids_list]
    # padding
    token_ids_list = [token_ids + [0] * (length - len(token_ids)) for token_ids in token_ids_list]
    attention_mask_list = [attention_mask + [0] * (length - len(attention_mask)) for attention_mask in
                           attention_mask_list]
    print(len(token_ids_list))

    # encode
    train_x = []
    data_length = len(token_ids_list)
    for i in tqdm(range(0, data_length, batch_size)):
        inputs = token_ids_list[i:i + batch_size]
        attention_mask = attention_mask_list[i:i + batch_size]
        inputs = torch.tensor(inputs).to(device)
        attention_mask = torch.tensor(attention_mask).to(device)
        last_hidden_states = model(inputs, attention_mask=attention_mask).pooler_output.cpu().detach()
        train_x.extend(last_hidden_states.tolist())

    print('数据转化成功')
    print(len(train_x))
    train_x = np.array(train_x)
    # 保存结果
    np.save(output_path + '/patent_feature_{}.npy'.format(length), train_x)
    print('数据保存成功')


if __name__ == '__main__':
    tokenizer = RobertaTokenizer.from_pretrained('roberta-large')
    model = RobertaModel.from_pretrained('roberta-large')
    device = torch.device('cuda:0')
    model.to(device)
    model.eval()

    index_list = []

    for index in index_list:
        file_path = '../../data/patent/inputs/patent_id2doc/patent_id2doc_{}.json'.format(index)
        print(file_path)
        output_path = '../../data/patent/inputs/doc2vec_{}'.format(index)
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        doc_trans_1(tokenizer, file_path, output_path)
        for length, batch_size in [(320, 26), (384, 22), (448, 18), (512, 14)]:
            doc_trans_2(model, output_path, length=length, batch_size=batch_size, device=device)
