import json
import multiprocessing as mp
from functools import partial
from tqdm import tqdm
import Levenshtein
import pandas as pd
from collections import defaultdict
from utils import load_sign_list, node_clean, match_single, holder_clean

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def get_node_list_sc():
    """
    此版本最大的调整，这里的sc的节点是sc+sc上下游的节点
    需要载入
        node_base2sc.json

        node2index_sc.json
        link_list_sc.json

    得到一个全面的node_list
    :return:
    """
    # load node_base2sc
    with open('../../data/match_base2sc/node_base2sc.json', 'r', encoding='utf-8') as f:
        node_base2sc = json.load(f)
    # load node2index_sc
    with open('../../data/supply_chain/inputs/node2index_sc.json', 'r', encoding='utf-8') as f:
        node2index = json.load(f)
    index2node = {index: node for node, index in node2index.items()}
    # load link_list_sc
    with open('../../data/supply_chain/inputs/link_list_sc.json', 'r', encoding='utf-8') as f:
        link_list = json.load(f)
    # get node_list in match result
    node_list_sc_core = []
    for _, node_sc_ in node_base2sc.items():
        node_list_sc_core.extend(node_sc_)
    # set
    node_list_sc_core = set(node_list_sc_core)
    node_list_sc_neighbor = set()
    for s_index, t_index, _ in link_list:
        s = index2node[s_index]
        t = index2node[t_index]
        if s in node_list_sc_core:
            node_list_sc_neighbor.add(t)
        if t in node_list_sc_core:
            node_list_sc_neighbor.add(s)
    logging.info('node_list_sc_core {}'.format(len(node_list_sc_core)))
    logging.info('node_list_sc_neighbor {}'.format(len(node_list_sc_neighbor)))
    # 并集
    node_list_sc = node_list_sc_core | node_list_sc_neighbor
    node_list_sc = sorted(list(node_list_sc))
    logging.info('node_list_sc {}'.format(len(node_list_sc)))
    # save
    with open('../../data/match_sc2patent/node_list_sc.json', 'w', encoding='utf-8') as f:
        json.dump(node_list_sc, f, ensure_ascii=False, indent=4)


def get_node_list_patent():
    """
    构建一个全面的专利权人节点列表
    需要载入
        node2index_patent.json
        dwpi2orig_safe.json (match)
    :return:
    """
    with open('../../data/patent/inputs/patent2holder.json', 'r', encoding='utf-8') as f:
        patent2holder = json.load(f)

    # 没有利用匹配结果
    node_patent_list_no_match = set()

    for patent, info in tqdm(patent2holder.items(), total=len(patent2holder)):
        holder_dwpi = info['holder_dwpi']
        inventors_dwpi = info['inventors_dwpi']
        holder_orig = info['holder_orig']
        inventors_orig = info['inventors_orig']
        holder_list_dwpi = holder_clean(holder_dwpi, inventors_dwpi)
        holder_list_orig = holder_clean(holder_orig, inventors_orig)
        # no match
        node_patent_list_no_match.update(holder_list_dwpi)
        node_patent_list_no_match.update(holder_list_orig)
    logging.info('node_patent_list_no_match {}'.format(len(node_patent_list_no_match)))

    with open('../../data/patent/inputs/dwpi2orig_safe.json', 'r', encoding='utf-8') as f:
        dwpi2orig_safe = json.load(f)
    orig2dwpi = dict()
    for dwpi, orig_dict in dwpi2orig_safe.items():
        for orig in orig_dict:
            orig2dwpi[orig] = dwpi
    # 利用了匹配结果
    node_patent_list_match = set()
    for node in list(node_patent_list_no_match):
        if node in orig2dwpi:
            node_patent_list_match.add(orig2dwpi[node])
        else:
            node_patent_list_match.add(node)

    logging.info('node_patent_list_match {}'.format(len(node_patent_list_match)))
    # save node_patent_list_match
    with open('../../data/match_sc2patent/node_list_patent.json', 'w', encoding='utf-8') as f:
        json.dump(list(node_patent_list_match), f, ensure_ascii=False, indent=4)


