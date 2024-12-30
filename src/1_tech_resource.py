import json
import logging
from collections import defaultdict
import numpy as np
import torch
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


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


def get_tech_resource(node_core2neighbor):
    """
    获取tech resource
    :return:
    """
    # load node_patent2vec_mix_max_average.npy
    node_patent2vec = np.load('../data/inputs/node_base2vec_mix_max_average.npy')
    # torch
    node_patent2vec = torch.tensor(node_patent2vec)

    logging.info('  node_patent2vec: %s', node_patent2vec.shape)
    tech_resource = torch.zeros(node_patent2vec.shape)
    logging.info('  tech_resource: %s', tech_resource.shape)
    for node_core, neighbor_list in node_core2neighbor.items():
        core_index = int(node_core.split('_')[-1])
        neighbor_index_list = [int(node.split('_')[-1]) for node in neighbor_list]
        resource_index = [core_index] + neighbor_index_list
        resource = torch.mean(node_patent2vec[resource_index], dim=0)
        tech_resource[core_index] = resource
    # save
    tech_resource = tech_resource.numpy()
    np.save('../data/inputs/node_base2tech_resource.npy', tech_resource)
    logging.info('  tech_resource saved successfully')


def main():
    """
    1. 节点清理
    2. 节点邻域统计
    3. 节点领域的tech resource聚合
    :return:
    """
    # 1. 节点清理
    logging.info('1. node clean')
    # 获取核心索引
    logging.info('1.1 get node core')
    node_index2node_core, node_core2node_index = get_node_core()
    # sc转换
    logging.info('1.2 trans sc')
    link_list = sc_trans(node_core2node_index)
    # 2. 节点邻域统计
    logging.info('2. get neighbor')
    node_core2neighbor = get_neighbors(node_index2node_core, link_list)
    # 3. 节点领域的tech resource聚合
    logging.info('3. tech resource')
    get_tech_resource(node_core2neighbor)


if __name__ == '__main__':
    main()
    print("Tech resource calculated successfully.")
