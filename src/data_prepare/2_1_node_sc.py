import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def get_link_list(label):
    """
    将link_list中的index转换为node
    :param label:
    :return:
    """
    # load link_list
    link_list_path = '../../data/supply_chain/source/link_list_{}.json'.format(label)
    with open(link_list_path, 'r', encoding='UTF-8') as file:
        link_list = json.load(file)
    # load node2index
    node2index_path = '../../data/supply_chain/source/node2index_{}.json'.format(label)
    with open(node2index_path, 'r', encoding='UTF-8') as file:
        node2index = json.load(file)
    index2node = {index: node for node, index in node2index.items()}
    # link_list
    link_list = [[index2node[s].lower(), index2node[t].lower(), time] for s, t, time in link_list]
    return link_list


def main():
    """
    数据格式如下：
        link:[index,index]
        node2index:{node:index}
        node2node:{node_code:node}

    第三个数据目前用不到

    整个节点提取的过程分为两步：
        1. 将每一个link_list中每一个link中的的index转换为node
        2. 组合所有的link_list中的node，去重，构建node2index
    :return:
    """
    link_list = []
    for label in ['communication', 'energy', 'industry', 'materials', 'medical', 'technology']:
        link_list_tmp = get_link_list(label)
        link_list.extend(link_list_tmp)
    # node2index
    node_list = list(set([s for s, _, _ in link_list] + [t for _, t, _ in link_list]))
    node2index = {node: index for index, node in enumerate(node_list)}
    # save
    with open('../../data/supply_chain/inputs/node2index_sc.json', 'w', encoding='UTF-8') as file:
        json.dump(node2index, file)
    logging.info('node2index {}'.format(len(node2index)))
    # save
    link_list = [[node2index[s], node2index[t], time] for s, t, time in link_list]
    logging.info('link_list {}'.format(len(link_list)))
    link_list = [str(s) + ',' + str(t) + ',' + str(time) for s, t, time in link_list]
    link_list = list(set(link_list))
    link_list = [[int(i) for i in link.split(',')] for link in link_list]
    with open('../../data/supply_chain/inputs/link_list_sc.json', 'w', encoding='UTF-8') as file:
        json.dump(link_list, file)
    logging.info('link_list {}'.format(len(link_list)))


if __name__ == '__main__':
    main()
