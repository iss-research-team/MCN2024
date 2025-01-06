import json
from tqdm import tqdm
import Levenshtein
from collections import defaultdict


def load_sign_list(file):
    sign_list = []
    with open('../../data/sign/{}'.format(file), 'r', encoding='utf-8') as f:
        for line in f:
            sign_list.append(line.strip())
    # lower
    sign_list = [sign.lower() for sign in sign_list]
    sign_list = [' ' + sign + ' ' for sign in sign_list]
    return sign_list


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


def match_single(dwpi2orig, dwpi2dwpi_clean, orig2orig_clean, k, dwpi):
    """
    从node_list_1中找到与node最相似的节点
    :param node_list_1:
    :param node:
    :return:
    """

    dwpi_clean = dwpi2dwpi_clean[dwpi]
    orig_list = dwpi2orig[dwpi]

    couple_list = []
    for orig in orig_list:
        orig_clean = orig2orig_clean[orig]
        sim_1 = Levenshtein.ratio(dwpi, orig)
        sim_2 = Levenshtein.ratio(dwpi_clean, orig_clean)
        if sim_1 > k and sim_2 > k:
            couple_list.append((dwpi, orig, sim_1, sim_2))
    return couple_list


def match():
    """
    :return:
    """
    with open('../../data/patent/inputs/dwpi2orig.json', 'r', encoding='utf-8') as f:
        dwpi2orig = json.load(f)

    sign_list_1 = load_sign_list('operation_list_clean')
    sign_list_2 = load_sign_list('organization_list_clean')

    dwpi_list = list(dwpi2orig.keys())
    orig_list = set()
    for dwpi in dwpi2orig:
        orig_list.update(dwpi2orig[dwpi])
    orig_list = list(orig_list)

    dwpi_list_clean = [node_clean(node, sign_list_1, sign_list_2) for node in tqdm(dwpi_list)]
    orig_list_clean = [node_clean(node, sign_list_1, sign_list_2) for node in tqdm(orig_list)]

    dwpi2dwpi_clean = dict(zip(dwpi_list, dwpi_list_clean))
    orig2orig_clean = dict(zip(orig_list, orig_list_clean))

    # match_stage_1
    couple_list = []

    for dwpi in tqdm(dwpi_list):
        dwpi_clean = dwpi2dwpi_clean[dwpi]
        orig_list = dwpi2orig[dwpi]
        for orig in orig_list:
            orig_clean = orig2orig_clean[orig]
            sim_1 = Levenshtein.ratio(dwpi, orig)
            sim_2 = Levenshtein.ratio(dwpi_clean, orig_clean)
            if sim_1 > 0.6 and sim_2 > 0.6:
                couple_list.append((dwpi, orig, sim_1, sim_2))
    print('couple_list', len(couple_list))
    # save
    with open('../../data/patent/inputs/dwpi2orig_couple.json', 'w', encoding='utf-8') as f:
        json.dump(couple_list, f, ensure_ascii=False, indent=4)


def clean_dwpi2orig(k1, k2):
    """
    clean
        剔除1-1
    :return:
    """
    with open('../../data/patent/inputs/dwpi2orig.json', 'r', encoding='utf-8') as f:
        dwpi2orig = json.load(f)
    print('dwpi2orig', len(dwpi2orig))
    with open('../../data/patent/inputs/dwpi2orig_couple.json', 'r', encoding='utf-8') as f:
        couple_list = json.load(f)
    # load match_stage_1 result
    dwpi2orig_match_result = defaultdict(dict)
    for dwpi, orig, sim_1, sim_2 in couple_list:
        if sim_1 > k1 and sim_2 > k2:
            dwpi2orig_match_result[dwpi][orig] = {'sim_1': sim_1, 'sim_2': sim_2}
    print('dwpi2orig_match_result', len(dwpi2orig_match_result))
    # clean
    dwpi2orig_clean = defaultdict(dict)
    for dwpi in dwpi2orig:
        orig_list = dwpi2orig[dwpi]
        for orig in orig_list:
            if orig in dwpi2orig_match_result[dwpi]:
                dwpi2orig_clean[dwpi][orig] = dwpi2orig_match_result[dwpi][orig]
    print('dwpi2orig_clean', len(dwpi2orig_clean))
    dwpi2orig_safe = {dwpi: dwpi2orig_clean[dwpi] for dwpi in dwpi2orig_clean if len(dwpi2orig_clean[dwpi]) <= 2}
    print('dwpi2orig_safe', len(dwpi2orig_safe))
    with open('../../data/patent/inputs/dwpi2orig_safe.json', 'w', encoding='utf-8') as f:
        json.dump(dwpi2orig_safe, f, ensure_ascii=False, indent=4)
    dwpi2orig_hand = {dwpi: dwpi2orig_clean[dwpi] for dwpi in dwpi2orig_clean if len(dwpi2orig_clean[dwpi]) > 2}
    dwpi2orig_hand = dict(sorted(dwpi2orig_hand.items(), key=lambda x: len(x[1]), reverse=True))
    print('dwpi2orig_hand', len(dwpi2orig_hand))
    with open('../../data/patent/inputs/dwpi2orig_hand.json', 'w', encoding='utf-8') as f:
        json.dump(dwpi2orig_hand, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    match()
    # 根据match_result的表二，k1,k2的阈值选择为0.67, 0.82
    clean_dwpi2orig(0.67, 0.82)
