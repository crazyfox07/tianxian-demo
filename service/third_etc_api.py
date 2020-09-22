# -*- coding: utf-8 -*-

"""
@author: liuxuewen
@file: third_etc_api.py
@time: 2020/9/8 9:57
"""
import json
import os
import traceback
from common.config import CommonConf
from common.db_client import DBClient
from common.http_client import http_session
from common.log import logger
from common.sign_verify import XlapiSignature
from common.utils import CommonUtil
from datetime import datetime
import time

from model.db_orm import db_session, ETCFeeDeductInfoOrm


class ThirdEtcApi(object):
    # TODO 调用第三方api
    # ETC_UPLOAD_URL = 'http://{host}:{port}/api/gateway/etc'.format(
    #     host=CommonConf.ETC_CONF_DICT['thirdApi']['host'],
    #     port=CommonConf.ETC_CONF_DICT['thirdApi']['port'])
    ETC_UPLOAD_URL = CommonConf.ETC_CONF_DICT['thirdApi']['url']
    # app_id
    APPID = CommonConf.ETC_CONF_DICT['thirdApi']['app_id']
    # 私钥
    PRIVATE_KEY = CommonConf.ETC_CONF_DICT['thirdApi']['private_key']

    @staticmethod
    def my_job1():
        time.sleep(30)
        logger.info(f'{datetime.now():%H:%M:%S} Hello job1  ============== ')

    @staticmethod
    def my_job2():
        logger.info(f'{datetime.now():%H:%M:%S} Hello job2 ')

    @staticmethod
    def etc_deduct_upload(etc_deduct_info_json) -> bool:
        """
        etc支付上传
        :return:
        """
        # # 如果上传成功upload_flag=1， 上传失败upload_flag=0, 默认上传失败
        upload_flag = 0
        # 业务编码报文
        # 将data 值base64 后，使用SHA256WithRSA 计算签名
        sign = XlapiSignature.to_sign_with_private_key(etc_deduct_info_json, private_key=ThirdEtcApi.PRIVATE_KEY)
        upload_body = dict(appid=ThirdEtcApi.APPID,
                           data=etc_deduct_info_json,
                           sign=sign.decode(encoding='utf8'))
        # print('+' * 30)
        logger.info('上传etc扣费数据： {}'.format(etc_deduct_info_json))
        try:
            res = http_session.post(ThirdEtcApi.ETC_UPLOAD_URL, data=upload_body)
            if res.json()['code'] == '000000':
                upload_flag = 1
        except:
            logger.error(traceback.format_exc())

        # 统计上传失败次数
        upload_fail_count = 0 if upload_flag else 1
        # TODO 存数据库
        DBClient.add(db_session=db_session,
                     orm=ETCFeeDeductInfoOrm(id=CommonUtil.random_str(32).lower(),
                                             etc_info=etc_deduct_info_json,
                                             upload_flag=upload_flag,
                                             upload_fail_count=upload_fail_count))

        return False

    @staticmethod
    def exists_in_blacklist(issuer_identifier, card_net, card_id):
        """
        通过第三方接口查询card_net+card_sn是否在黑名单中
        :param issuer_identifier 发行商代码
        :param card_net: card网络编号
        :param card_id: card id
        :return:
        """
        data_dict = {
            "method": "blacklist",
            "params": {
                "issuer_identifier": issuer_identifier,
                "card_net": str(card_net),
                "card_sn": card_id
            }
        }
        data_json = json.dumps(data_dict, ensure_ascii=False)
        print('+=' * 50)
        print(data_json)
        sign = XlapiSignature.to_sign_with_private_key(data_json, private_key=ThirdEtcApi.PRIVATE_KEY)
        upload_body = dict(appid=ThirdEtcApi.APPID,
                           data=data_json,
                           sign=sign.decode(encoding='utf8'))
        try:
            res = http_session.post(ThirdEtcApi.ETC_UPLOAD_URL, data=upload_body)
            res_json = res.json()
            print(res_json)
            status = res_json['data']['status']
            exist_flag = True if str(status) == '1' else False
            return exist_flag

        except:
            logger.error(traceback.format_exc())

    @staticmethod
    def download_blacklist_base():
        """
        下载基础黑名单, 定时每天凌晨一点跑一次
        :return:
        """
        data_dict = {
            "method": "getBlackListFile",
            "params": {
                "last_file_name": "",
                "version": "",
                "para_code": "97"
            }
        }
        data_json = json.dumps(data_dict, ensure_ascii=False)
        sign = XlapiSignature.to_sign_with_private_key(data_json, private_key=ThirdEtcApi.PRIVATE_KEY)
        upload_body = dict(appid=ThirdEtcApi.APPID,
                           data=data_json,
                           sign=sign.decode(encoding='utf8'))
        res = http_session.post(ThirdEtcApi.ETC_UPLOAD_URL, data=upload_body)
        res_json = res.json()
        logger.info('下载基础黑名单： {}'.format(res_json))
        file_url = res_json['data']['file_url']
        new_version = res_json['data']['new_version']
        para_code = res_json['data']['para_code']
        file_name = res_json['data']['file_name']
        file_path = os.path.join(CommonConf.SQLITE_DIR, file_name)
        # 下载文件
        CommonUtil.download_file(url=file_url, file_path=file_path)
        # 解压下载的zip文件
        CommonUtil.unzipfile(src_file=file_path, dest_dir=CommonConf.SQLITE_DIR)

    @staticmethod
    def download_blacklist_incre():
        """
        下载增量黑名单, 定时每隔一小时跑一次
        :return:
        """
        data_dict = {
            "method": "getBlackListFile",
            "params": {
                "last_file_name": "",
                "version": "",
                "para_code": "65"
            }
        }
        data_json = json.dumps(data_dict, ensure_ascii=False)
        sign = XlapiSignature.to_sign_with_private_key(data_json, private_key=ThirdEtcApi.PRIVATE_KEY)
        upload_body = dict(appid=ThirdEtcApi.APPID,
                           data=data_json,
                           sign=sign.decode(encoding='utf8'))
        res = http_session.post(ThirdEtcApi.ETC_UPLOAD_URL, data=upload_body)
        res_json = res.json()
        logger.info('下载增量黑名单： {}'.format(res_json))
        file_url = res_json['data']['file_url']
        new_version = res_json['data']['new_version']
        para_code = res_json['data']['para_code']
        file_name = res_json['data']['file_name']
        file_path = os.path.join(CommonConf.SQLITE_DIR, file_name)
        # 下载文件
        CommonUtil.download_file(url=file_url, file_path=file_path)
        # 解压下载的zip文件
        CommonUtil.unzipfile(src_file=file_path, dest_dir=CommonConf.SQLITE_DIR)

    @staticmethod
    def reupload_etc_deduct_from_db():
        """
        查找数据库中没能成功上传的数据，重新上传
        :return:
        """
        query_items = db_session.query(ETCFeeDeductInfoOrm).filter(ETCFeeDeductInfoOrm.upload_flag == 0)
        for item in query_items:
            #  调用第三方api
            request_flag = ThirdEtcApi.etc_deduct_upload(item.etc_info)
            if request_flag:  # 如果上传成功，更新upload_flag为1
                item.upload_flag = 1
            else:  # 如果上传失败，更新upload_fail_count 加 1
                item.upload_fail_count += 1
            db_session.commit()

    @staticmethod
    def tianxian_heartbeat(params):
        """
        天线心跳
        :return:
        """
        data_dict = {
            "method": "heartbeat",
            "params": params
        }
        data_json = json.dumps(data_dict, ensure_ascii=False)
        logger.info('天线心跳：{}'.format(data_json))
        sign = XlapiSignature.to_sign_with_private_key(data_json, private_key=ThirdEtcApi.PRIVATE_KEY)
        upload_body = dict(appid=ThirdEtcApi.APPID,
                           data=data_json,
                           sign=sign.decode(encoding='utf8'))
        # res = http_session.post(ThirdEtcApi.ETC_UPLOAD_URL, data=upload_body)
        # logger.info(res.json())


