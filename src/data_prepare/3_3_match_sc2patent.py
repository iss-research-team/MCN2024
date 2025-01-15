import json
import multiprocessing as mp
from functools import partial
from tqdm import tqdm
import pandas as pd
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from utils import load_sign_list, node_clean, match_single, holder_clean


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
    """
    node_list_1: sc
    node_list_2: patent
    :return:
    """
    # load_node_list_sc
    with open('../../data/match_sc2patent/node_list_sc.json', 'r', encoding='utf-8') as f:
        node_list_1 = json.load(f)
    logging.info('node_list_sc {}'.format(len(node_list_1)))
    # load_node_list_patent
    with open('../../data/match_sc2patent/node_list_patent.json', 'r', encoding='utf-8') as f:
        node_list_2 = json.load(f)
    logging.info('node_list_patent {}'.format(len(node_list_2)))

    sign_list_1 = load_sign_list('operation_list_clean')
    sign_list_2 = load_sign_list('organization_list_clean')

    node_list_1_clean = [node_clean(node, sign_list_1, sign_list_2) for node in tqdm(node_list_1)]
    node_list_2_clean = [node_clean(node, sign_list_1, sign_list_2) for node in tqdm(node_list_2)]

    node2node_clean_1 = dict(zip(node_list_1, node_list_1_clean))
    node2node_clean_2 = dict(zip(node_list_2, node_list_2_clean))

    # match_stage_1
    couple_list = []
    pool = mp.Pool()
    func = partial(match_single, node2node_clean_1, node2node_clean_2, 0.6, node_list_1)

    result_list = pool.map(func, range(len(node_list_1)))
    for couple_list_ in result_list:
        couple_list.extend(couple_list_)

    pool.close()
    pool.join()
    logging.info('couple_list {}'.format(len(couple_list)))

    # save
    with open('../../data/match_sc2patent/match_result.json', 'w', encoding='utf-8') as f:
        json.dump(couple_list, f, ensure_ascii=False, indent=4)


def analysis():
    """
    热力图
    :return:
    """
    # load couple_list
    with open('../../data/match_sc2patent/match_result.json', 'r', encoding='utf-8') as f:
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
    df.to_excel('../../data/match_sc2patent/match_result_link_num_heatmap.xlsx', index=True)
    df = pd.DataFrame(num_collection_node_num)
    df.to_excel('../../data/match_sc2patent/match_result_node_num_heatmap.xlsx', index=True)


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
    with open('../../data/match_sc2patent/match_result.json', 'r', encoding='utf-8') as f:
        couple_list = json.load(f)
    node_sc2patent4safe_1 = defaultdict(dict)
    for node_sc, node_patent, sim_1, sim_2 in couple_list:
        if sim_1 > 0.95 and sim_2 > 0.95:
            node_sc2patent4safe_1[node_sc][node_patent] = {'sim_1': sim_1, 'sim_2': sim_2}
    logging.info('node_sc2patent4safe_1: %d', len(node_sc2patent4safe_1))
    with open('../../data/match_sc2patent/node_sc2patent4safe_1.json', 'w', encoding='utf-8') as f:
        json.dump(node_sc2patent4safe_1, f, ensure_ascii=False, indent=4)
    node_sc2patent = defaultdict(dict)
    for node_sc, node_patent, sim_1, sim_2 in couple_list:
        if sim_1 > k1 and sim_2 > k2:
            if node_sc in node_sc2patent4safe_1 and node_patent in node_sc2patent4safe_1[node_sc]:
                continue
            node_sc2patent[node_sc][node_patent] = {'sim_1': sim_1, 'sim_2': sim_2}
    logging.info('node_sc2patent: %d', len(node_sc2patent))
    node_sc2patent4safe_2 = {node: node_sc2patent[node] for node in node_sc2patent if len(node_sc2patent[node]) <= 2}
    logging.info('node_sc2patent4safe_2: %d', len(node_sc2patent4safe_2))
    safe_list = list(set(node_sc2patent4safe_1.keys()) | set(node_sc2patent4safe_2.keys()))
    logging.info('node_base2sc4safe: %d', len(safe_list))

    with open('../../data/match_sc2patent/node_sc2patent4safe_2.json', 'w', encoding='utf-8') as f:
        json.dump(node_sc2patent4safe_2, f, ensure_ascii=False, indent=4)
    node_sc2patent4hand = {node: node_sc2patent[node] for node in node_sc2patent if len(node_sc2patent[node]) > 2}
    node_sc2patent4hand = dict(sorted(node_sc2patent4hand.items(), key=lambda x: len(x[1]), reverse=True))
    logging.info('node_sc2patent4hand: %d', len(node_sc2patent4hand))
    hand_list = list(set(node_sc2patent4hand.keys()) - set(node_sc2patent4safe_1.keys()))
    logging.info('node_sc2patent4hand: %d', len(hand_list))
    with open('../../data/match_sc2patent/node_sc2patent4hand.json', 'w', encoding='utf-8') as f:
        json.dump(node_sc2patent4hand, f, ensure_ascii=False, indent=4)


def match_result_combine():
    with open('../../data/match_sc2patent/node_sc2patent4safe_1.json', 'r', encoding='utf-8') as f:
        node_base2patent4safe_1 = json.load(f)
    with open('../../data/match_sc2patent/node_sc2patent4safe_2.json', 'r', encoding='utf-8') as f:
        node_base2patent4safe_2 = json.load(f)
    with open('../../data/match_sc2patent/node_sc2patent4hand_clean.json', 'r', encoding='utf-8') as f:
        node_base2patent4hand_clean = json.load(f)
    node_base2patent4safe_1 = {node: set(node_base2patent4safe_1[node].keys()) for node in node_base2patent4safe_1}
    logging.info('node_base2patent4safe_1: %d', len(node_base2patent4safe_1))
    node_base2patent4safe_2 = {node: set(node_base2patent4safe_2[node].keys()) for node in node_base2patent4safe_2}
    logging.info('node_base2patent4safe_2: %d', len(node_base2patent4safe_2))
    node_base2patent4hand_clean = {node: set(node_base2patent4hand_clean[node]) for node in node_base2patent4hand_clean}
    logging.info('node_base2patent4hand_clean: %d', len(node_base2patent4hand_clean))
    node_base2patent_combine = defaultdict(set)
    for node_base2patent in [node_base2patent4safe_1, node_base2patent4safe_2, node_base2patent4hand_clean]:
        for node_base, node_patent_list in node_base2patent.items():
            node_base2patent_combine[node_base].update(node_patent_list)
        logging.info('node_base2patent_combine: %d', len(node_base2patent_combine))

    # save
    node_base2patent_combine = {k: list(v) for k, v in node_base2patent_combine.items()}
    with open('../../data/match_sc2patent/node_sc2patent.json', 'w', encoding='utf-8') as f:
        json.dump(node_base2patent_combine, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    # get node list for match
    # get_node_list_sc()
    # get_node_list_patent()
    # match()
    # analysis()
    # 根据match_result的表二，k1,k2的阈值选择为0.67,0.8
    # k1 = 0.67
    # k2 = 0.8
    # match_output(k1, k2)
    match_result_combine()
