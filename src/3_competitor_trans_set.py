import numpy as np
import torch
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def get_integrate_set_list(target, potential, target_potential_tech_resource, dim, p):
    """
    get integrate set list
    :param target:
    :param potential:
    :param target_potential_tech_resource:
    :param dim:
    :param p:
    :return:
    """
    integrate_set_list = []
    step_list = []
    integrate = potential.clone()

    while True:
        # get sim
        sim = torch.matmul(target_potential_tech_resource, integrate)
        # get integrate set
        integrate_set = torch.nonzero(sim > p).squeeze()
        integrate_set_list.append(integrate_set.tolist())
        # update


def main():
    """
    对于每一个节点
    计算其他节点从它的间接竞争者转换为直接竞争者需要整合的节点资源集和
    :return:
    node(target): node(potential): [node(to integrate)]
    """
    p = 0.9829413220286369
    # load tech resource
    tech_resource = np.array([[1, 2, 3, 4],
                              [2, 4, 5, 8],
                              [0., 0., 0., 0.],
                              [1, 999, 0, -999]])
    tech_resource = torch.tensor(tech_resource)
    dim = tech_resource.shape[1]
    # get index torch.sum(tech_resource, dim=1) != 0
    index_list = torch.nonzero(torch.sum(tech_resource, dim=1) != 0).squeeze()
    logging.info('  tech_resource: %s', tech_resource)
    logging.info('  index_list: %s', index_list)
    # norm
    tech_resource = tech_resource / torch.norm(tech_resource, dim=1, keepdim=True)
    logging.info('  tech_resource: %s', tech_resource)

    node2competitor_direct = defaultdict(list)
    node2competitor_potential = defaultdict(lambda: defaultdict(list))

    for target_index in index_list:
        logging.info('---------- target_index: %s ----------', target_index)
        # get target
        target = tech_resource[target_index]
        # target_tech_resource: target_index -> nan
        target_tech_resource = tech_resource.clone()
        target_tech_resource[target_index] = torch.tensor([float('nan')] * dim)
        sim = torch.matmul(target_tech_resource, target)
        logging.info('  sim: %s', sim)
        competitor_direct_list = torch.nonzero(sim > p).squeeze()
        # if competitor_direct_list exists: add to node2competitor_direct & update target_tech_resource
        if competitor_direct_list.dim() == 0:
            logging.info('  competitor_direct_list: %s', competitor_direct_list)
            # get competitor_direct
            node2competitor_direct[target_index.item()] = competitor_direct_list.tolist()
            # update target_tech_resource
            target_tech_resource[competitor_direct_list] = torch.tensor([float('nan')] * dim)
        # if all nan in target_tech_resource: no potential competitor
        if torch.sum(torch.isnan(target_tech_resource)) == dim:
            continue

        potential2integrate = defaultdict(list)
        potential_list = torch.nonzero(torch.sum(torch.isnan(target_tech_resource), dim=1) == 0).squeeze()
        potential_list = potential_list.numpy().tolist()
        for potential_index in potential_list:
            potential = tech_resource[potential_index]
            target_potential_tech_resource = target_tech_resource.clone()
            target_potential_tech_resource[potential_index] = torch.tensor([float('nan')] * dim)


if __name__ == "__main__":
    main()
