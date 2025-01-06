import os
import csv
import json
from tqdm import tqdm
from collections import defaultdict


def get_str(str1, str2):
    if str1 != '':
        inf = str1
    elif str2 != '':
        inf = str2
    else:
        inf = ''
    # 保证每一个句子的末尾是“. ”
    if inf:
        if inf[-1] == '.':
            inf += ' '
        else:
            inf += '. '
    return inf


def not_empty(s):
    return s and s.strip()


def time_deal(time):
    """
    example:
        1989-08-03 | 1990-01-24 | 1990-09-14 | 1991-10-11 | 1992-09-29
    :param time:
    :return:
        year_list: [1989, 1990, 1990, 1991, 1992]
    """
    time_list = time.split(' | ')
    year_list = [time.strip().split('-')[0] for time in time_list]
    year_list = [int(year) for year in year_list if year]
    year_list = sorted(year_list)
    return year_list


def get_year(time_dwpi, time):
    """

    :param time_dwpi:
    :param time:
    :return:
    """
    time_dwpi_list = time_deal(time_dwpi)
    time_list = time_deal(time)
    if time_dwpi_list:
        # dwpi优先
        return time_dwpi_list[0]
    elif time_list:
        # dwpi为空，time优先
        return time_list[0]
    else:
        return 0


def get_info(inf_list, inf_index):
    try:
        inf = inf_list[inf_index]
    except IndexError:
        inf = ''
    return inf


def deal(prepare_path):
    """
    专利信息处理
    :param prepare_path:
    :return:
    """
    csv.field_size_limit(500 * 1024 * 1024)

    prepare_file_list = os.listdir(prepare_path)

    patent_id2holders = {}

    for each_file in prepare_file_list:
        csv_read = csv.reader(open(os.path.join(prepare_path, each_file), 'r', encoding='UTF-8'))
        next(csv_read)
        # 判断第二行是否是表头
        header = next(csv_read)
        if '公开号' not in header:
            header = next(csv_read)

        patent_id_index = header.index('公开号')
        holder_dwpi_index = header.index('专利权人 - DWPI')
        holder_orig_index = header.index('专利权人 - 原始')
        inventors_dwpi_index = header.index('发明人 - DWPI')
        inventors_orig_index = header.index('发明人 - 原始')
        time_dwpi_index = header.index('优先权日 - DWPI')
        time_index = header.index('优先权日')

        for inf_list in tqdm(csv_read, desc=each_file):
            # 信息归拢
            patent_id = get_info(inf_list, patent_id_index)
            holder_dwpi = get_info(inf_list, holder_dwpi_index)
            holder_orig = get_info(inf_list, holder_orig_index)
            inventors_dwpi = get_info(inf_list, inventors_dwpi_index)
            inventors_orig = get_info(inf_list, inventors_orig_index)
            time_dwpi = get_info(inf_list, time_dwpi_index)
            time = get_info(inf_list, time_index)
            # 根据time_dwpi和time判断优先权年
            time_year = get_year(time_dwpi, time)
            # 1.时间的问题时间为空跳过循环
            if time_year == 0:
                continue
            # 2.去除holder为空的情况
            if not holder_dwpi and not holder_orig:
                continue
            # 2.去重机制
            if patent_id not in patent_id2holders:
                patent_id2holders[patent_id] = {
                    'holder_dwpi': holder_dwpi,
                    'holder_orig': holder_orig,
                    'inventors_dwpi': inventors_dwpi,
                    'inventors_orig': inventors_orig,
                    'time': time_year
                }
    print('file:', prepare_path, 'patent_count:', len(patent_id2holders))
    return patent_id2holders


def get_patent2holder_part(part, part_file_list):
    # 去重机制
    patent_id2holders = {}
    patent_path = '../../data/patent/'

    for index, prepare_path in enumerate(part_file_list):
        prepare_path = os.path.join(patent_path, prepare_path)
        patent_id2holders.update(deal(prepare_path))

    print('获取专利数量：', len(patent_id2holders))
    # 3.写入json
    with open('../../data/patent/inputs/patent2holder_part{}.json'.format(part), 'w', encoding='utf-8') as file:
        json.dump(patent_id2holders, file, ensure_ascii=False, indent=4)


