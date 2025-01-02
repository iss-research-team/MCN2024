import numpy as np
import torch
from utils import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


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
        # check 0
        # 存在有专利信息但是没有向量的情况 - 非常不好的情况
        if torch.sum(resource) == 0.0:
            logging.info('  resource has 0')
            logging.info('  resource_index: %s', resource_index)
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
