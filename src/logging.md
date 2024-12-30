2024-12-30 13:05:40,946 - root - INFO - 1. node clean
2024-12-30 13:05:40,946 - root - INFO - 1.1 get node core
2024-12-30 13:05:40,988 - root - INFO -   node_index2node_core: 12197
2024-12-30 13:05:40,988 - root - INFO -   node_core2node_index: 23637
2024-12-30 13:05:40,990 - root - INFO - 1.2 trans sc
2024-12-30 13:05:40,990 - root - INFO -   1. node collection from link_list_sc
2024-12-30 13:05:44,618 - root - INFO -       node_sc_list: 232250
2024-12-30 13:05:44,619 - root - INFO -   2. get node_sc2node_index, which is not in node_core2node_index
2024-12-30 13:05:44,714 - root - INFO -   3. link trans and link remove
2024-12-30 13:05:46,114 - root - INFO -       num of link_list original: 1181605
2024-12-30 13:05:46,279 - root - INFO -       num of link_list after remove self link: 1181330
2024-12-30 13:05:46,571 - root - INFO -       num of link_list after remove non-core link: 567851
2024-12-30 13:05:46,691 - root - INFO - 2. get neighbor
2024-12-30 13:05:46,855 - root - INFO -   node_core2neighbor_dict: 9147
2024-12-30 13:05:46,857 - root - INFO -   node_core2neighbor_dict: 12197
2024-12-30 13:05:46,857 - root - INFO - 3. tech resource
2024-12-30 13:05:46,916 - root - INFO -   node_patent2vec: torch.Size([12197, 1024])
2024-12-30 13:05:46,919 - root - INFO -   tech_resource: torch.Size([12197, 1024])
2024-12-30 13:05:48,339 - root - INFO -   tech_resource saved successfully
Tech resource calculated successfully.
