import json
import socket
import time
from func_timeout import func_set_timeout
from common.db_client import DBClient
from model.db_orm import ETCFeeDeductInfoOrm, db_session
from model.obu_model import OBUModel
from service.command_receive_set import CommandReceiveSet
from common.config import CommonConf
from common.utils import CommonUtil
from service.command_send_set import CommandSendSet
from common.log import logger
from service.third_etc_api import ThirdEtcApi


class SocketClient(object):
    """
    创建socket客户端
    :author: liuxuewen
    :date: 2020/9/1 8:52
    """

    def __init__(self, body: OBUModel):
        """
        socket客户初始化
        :param body 接收到的请求体
        """
        # 获取etc交易配置
        self.etc_conf = self.get_etc_conf(body.park_code, body.lane_num)
        # 创建一个客户端的socket对象
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 连接服务端
        self.client.connect((self.etc_conf['ip'], self.etc_conf['port']))
        # 创建命令收集对象，用于后期解析天线发送过来的命令
        self.command_recv_set = CommandReceiveSet()
        # self.etc_charge_flag=True表示交易成功，self.etc_charge_flag=False表示交易失败
        self.etc_charge_flag = False
        # 接收到的指令为空，可能是socket关闭异常导致，需要再重新建立一次socket连接
        self.msg_receive_is_empty = False
        self.obu_body = body

    def get_etc_conf(self, park_code, lane_num):
        """
        通过天线ip获取etc交易配置
        :param park_code: 停车场编号
        :param lane_num: 车道号
        :return:
        """
        for etc_conf_item in CommonConf.ETC_CONF_DICT['etc']:
            if (etc_conf_item['park_code'] == park_code) and (etc_conf_item['lane_num'] == lane_num):
                return etc_conf_item
        error_info = 'could not match lane_num: %s' % (lane_num,)
        logger.error(error_info)
        raise Exception(error_info)

    def get_client(self):
        """
        获取客户端
        :return:
        """
        return self.client

    @func_set_timeout(CommonConf.TIME_OUT)
    def fee_deduction(self):
        """
        etc扣费, 正常扣费指令流程  c0->b0->b2->c1->b3->c1->b4->c6->b5，其中
        c0: 发送初始化指令
        b0: 接收设备状态信息帧
        b2: 接收电子标签信息帧
        c1: 发送继续交易指令
        b3: 接收设备车辆信息帧
        c1: 发送继续交易指令
        b4: 接收速通卡信息帧
        c6: 发送消费交易指令，出口消费写过站
        b5: 接收交易信息帧，表示此次交易成功结束
        : param money: etc费用
        :return:
        """
        logger.info('=============================etc扣费开始=============================')
        # 发送c0初始化指令，以二进制的形式发送数据，所以需要进行编码
        c0 = CommandSendSet.combine_c0(lane_mode=self.etc_conf['lane_mode'], wait_time=self.etc_conf['wait_time'],
                                       tx_power=self.etc_conf['tx_power'],
                                       pll_channel_id=self.etc_conf['pll_channel_id'],
                                       trans_mode=self.etc_conf['trans_mode']).strip()
        logger.info('发送c0指令： %s' % (c0,))
        self.client.send(bytes.fromhex(c0))
        while True:
            # 接收数据
            msg_bytes = self.client.recv(1024)
            msg_str = msg_bytes.hex()  # 字节转十六进制
            logger.info('接收数据： {}'.format(msg_str))
            # b0 设备状态信息帧
            if msg_str[6: 8] == 'b0':
                self.command_recv_set.parse_b0(msg_str)  # 解析b0指令
            # b2 电子标签信息帧
            elif msg_str[6:8] == 'b2':
                if msg_str[8:24] == 'fe01fe01fe01fe01':  # 'fe01fe01fe01fe01' 表示心跳
                    logger.info('心跳')
                else:
                    info_b2 = self.command_recv_set.parse_b2(msg_str)  # 解析b2指令
                    # 电子标签mac地址
                    obuid = info_b2['OBUID']
                    # 获取c1指令
                    c1 = CommandSendSet.combine_c1(obuid, obu_div_factor=self.etc_conf['obu_div_factor'])
                    logger.info('b2后发送c1指令：%s' % (c1))
                    self.client.send(bytes.fromhex(c1))
            # b3 车辆信息帧
            elif msg_str[6:8] == 'b3':
                if msg_str[16: 18] == '00':  # obu信息帧状态执行码，取值00正常
                    self.command_recv_set.parse_b3(msg_str)  # 解析b3指令
                    # TODO 车牌号，车颜色 需要校验， 不匹配需要返回
                    plate_no = self.command_recv_set.info_b3['VehicleLicencePlateNumber']
                    plate_no = CommonUtil.parse_plate_code(plate_no).replace('测A', '鲁L')
                    # 车牌颜色
                    obu_plate_color = str(int(self.command_recv_set.info_b3['VehicleLicencePlateColor'], 16))  # obu车颜色
                    if (self.obu_body.plate_no != plate_no) or (self.obu_body.plate_color_code != obu_plate_color):
                        error_msg = "车牌号或车颜色不匹配： 监控获取的车牌号：%s, 车颜色：%s; obu获取的车牌号：%s,车颜色：%s" % (
                            self.obu_body.plate_no, self.obu_body.plate_color_code, plate_no, obu_plate_color)
                        logger.error(error_msg)
                        return dict(flag=False,
                                    error_msg=error_msg)
                    # 再次获取c1指令并发送
                    c1 = CommandSendSet.combine_c1(obuid, obu_div_factor=self.etc_conf['obu_div_factor'])
                    logger.info('b3后发送c1指令：%s' % (c1,))
                    self.client.send(bytes.fromhex(c1))
                else:  # 状态执行码不正常，发送c2指令，终止交易
                    c2 = CommandSendSet.combine_c2(obuid, stop_type='01')
                    logger.info('发送c2指令，终止交易:  %s' % (c2,))
                    self.client.send(bytes.fromhex(c2))
            # b4 速通卡信息帧
            elif msg_str[6:8] == 'b4':
                if msg_str[16: 18] == '00':  # 状态执行码，00说明后续速通卡信息合法有效
                    self.command_recv_set.parse_b4(msg_str)  # 解析b4指令

                    # # TODO 判断card_net和card_sn 物理卡号是否存在于黑名单中
                    issuer_info = self.command_recv_set.info_b4['IssuerInfo']
                    card_net = int(issuer_info[20: 24])  # 需要转换为整数
                    card_sn = issuer_info[24: 40]
                    begin_query = int(time.time())
                    card_sn_in_blacklist_flag = DBClient.exists_in_blacklist(card_net=card_net, card_id=card_sn)
                    end_query = int(time.time())
                    print('query blacklist use time: {}, card_sn_in_blacklist_flag: {}'.format(
                        end_query-begin_query, card_sn_in_blacklist_flag))
                    # 物理卡号存在于黑名单中直接返回
                    if card_sn_in_blacklist_flag:
                        error_msg = 'card_id:%s in blacklist' % card_sn
                        logger.error(error_msg)
                        return dict(flag=False,
                                    error_msg=error_msg)

                    # 获取并发送c6消费交易指令
                    deduct_amount = CommonUtil.etcfee_to_hex(self.obu_body.deduct_amount)  # 扣款额，高字节在前
                    purchase_time = CommonUtil.timestamp_format(int(time.time()))
                    station = msg_str[132:212]  # 过站信息,40个字节
                    c6 = CommandSendSet.combine_c6(obuid, card_div_factor=self.etc_conf['obu_div_factor'],
                                                   reserved='00000000',
                                                   deduct_amount=deduct_amount, purchase_time=purchase_time,
                                                   station=station)
                    logger.info('发送c6指令，消费交易，出口消费写过站: {}， 其中扣除费用{}'.format(c6, self.obu_body.deduct_amount))
                    self.client.send(bytes.fromhex(c6))
            # b5 交易信息帧，表示此次交易成功结束
            elif msg_str[6:8] == 'b5':
                if msg_str[16: 18] == '00':  # 状态执行码，00说明正常
                    self.command_recv_set.parse_b5(msg_str)  # 解析b5指令
                    #  获取并发送c1继续交易指令
                    c1 = CommandSendSet.combine_c1(obuid, obu_div_factor=self.etc_conf['obu_div_factor'])
                    print('b5后发送c1指令：%s， 电子标签mac地址 obuid = %s' % (c1, obuid))
                    # self.client.send(bytes.fromhex(c1))
                    self.etc_charge_flag = True
                    return self.command_recv_set
            elif not msg_str:
                logger.error('接收到的指令为空')
                self.msg_receive_is_empty = True
                return self.command_recv_set
            else:
                logger.error('未能解析的指令：%s' % (msg_str))
                return self.command_recv_set

    def handle_data(self, body: OBUModel):
        """
        处理self.command_recv_set，也就是收到的天线的信息
        :param body: 接收到的数据
        :return:
        """
        # TODO 待待删打印信息
        self.command_recv_set.print_obu_info()
        # 计算停车时长
        park_record_time = CommonUtil.time_difference(body.entrance_time, body.exit_time)
        # 入场时间戳格式化 yyyyMMddHHmmss
        entrance_time = CommonUtil.timestamp_format(body.entrance_time, format='%Y%m%d%H%M%S')
        # 交易时间格式化（yyyyMMddHHmmss）
        # exit_time = CommonUtil.timestamp_format(body.exit_time, format='%Y%m%d%H%M%S')
        exit_time = self.command_recv_set.info_b5['TransTime']
        # 交易后余额
        balance = self.command_recv_set.info_b5['CardBalance']
        # 交易前余额 1999918332 单位分
        trans_before_balance = self.command_recv_set.info_b4['CardRestMoney']
        # 卡片发行信息
        issuer_info = self.command_recv_set.info_b4['IssuerInfo']
        # PSAM 卡编号
        psam_id = issuer_info[20: 40]
        # TODO card_sn 物理卡号待确认
        card_sn = psam_id[4:]
        # TODO 待确认
        card_type = (self.command_recv_set.info_b4['CardType']).replace('00', '23')
        params = dict(algorithm_type="1",
                      # TODO 金额位数待确定
                      balance=CommonUtil.hex_to_etcfee(balance, unit='fen'),  # 交易后余额
                      # TODO 待确认
                      card_net_no=issuer_info[20:24],  # 网络编号
                      card_rnd=CommonUtil.random_str(8),  # 卡内随机数
                      # TODO 待确认
                      card_serial_no=self.command_recv_set.info_b5['ICCPaySerial'],  # 卡内交易序号
                      # TODO 待确认, 16位
                      card_sn=card_sn,  # self.command_recv_set.info_b4['CardID'],  # "1030230218354952",ETC 支付时与卡物理号一致；非 ETC 时上传车牌号
                      # TODO 待确认，注意与b4中的CardType的区别
                      card_type=card_type,  # "23",  # ETC 卡片类型（22:储值卡；23:记账卡）
                      charging_type="0",  # 扣费方式(0:天线 1:刷卡器)
                      deduct_amount=CommonUtil.yuan_to_fen(body.deduct_amount),  # 扣款金额
                      # TODO 待确认
                      device_no=self.etc_conf['device_no'],  # 设备号
                      # TODO 待确认
                      device_type=self.etc_conf['device_type'],  # 设备类型（0:天线；1:刷卡器；9:其它）
                      discount_amount=CommonUtil.yuan_to_fen(body.discount_amount),  # 折扣金额
                      entrance_time=entrance_time,  # 入场时间 yyyyMMddHHmmss
                      exit_time=exit_time,  # 交易时间（yyyyMMddHHmmss）
                      issuer_identifier=self.command_recv_set.info_b2['IssuerIdentifier'].upper(),  # 发行商代码
                      obu_id=self.command_recv_set.info_b2['OBUID'].upper(),  # OBU 序号编码
                      park_code=body.park_code,  # 车场编号
                      park_record_time=park_record_time,  # 停车时长,时间精确到秒， 6小时50分钟
                      plate_color_code=body.plate_color_code,  # 车牌颜色编码 0:蓝色、1:黄色、2:黑色、3:白色、4:渐变绿色、5:黄绿双拼、6:绿色、7:蓝白渐变
                      plate_no=self.obu_body.plate_no,  # 车牌号码 "皖LX4652",
                      plate_type_code=body.plate_type_code,  # 车辆类型编码 0:小车 1:大车 2:超大车
                      psam_id=psam_id,  # PSAM 卡编号 "37010101000000295460"
                      psam_serial_no=self.command_recv_set.info_b5['PSAMTransSerial'],  # PSAM 流水号 "00005BA2",
                      receivable_total_amount=CommonUtil.yuan_to_fen(body.receivable_total_amount),  # 应收金额
                      serial_number=self.command_recv_set.info_b2['SerialNumber'],  # 合同序列号"340119126C6AFEDE"
                      tac=self.command_recv_set.info_b5['TAC'],  # 交易认证码
                      terminal_id=self.command_recv_set.info_b5['PSAMNo'],  # 终端编号
                      trans_before_balance=CommonUtil.hex_to_etcfee(trans_before_balance, unit='fen'),  # 交易前余额 1999918332 单位分
                      trans_order_no=body.trans_order_no,  # 交易订单号 "6711683258167489287"
                      trans_type=self.command_recv_set.info_b5['TransType'],  # 交易类型（06:传统；09:复合）
                      vehicle_type=str(int(self.command_recv_set.info_b3['VehicleClass']))  # 收费车型
                      )
        etc_deduct_info_dict = {"method": "etcPayUpload",
                                "params": params}
        # 业务编码报文json格式
        etc_deduct_info_json = json.dumps(etc_deduct_info_dict, ensure_ascii=False)
        # TODO 调用第三方api
        request_flag = ThirdEtcApi.etc_deduct_upload(etc_deduct_info_json)
        # # 如果上传成功，upload_flag=1， 上传失败， upload_fla=0
        upload_flag = 1 if request_flag else 0
        # 统计上传失败次数
        upload_fail_count = 0 if upload_flag else 1

        # TODO 存数据库
        DBClient.add(db_session=db_session,
                     orm=ETCFeeDeductInfoOrm(id=CommonUtil.random_str(32).lower(),
                                             etc_info=etc_deduct_info_json,
                                             upload_flag=upload_flag,
                                             upload_fail_count=upload_fail_count))

        return params

    def close_client(self):
        """
        关闭客户端
        :return:
        """
        self.client.shutdown(2)
        self.client.close()


if __name__ == '__main__':
    pass
    # from pprint import pprint
    #
    # s_client = SocketClient(park_code='11111', lane_num='1')
    # s_client.fee_deduction(0.01)
    # print('======================b0======================')
    # pprint(s_client.command_recv_set.info_b0)
    # print('======================b2======================')
    # pprint(s_client.command_recv_set.info_b2)
    # print('======================b3======================')
    # pprint(s_client.command_recv_set.info_b3)
    # print('======================b4======================')
    # pprint(s_client.command_recv_set.info_b4)
    # print('======================b5======================')
    # pprint(s_client.command_recv_set.info_b5)
    # etc_toll(ip_tianxian, port=60001)
    # tianxian_demo()
    # c2 = CommandSendSet.combine_c2(obu_id='6a81353e', stop_type='01')
    # print(c0)
    # CommonUtil.bcc_xor('ffff80c05f493bf2020082817163203020a0002')
    # 'ffff82c16a81353ecdf2bcafcdf2bcaf'
    # CommandSendSet.combine_c1(obu_id='6a81353e', obu_div_factor=CommonConf.OBU_DIV_FACTOR)
