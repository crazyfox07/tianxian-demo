import socket
import traceback
from retrying import retry
from func_timeout import func_set_timeout
from service.command_receive_set import CommandReceiveSet
from common.config import CommonConf
from common.utils import CommonUtil
from service.command_send_set import CommandSendSet
from common.log import logger


class SocketClient(object):
    """
    创建socket客户端
    :author: liuxuewen
    :date: 2020/9/1 8:52
    """

    def __init__(self, tianxian_ip, port=60001):
        """
        socket客户初始化
        :param tianxian_ip: 天线ip
        :param port: 天线socket端口
        """
        # 创建一个客户端的socket对象
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 连接服务端
        self.client.connect((tianxian_ip, port))
        # 创建命令收集对象，用于后期解析天线发送过来的命令
        self.command_recv_set = CommandReceiveSet()
        # self.etc_charge_flag=True表示交易成功，self.etc_charge_flag=False表示交易失败
        self.etc_charge_flag = False
        # 接收到的指令为空，可能是socket关闭异常导致，需要再重新建立一次socket连接
        self.msg_receive_is_empty = False

    def get_client(self):
        """
        获取客户端
        :return:
        """
        return self.client

    @func_set_timeout(CommonConf.TIME_OUT * 100)
    def fee_deduction(self, money: float) -> CommandReceiveSet:
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
        c0 = CommandSendSet.combine_c0().strip()
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
                    c1 = CommandSendSet.combine_c1(obuid, obu_div_factor=CommonConf.OBU_DIV_FACTOR)
                    logger.info('b2后发送c1指令：%s' % (c1))
                    self.client.send(bytes.fromhex(c1))
            # b3 车辆信息帧
            elif msg_str[6:8] == 'b3':
                if msg_str[16: 18] == '00':  # obu信息帧状态执行码，取值00正常
                    self.command_recv_set.parse_b3(msg_str)  # 解析b3指令
                    # 再次获取c1指令并发送
                    c1 = CommandSendSet.combine_c1(obuid, obu_div_factor=CommonConf.OBU_DIV_FACTOR)
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
                    # 获取并发送c6消费交易指令
                    deduct_amount = CommonUtil.etcfee_to_hex(money)  # 扣款额，高字节在前
                    purchase_time = CommonUtil.timestamp_format()
                    station = msg_str[132:212]  # 过站信息,40个字节
                    c6 = CommandSendSet.combine_c6(obuid, card_div_factor=CommonConf.OBU_DIV_FACTOR,
                                                   reserved='00000000',
                                                   deduct_amount=deduct_amount, purchase_time=purchase_time,
                                                   station=station)
                    logger.info('发送c6指令，消费交易，出口消费写过站: {}， 其中扣除费用{}'.format(c6, money))
                    self.client.send(bytes.fromhex(c6))
            # b5 交易信息帧，表示此次交易成功结束
            elif msg_str[6:8] == 'b5':
                if msg_str[16: 18] == '00':  # 状态执行码，00说明正常
                    self.command_recv_set.parse_b5(msg_str)  # 解析b5指令
                    # # 获取并发送c1继续交易指令
                    # c1 = CommandSendSet.combine_c1(obuid, obu_div_factor=CommonConf.OBU_DIV_FACTOR)
                    # print('b5后发送c1指令：%s， 电子标签mac地址 obuid = %s' % (c1, obuid))
                    # self.client.send(bytes.fromhex(c1))
                    # 关闭天线
                    self.client.close()
                    self.etc_charge_flag = True
                    return self.command_recv_set
            elif msg_str is None:
                logger.error('接收到的指令为空')
                self.client.close()
                self.msg_receive_is_empty = True
                return self.command_recv_set
            else:
                logger.exception('未能解析的指令：%s' % (msg_str))
                self.client.close()
                return self.command_recv_set

    def handle_data(self) -> dict:
        """
        处理self.command_recv_set，也就是收到的天线的信息
        :return:
        """
        data = dict(
            obu_id=self.command_recv_set.info_b2['OBUID'],  # obuid
            issuer_identifier=self.command_recv_set.info_b2['IssuerIdentifier'],  # 发行商代码
            serial_number=self.command_recv_set.info_b2['SerialNumber'],  # 应用序列号
            data_of_issue = self.command_recv_set.info_b2['DataOfIssue'],  # 启用日期
            data_of_expire=self.command_recv_set.info_b2['DataOfExpire'],  # 过期日期
            equitment_cv=self.command_recv_set.info_b2['EquitmentCV'],  # 设备类型
            obu_status=self.command_recv_set.info_b2['OBUStatus'],  # obu状态

            plate_no=self.command_recv_set.info_b3['VehicleLicencePlateNumber'],  # 车牌号
            plate_color_code=self.command_recv_set.info_b3['VehicleLicencePlateColor'],  # 车牌颜色
            vehicl_class=self.command_recv_set.info_b3['VehicleClass'],  # 车辆类型
            vehicle_user_type=self.command_recv_set.info_b3['VehicleUserType'],  # 车辆用户类型

            card_type=self.command_recv_set.info_b4['CardType'],  # 卡类型
            physical_card_type=self.command_recv_set.info_b4['PhysicalCardType'],  # 物理卡类型
            trans_before_balance=self.command_recv_set.info_b4['CardRestMoney'],  # 交易前卡余额
            vehicle_class=self.command_recv_set.info_b4['VehicleClass'],  # 物理卡号
            issuer_info=self.command_recv_set.info_b4['IssuerInfo'],  # 卡发行信息
            last_station=self.command_recv_set.info_b4['LastStation'],  # 上次过站信息

            TAC=self.command_recv_set.info_b5['TAC'],  # 交易认证码
            TransTime=self.command_recv_set.info_b5['TransTime'],  # 交易时间
            psam_serial_no=self.command_recv_set.info_b5['PSAMNo'],  # PSAM卡终端机编号
            trans_type =self.command_recv_set.info_b5['TransType'],  # 交易类型
            psam_trans_serial=self.commanmand_recv_set.info_b5['PSAMTransSerial'],  # PSAM卡终端交易序号
            icc_pay_serial=self.command_d_recv_set.info_b5['ICCPaySerial'],  # 速通卡脱机交易序号，对于不涉及消费的交易填充0
            card_balance=self.comrecv_set.info_b5['CardBalance'],  # 交易后余额
        )

        return data

    def close_client(self):
        """
        关闭客户端
        :return:
        """
        self.client.close()





if __name__ == '__main__':
    # etc_toll(ip_tianxian, port=60001)
    # tianxian_demo()
    c2 = CommandSendSet.combine_c2(obu_id='6a81353e', stop_type='01')
    # print(c0)
    # CommonUtil.bcc_xor('ffff80c05f493bf2020082817163203020a0002')
    # 'ffff82c16a81353ecdf2bcafcdf2bcaf'
    # CommandSendSet.combine_c1(obu_id='6a81353e', obu_div_factor=CommonConf.OBU_DIV_FACTOR)
