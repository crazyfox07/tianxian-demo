# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: etc_toll.py
@time: 2020/9/2 11:24
"""
import traceback
import json

from func_timeout import func_set_timeout

from common.config import CommonConf
from common.log import logger
from common.utils import CommonUtil
from model.obu_model import OBUModel
from service.rsu_socket import RsuSocket


class EtcToll(object):
    @staticmethod
    @func_set_timeout(CommonConf.FUNC_TIME_OUT)
    def toll(body: OBUModel) -> dict:
        """
        etc收费
        :param body: 接收到的数据
        :return:
        """
        # 默认扣费失败
        result = dict(flag=False,
                      errorCode='01',
                      errorMessage='etc扣费失败',
                      data=None)

        rsu_client: RsuSocket = CommonConf.RSU_SOCKET_STORE_DICT[body.lane_num]  # RsuSocket(body.lane_num)
        try:
            # etc开始扣费，并解析天线返回的数据
            try:
                msg = rsu_client.fee_deduction(body)
            finally:
                rsu_client.monitor_rsu_status_on = True  # 恢复开启心跳检测
            # 如果扣费失败
            if (type(msg) is dict) and (msg['flag'] is False):
                result['errorMessage'] = msg['error_msg']
            elif rsu_client.etc_charge_flag:  # 表示交易成功
                # etc扣费成功后做进一步数据解析
                handle_data_result = rsu_client.handle_data(body)
                result['flag'] = handle_data_result['flag']
                result['errorMessage'] = handle_data_result['error_msg']
                params = handle_data_result['data']
                # handle_data_result['flag']=Falase一般是存在黑名单
                if handle_data_result['flag'] and handle_data_result['data']:
                    # 交易时间格式转换
                    pay_time = CommonUtil.timeformat_convert(timestr1=params['exit_time'], format1='%Y%m%d%H%M%S',
                                                             format2='%Y-%m-%d %H:%M:%S')
                    result['data'] = dict(parkCode=params['park_code'],
                                          orderNo=params['trans_order_no'],
                                          outTradeNo=params['trans_order_no'],
                                          payFee=params['deduct_amount'] / 100,
                                          derateFee=params['discount_amount'],
                                          payTime=pay_time)
                    # result['data'] = '交易成功'
                    data = dict(method='etcPayUpload',
                                params=params, )
                    logger.info('etc交易成功')
                    logger.info(json.dumps(data, ensure_ascii=False))

            else:
                logger.error("etc扣费失败")
        except:
            logger.error(traceback.format_exc())
        # 记入日志
        logger.info(json.dumps(result, ensure_ascii=False))
        return result



class ETCTollBak(object):

    @staticmethod
    def toll(body: OBUModel) -> dict:
        """
        etc收费
        :param body: 接收到的数据
        :return:
        """
        park_code = body.park_code  # 停车场编号
        lane_num = body.lane_num  # 车道号
        deduct_amount = body.deduct_amount  # etc扣款金额
        # 默认扣费失败
        result = dict(flag=False,
                      errorCode='01',
                      errorMessage='etc扣费失败',
                      data=None)

        socket_client = SocketClient(body)
        try:
            # etc开始扣费，并解析天线返回的数据
            msg = socket_client.fee_deduction()
            # 如果返回的信息中包含“in blacklist”，则报错
            if (type(msg) is dict) and ('flag' in msg) and (msg['flag'] is False):
                result['errorMessage'] = msg['error_msg']
            # 可能由于之前socket没有正常关闭，再试一次
            elif socket_client.msg_receive_is_empty:
                logger.error('试图第二次尝试打开socket')
                socket_client = SocketClient(body)
                # etc开始扣费，并解析天线返回的数据
                msg = socket_client.fee_deduction()
                if (type(msg) is dict) and ('flag' in msg) and (msg['flag'] is False):
                    result['errorMessage'] = msg['error_msg']

            if socket_client.etc_charge_flag:  # 表示交易成功
                params = socket_client.handle_data(body)
                # params为空，一般是车牌号或车颜色不匹配
                if params:
                    result['flag'] = True
                    result['errorCode'] = None
                    result['errorMessage'] = None
                    # 交易时间格式转换
                    pay_time = CommonUtil.timeformat_convert(timestr1=params['exit_time'], format1='%Y%m%d%H%M%S',
                                                             format2='%Y-%m-%d %H:%M:%S')
                    result['data'] = dict(parkCode=params['park_code'],
                                          orderNo=params['trans_order_no'],
                                          outTradeNo=params['trans_order_no'],
                                          payFee=params['deduct_amount']/100,
                                          derateFee=params['discount_amount'],
                                          payTime=pay_time)
                    # result['data'] = '交易成功'
                    data = dict(method='etcPayUpload',
                                params=params, )
                    logger.info('etc交易成功')
                    logger.info(json.dumps(data, ensure_ascii=False))
                else:
                    result['errorMessage'] = '车牌号或车颜色不匹配'
            else:
                logger.error("etc扣费失败")
        except:
            logger.error(traceback.format_exc())
            # socket_client.close_client()
        # 记入日志
        # socket_client.close_client()
        logger.info(json.dumps(result, ensure_ascii=False))
        return result


if __name__ == '__main__':
    obumodel = OBUModel()
    obumodel.lane_num = '1'
    obumodel.deduct_amount = 0.01
    result = ETCToll.toll(obumodel)