def get_patent2holder():
    part_file_list = [['part1'], ['part2'], ['part3_1', 'part3_2', 'part3_3']]
    for part, part_file_list in enumerate(part_file_list):
        get_patent2holder_part(part, part_file_list)


def patent_combine():
    """
    将3个专利合并
    :return:
    """
    with open('../../data/patent/inputs/patent2holder_part0.json', 'r', encoding='utf-8') as f:
        patent2holder_1 = json.load(f)
    with open('../../data/patent/inputs/patent2holder_part1.json', 'r', encoding='utf-8') as f:
        patent2holder_2 = json.load(f)
    with open('../../data/patent/inputs/patent2holder_part2.json', 'r', encoding='utf-8') as f:
        patent2holder_3 = json.load(f)

    print('patent2holder_1', len(patent2holder_1))
    print('patent2holder_2', len(patent2holder_2))
    print('patent2holder_3', len(patent2holder_3))

    patent2holder = {}
    patent2holder.update(patent2holder_1)
    patent2holder.update(patent2holder_2)
    patent2holder.update(patent2holder_3)
    print('patent2holder', len(patent2holder))
    with open('../../data/patent/inputs/patent2holder.json', 'w', encoding='utf-8') as f:
        json.dump(patent2holder, f, ensure_ascii=False, indent=4)


def holder_clean(holders, inventors):
    """
    从专利权人中去除发明人
    :param holders:
    :param inventors:
    :return:
    """
    holder_list = holders.split(' | ')
    holder_list = [holder.lower() for holder in holder_list]
    holder_list = filter(not_empty, holder_list)
    inventor_list = inventors.split(' | ')
    inventor_list = [inventor.lower() for inventor in inventor_list]
    inventor_list = filter(not_empty, inventor_list)
    holder_list = list(set(holder_list) - set(inventor_list))
    return holder_list


def holder_clean_plus(holder_dwpi_list, holder_orig_list, dwpi2orig, orig2dwpi):
    """

    :param holder_dwpi_list:
    :param holder_orig_list:
    :param dwpi2orig:
    :param orig2dwpi:
    :return:
    """
    holder_dwpi_list_clean = holder_dwpi_list.copy()
    holder_orig_list_clean = holder_orig_list.copy()
    for h_dwpi in holder_dwpi_list:
        if h_dwpi in dwpi2orig:
            h_orig_set = dwpi2orig[h_dwpi]
            if h_orig_set & set(holder_orig_list):
                # h_dwpi在holder_dwpi_list中，h_orig在holder_orig_list中
                holder_dwpi_list_clean = list(set(holder_dwpi_list_clean) - {h_dwpi})
                holder_orig_list_clean = list(set(holder_orig_list_clean) - h_orig_set)
    for h_orig in holder_orig_list:
        if h_orig in orig2dwpi:
            h_dwpi_set = orig2dwpi[h_orig]
            if h_dwpi_set & set(holder_dwpi_list):
                # h_orig在holder_orig_list中，h_dwpi在holder_dwpi_list中
                holder_orig_list_clean = list(set(holder_orig_list_clean) - {h_orig})
                holder_dwpi_list_clean = list(set(holder_dwpi_list_clean) - h_dwpi_set)
    return holder_dwpi_list_clean, holder_orig_list_clean


