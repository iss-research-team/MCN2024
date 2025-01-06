import json
import Levenshtein


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


def match_single(node2node_clean_1, node2node_clean_2, k, node_1):
    """
    在node2node_clean_2中找到与node_1最相似的节点
    :param node2node_clean_1:
    :param node2node_clean_2:
    :param k:
    :param node_1:
    :return:
    """
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