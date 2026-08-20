"""
1.生成行为one-hot
2.计算每个session中每种event的个数
3.计算每个session中每个aid的每种event的个数
4.计算每个session中每个aid最近一次出现距离session尾部的距离
5.ts_diff_pre-计算每个session中每个event和上一个event的时间间隔
6.ts_diff_post-计算每个session中每个event和下一个event的时间间隔
7.对ts_diff_pre和ts_diff_post按照aid计算mean,即这个 aid 在该 session 中出现时，与前一个行为时间间隔的平均值。或者这个 aid 出现后，到下一次行为之间的平均间隔。

最终(session,aid)得到
session aid
isin_0_count	出现总次数
isin_0_clicks	点击次数
isin_0_carts	加购次数
isin_0_orders	购买次数
isin_0_rank	最近一次出现距离 session 尾部的位置
isin_0_ts_diff_pre	与前一个 event 的平均时间差
isin_0_ts_diff_post	与后一个 event 的平均时间差


"""