def get_holder_couple():
    """
    构建holder dwpi2ori组合，用于匹配
    :return:
    """
    with open('../../data/patent/inputs/patent2holder.json', 'r', encoding='utf-8') as f:
        patent2holder = json.load(f)

    # step1
    # len(holder_dwpi_list) == 1 and len(holder_orig_list) == 1:
    dwpi2orig = defaultdict(set)
    orig2dwpi = defaultdict(set)
    patent2holder_left = {}
    for patent, info in tqdm(patent2holder.items(), total=len(patent2holder)):
        holder_dwpi = info['holder_dwpi']
        holder_orig = info['holder_orig']
        inventors_dwpi = info['inventors_dwpi']
        inventors_orig = info['inventors_orig']
        holder_dwpi_list = holder_clean(holder_dwpi, inventors_dwpi)
        holder_orig_list = holder_clean(holder_orig, inventors_orig)
        if len(holder_dwpi_list) == 1 and len(holder_orig_list) == 1:
            dwpi2orig[holder_dwpi_list[0]].add(holder_orig_list[0])
            orig2dwpi[holder_orig_list[0]].add(holder_dwpi_list[0])
        if len(holder_dwpi_list) > 1 or len(holder_orig_list) > 1:
            patent2holder_left[patent] = (holder_dwpi_list, holder_orig_list)

    print('dwpi2orig', len(dwpi2orig))
    print('orig2dwpi', len(orig2dwpi))

    # step2
    # len(holder_dwpi_list) > 1 or len(holder_orig_list) > 1:
    while True:
        print('patent2holder_left', len(patent2holder_left))
        patent2holder = patent2holder_left
        dwpi2orig_add = defaultdict(set)
        orig2dwpi_add = defaultdict(set)
        patent2holder_left = {}

        for patent, (holder_dwpi_list, holder_orig_list) in tqdm(patent2holder.items(), total=len(patent2holder)):
            holder_dwpi_list, holder_orig_list = holder_clean_plus(holder_dwpi_list, holder_orig_list,
                                                                   dwpi2orig, orig2dwpi)
            if len(holder_dwpi_list) == 1 and len(holder_orig_list) == 1:
                dwpi2orig_add[holder_dwpi_list[0]].add(holder_orig_list[0])
                orig2dwpi_add[holder_orig_list[0]].add(holder_dwpi_list[0])
            if len(holder_dwpi_list) > 1 or len(holder_orig_list) > 1:
                patent2holder_left[patent] = (holder_dwpi_list, holder_orig_list)

        print('dwpi2orig_add', len(dwpi2orig_add))
        print('orig2dwpi_add', len(orig2dwpi_add))

        for node in dwpi2orig_add:
            dwpi2orig[node] |= dwpi2orig_add[node]
        for node in orig2dwpi_add:
            orig2dwpi[node] |= orig2dwpi_add[node]

        if dwpi2orig_add == {} and orig2dwpi_add == {}:
            break

    print('dwpi2orig', len(dwpi2orig))
    print('orig2dwpi', len(orig2dwpi))

    # save
    dwpi2orig4save = {k: list(v) for k, v in dwpi2orig.items()}
    with open('../../data/patent/inputs/dwpi2orig.json', 'w', encoding='utf-8') as f:
        json.dump(dwpi2orig4save, f, ensure_ascii=False, indent=4)
    orig2dwpi4save = {k: list(v) for k, v in orig2dwpi.items()}
    with open('../../data/patent/inputs/orig2dwpi.json', 'w', encoding='utf-8') as f:
        json.dump(orig2dwpi4save, f, ensure_ascii=False, indent=4)


# def get_holder():
#     with open('../../data/patent/inputs/patent2holder.json', 'r', encoding='utf-8') as f:
#         patent2holder = json.load(f)
#
#     holder2patent = defaultdict(list)
#     for patent, info in tqdm(patent2holder.items(), total=len(patent2holder)):
#         holder_dwpi = info['holder_dwpi']
#         inventors_dwpi = info['inventors_dwpi']
#         holder_list = holder_clean(holder_dwpi, inventors_dwpi)
#         for holder in holder_list:
#             holder2patent[holder].append(patent)
#
#     print('num of holder:', len(holder2patent))
#     with open('../../data/patent/inputs/holder2patent.json', 'w', encoding='utf-8') as f:
#         json.dump(holder2patent, f, ensure_ascii=False, indent=4)
#
#
# def get_node2index():
#     with open('../../data/patent/inputs/holder2patent.json', 'r', encoding='utf-8') as f:
#         holder2patent = json.load(f)
#
#     node2index = {}
#     for index, node in enumerate(holder2patent):
#         node2index[node] = index
#     with open('../../data/patent/inputs/node2index_patent.json', 'w', encoding='utf-8') as f:
#         json.dump(node2index, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    # 1.专利获取
    get_patent2holder()
    # 2.专利合并
    patent_combine()
    # 3.获取专利权人组合
    get_holder_couple()
    # 这里对原始的代码进行修改，在进行完整的匹配后再进行索引

    # # 3.获取专利权人
    # get_holder()
    # # 5.获取node2index
    # get_node2index()
