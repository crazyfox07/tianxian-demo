import socket
import time

from pprint import pprint
from command_receive_set import CommandReceiveSet
from config import CommonConf
from utils import CommonUtil
from command_send_set import CommandSendSet

ip_local = socket.gethostname()  # '192.168.1.109'
ip_tianxian = '192.168.1.69'


def tianxian_demo():
    # 创建一个客户端的socket对象
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 设置服务端的ip地址
    host = ip_tianxian  # "192.168.1.69"
    # 设置端口
    port = 60001
    # 连接服务端
    client.connect((host, port))
    # 创建命令收集对象
    command_recv_set = CommandReceiveSet()
    # 发送数据，以二进制的形式发送数据，所以需要进行编码
    c0 = CommandSendSet.combine_c0().strip()
    print('发送c0指令： ', c0)
    client.send(bytes.fromhex(c0))
    count = 0
    while True:
        msg_bytes = client.recv(1024)
        msg_str = msg_bytes.hex()  # 字节转十六进制
        print('第 {} 次 接收数据： {}'.format(count, msg_str))
        # b0 设备状态信息帧
        if msg_str[6: 8]== 'b0':
            command_recv_set.parse_b0(msg_str)  # 解析b0指令
        # b2 电子标签信息帧
        elif msg_str[6:8] == 'b2':
            if msg_str[8:12] == 'fe01':
                print('心跳')
            else:
                info_b2 = command_recv_set.parse_b2(msg_str) # 解析b2指令
                # 电子标签mac地址
                obuid = info_b2['OBUID']
                # 获取c1指令
                c1 = CommandSendSet.combine_c1(obuid, obu_div_factor=CommonConf.OBU_DIV_FACTOR)
                print('b2后发送c1指令：%s， 电子标签mac地址 obuid = %s' % (c1, obuid))
                client.send(bytes.fromhex(c1))
        # b3 车辆信息帧
        elif msg_str[6:8] == 'b3':
            if msg_str[16: 18] == '00':  # obu信息帧状态执行码，取值00正常
                command_recv_set.parse_b3(msg_str)  # 解析b3指令
                # 再次获取c1指令并发送
                c1 = CommandSendSet.combine_c1(obuid, obu_div_factor=CommonConf.OBU_DIV_FACTOR)
                print('b3后发送c1指令：%s， 电子标签mac地址 obuid = %s' % (c1, obuid))
                client.send(bytes.fromhex(c1))
            else:  # 状态执行码不正常，发送c2指令，终止交易
                c2 = CommandSendSet.combine_c2(obuid, stop_type='01')
                print('发送c2指令，终止交易:  %s' % (c2,))
                client.send(bytes.fromhex(c2))
        # b4 速通卡信息帧
        elif msg_str[6:8] == 'b4':
            if msg_str[16: 18] == '00':  # 状态执行码，00说明后续速通卡信息合法有效
                command_recv_set.parse_b4(msg_str)  # 解析b4指令
                # 获取并发送c6消费交易指令
                # TODO 扣款额度计算待解决
                consume_money = '00000000'  # 扣款额，高字节在前
                purchase_time = CommonUtil.timestamp_format()
                station = msg_str[132:212]  # 过站信息,40个字节
                c6 = CommandSendSet.combine_c6(obuid, card_div_factor=CommonConf.OBU_DIV_FACTOR, reserved='00000000',
                                               consume_money=consume_money, purchase_time=purchase_time,
                                               station=station)
                print('发送c6指令，消费交易，出口消费写过站: %s' % (c6,))
                client.send(bytes.fromhex(c6))
        # b5 交易信息帧，表示此次交易成功结束
        elif msg_str[6:8] == 'b5':
            if msg_str[16: 18] == '00':  # 状态执行码，00说明正常
                command_recv_set.parse_b5(msg_str)  # 解析b5指令
                # 获取并发送c1继续交易指令
                c1= CommandSendSet.combine_c1(obuid, obu_div_factor=CommonConf.OBU_DIV_FACTOR)
                print('b5后发送c1指令：%s， 电子标签mac地址 obuid = %s' % (c1, obuid))
                client.send(bytes.fromhex(c1))

                client.close()
                return command_recv_set



        count += 1
        time.sleep(0.1)
        if count > 11:
            # 关闭客户端
            client.close()
            break


if __name__ == '__main__':
    # tianxian_demo()
    # c2 = CommandSendSet.combine_c2(obu_id='6a81353e', stop_type='01')
    # print(c0)
    CommonUtil.bcc_xor('ffff80c05f493bf2020082817163203020a0002')
    # 'ffff82c16a81353ecdf2bcafcdf2bcaf'
    # CommandSendSet.combine_c1(obu_id='6a81353e', obu_div_factor=CommonConf.OBU_DIV_FACTOR)
