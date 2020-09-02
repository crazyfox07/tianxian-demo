import time

from common.config import CommonConf


class CommonUtil(object):
    @staticmethod
    def timestamp_format(timestamp=int(time.time()), format='%Y%m%d%H%M%S'):
        """
        时间戳格式化
        :param timestamp:
        :param format:
        :return:
        """
        timeformat = time.strftime(format, time.localtime(timestamp))
        return timeformat

    @staticmethod
    def get_rsctl():
        """
        获取发送到天线的数据帧
        :return:
        """
        index = CommonConf.COUNT % len(CommonConf.RSCTL)
        rsctl = '8' + str(CommonConf.RSCTL[index])
        CommonConf.COUNT += 1
        return rsctl

    @staticmethod
    def bcc_xor(value_verify):
        """
        bcc 异或值校验
        :param value_verify: 待校验的值
        :return:
        """
        # 将‘ffff89’转换成['ff', 'ff', '89']
        str_to_list = [value_verify[2 * i] + value_verify[2 * i + 1] for i in range(len(value_verify) // 2)]
        bcc = int(str_to_list[0], 16)
        for item in str_to_list[1:]:
            bcc = bcc ^ int(item, 16)
        bcc = hex(bcc)[2:]
        bcc = '0' + bcc if len(bcc) == 1 else bcc
        return bcc

    @staticmethod
    def etcfee_to_hex(consume_money):
        """
        etc费用转hex,
        :param consume_money: 消费金额
        :return:
        """
        consume_money = int(consume_money * 100)
        consume_money_hex = hex(consume_money)[2:]
        zero_pad_num = 0 if (8 - len(consume_money_hex)) < 0 else (8 - len(consume_money_hex))
        consume_money_hex = '0' * zero_pad_num + consume_money_hex
        return consume_money_hex[-8:]

    @staticmethod
    def hex_to_etcfee(consume_money_hex):
        """
        hex转etc费用
        :param consume_money_hex: etc费用的hex形式
        :return:
        """
        consume_money = int(consume_money_hex, 16) / 100
        return consume_money


if __name__ == '__main__':
    consume_money_hex = CommonUtil.etcfee_to_hex(999.99)
    print(consume_money_hex)
    consume_money = CommonUtil.hex_to_etcfee(consume_money_hex)
    print(consume_money)

    print(CommonUtil.hex_to_etcfee('fe01fe01'))
    print(CommonUtil.hex_to_etcfee('ffffa579'))