def match():
    # load_node_list_1
    with open('../../data/base/inputs/node_base2sc.json', 'r', encoding='utf-8') as f:
        node_base2sc = json.load(f)
    print(len(node_base2sc))

    node_list_1 = []
    for node_base, node_sc_list in node_base2sc.items():
        node_list_1.append(node_base)
        node_list_1.extend(node_sc_list)
    node_list_1 = list(set(node_list_1))
    # load_node_list_2
    with open('../../data/patent/inputs/node2index_patent.json', 'r', encoding='utf-8') as f:
        node2index = json.load(f)
    node_list_2 = list(node2index.keys())

    print('node_list_1', len(node_list_1))
    print('node_list_2', len(node_list_2))

    sign_list_1 = load_sign_list('operation_list_clean')
    sign_list_2 = load_sign_list('organization_list_clean')

    node_list_1_clean = [node_clean(node, sign_list_1, sign_list_2) for node in tqdm(node_list_1)]
    node_list_2_clean = [node_clean(node, sign_list_1, sign_list_2) for node in tqdm(node_list_2)]

    node2node_clean_1 = dict(zip(node_list_1, node_list_1_clean))
    node2node_clean_2 = dict(zip(node_list_2, node_list_2_clean))

    # match_stage_1
    # couple_list = []
    # pool = mp.Pool()
    # func = partial(match_single, node2node_clean_1, node2node_clean_2, 0.6)
    # for couple in tqdm(pool.imap(func, node_list_1), total=len(node_list_1)):
    #     couple_list.extend(couple)
    # pool.close()
    # pool.join()
    couple_list = []
    for node_1 in tqdm(node_list_1):
        couple_list_ = match_single(node2node_clean_1, node2node_clean_2, 0.6, node_1)
        couple_list.extend(couple_list_)
    print('couple_list', len(couple_list))

    # save
    with open('../../data/base/match_stage_3/match_result.json', 'w', encoding='utf-8') as f:
        json.dump(couple_list, f, ensure_ascii=False, indent=4)


def analysis():
    """
    热力图
    :return:
    """
    # load couple_list
    with open('../../data/base/match_stage_3/match_result.json', 'r', encoding='utf-8') as f:
        couple_list = json.load(f)
    num_collection_link_num = dict()
    num_collection_node_num = dict()
    for k1 in tqdm([0.6 + 0.01 * i for i in range(40)]):
        num_collection_link_num[k1] = dict()
        num_collection_node_num[k1] = dict()
        for k2 in [0.6 + 0.01 * i for i in range(40)]:
            couple_list_ = [couple for couple in couple_list if couple[2] > k1 and couple[3] > k2]
            num_collection_link_num[k1][k2] = len(couple_list_)
            node_base2sc = defaultdict(set)
            for couple in couple_list_:
                node_base2sc[couple[0]].add(couple[1])
            num_collection_node_num[k1][k2] = len(node_base2sc)
    # to excel for heatmap by pandas
    df = pd.DataFrame(num_collection_link_num)
    df.to_excel('../../data/base/match_stage_3/match_result_link_num_heatmap.xlsx', index=True)
    df = pd.DataFrame(num_collection_node_num)
    df.to_excel('../../data/base/match_stage_3/match_result_node_num_heatmap.xlsx', index=True)


def dwpi2orig_check(node1, node2, dwpi2orig_safe):
    status = False
    if node1 in dwpi2orig_safe and node2 in dwpi2orig_safe[node1]:
        status = True
    if node2 in dwpi2orig_safe and node1 in dwpi2orig_safe[node2]:
        status = True
    return status


