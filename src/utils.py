import json
import logging
from collections import defaultdict

logging = logging.getLogger(__name__)


def get_node_core():
    """
    对
    node_base2sc.json
    node_base2patent.json
    取交集
    :return:
    """
    # load node_base2sc
    with open('../data/inputs/node_base2sc.json', 'r', encoding='utf-8') as f:
        node_base2sc = json.load(f)

    # load node_base2patent
    with open('../data/inputs/node_base2patent.json', 'r', encoding='utf-8') as f:
        node_base2patent = json.load(f)

    # 基于patent维数据创建一个唯一的字典
    node_index2node_core = {"core_" + str(index): node for index, node in enumerate(node_base2patent.keys())}
    node_core2node_index = {}

    for index, node in node_index2node_core.items():
        node_list_sc = node_base2sc.get(node, [])
        for node_sc in node_list_sc + [node]:
            node_core2node_index[node_sc] = index

    logging.info("  node_index2node_core: %s", len(node_index2node_core))
    logging.info("  node_core2node_index: %s", len(node_core2node_index))

    return node_index2node_core, node_core2node_index


def sc_trans(node_core2node_index):
    """
    sc转换
    :return:
    """
    logging.info('  1. node collection from link_list_sc')
    # load node_sc2index
    with open('../data/inputs/node2index_sc.json', 'r', encoding='utf-8') as f:
        node_sc2index = json.load(f)
    # trans index2node
    index2node_sc = {index: node for node, index in node_sc2index.items()}

    # load link_sc
    with open('../data/inputs/link_list_sc.json', 'r', encoding='utf-8') as f:
        link_list = json.load(f)
    # link_clean
    link_list = [link[:2] for link in link_list]
    # index 2 node_sc
    link_list = [[index2node_sc[s], index2node_sc[t]] for s, t in link_list]
    # node_list
    node_sc_list = sorted(list(set([s for s, t in link_list] + [t for s, t in link_list])))
    logging.info('      node_sc_list: %s', len(node_sc_list))

    logging.info('  2. get node_sc2node_index, which is not in node_core2node_index')
    # node_sc2node_index: not in node_core2node_index
    node_sc2node_index = {}
    index = 0
    for node_sc in node_sc_list:
        if node_sc not in node_core2node_index:
            node_sc2node_index[node_sc] = "sc_" + str(index)
            index += 1

    logging.info('  3. link trans and link remove')
    link_list_trans = []
    for s, t in link_list:
        if s in node_core2node_index:
            s = node_core2node_index[s]
        else:
            s = node_sc2node_index[s]
        if t in node_core2node_index:
            t = node_core2node_index[t]
        else:
            t = node_sc2node_index[t]
        link_list_trans.append([s, t])

    logging.info('      num of link_list original: %s', len(link_list_trans))
    # remove self link
    link_list_trans = [link for link in link_list_trans if link[0] != link[1]]
    logging.info('      num of link_list after remove self link: %s', len(link_list_trans))
    link_list_trans = [link for link in link_list_trans if link[0].startswith('core_') or link[1].startswith('core_')]
    logging.info('      num of link_list after remove non-core link: %s', len(link_list_trans))
    return link_list_trans


def get_neighbors(node_index2node_core, link_list):
    """
    获取core的邻域
    bug report: list -> set
    :param node_index2node_core:
    :param link_list:
    :return:dict{list}
    """

    node_core2neighbor_dict = defaultdict(list)
    for s, t in link_list:
        if s in node_index2node_core and t in node_index2node_core:
            node_core2neighbor_dict[s].append(t)
            node_core2neighbor_dict[t].append(s)
    logging.info('  node_core2neighbor_dict: %s', len(node_core2neighbor_dict))
    for node_index in node_index2node_core:
        if node_index not in node_core2neighbor_dict:
            node_core2neighbor_dict[node_index] = []
    logging.info('  node_core2neighbor_dict: %s', len(node_core2neighbor_dict))

    return node_core2neighbor_dict
