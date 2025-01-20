import json
import numpy as np
from collections import defaultdict
from utils import mix_max
from tqdm import tqdm


def node2vec():
    """
    :return:
    """
    data_path = '../../data/patent/inputs/'
    file_index_list = ['1_0', '1_1', '1_2', '1_3', '1_4', '1_5', '1_6', '1_7', '1_8', '1_9',
                       '1_10', '1_11', '1_12', '1_13', '1_14', '1_15', '1_16',
                       '2_0', '2_1', '2_2', '2_3', '2_4', '2_5', '2_6', '2_7', '2_8', '2_9',
                       '2_10', '2_11',
                       '3_0', '3_1', '3_2', '3_3', '3_4', '3_5', '3_6', '3_7', '3_8', '3_9',
                       '3_10']
    # load file_index2id2index
    file_index2id2index = defaultdict(lambda: defaultdict(int))
    for file_index in file_index_list:
        with open(data_path + f'doc2vec_{file_index}/id_index.json', 'r', encoding='utf-8') as f:
            id_list = json.load(f)
        for id_index, id_ in enumerate(id_list):
            file_index2id2index[file_index][id_] = id_index

    # load patent_feature
    file_index2patent_feature = dict()
    for file_index in file_index_list:
        # load with np
        file_index2patent_feature[file_index] = np.load(data_path + f'doc2vec_{file_index}/patent_feature.npy')

    # load node_base2patent_id
    with open(data_path + 'node_sc2patent_id.json', 'r', encoding='utf-8') as f:
        node_sc2patent_id = json.load(f)

    # node_sc2vec
    node_sc2vec = np.zeros((len(node_sc2patent_id), 1024))

    for node_index, (node_sc, patent_id_list) in tqdm(enumerate(node_sc2patent_id.items())):
        patent_id_list_collect = []
        vec_list = []
        for patent_id in patent_id_list:
            for file_index in file_index_list:
                if patent_id in file_index2id2index[file_index]:
                    if patent_id not in patent_id_list_collect:
                        patent_id_list_collect.append(patent_id)
                        patent_index = file_index2id2index[file_index][patent_id]
                        vec_list.append(file_index2patent_feature[file_index][patent_index])
        vec = mix_max(vec_list, average='mean')
        node_sc2vec[node_index] = vec

    # save node_sc2vec

    np.save('../../data/patent/outputs/node_sc2vec.npy', node_sc2vec)
    print('node_sc2vec save success')


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


if __name__ == '__main__':
    node2vec()
    print("Node2vec calculated successfully.")
    # feature_combine()