def match_output(k1, k2):
    """
    根据k1和k2输出匹配结果
    分两步保存
    :return:
    """
    with open('../../data/base/inputs/node_base2sc.json', 'r', encoding='utf-8') as f:
        node_base2sc = json.load(f)
    # get node_sc2base
    node_sc2base = defaultdict(set)
    for node_base, node_sc_list in node_base2sc.items():
        for node_sc in node_sc_list:
            node_sc2base[node_sc].add(node_base)
    node_sc2base = {node: list(node_sc2base[node]) for node in node_sc2base}
    # load couple_list
    with open('../../data/base/match_stage_3/match_result.json', 'r', encoding='utf-8') as f:
        couple_list = json.load(f)
    # load dwpi2orig_safe
    with open('../../data/patent/inputs/dwpi2orig_safe.json', 'r', encoding='utf-8') as f:
        dwpi2orig_safe = json.load(f)
    node_base2patent_safe_1 = defaultdict(dict)
    for node, node_patent, sim_1, sim_2 in couple_list:
        # 这里增加一个非常重要的机制引入的dwpi2orig_safe
        if dwpi2orig_check(node, node_patent, dwpi2orig_safe) or sim_1 > 0.95 and sim_2 > 0.95:
            if node in node_base2sc:
                node_base2patent_safe_1[node][node_patent] = {'sim_1': sim_1, 'sim_2': sim_2}
            elif node in node_sc2base:
                for node_base in node_sc2base[node]:
                    node_base2patent_safe_1[node_base][node_patent] = {'sim_1': sim_1, 'sim_2': sim_2}
    print('node_base2patent4safe_1', len(node_base2patent_safe_1))
    with open('../../data/base/match_stage_3/node_base2patent4safe_1.json', 'w', encoding='utf-8') as f:
        json.dump(node_base2patent_safe_1, f, ensure_ascii=False, indent=4)
    node_base2patent = defaultdict(dict)
    for node, node_patent, sim_1, sim_2 in couple_list:
        if sim_1 > k1 and sim_2 > k2:
            if node in node_base2sc:
                if node in node_base2patent_safe_1 and node_patent in node_base2patent_safe_1[node]:
                    continue
                node_base2patent[node][node_patent] = {'sim_1': sim_1, 'sim_2': sim_2}
            elif node in node_sc2base:
                for node_base in node_sc2base[node]:
                    if node in node_base2patent_safe_1 and node_patent in node_base2patent_safe_1[node]:
                        continue
                    node_base2patent[node_base][node_patent] = {'sim_1': sim_1, 'sim_2': sim_2}

    print('node_base2patent', len(node_base2patent))
    node_base2patent4safe_2 = {node: node_base2patent[node] for node in node_base2patent
                               if len(node_base2patent[node]) <= 2}
    print('node_base2patent4safe_2', len(node_base2patent4safe_2))
    with open('../../data/base/match_stage_3/node_base2patent4safe_2.json', 'w', encoding='utf-8') as f:
        json.dump(node_base2patent4safe_2, f, ensure_ascii=False, indent=4)
    safe_list = list(set(node_base2patent_safe_1.keys()) | set(node_base2patent4safe_2.keys()))
    print('node_base2patent_safe', len(safe_list))

    node_base2patent4hand = {node: node_base2patent[node] for node in node_base2patent
                             if len(node_base2patent[node]) > 2}
    node_base2patent4hand = dict(sorted(node_base2patent4hand.items(), key=lambda x: len(x[1]), reverse=True))
    print('node_base2patent4hand', len(node_base2patent4hand))
    with open('../../data/base/match_stage_3/node_base2patent4hand.json', 'w', encoding='utf-8') as f:
        json.dump(node_base2patent4hand, f, ensure_ascii=False, indent=4)
    hand_list = list(set(node_base2patent4hand.keys()) - set(node_base2patent_safe_1.keys()))
    print('node_base2patent4hand', len(hand_list))


def match_result_combine():
    with open('../../data/base/match_stage_3/node_base2patent4safe_1.json', 'r', encoding='utf-8') as f:
        node_base2patent4safe_1 = json.load(f)
    with open('../../data/base/match_stage_3/node_base2patent4safe_2.json', 'r', encoding='utf-8') as f:
        node_base2patent4safe_2 = json.load(f)
    with open('../../data/base/match_stage_3/node_base2patent4hand_clean.json', 'r', encoding='utf-8') as f:
        node_base2patent4hand_clean = json.load(f)
    node_base2patent4safe_1 = {node: set(node_base2patent4safe_1[node].keys()) for node in node_base2patent4safe_1}
    node_base2patent4safe_2 = {node: set(node_base2patent4safe_2[node].keys()) for node in node_base2patent4safe_2}
    node_base2patent4hand_clean = {node: set(node_base2patent4hand_clean[node]) for node in node_base2patent4hand_clean}
    node_base2patent = defaultdict(set)
    for node in node_base2patent4safe_1:
        node_base2patent[node].update(node_base2patent4safe_1[node])
    for node in node_base2patent4safe_2:
        node_base2patent[node].update(node_base2patent4safe_2[node])
    for node in node_base2patent4hand_clean:
        node_base2patent[node].update(node_base2patent4hand_clean[node])
    print('node_base2patent', len(node_base2patent))
    # save
    node_base2patent = {node: list(node_base2patent[node]) for node in node_base2patent}
    with open('../../data/base/inputs/node_base2patent.json', 'w', encoding='utf-8') as f:
        json.dump(node_base2patent, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    get_node_list_sc()
    get_node_list_patent()
    # match()
    # analysis()
    # 根据match_result的表二，k1,k2的阈值选择为0.81,0.9
    # k1 = 0.68
    # k2 = 0.835
    # print(k1, k2)
    # match_output(k1, k2)
    # match_result_combine()
