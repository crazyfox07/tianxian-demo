import os
import sys

import yaml


# class ETCCONF(object):
#     """
#     etc交易设置
#     """
#
#     def __init__(self, lane_num='0', communicate_interface='以太网', ip='192.168.1.69', port=60001, lane_mode='03',
#                  trans_mode='02', wait_time='03', pll_channel_id='00', tx_power='08', obu_div_factor='cdf2bcafcdf2bcaf',
#                  device_no='ShowLinx - 3202005006', device_type='0'):
#         """
#         :param lane_num: 车道号
#         :param communicate_interface: 通讯接口
#         :param ip:  天线ip
#         :param port:  端口
#         :param lane_mode: 车道模式
#         :param trans_mode: 交易模式
#         :param wait_time: 最小重读时间
#         :param pll_channel_id: 信道号
#         :param tx_tower: 功率级数
#         :param obu_div_factor: 电子标签一级分散因子 比如"万集万集"的十六进制 'CDF2BCAFCDF2BCAF'， 山东： 'c9bdb6abc9bdb6ab'
#         :param device_no: 设备号
#         :param device_type: 设备类型
#         """
#         self.lane_num = lane_num
#         self.communicate_interface = communicate_interface
#         self.ip = ip
#         self.port = port
#         self.lane_mode = lane_mode
#         self.trans_mode = trans_mode
#         self.wait_time = wait_time
#         self.pll_channel_id = pll_channel_id
#         self.tx_power = tx_power
#         self.obu_div_factor = obu_div_factor
#         self.device_no = device_no
#         self.device_type = device_type


def parse_ect_conf_yaml(file_path='etc_conf.yaml'):
    """
    解析etc配置文件
    :param file_path: etc配置文件路径
    :return:
    """
    with open(file_path, encoding='utf-8') as fr:
        etc_conf_dict = yaml.safe_load(fr)
        return etc_conf_dict

def app_path():
    """Returns the base application path."""
    if hasattr(sys, 'frozen'):
        # Handles PyInstaller
        print('1111111111111111111111111111111111111111111')
        print(getattr(sys, 'frozen'))
        print(sys.executable)
        return os.path.dirname(sys.executable).rsplit('common')[0]  #使用pyinstaller打包后的exe目录
    return os.path.dirname(__file__).rsplit('common')[0]                 #没打包前的py目录

class CommonConf(object):
    """公共配置"""
    # 数据帧序列号计数器
    COUNT = 0
    # 数据帧序列号8XH中X可选数值
    RSCTL = [0, 1, 2, 3, 4, 5, 6, 7, 9]
    # 指令开始标志
    COMMAND_BEGIN_FLAG = 'ffff'
    # 指令结束标志
    COMMAND_END_FLAG = 'ff'
    # 项目根目录
    # ROOT_DIR = os.path.realpath(__file__).rsplit('common')[0]
    ROOT_DIR = app_path()
    # 日志路径
    LOG_DIR = os.path.join(ROOT_DIR, 'logs')
    # 超时时间
    TIME_OUT = 20
    # etc配置文件路径
    ETC_CONF_PATH = os.path.join(ROOT_DIR, 'common', 'etc_conf.yaml')
    # etc_conf.yaml转为python的字典形式
    ETC_CONF_DICT = parse_ect_conf_yaml(ETC_CONF_PATH)
    # sqlite的路径
    SQLITE_DIR = ETC_CONF_DICT['sqlite_dir']



if __name__ == '__main__':
    from pprint import pprint
    pprint(CommonConf.ETC_CONF_DICT)
    print(app_path())
    print(CommonConf.SQLITE_DIR)
