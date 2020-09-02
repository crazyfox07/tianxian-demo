# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: etc_toll.py
@time: 2020/9/2 11:24
"""
import traceback

from common.log import logger
from service.socket_client import SocketClient


class ETCToll(object):

    @staticmethod
    def toll(tianxian_ip, port=60001, money=0.01) -> dict:
        """
        etc收费
        :param tianxian_ip: 天线ip
        :param port: 天线端口号
        :param money: etc扣款费用
        :return:
        """
        result = dict()
        try:
            socket_client = SocketClient(tianxian_ip, port)
            # etc开始扣费，并解析天线返回的数据
            socket_client.fee_deduction(money)
            # 可能由于之前socket没有正常关闭，再试一次
            if socket_client.msg_receive_is_empty:
                socket_client = SocketClient(tianxian_ip, port)
                # etc开始扣费，并解析天线返回的数据
                socket_client.fee_deduction(money)

            if socket_client.etc_charge_flag:  # 表示交易成功
                result['flag'] = True
                result['errorCode'] = None
                result['data'] = dict(method='etcPayUpload',
                                      params=socket_client.handle_data())
                return result
            else:
                result['flag'] = False
                result['errorCode'] = '01'
                result['data'] = None
                logger.error("etc扣费失败")
                return result
        except:
            result['flag'] = False
            result['errorCode'] = '02'
            result['data'] = None
            logger.error("etc扣费失败")
            logger.error(traceback.format_exc())
            socket_client.close_client()
            return result


if __name__ == '__main__':
    result = ETCToll.toll(tianxian_ip='192.168.1.69', port=60001, money=0.01)
    print(result)