if __name__ == '__main__':
    print('start')
    # sched.start()
    begin = time.time()
    print(ThirdEtcApi.tianxian_heartbeat())
    # print(ThirdEtcApi.exists_in_blacklist('1' * 16, '1111', '22222222222222222222'))
    # ThirdEtcApi.download_blacklist_base()
    # ThirdEtcApi.download_blacklist_incre()
    # ThirdEtcApi.reupload_etc_deduct_from_db()
    #     etc_deduct_info_dict = {
    #     "method": "etcPayUpload",
    #     "params": {
    #         "algorithm_type": "1",
    #         "balance": 4294964440,
    #         "card_net_no": "3401",
    #         "card_rnd": "45TGUM2W",
    #         "card_serial_no": "001d",
    #         "card_sn": "1901230202361703",
    #         "card_type": "23",
    #         "charging_type": "0",
    #         "deduct_amount": 1,
    #         "device_no": "ShowLinx - 3202001001",
    #         "device_type": "0",
    #         "discount_amount": 0,
    #         "entrance_time": "20200910090150",
    #         "exit_time": "20200910091559",
    #         "issuer_identifier": "C9BDB6AB37010001",
    #         "obu_id": "014E7E95",
    #         "park_code": "371104",
    #         "park_record_time": "1分40秒",
    #         "plate_color_code": "4",
    #         "plate_no": "鲁LD10103",
    #         "plate_type_code": "0",
    #         "psam_id": "37011901230202361703",
    #         "psam_serial_no": "0000053c",
    #         "receivable_total_amount": 1,
    #         "serial_number": "3701011925377913",
    #         "tac": "5232d485",
    #         "terminal_id": "01110004dea0",
    #         "trans_before_balance": 4294964441,
    #         "trans_order_no": "1818620411622008754",
    #         "trans_type": "09",
    #         "vehicle_type": "1"
    #     }
    # }
    #     # TODO 存数据库
    #     DBClient.add(db_session=db_session,
    #                  orm=ETCFeeDeductInfoOrm(id=CommonUtil.random_str(32).lower(),
    #                                          etc_info=json.dumps(etc_deduct_info_dict, ensure_ascii=False),
    #                                          upload_flag=0,
    #                                          upload_fail_count=1))

    end = time.time()
    print('time use %ss' % (int(end) - int(begin)))
