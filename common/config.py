import os
import sys

import yaml


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
    # RSU状态列表
    RSU_STATUS_LIST = []


os.makedirs(CommonConf.LOG_DIR, exist_ok=True)
os.makedirs(CommonConf.SQLITE_DIR, exist_ok=True)



if __name__ == '__main__':
    from pprint import pprint
    pprint(CommonConf.ETC_CONF_DICT)
    print(app_path())
    print(CommonConf.SQLITE_DIR)
