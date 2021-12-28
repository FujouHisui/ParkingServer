import datetime
import json
import math

import pymysql

import MQTTcard


class sql_info:
    host = '127.0.0.1'
    port = 3306
    user = 'root'
    passwd = ''
    db = 'Parking'


# 入库添加记录
def log_add(card_id):
    conn = pymysql.connect(host=sql_info.host, port=sql_info.port,
                           user=sql_info.user, passwd=sql_info.passwd, db=sql_info.db)
    cursor = conn.cursor()
    try:
        cursor.execute('''INSERT INTO parking_log(card_id,start_time) VALUES( \"''' + card_id + '''\",NOW())''')
        conn.commit()
    except pymysql.err.OperationalError:
        print("输入数据有误")
        # 关闭游标
        cursor.close()
        # 关闭连接
        conn.close()
        return -1
    else:
        conn.commit()
        # 关闭游标
        cursor.close()
        # 关闭连接
        conn.close()
        return 0


def sql_delete():
    # 删
    # 表 条件
    conn = pymysql.connect(host=sql_info.host, port=sql_info.port,
                           user=sql_info.user, passwd=sql_info.passwd, db=sql_info.db)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM library.book_table WHERE book_id = 5")
    conn.commit()
    # 关闭游标
    cursor.close()
    # 关闭连接
    conn.close()


# 查
def sql_select(target, table, search):
    # 表，搜索条件
    # 创建链接对象
    conn = pymysql.connect(host=sql_info.host, port=sql_info.port,
                           user=sql_info.user, passwd=sql_info.passwd, db=sql_info.db)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT " + target + " from " + table + " where " + search)
    except pymysql.err.OperationalError:
        return -1
    else:
        result = cursor.fetchall()
        print(result)
        # 关闭游标
        cursor.close()
        # 关闭连接
        conn.close()
        return result


def search_state(card_id):  # 查询卡的状态，输入卡的ID，在库返回True，未入库返回False
    result = sql_select("*", "parking_log",
                        "parking_log.end_time IS NULL AND parking_log.start_time IS NOT NULL AND parking_log.card_id = \'"
                        + card_id + "\'")
    if len(result) != 0:
        return True
    else:
        return False


def membership_state(card_id):  # 查询卡的会员状态，输入卡的ID，返回True为未过期，False为过期
    result = sql_select("*", "member",
                        "member.expire_date >= CURRENT_DATE AND member.card_id = \'"
                        + card_id + "\'")
    if len(result) != 0:
        return True
    else:
        return False


def expire_date(card_id):  # 查询卡的会员状态，输入卡的ID，返回True为未过期，False为过期
    result = sql_select("expire_date", "member",
                        "member.expire_date >= CURRENT_DATE AND member.card_id = \'"
                        + card_id + "\'")
    if len(result) != 0:
        return result[0][0].strftime("%Y-%m-%d")
    else:
        return None


def park_end(card_id):
    conn = pymysql.connect(host=sql_info.host, port=sql_info.port,
                           user=sql_info.user, passwd=sql_info.passwd, db=sql_info.db)
    cursor = conn.cursor()
    # current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 获得时间数组
    try:
        if card_id[0] != 'T':
            if membership_state(card_id):
                cursor.execute("UPDATE parking_log SET is_member = 1, end_time = NOW() WHERE card_id = \""
                               + card_id + "\" and end_time is null")
                conn.commit()
                # 关闭游标
                cursor.close()
                # 关闭连接
                conn.close()
                return 1
        cursor.execute("UPDATE parking_log SET end_time = NOW() WHERE card_id = \""
                       + card_id + "\" and end_time is null")
    except pymysql.err.OperationalError:
        return -1
    conn.commit()
    # 关闭游标
    cursor.close()
    # 关闭连接
    conn.close()
    return 0


def user_info(user_id):
    info = sql_select("username, is_admin", "user", "id = \"" + user_id + "\"")
    if len(info) != 0:
        return info[0]
    return None


def member_info(card):
    if MQTTcard.legit_data(card) == 1:
        info = sql_select("name, expire_date", "member", "card_id = \"" + card + "\"")
        if len(info) != 0:
            return info[0]
    return None


def search_passwd(identity, user):
    if identity == 0:
        return sql_select("password", "user", "is_admin = 0 and username = " + user)
    elif identity == 1:
        return sql_select("password", "user", "is_admin = 1 and username = " + "\"" + user + "\"")


def time_calculate(card):
    return sql_select("parking_log.start_time, parking_log.end_time", "parking_log",
                      "parking_log.card_id = \'" + card + "\' ORDER BY	parking_log.start_time DESC LIMIT 1")


#if __name__ == '__main__':
#    print(member_info('M000001'))
