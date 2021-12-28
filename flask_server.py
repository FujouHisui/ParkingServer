import math
import threading

from flask import Flask, request
import json
import MQTTcard
import MQTTpark
import SQLLink
import globalvar as gl

app = Flask(__name__)
threadLock = threading.Lock()


@app.route("/login", methods=["GET"])
def login():
    # 默认返回内容
    return_dict = {'return_code': '200', 'return_info': 'Success', 'result': False}
    # 判断入参是否为空
    if request.args is None:
        return_dict['return_code'] = '5004'
        return_dict['return_info'] = 'Empty Parameter'
        return json.dumps(return_dict, ensure_ascii=False)
    # 获取传入的params参数
    get_data = request.args.to_dict()
    identity = get_data.get('identity')
    user = get_data.get('user')
    passwd = get_data.get('passwd')
    # 对参数进行操作
    answer = SQLLink.search_passwd(int(identity), user)[0][0]
    if answer is not None:
        answer = str(answer)
        return_dict['result'] = str(passwd == answer)
    else:
        return_dict['result'] = 'False'

    return json.dumps(return_dict, ensure_ascii=False)


# 获取刷卡信息
@app.route("/card", methods=["GET"])
def get_card():
    payloads = gl.get_value('payloads')
    return_dict = {'return_code': '200', 'card_id': 'NULL', 'status': "NULL"}
    # 线程锁
    # threadLock.acquire()
    if len(payloads) != 0:
        return_dict['card_id'] = payloads
        return_dict['status'] = str(SQLLink.search_state(payloads))
    # threadLock.release()
    return json.dumps(return_dict, ensure_ascii=False)


# 获取车位信息
@app.route("/stat", methods=["GET"])
def get_stat():
    area_1 = gl.get_value('area_1')
    area_2 = gl.get_value('area_2')
    return_dict = {'return_code': '200', 'Area_1': False, 'Area_2': False, 'Remain': '2'}
    # 线程锁
    # threadLock.acquire()
    if (area_1 is not None) and (area_2 is not None):
        return_dict['area_1'] = (area_1 == '1')
        return_dict['area_2'] = (area_2 == '1')
        return_dict['remain'] = 2 - (int(area_1) + int(area_2))
    # threadLock.release()
    return json.dumps(return_dict, ensure_ascii=False)


@app.route("/park", methods=["GET"])
def park():
    # 默认返回内容
    return_dict = {'return_code': '200', 'return_info': 'Failed', 'result': False}
    # 判断入参是否为空
    if request.args is None:
        return_dict['return_code'] = '5004'
        return_dict['return_info'] = 'Empty Parameter'
        return json.dumps(return_dict, ensure_ascii=False)
    # 获取传入的params参数
    get_data = request.args.to_dict()
    card = get_data.get('card')
    op = get_data.get('op')
    # 对参数进行操作
    if op == '1':
        if not SQLLink.search_state(card):
            return_num = SQLLink.log_add(card)
            if return_num == 0:
                return_dict['return_info'] = 'Park Success'
                return_dict['result'] = True
            elif return_num == -1:
                return_dict['return_info'] = 'Park Failed'
                return_dict['result'] = False
        else:
            return_dict['return_info'] = 'Already parked'
            return_dict['result'] = False
    elif op == '0':
        return_num = SQLLink.park_end(card)
        if return_num == 0:
            time_calc = SQLLink.time_calculate(card)
            start_time = time_calc[0][0]
            end_time = time_calc[0][1]
            hour = math.ceil((end_time - start_time).total_seconds() / 3600)
            cost = hour * 5
            return_dict['return_info'] = 'Out Success, charge please'
            return_dict['result'] = True
            return_dict['cost'] = cost
        elif return_num == 1:
            expire_date = SQLLink.expire_date(card)
            return_dict['return_info'] = 'Out Success, Vip member'
            return_dict['result'] = True
            return_dict['expire_date'] = expire_date
        else:
            return_dict['return_info'] = 'Out Failed'
            return_dict['result'] = False

    return json.dumps(return_dict, ensure_ascii=False)


@app.route("/userinfo", methods=["GET"])
def get_user():
    return_dict = {'return_code': '200', 'return_info': 'Failed', 'result': False}
    # 判断入参是否为空
    if request.args is None:
        return_dict['return_code'] = '5004'
        return_dict['return_info'] = 'Empty Parameter'
        return json.dumps(return_dict, ensure_ascii=False)
    # 获取传入的params参数
    get_data = request.args.to_dict()
    userid = get_data.get('id')
    info = SQLLink.user_info(userid)
    if info is not None:
        return_dict['return_info'] = 'Success'
        return_dict['result'] = True
        return_dict['name'] = info[0]
        return_dict['is_admin'] = info[1]

    return json.dumps(return_dict, ensure_ascii=False)


@app.route("/memberinfo", methods=["GET"])
def get_member():
    return_dict = {'return_code': '200', 'return_info': 'Failed', 'result': False}
    # 判断入参是否为空
    if request.args is None:
        return_dict['return_code'] = '5004'
        return_dict['return_info'] = 'Empty Parameter'
        return json.dumps(return_dict, ensure_ascii=False)
    # 获取传入的params参数
    get_data = request.args.to_dict()
    card_id = get_data.get('card')
    info = SQLLink.member_info(card_id)
    if info is not None:
        return_dict['return_info'] = 'Success'
        return_dict['result'] = True
        return_dict['name'] = info[0]
        return_dict['expire_date'] = info[1].strftime("%Y-%m-%d")

    return json.dumps(return_dict, ensure_ascii=False)


class mqttThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        MQTTcard.run()


class mqttParkThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        MQTTpark.run()


def run():
    # threads = []
    gl._init()
    gl.set_value('payloads', "")
    gl.set_value('area_1', None)
    gl.set_value('area_2', None)
    # 创建新线程
    thread1 = mqttThread()
    thread2 = mqttParkThread()
    # 开启新线程
    thread1.start()
    thread2.start()

    # 添加线程到线程列表
    # threads.append(thread1)

    app.run(debug=True, threaded=True, host='0.0.0.0', port=80)
