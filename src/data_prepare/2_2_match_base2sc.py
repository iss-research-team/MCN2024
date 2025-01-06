import json
import multiprocessing as mp
from functools import partial
from tqdm import tqdm
import pandas as pd
from collections import defaultdict
import logging
from utils import load_node_list, match_single, node_clean, load_sign_list

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def match():
    node_list_1 = load_node_list('base')
    node_list_2 = load_node_list('sc')
    logging.info('node_list_1 {}'.format(len(node_list_1)))
    logging.info('node_list_2 {}'.format(len(node_list_2)))

    sign_list_1 = load_sign_list('operation_list_clean')
    sign_list_2 = load_sign_list('organization_list_clean')

    node_list_1_clean = [node_clean(node, sign_list_1, sign_list_2) for node in tqdm(node_list_1)]
    node_list_2_clean = [node_clean(node, sign_list_1, sign_list_2) for node in tqdm(node_list_2)]

    node2node_clean_1 = dict(zip(node_list_1, node_list_1_clean))
    node2node_clean_2 = dict(zip(node_list_2, node_list_2_clean))

    # match_stage_1
    couple_list = []
    pool = mp.Pool()
    func = partial(match_single, node2node_clean_1, node2node_clean_2, 0.6)
    for couple in tqdm(pool.imap(func, node_list_1), total=len(node_list_1)):
        couple_list.extend(couple)
    pool.close()
    pool.join()

    # save
    with open('../../data/match_base2sc/match_result.json', 'w', encoding='utf-8') as f:
        json.dump(couple_list, f, ensure_ascii=False, indent=4)


def analysis():
    """
    热力图
    :return:
    """
    # load couple_list
    with open('../../data/match_base2sc/match_result.json', 'r', encoding='utf-8') as f:
        couple_list = json.load(f)
    num_collection_link_num = dict()
    num_collection_node_num = dict()
    for k1 in tqdm([0.7 + 0.01 * i for i in range(30)]):
        num_collection_link_num[k1] = dict()
        num_collection_node_num[k1] = dict()
        for k2 in [0.7 + 0.01 * i for i in range(30)]:
            couple_list_ = [couple for couple in couple_list if couple[2] > k1 and couple[3] > k2]
            num_collection_link_num[k1][k2] = len(couple_list_)
            node_base2sc = defaultdict(set)
            for couple in couple_list_:
                node_base2sc[couple[0]].add(couple[1])
            num_collection_node_num[k1][k2] = len(node_base2sc)
    # to excel for heatmap by pandas
    df = pd.DataFrame(num_collection_link_num)
    df.to_excel('../../data/match_base2sc/match_result_link_num_heatmap.xlsx', index=True)
    df = pd.DataFrame(num_collection_node_num)
    df.to_excel('../../data/match_base2sc/match_result_node_num_heatmap.xlsx', index=True)


def match_output(k1, k2):
    """
    根据k1和k2输出匹配结果
    分两步保存
    :return:
    """
    with open('../../data/match_base2sc/match_result.json', 'r', encoding='utf-8') as f:
        couple_list = json.load(f)
    node_base2sc4safe_1 = defaultdict(dict)
    for node_base, node_sc, sim_1, sim_2 in couple_list:
        if sim_1 > 0.95 and sim_2 > 0.95:
            node_base2sc4safe_1[node_base][node_sc] = {'sim_1': sim_1, 'sim_2': sim_2}
    logging.info('node_base2sc4safe_1: %d', len(node_base2sc4safe_1))
    with open('../../data/match_base2sc/node_base2sc4safe_1.json', 'w', encoding='utf-8') as f:
        json.dump(node_base2sc4safe_1, f, ensure_ascii=False, indent=4)
    node_base2sc = defaultdict(dict)
    for node_base, node_sc, sim_1, sim_2 in couple_list:
        if sim_1 > k1 and sim_2 > k2:
            if node_base in node_base2sc4safe_1 and node_sc in node_base2sc4safe_1[node_base]:
                continue
            node_base2sc[node_base][node_sc] = {'sim_1': sim_1, 'sim_2': sim_2}
    logging.info('node_base2sc: %d', len(node_base2sc))
    node_base2sc4safe_2 = {node: node_base2sc[node] for node in node_base2sc if len(node_base2sc[node]) <= 2}
    logging.info('node_base2sc4safe_2: %d', len(node_base2sc4safe_2))
    safe_list = list(set(node_base2sc4safe_1.keys()) | set(node_base2sc4safe_2.keys()))
    logging.info('node_base2sc4safe: %d', len(safe_list))

    with open('../../data/match_base2sc/node_base2sc4safe_2.json', 'w', encoding='utf-8') as f:
        json.dump(node_base2sc4safe_2, f, ensure_ascii=False, indent=4)
    node_base2sc4hand = {node: node_base2sc[node] for node in node_base2sc if len(node_base2sc[node]) > 2}
    node_base2sc4hand = dict(sorted(node_base2sc4hand.items(), key=lambda x: len(x[1]), reverse=True))
    logging.info('node_base2sc4hand: %d', len(node_base2sc4hand))
    hand_list = list(set(node_base2sc4hand.keys()) - set(node_base2sc4safe_1.keys()))
    logging.info('node_base2sc4hand: %d', len(hand_list))
    with open('../../data/match_base2sc/node_base2sc4hand.json', 'w', encoding='utf-8') as f:
        json.dump(node_base2sc4hand, f, ensure_ascii=False, indent=4)


def match_result_combine():
    with open('../../data/match_base2sc/node_base2sc4safe_1.json', 'r', encoding='utf-8') as f:
        node_base2sc4safe_1 = json.load(f)
    with open('../../data/match_base2sc/node_base2sc4safe_2.json', 'r', encoding='utf-8') as f:
        node_base2sc4safe_2 = json.load(f)
    with open('../../data/match_base2sc/node_base2sc4hand_clean.json', 'r', encoding='utf-8') as f:
        node_base2sc4hand_clean = json.load(f)
    node_base2sc4hand_clean = {node: set(match_items) for node, match_items in node_base2sc4hand_clean.items()}
    node_base2sc4safe_1 = {node: set(match_items.keys()) for node, match_items in node_base2sc4safe_1.items()}
    node_base2sc4safe_2 = {node: set(match_items.keys()) for node, match_items in node_base2sc4safe_2.items()}
    node_base2sc_combine = defaultdict(set)
    for node_base2sc in [node_base2sc4safe_1, node_base2sc4safe_2, node_base2sc4hand_clean]:
        for node_base, node_sc_list in node_base2sc.items():
            node_base2sc_combine[node_base].update(node_sc_list)

    logging.info('node_base2sc: %d', len(node_base2sc_combine))
    # set 2 list
    node_base2sc_combine = {node: list(node_base2sc_combine[node]) for node in node_base2sc_combine}
    # save
    with open('../../data/match_base2sc/node_base2sc.json', 'w', encoding='utf-8') as f:
        json.dump(node_base2sc_combine, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    # match()
    # analysis()
    # 根据match_result的表二，k1,k2的阈值选择为0.67, 0.82
    # match_output(0.67, 0.82)
    match_result_combine()
