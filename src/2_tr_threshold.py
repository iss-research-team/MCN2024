import numpy as np
import torch
import logging
from scipy.stats import jarque_bera
from scipy.stats import kstest
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def direct_competitor_count(sim, threshold):
    """
    计算直接竞争者的数量
    :param sim:
    :param threshold:
    :return:
    """
    logging.info('  threshold: %s', threshold)
    count_list = np.sum(sim > threshold, axis=1)
    return count_list


def main():
    """
    估计一个技术资源之间的相似度的阈值
        大于该阈值为直接竞争者
        小于该阈值为潜在竞争者
    :return:
    """
    logging.info('Estimate the threshold of similarity between two tech resources')
    # load tech resource
    tech_resource = np.load('../data/inputs/node_base2tech_resource.npy')
    tech_resource = torch.tensor(tech_resource)
    tech_resource.cuda()
    logging.info('  tech_resource: %s', tech_resource.shape)
    # remove 0 line
    tech_resource = tech_resource[torch.sum(tech_resource, dim=1) != 0]
    logging.info('  tech_resource: %s', tech_resource.shape)
    # norm
    tech_resource = tech_resource / torch.norm(tech_resource, dim=1, keepdim=True)
    sim = torch.mm(tech_resource, tech_resource.T)
    upper_triangle = sim[torch.triu(torch.ones(sim.shape), diagonal=1) == 1]
    sim = sim.cpu().numpy()
    upper_triangle = upper_triangle.cpu().numpy()
    logging.info('  upper_triangle: %s', upper_triangle.shape)

    # JS test
    _, p_value = jarque_bera(upper_triangle)
    logging.info('  JB test')
    logging.info('  p_value: %s', p_value)
    if p_value < 0.05:
        logging.info('  JS test: tech resource is not normal distribution')
    else:
        logging.info('  JS test: tech resource is normal distribution')

    # KS test
    stat, p_value = kstest(upper_triangle, 'norm')
    logging.info('  KS test')
    logging.info('  p_value: %s', p_value)
    if p_value < 0.05:
        logging.info('  KS test: tech resource is not normal distribution')
    else:
        logging.info('  KS test: tech resource is normal distribution')

    # 抽取1000000个样本，概率密度图
    np.random.seed(20241230)
    sample = np.random.choice(upper_triangle, 1000000)
    sns.kdeplot(sample, fill=True)
    plt.xlabel('similarity')
    plt.ylabel('density')
    plt.title('Tech Resource Similarity Distribution')
    plt.savefig('../img/tech_resource_similarity_distribution.png')

    # 均值
    mean = np.mean(upper_triangle)
    logging.info('  mean: %s', mean)
    # 方差
    std = np.std(upper_triangle)
    logging.info('  std: %s', std)
    # 阈值 = 均值 + k * 方差， k = 1，2, 3
    threshold_1 = mean + std
    count_list_1 = direct_competitor_count(sim, threshold_1)
    threshold_2 = mean + 2 * std
    count_list_2 = direct_competitor_count(sim, threshold_2)
    threshold_3 = mean + 3 * std
    count_list_3 = direct_competitor_count(sim, threshold_3)
    # 概率密度图
    sns.kdeplot(count_list_1, fill=True, label='p=mean + std')
    sns.kdeplot(count_list_2, fill=True, label='p=mean + 2 * std')
    sns.kdeplot(count_list_3, fill=True, label='p=mean + 3 * std')
    plt.xlabel('count')
    plt.ylabel('density')
    plt.title('Direct Competitor Count Distribution')
    plt.legend()
    # log 坐标
    plt.yscale('log')
    plt.xscale('log')

    plt.savefig('../img/direct_competitor_count_distribution.png')


if __name__ == '__main__':
    main()
    print("Threshold calculated successfully.")
