import json
import os
from collections import defaultdict
from tqdm import tqdm
import csv
from utils import holder_clean


def get_node2patent():
    """
    get node2patent
    :return:
    """
    # load holder2patent
    with open('../../data/patent/inputs/patent2holder.json', 'r', encoding='utf-8') as f:
        patent2holder = json.load(f)

    # load node_base2patent
    with open('../../data/match_sc2patent/node_sc2patent.json', 'r', encoding='utf-8') as f:
        node_sc2patent = json.load(f)

    node_patent2sc = dict()
    for node_sc, node_patent_list in node_sc2patent.items():
        for node_patent in node_patent_list:
            node_patent2sc[node_patent] = node_sc

    node_sc2patent_id = defaultdict(set)

    for patent_id, info in tqdm(patent2holder.items(), total=len(patent2holder)):
        holder_dwpi = info['holder_dwpi']
        holder_orig = info['holder_orig']
        inventors_dwpi = info['inventors_dwpi']
        inventors_orig = info['inventors_orig']
        holder_dwpi_list = holder_clean(holder_dwpi, inventors_dwpi)
        holder_orig_list = holder_clean(holder_orig, inventors_orig)
        holder_list = list(set(holder_dwpi_list + holder_orig_list))
        for holder in holder_list:
            if holder in node_patent2sc:
                node_sc2patent_id[node_patent2sc[holder]].add(patent_id)

    # set2list
    node_sc2patent_id = {node: list(node_sc2patent_id[node]) for node in node_sc2patent_id}
    # save node2patent
    with open('../../data/patent/inputs/node_sc2patent_id.json', 'w', encoding='utf-8') as f:
        json.dump(node_sc2patent_id, f, ensure_ascii=False, indent=4)


def get_info(inf_list, inf_index):
    try:
        inf = inf_list[inf_index]
    except IndexError:
        inf = ''
    return inf


def extract_patent():
    with open('../../data/patent/inputs/node_sc2patent_id.json', 'r', encoding='utf-8') as f:
        node_base2patent_id = json.load(f)

    patent_id_list_collect = set()
    for node_base, patent_id_list in node_base2patent_id.items():
        for patent_id in patent_id_list:
            patent_id_list_collect.add(patent_id)

    print('patent_id_list_collect', len(patent_id_list_collect))
    patent_id2doc = {}

    num = 0
    part = 2

    for prepare_path in ['../../data/patent/source/part_2']:
        csv.field_size_limit(500 * 1024 * 1024)
        prepare_file_list = os.listdir(prepare_path)

        for each_file in prepare_file_list:
            csv_read = csv.reader(open(os.path.join(prepare_path, each_file), 'r', encoding='UTF-8'))
            next(csv_read)
            # 判断第二行是否是表头
            header = next(csv_read)
            if '公开号' not in header:
                header = next(csv_read)

            patent_id_index = header.index('公开号')
            title_index = header.index('标题 - DWPI')
            abstract_index = header.index('摘要 - DWPI')
            claims_index = header.index('独立权利要求')

            for inf_list in tqdm(csv_read, desc=each_file):
                # 信息归拢
                patent_id = get_info(inf_list, patent_id_index)
                if patent_id not in patent_id_list_collect:
                    continue
                title = get_info(inf_list, title_index)
                abstract = get_info(inf_list, abstract_index)
                claims = get_info(inf_list, claims_index)
                if title == '' and abstract == '' and claims == '':
                    continue
                patent_id2doc[patent_id] = {'title': title, 'abstract': abstract, 'claims': claims}
                # 专利数量到500000保存一次
                if len(patent_id2doc) % 500000 == 0:
                    with open(f'../../data/patent/inputs/patent_id2doc/patent_id2doc_{part}_{num}.json', 'w',
                              encoding='utf-8') as f:
                        json.dump(patent_id2doc, f, ensure_ascii=False, indent=4)
                    num += 1
                    patent_id2doc = {}

    # save
    with open(f'../../data/patent/inputs/patent_id2doc/patent_id2doc_{part}_{num}.json', 'w', encoding='utf-8') as f:
        json.dump(patent_id2doc, f, ensure_ascii=False, indent=4)


# def patent_combine():
#     patent_id2doc = {}
#     patent_id2doc_path = '../../data/patent/inputs/patent_id2doc'
#     patent_id2doc_file_list = os.listdir(patent_id2doc_path)
#
#     for file in tqdm(patent_id2doc_file_list):
#         with open(os.path.join(patent_id2doc_path, file), 'r', encoding='utf-8') as f:
#             patent_id2doc_ = json.load(f)
#         patent_id2doc.update(patent_id2doc_)
#     # 500000保存一次
#     patent_id2doc_clean_path = '../../data/patent/inputs/patent_id2doc'
#     if not os.path.exists(patent_id2doc_clean_path):
#         os.makedirs(patent_id2doc_clean_path)
#
#     num = 0
#     patent_id2doc_clean = {}
#     for patent_id in tqdm(patent_id2doc):
#         patent_id2doc_clean[patent_id] = patent_id2doc[patent_id]
#         if len(patent_id2doc_clean) % 500000 == 0:
#             with open(os.path.join(patent_id2doc_clean_path, 'patent_id2doc_{}.json'.format(num)), 'w',
#                       encoding='utf-8') as f:
#                 json.dump(patent_id2doc_clean, f, ensure_ascii=False, indent=4)
#             num += 1
#             patent_id2doc_clean = {}


if __name__ == '__main__':
    # get_node2patent()
    extract_patent()
    # patent_combine()
