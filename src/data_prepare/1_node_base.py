import pandas as pd
import json


def get_node2index():
    """
    获取node2index
    :return:
    """
    df = pd.read_excel('../../data/base/source/10-39.xls', sheet_name='检索结果')['公司名称'].tolist()
    node2index = {node.lower(): index for index, node in enumerate(df)}
    with open('../../data/base/inputs/node2index_base.json', 'w', encoding='UTF-8') as file:
        json.dump(node2index, file)
    print('node2index', len(node2index))


if __name__ == '__main__':
    get_node2index()
