import numpy as np
import torch
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def get_sim(target, target_tech_resource, step_list):
    """
    获取sim
    聚合step_list上面所有的节点
    计算step_list+target_tech_resource到target的相似度

    :param target: [dim]
    :param target_tech_resource: [n, dim]
    :param step_list: list
    :return:
    """
    if not step_list:
        sim = torch.matmul(target_tech_resource, target)
    else:
        integrate = torch.sum(target_tech_resource[step_list], dim=0).unsqueeze(0)
        sim = torch.matmul((integrate + target_tech_resource) / (len(step_list) + 1), target)

    return sim


def get_max_index(sim, remove_list):
    """
    get max index besides remove_list
    :param sim:
    :param remove_list:
    :return:
    """
    sim[remove_list] = float('-inf')
    max_index = torch.argmax(sim)
    return max_index.item()


def get_integrate_set_list(target_index, tech_resource, dim, p):
    """
    get integrate set list
    :param target_index:
    :param tech_resource:
    :param dim:
    :param p:
    :return:
    """
    integrate_set_list = []
    step_list = []

    remove_list = [target_index]
    target = tech_resource[target_index]

    while True:
        # get sim
        sim = get_sim(target, tech_resource, step_list)
        logging.info('  sim: %s', sim[target_index])
        # get integrate set
        integrate_set = torch.nonzero(sim > p).squeeze(1).numpy().tolist()
        integrate_set = [index for index in integrate_set if index not in remove_list]
        logging.info('  integrate_set: %s', integrate_set)
        if len(integrate_set) > 0:
            # not empty
            # 可以达成目标
            for index in integrate_set:
                integrate_set_list.append(step_list + [index.item()])
            logging.info('  integrate_set: %s', integrate_set)
            remove_list += integrate_set
        else:
            # empty
            index_max = get_max_index(sim, remove_list)
            step_list.append(index_max)
            remove_list.append(index_max)
            logging.info('  step_list: %s', step_list)

        if len(remove_list) == tech_resource.shape[0]:
            break

    return integrate_set_list


def main():
    """
    对于每一个节点
    计算其他节点从它的间接竞争者转换为直接竞争者需要整合的节点资源集和
    :return:
    node(target): node(potential): [node(to integrate)]
    """
    p = 0.9
    # load tech resource
    tech_resource = np.load('../data/inputs/node_base2tech_resource.npy')
    tech_resource = torch.tensor(tech_resource)
    dim = tech_resource.shape[1]
    # get index torch.sum(tech_resource, dim=1) != 0
    index_list = torch.nonzero(torch.sum(tech_resource, dim=1) != 0).squeeze()
    index_list = index_list.numpy().tolist()
    index_old2index_new = {index_old: index_new for index_new, index_old in enumerate(index_list)}
    tech_resource = tech_resource[index_list]  # 不存在 0 行
    # norm
    tech_resource = tech_resource / torch.norm(tech_resource, dim=1, keepdim=True)
    node2competitor = dict()

    for target_index in index_list:
        logging.info('---------- target_index: %s ----------', target_index)
        # target_tech_resource: target_index -> nan
        integrate_set_list = get_integrate_set_list(target_index, tech_resource, dim, p)
        node2competitor[target_index] = integrate_set_list


if __name__ == "__main__":
    main()
