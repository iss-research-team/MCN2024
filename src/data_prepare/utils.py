import json
import Levenshtein
import logging

import numpy as np
import torch

logging = logging.getLogger(__name__)


def load_node_list(label):
    if label == 'base':
        with open('../../data/base/inputs/node2index_base.json', 'r', encoding='utf-8') as f:
            node2index = json.load(f)
    elif label == 'sc':
        with open('../../data/supply_chain/inputs/node2index_sc.json', 'r', encoding='utf-8') as f:
            node2index = json.load(f)
    elif label == 'patent':
        with open('../../data/patent/inputs/node2index_patent.json', 'r', encoding='utf-8') as f:
            node2patent = json.load(f)
        node2index = {node: index for index, node in enumerate(node2patent.keys())}
    else:
        raise ValueError('label error')
    node_list = list(node2index.keys())
    return node_list


def match_single(node2node_clean_1, node2node_clean_2, k, node_list_1, index):
    """
    在node2node_clean_2中找到与node_1最相似的节点
    :param node2node_clean_1:
    :param node2node_clean_2:
    :param k:
    :param node_1:
    :return:
    """
    logging.info(index)
    node_1 = node_list_1[index]
    node_1_clean = node2node_clean_1[node_1]
    couple_list = []
    for node_2 in node2node_clean_2:
        node_2_clean = node2node_clean_2[node_2]
        sim_1 = Levenshtein.ratio(node_1, node_2)
        sim_2 = Levenshtein.ratio(node_1_clean, node_2_clean)
        if sim_1 > k and sim_2 > k:
            couple_list.append((node_1, node_2, sim_1, sim_2))
    return couple_list


def node_clean(node, sign_list_1, sign_list_2):
    node = ' ' + node + ' '
    for sign in sign_list_1:
        node = node.replace(sign, ' ')
    for sign in sign_list_2:
        node = node.replace(sign, ' ')
    # for sign in sign_list_3:
    #     node = node.replace(sign, ' ')
    node = node.strip()
    return node


def load_sign_list(file):
    sign_list = []
    with open('../../data/sign/{}'.format(file), 'r', encoding='utf-8') as f:
        for line in f:
            sign_list.append(line.strip())
    # lower
    sign_list = [sign.lower() for sign in sign_list]
    sign_list = [' ' + sign + ' ' for sign in sign_list]
    return sign_list


def not_empty(s):
    return s and s.strip()


def holder_clean(holders, inventors):
    """
    从专利权人中去除发明人
    :param holders:
    :param inventors:
    :return:
    """
    holder_list = holders.split(' | ')
    holder_list = [holder.lower() for holder in holder_list]
    holder_list = filter(not_empty, holder_list)
    inventor_list = inventors.split(' | ')
    inventor_list = [inventor.lower() for inventor in inventor_list]
    inventor_list = filter(not_empty, inventor_list)
    holder_list = list(set(holder_list) - set(inventor_list))
    return holder_list


def mix_max(tensor, average='0'):
    """
    mix max
    :param tensor:
        [batch, dim]
    :param average:
        mean
    :return:
    """
    # to torch
    tensor = np.array(tensor)
    tensor = torch.tensor(tensor)
    # to cuda
    tensor = tensor.cuda()

    # device
    if average == 'mean':
        average = torch.mean(tensor, dim=0)
    elif average == '0':
        average = torch.zeros(tensor.shape[-1])
    else:
        raise ValueError('average must be mean or 0')

    # mix max
    # max | v > average
    # min | v < average
    tensor_max = torch.max(tensor, dim=0).values
    tensor_min = torch.min(tensor, dim=0).values
    # diff
    diff_max = tensor_max - average
    diff_min = average - tensor_min
    # mix max
    tensor_mix_max = torch.where(diff_max > diff_min, tensor_max, tensor_min)
    return tensor_mix_max.cpu().numpy()
