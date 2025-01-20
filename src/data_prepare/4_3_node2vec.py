import json
import numpy as np
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

import multiprocessing as mp
from functools import partial
from utils import mix_max


def feature_combine():
    """
    将几个长度的id_list组合 patent_feature组合
    :return:
    """
    file_index_list = ['1_0', '1_1', '1_2', '1_3', '1_4', '1_5', '1_6', '1_7', '1_8', '1_9',
                       '1_10', '1_11', '1_12', '1_13', '1_14', '1_15', '1_16',
                       '2_0', '2_1', '2_2', '2_3', '2_4', '2_5', '2_6', '2_7', '2_8', '2_9',
                       '2_10', '2_11',
                       '3_0', '3_1', '3_2', '3_3', '3_4', '3_5', '3_6', '3_7', '3_8', '3_9',
                       '3_10']
    length_list = [320, 384, 448, 512]
    for file_index in file_index_list:
        print(f'{file_index} start')
        id_list_all = []
        patent_feature_all = []
        for length in length_list:
            patent_feature_temp = np.load(f'../../data/patent/inputs/doc2vec_{file_index}/patent_feature_{length}.npy')
            patent_feature_temp = patent_feature_temp.tolist()
            with open(f'../../data/patent/inputs/doc2vec_{file_index}/id_{length}.json', 'r', encoding='utf-8') as f:
                id_list_temp = json.load(f)
            # length check
            assert len(id_list_temp) == len(patent_feature_temp)
            print(f'{file_index}_{length} check success')
            id_list_all.extend(id_list_temp)
            patent_feature_all.extend(patent_feature_temp)
        # save
        with open(f'../../data/patent/inputs/doc2vec_{file_index}/id.json', 'w', encoding='utf-8') as f:
            json.dump(id_list_all, f)
        np.save(f'../../data/patent/inputs/doc2vec_{file_index}/patent_feature.npy', patent_feature_all)


def patent_extract(file_index_list, file_index2id2index, file_index2patent_feature,
                   node_sc2index, node_sc2patent_id, node_sc):
    """
    :param file_index_list:
    :param file_index2id2index:
    :param file_index2patent_feature:
    :param node_sc2index
    :param node_sc2patent_id
    :param node_sc:
    :return:
    """
    patent_id_list_collect = set()
    vec_list = []
    node_index = node_sc2index[node_sc]
    logging.info(node_index)
    patent_id_list = node_sc2patent_id[node_sc]
    for patent_id in patent_id_list:
        for file_index in file_index_list:
            if patent_id in file_index2id2index[file_index]:
                if patent_id not in patent_id_list_collect:
                    patent_id_list_collect.add(patent_id)
                    patent_index = file_index2id2index[file_index][patent_id]
                    vec_list.append(file_index2patent_feature[file_index][patent_index])
    # patent number check
    if len(patent_id_list) == len(patent_id_list_collect):
        logging.info('  patent number check pass')
    else:
        logging.info('  patent number check failed, %s, %s', len(patent_id_list), len(patent_id_list_collect))

    vec = mix_max(vec_list, average='mean')
    return node_index, vec


def load_data(data_path, file_index_list):
    """

    :param data_path:
    :param file_index_list:
    :return:
    """
    # load file_index2id2index
    file_index2id2index = dict()
    for file_index in file_index_list:
        with open(data_path + f'doc2vec_{file_index}/id.json', 'r', encoding='utf-8') as f:
            id_list = json.load(f)
        id2index = {id_: id_index for id_index, id_ in enumerate(id_list)}
        file_index2id2index[file_index] = id2index
    logging.info('file_index2id2index load success')
    # load patent_feature
    file_index2patent_feature = dict()
    for file_index in file_index_list:
        # load with np
        file_index2patent_feature[file_index] = np.load(data_path + f'doc2vec_{file_index}/patent_feature.npy')
    logging.info('file_index2patent_feature load success')
    # load node_base2patent_id
    with open(data_path + 'node_sc2patent_id.json', 'r', encoding='utf-8') as f:
        node_sc2patent_id = json.load(f)
    node_sc2index = {node_sc: node_index for node_index, node_sc in enumerate(node_sc2patent_id)}
    logging.info('node_sc2patent_id load success')
    return file_index2id2index, file_index2patent_feature, node_sc2index, node_sc2patent_id


def node2vec(file_index_list, file_index2id2index, file_index2patent_feature, node_sc2index, node_sc2patent_id,
             data_path):
    """
    :return:
    """
    # node_sc2vec
    node_sc2vec = np.zeros((len(node_sc2patent_id), 1024))

    # mp
    # pool = mp.Pool(32)
    # fun = partial(patent_extract,
    #               file_index_list=file_index_list,
    #               file_index2id2index=file_index2id2index,
    #               file_index2patent_feature=file_index2patent_feature,
    #               node_sc2index=node_sc2index,
    #               node_sc2patent_id=node_sc2patent_id)

    # result = pool.map(fun, node_sc2patent_id.keys())
    # for node_index, vec in result:
    #     node_sc2vec[node_index] = vec
    # pool.close()
    # pool.join()

    for node_sc in node_sc2patent_id.keys():
        node_index, vec = patent_extract(file_index_list, file_index2id2index, file_index2patent_feature,
                                         node_sc2index, node_sc2patent_id, node_sc)
        node_sc2vec[node_index] = vec

    # save node_sc2vec

    np.save(data_path + 'node_sc2vec.npy', node_sc2vec)
    print('node_sc2vec save success')


def main():
    data_path = '../../data/patent/inputs/'

    file_index_list = ['1_0', '1_1', '1_2', '1_3', '1_4', '1_5', '1_6', '1_7', '1_8', '1_9',
                       '1_10', '1_11', '1_12', '1_13', '1_14', '1_15', '1_16',
                       '2_0', '2_1', '2_2', '2_3', '2_4', '2_5', '2_6', '2_7', '2_8', '2_9',
                       '2_10', '2_11',
                       '3_0', '3_1', '3_2', '3_3', '3_4', '3_5', '3_6', '3_7', '3_8', '3_9',
                       '3_10']
    # load data
    file_index2id2index, file_index2patent_feature, node_sc2index, node_sc2patent_id = load_data(data_path,
                                                                                                 file_index_list)

    node2vec(file_index_list, file_index2id2index, file_index2patent_feature,
             node_sc2index, node_sc2patent_id,
             data_path)


def data_test():
    """
    load data & show
    :return:
    """
    data_path = '../../data/patent/inputs/'
    node_sc2vec = np.load(data_path + 'node_sc2vec.npy')
    print(node_sc2vec.shape)
    print(node_sc2vec[0])


if __name__ == '__main__':
    main()
    print("Node2vec calculated successfully.")
