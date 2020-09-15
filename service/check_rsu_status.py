# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: check_rsu_status.py
@time: 2020/9/15 15:32
"""
import traceback
import socket

from func_timeout import func_set_timeout

from common.config import CommonConf
from common.log import logger
from service.command_receive_set import CommandReceiveSet
from service.command_send_set import CommandSendSet


class RsuStatus(object):

    @staticmethod
    def init_rsu_status_list():
        """
        初始化天线状态列表
        :return:
        """

        tianxian_list = CommonConf.ETC_CONF_DICT['etc']
        for item in tianxian_list:  # 从配置文件中获取的天线列表
            tianxian_status_item = dict(park_code=item['park_code'],
                                        lane_num=item['lane_num'],
                                        sn=item['sn'],
                                        ip=item['ip'],
                                        port=item['port'],
                                        rsu_status=1,  # 天线状态,0表示正常，1表示异常， 默认异常
                                        )
            CommonConf.RSU_STATUS_LIST.append(tianxian_status_item)

    @staticmethod
    def timing_update_rsu_status_list(callback):
        """
        定时更新天线状态列表CommonConf.RSU_STATUS_LIST。
        对于CommonConf.RSU_STATUS_LIST中异常的天线，需要重新建立socket连接检查是否依然异常，并更新CommonConf.RSU_STATUS_LIST中的状态。
        对于CommonConf.RSU_STATUS_LIST中正常的天线，直接跳过，不需要再次检测
        :tianxian_heartbeat: 回调函数，向第三方接口发送心跳
        :return:
        """
        # 如果CommonConf.RSU_STATUS_LIST为空，说明还初始化过，需要初始化
        if not CommonConf.RSU_STATUS_LIST:
            RsuStatus.init_rsu_status_list()

        for rsu_status_item in CommonConf.RSU_STATUS_LIST:
            # rsu_status=1异常，则尝试再次获取天线状态， 并更新rsu_status_item的rsu_status,
            # rsu_status=0正常的话，不需要开启天线重新获取状态
            if rsu_status_item['rsu_status'] == 1:
                for item in CommonConf.ETC_CONF_DICT['etc']:
                    if (rsu_status_item['park_code'] == item['park_code']) and (rsu_status_item['lane_num'] ==
                                                                                item['lane_num']):
                        try:
                            rsu_status_hex = RsuStatus.get_rsu_status(item)  # 获取天线状态
                            rsu_status = 0 if rsu_status_hex == '00' else 1 # 天线状态,0表示正常，1表示异常， 默认异常
                            rsu_status_item['rsu_status'] = rsu_status
                        except:
                            logger.error(traceback.format_exc())
                        break  # 跳出当前for循环

        # 回调函数，向第三方接口发送心跳
        callback()

    @staticmethod
    @func_set_timeout(5)
    def get_rsu_status(etc_conf):
        """
        获取天线状态
        :param ip:
        :param port:
        :return:
        """
        # 创建一个客户端的socket对象
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # 连接服务端
            client.connect((etc_conf['ip'], etc_conf['port']))
            # 发送c0初始化指令，以二进制的形式发送数据，所以需要进行编码
            c0 = CommandSendSet.combine_c0(lane_mode=etc_conf['lane_mode'], wait_time=etc_conf['wait_time'],
                                           tx_power=etc_conf['tx_power'],
                                           pll_channel_id=etc_conf['pll_channel_id'],
                                           trans_mode=etc_conf['trans_mode']).strip()
            client.send(bytes.fromhex(c0))
            # 接收数据
            msg_bytes = client.recv(1024)
            msg_str = msg_bytes.hex()  # 字节转十六进制

            command_recv_set = CommandReceiveSet()
            # b0 设备状态信息帧
            if msg_str[6: 8] == 'b0':
                command_recv_set.parse_b0(msg_str)  # 解析b0指令
                # 天线状态
                rsu_status = command_recv_set.info_b0['RSUStatus']
                return rsu_status
        except:
            logger.error(traceback.format_exc())
        finally:
            # 关闭client
            client.shutdown(2)
            client.close()
