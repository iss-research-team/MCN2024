import numpy as np
import torch
import networkx as nx
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from utils import *


def dp_competitor(p):
    """
    直接竞争者 间接竞争者检测
    :return:
    """
    with open(f'../data/outputs/node2integrate_set_list_{p}.json', 'r') as f:
        node2integrate_set_list = json.load(f)

    node2direct_competitor = defaultdict(list)
    node2potential_competitor = defaultdict(list)

    for target_index, integrate_set_list in node2integrate_set_list.items():
        if len(integrate_set_list) == 0:
            continue
        for integrate_set in integrate_set_list:
            if len(integrate_set) == 1:
                # 直接竞争者
                node2direct_competitor[target_index].append(integrate_set[0])
            else:
                # 潜在竞争者-集团
                node2potential_competitor[target_index].append(integrate_set)

    with open(f'../data/outputs/node2direct_competitor_{p}.json', 'w') as f:
        json.dump(node2direct_competitor, f)
    with open(f'../data/outputs/node2potential_competitor_{p}.json', 'w') as f:
        json.dump(node2potential_competitor, f)


def set_list(node_list):
    """
    list去重
    :param node_list:
    :return:
    """
    return list(set(node_list))


def get_mean_vec(node_list, node2vec):
    """
    获取平均向量
    :param node_list:
    :param node2vec:
    :return:
    """
    vec = node2vec[node_list]
    vec = vec[torch.sum(vec, dim=1) != 0]
    return torch.mean(vec, dim=0)


def tr_sim(node_list1, node_list2, node2vec):
    """
    计算相似度
    归一化之后的向量，不需要除以模长
    :param node_list1:
    :param node_list2:
    :param node2vec:
    :return:
    """
    vec1 = get_mean_vec(node_list1, node2vec)
    vec2 = get_mean_vec(node_list2, node2vec)
    return torch.dot(vec1, vec2)


def link_filter(node_list, link_list):
    """
    过滤link
    :param node_list:
    :param link_list:
    :return:
    """
    return [link for link in link_list if link[0] in set(node_list) or link[1] in set(node_list)]


def get_sub_graph(node_list, link_list):
    """
    获取子图
    :param node_list:
    :param link_list:
    :return:
    """
    sub_g = nx.Graph()
    link_list_filter = link_filter(node_list, link_list)
    sub_g.add_edges_from(link_list_filter)
    return sub_g


def get_graph_dis(node_list1, node_list2, link_list):
    """
    计算图距离
    :param node_list1:
    :param node_list2:
    :param link_list:
    :return:
    """
    G1 = get_sub_graph(node_list1, link_list)
    G2 = get_sub_graph(node_list2, link_list)
    return nx.graph_edit_distance(G1, G2)


def get_plasticity_single(target, node_p, integrate_set, link_list, node_core2neighbor, node2vec):
    """
    计算图距离
    :param target:
    :param node_p:
    :param integrate_set:
    :param link_list:
    :param node_core2neighbor:
    :param node2vec:
    :return:
        sim_tr_old
        sim_tk_new
        graph_dis
    """
    # 1.rt rk_old rk_new
    rt_node_list = set_list([target] + node_core2neighbor[target])
    rk_old_node_list = set_list([node_p] + node_core2neighbor[node_p])
    rk_new_node_list = set_list([node_p] + integrate_set + node_core2neighbor[node_p])
    # 2. sim
    sim_tr_old = tr_sim(rt_node_list, rk_old_node_list, node2vec)
    sim_tr_new = tr_sim(rt_node_list, rk_new_node_list, node2vec)
    # 3. graph_dis
    graph_dis = get_graph_dis(rk_old_node_list, rk_new_node_list, link_list)
    return sim_tr_old, sim_tr_new, 1 / graph_dis


def get_plasticity(p):
    """
    计算指标

    :return:
    target_node:
        node:
            [
                {
                    integrate_set: [node]
                    sim_tr_old: float
                    sim_tr_new: float
                    plasticity(graph_dis): float

                }
            ]
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

    with open(f'../data/outputs/node2potential_competitor_{p}.json', 'r') as f:
        node2potential_competitor = json.load(f)

    node2potential_competitor_plasticity = defaultdict(lambda: defaultdict(list))
    node2vec = np.load('../data/inputs/node_base2vec_mix_max_average.npy')
    node2vec = torch.tensor(node2vec)
    # 归一化
    node2vec = node2vec / torch.norm(node2vec, dim=1, keepdim=True)

    for target, integrate_set_list in node2potential_competitor.items():
        for integrate_set in integrate_set_list:
            for node_p in integrate_set:
                # 计算指标
                sim_tr_old, sim_tr_new, plasticity = get_plasticity_single(target, node_p, integrate_set, link_list,
                                                                           node_core2neighbor, node2vec)
                node2potential_competitor_plasticity[target][node_p].append(
                    {
                        'integrate_set': integrate_set,
                        'sim_tr_old': sim_tr_old.item(),
                        'sim_tr_new': sim_tr_new.item(),
                        'plasticity': plasticity
                    }
                )

    with open(f'../data/outputs/node2potential_competitor_plasticity_{p}.json', 'w') as f:
        json.dump(node2potential_competitor_plasticity, f)


if __name__ == "__main__":
    threshold = 0.5
    dp_competitor(threshold)
    logging.info("Direct competitor and potential competitor detected successfully.")
    get_plasticity(threshold)
    logging.info("Plasticity calculated successfully.")
