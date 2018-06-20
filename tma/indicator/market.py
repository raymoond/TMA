# -*- coding: UTF-8 -*-

"""
indicator.market - A股市场指标计算
====================================================================
"""

from datetime import datetime
import pandas as pd

from tma.collector import today_market
from tma.collector.ts import filter_tp










def up_rate(tm=None):
    """计算市场的赚钱效应

    :param tm: pd.DataFrame 默认为 None
        get_today_market()函数的返回值；值为None时，会调用get_today_market()函数获取
    :return: {
        "总数": total,
        "上涨个股数量": up,
        "涨3个点以上个股数量": up3,
        "跌3个点以上个股数量": down3,
        "dt": dt,
        "type": "全市场"
    }

    .. versionadded:: 0.0.2
    """
    if tm is None:
        tm = today_market(use_latest=True)
    dt = datetime.now().__str__().split(".")[0]
    ntp = filter_tp(tm)
    ntp['is_up'] = ntp['changepercent'].apply(lambda x: True if x > 0.0 else False)
    ntp['is_up_3'] = ntp['changepercent'].apply(lambda x: True if x > 3.0 else False)
    ntp['is_down_3'] = ntp['changepercent'].apply(lambda x: True if x < -3.0 else False)
    up3 = dict(ntp['is_up_3'].value_counts())[True]
    up = dict(ntp['is_up'].value_counts())[True]
    down3 = dict(ntp['is_down_3'].value_counts())[True]
    total = len(ntp)
    res = {
        "总数": total,
        "上涨个股数量": up,
        "涨3个点以上个股数量": up3,
        "跌3个点以上个股数量": down3,
        "dt": dt,
        "type": "全市场"
    }
    return res

def up_rate_index():
    raise NotImplementedError

def get_turnover_top50(tm=None):
    if tm is None:
        tm = today_market(filters=['tp', 'st'], use_latest=True)
    tm.sort_values('turnoverratio', inplace=True)
    tm.reset_index(drop=True, inplace=True)
    tt_50 = tm.tail(50)
    return tt_50


def analyze_top50(tt_50=None):
    """分析换手率前五十个股的赚钱效应"""
    if tt_50 is None:
        tt_50 = get_turnover_top50()
    res = up_rate(tt_50)
    res['type'] = "换手率前50"
    return res


def get_limit_arrived(tm=None):
    """涨跌停板统计

    :param tm: pd.DataFrame: return of function today_market
    :return: pa.DataFrame
    """
    if tm is None:
        tm = today_market(use_latest=True)
    tm = filter_tp(tm)
    la = []
    for i in tm.index:
        data = tm.loc[i]
        if data['volume'] == 0.0:
            continue
        # 涨停板观察
        if data['high'] > data['settlement'] * 1.0992:
            if data['high'] > data['trade']:  # 盘中触及涨停板
                x = dict(data)
                x['kind'] = "盘中触及涨停板"
                la.append(x)
            elif data['high'] == data['low']:  # 一字涨停板
                x = dict(data)
                x['kind'] = "一字涨停板"
                la.append(x)
            elif data['high'] == data['trade']:  # 涨停板
                x = dict(data)
                x['kind'] = "涨停板"
                la.append(x)
            else:
                continue
        # 跌停板观察
        if data['low'] < data['settlement'] * 0.902:
            if data['trade'] > data['low']:  # 盘中触及跌停板
                x = dict(data)
                x['kind'] = "盘中触及跌停板"
                la.append(x)
            elif data['high'] == data['low']:  # 一字跌停板
                x = dict(data)
                x['kind'] = "一字跌停板"
                la.append(x)
            elif data['low'] == data['trade']:  # 跌停板
                x = dict(data)
                x['kind'] = "跌停板"
                la.append(x)
            else:
                continue
    df_la = pd.DataFrame(la)
    df_sel = df_la[['code', 'name', 'trade',
                    'kind', 'turnoverratio', 'changepercent']]
    df_sel = df_sel.sort_values('kind')
    return df_sel.reset_index(drop=True)


def analyze_la(la=None):
    """涨跌停板分析

    :param la: pd.DataFrame: return of function limit_arrived
    :return:
    """
    if la is None:
        la = get_limit_arrived()
    la_kind = dict(la['kind'].value_counts())

    x1 = la_kind['涨停板'] if '涨停板' in la_kind.keys() else 0
    x2 = la_kind['一字涨停板'] if '一字涨停板' in la_kind.keys() else 0
    x3 = la_kind['盘中触及涨停板'] if '盘中触及涨停板' in la_kind.keys() else 0
    x4 = la_kind['跌停板'] if '跌停板' in la_kind.keys() else 0
    x5 = la_kind['一字跌停板'] if '一字跌停板' in la_kind.keys() else 0
    x6 = la_kind['盘中触及跌停板'] if '盘中触及跌停板' in la_kind.keys() else 0

    msg = "目前两市涨停%i家，其中一字板%i家；盘中触及涨停后打开家数为%i，" \
          "封板成功率为%s；两市跌停%i家，其中一字板%i家，盘中触及跌停板%i家。" % (
              x1 + x2, x2, x3, str(round((x1 + x2) / (x1 + x2 + x3), 2) * 100) + "%",
              x4 + x5, x5, x6)
    for key in la_kind.keys():
        la_kind[key] = str(la_kind[key])
    return msg, la_kind




def get_env_status(console_print=True):
    """获取市场大环境的综合状态，包括全市场赚钱效应、换手率TOP50赚钱效应、涨跌停分析"""
    tm = today_market(use_latest=True)

    res_m = up_rate(tm)
    msg_m = "开盘个股总数为%i家，上涨个股数量为%i家，其中涨3个点以上个股数量是%i家，跌3个点以上个股数量是%i家" % (
        res_m['总数'], res_m['上涨个股数量'],
        res_m['涨3个点以上个股数量'], res_m['跌3个点以上个股数量']
    )

    tt_50 = get_turnover_top50(tm)
    res_t50 = analyze_top50(tt_50)
    msg_t50 = "换手率前50只个股中，上涨个股数量为%i家，其中涨3个点以上个股数量是%i家，跌3个点以上个股数量是%i家" % (
        res_t50['上涨个股数量'], res_t50['涨3个点以上个股数量'], res_t50['跌3个点以上个股数量']
    )


    la = get_limit_arrived(tm)
    msg_zdt, la_kind = analyze_la(la)
    if console_print:
        print("%s : " % datetime.now().__str__().split(".")[0])
        print("【A股全市场】 - " + msg_m)
        print("【换手率TOP50】 - " + msg_t50)
        print("【涨跌停分析】 - " + msg_zdt)

    res_raw = {
        "A股全市场": {
            "raw": str(res_m),
            "msg": msg_m
        },
        "换手率TOP50": {
            "raw": str(res_t50),
            "msg": msg_t50
        },
        "涨跌停分析": {
            "raw": str(la_kind),
            "msg": msg_zdt
        }
    }
    return res_raw


