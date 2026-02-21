'''
    FANUC CNC Data Collection Program
    v1.2 Su600
    2023-1-9 只高频采集dynamic2 坐标信息，其它参数都1000次（约1分钟）采集一次
    1-10 恢复设置里的cycle参数
    2026-2-21 代码优化和改进

    功能说明:
    - 通过FOCAS库连接FANUC CNC机床
    - 高频采集坐标信息
    - 低频采集参数、定时器和状态信息
    - 通过MQTT发布数据

    todo 文件加密 二进制
'''
import ctypes
import os
import logging
import json
import time
import signal
import sys
from ctypes import *

import paho.mqtt.client as mqtt

# MQTT版本兼容性处理 (支持paho-mqtt 1.x和2.x)
try:
    from paho.mqtt.client import CallbackAPIVersion
    MQTT_V2 = True
except ImportError:
    MQTT_V2 = False

# ==================== 常量定义 ====================
MAX_AXIS = 48                    # 最大轴数
CNC_PORT = 8193                  # CNC默认端口
CNC_TIMEOUT = 10                 # CNC连接超时时间(秒)
MQTT_PORT = 1883                 # MQTT默认端口
MQTT_KEEPALIVE = 60              # MQTT保持连接时间(秒)
MQTT_QOS = 1                     # MQTT消息质量等级
LOW_FREQ_INTERVAL = 1000         # 低频数据采集间隔(次数)
PART_COUNT_PARAMETER = 6711      # 零件计数参数编号

# ==================== 全局变量 ====================
libpath = os.path.join(os.getcwd(), "libfwlib32.so")
focas = ctypes.cdll.LoadLibrary(libpath)

# 初始化FOCAS库
ret = focas.cnc_startupprocess(0, "focas.log")
if ret != 0:
    raise Exception(f"Failed to create required log file! ({ret})")

cnc_data = {}
libh = ctypes.c_ushort(0)
mqttclient = None
running = True  # 用于控制主循环

# ==================== 配置文件读取 ====================
'''
    打开配置文件
'''
def load_config(config_file='fanuc-config.json'):
    """
    读取配置文件并返回配置信息

    Args:
        config_file: 配置文件路径

    Returns:
        dict: 配置信息字典

    Raises:
        FileNotFoundError: 配置文件不存在
        json.JSONDecodeError: 配置文件格式错误
        KeyError: 缺少必要的配置项
    """
    try:
        with open(config_file, 'r', encoding='utf8') as fp:
            config = json.load(fp)

        # 验证必要的配置项
        required_keys = ['device_name', 'device_ip', 'cycle', 'mqtt_ip', 'mqtt_topic']
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required config key: {key}")

        # 转换cycle为浮点数
        config['cycle'] = float(config['cycle'])

        return config
    except FileNotFoundError:
        logging.error(f"配置文件 {config_file} 不存在")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"配置文件格式错误: {e}")
        raise
    except Exception as e:
        logging.error(f"读取配置文件失败: {e}")
        raise

## 读取配置文件 并输出连接信息
config = load_config()
device_name = config["device_name"]
device_ip = config["device_ip"]
cycle = config["cycle"]
mqtt_ip = config["mqtt_ip"]
mqtt_topic = config["mqtt_topic"]

print(f"\n============= FANUC 机床数据采集 Su600 =============== \n\
|| 【设备名称: 】  {device_name}\n\
|| 【机床IP:   】  {device_ip}\n\
|| 【循环延迟: 】  {cycle}\n\
|| 【MQTT地址: 】  {mqtt_ip}\n\
|| 【MQTT主题: 】  {mqtt_topic}\n\
===========================================================\n")

# ==================== MQTT相关函数 ====================
def create_mqtt_client(client_id):
    """
    创建MQTT客户端，兼容paho-mqtt 1.x和2.x

    Args:
        client_id: 客户端ID

    Returns:
        mqtt.Client: MQTT客户端实例
    """
    if MQTT_V2:
        return mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION1, client_id=client_id)
    else:
        return mqtt.Client(client_id)

mqttclient = create_mqtt_client(device_name)

# 连接MQTT服务器
def on_mqtt_connect(client, userdata, flags, rc):
    """
    MQTT连接回调函数

    Args:
        client: MQTT客户端实例
        userdata: 用户数据
        flags: 连接标志
        rc: 连接结果代码
    """
    if rc == 0:
        logging.info(f"MQTT连接成功")
    else:
        logging.error(f"MQTT连接失败，返回码: {rc}")

def connect_mqtt(mqtt_ip, port=MQTT_PORT, keepalive=MQTT_KEEPALIVE):
    """
    连接到MQTT服务器

    Args:
        mqtt_ip: MQTT服务器IP
        port: MQTT端口
        keepalive: 保持连接时间
    """
    try:
        mqttclient.on_connect = on_mqtt_connect
        mqttclient.connect(mqtt_ip, port, keepalive)
        mqttclient.loop_start()
        return True
    except Exception as e:
        logging.error(f"MQTT连接错误: {e}")
        return False

# 消息处理函数
def on_message_come(client, userdata, msg):
    """
    MQTT消息接收回调函数

    Args:
        client: MQTT客户端实例
        userdata: 用户数据
        msg: 接收到的消息
    """
    try:
        print(f'【{msg.topic}:{str(msg.payload)}】')
        aa = json.loads(msg.payload)
        print('收到消息了', aa)
    except Exception as e:
        logging.error(f"处理MQTT消息失败: {e}")

# ==================== 数据结构定义 ====================
class IODBPSD_U(Union):
    """参数数据联合体"""
    _fields_ = [
        ('cdata', c_char),
        ('idata', c_short),
        ('ldata', c_int32),
        ('cdatas', c_char * MAX_AXIS),
        ('idatas', c_short * MAX_AXIS),
        ('ldatas', c_int32 * MAX_AXIS)
    ]

class IODBPSD(Structure):
    """参数数据结构体"""
    _fields_ = [
        ('datano', c_short),
        ('type', c_short),
        ('u', IODBPSD_U)
    ]

class ODBACT(Structure):
    """实际主轴/进给速度结构体"""
    _fields_ = [
        ('dummy', c_short * 2),  # 修正：原'dummp[2]'语法错误
        ('data', c_int32)
    ]

#################### dynamic2 动态数据结构 ###############
class FAXIS(Structure):
    """多轴位置数据结构"""
    _fields_ = [
        ('absolute', c_int32 * MAX_AXIS),
        ('machine', c_int32 * MAX_AXIS),
        ('relative', c_int32 * MAX_AXIS),
        ('distance', c_int32 * MAX_AXIS),
    ]

class OAXIS(Structure):
    """单轴位置数据结构"""
    _fields_ = [
        ('absolute', c_int32),
        ('machine', c_int32),
        ('relative', c_int32),
        ('distance', c_int32),
    ]

class POS(Union):
    """位置数据联合体"""
    _fields_ = [
        ('faxis', FAXIS),
        ('oaxis', OAXIS)
    ]

class ODBDY2(Structure):
    """动态数据结构体"""
    _fields_ = [
        ('dummy', c_short),  # 修正：原'dummp'拼写错误
        ('axis', c_short),
        ('alarm', c_short),
        ('prgnum', c_int32),
        ('prgmnum', c_int32),
        ('seqnum', c_int32),
        ('actf', c_int32),
        ('acts', c_int32),
        ('pos', POS)
    ]
####################################

class ODBTLIFE4(Structure):
    """刀具寿命数据结构体"""
    _fields_ = [
        ('datano', c_short),
        ('type', c_short),
        ('data', c_int32)
    ]

class IODBTLMAG(Structure):
    """刀库数据结构体"""
    _fields_ = [
        ('magazine', c_short),
        ('pot', c_short),
        ('tool_index', c_short)
    ]

class IODBTIME(Structure):
    """时间数据结构体"""
    _fields_ = [
        ('minute', c_int32),
        ('msec', c_int32)
    ]

class ODBST(Structure):
    """状态信息结构体"""
    _fields_ = [
        ('hdck', c_short),
        ('tmmode', c_short),
        ('auto', c_short),
        ('run', c_short),
        ('motion', c_short),
        ('mstb', c_short),
        ('emergency', c_short),
        ('alarm', c_short),
        ('edit', c_short)
    ]
'''
hdck (30i/31i/32i, 0i-D/F only)
    Status of manual handle re-trace
    0	:	Invalid of manual handle re-trace
    1	:	M.H.RTR.(Manual handle re-trace)
    2	:	NO RVRS.(Backward movement prohibition)
    3	:	NO CHAG.(Direction change prohibition)
tmmode
    T/M mode selection (only with compound machining function)
    0	:	T mode
    1	:	M mode
====================================
aut(auto)
    AUTOMATIC/MANUAL mode selection
    0	:	MDI
    1	:	MEMory
    2	:	****
    3	:	EDIT
    4	:	HaNDle
    5	:	JOG
    6	:	Teach in JOG
    7	:	Teach in HaNDle
    8	:	INC·feed
    9	:	REFerence
    10	:	ReMoTe
run
    Status of automatic operation
    0	:	****(reset)
    1	:	STOP 
    2	:	HOLD 
    3	:	STaRT 
    4	:	MSTR(during retraction and re-positioning of tool retraction and recovery, and operation of JOG MDI)
emergency
    Status of emergency
    0	:	(Not emergency)
    1	:	EMerGency
    2	:	ReSET
    3	:	WAIT(FS35i only)
alarm
    Status of alarm
    0	:	***(Others)
    1	:	ALarM
    2	:	BATtery low
    3	:	FAN(NC or Servo amplifier)
    4	:	PS Warning
    5	:	FSsB warning
    6	:	INSulate warning
    7	:	ENCoder warning
    8	:	PMC alarm
================================================
motion
    Status of axis movement, dwell
    0	:	***
    1	:	MoTioN
    2	:	DWeLl
mstb
    Status of M,S,T,B function
    0	:	***(Others)
    1	:	FIN
edit
    分型号 程序编辑状态 暂不处理
'''

class LOADELM(Structure):
    _fields_=[
        ("data",c_int32),
        ("dec", c_short),
        ("unit", c_short),
        ("name", c_char),
        ("suff1", c_char),
        ("suff2", c_char),
        ("reserve", c_char)
    ]

class ODBSPLOAD(Structure):
    _fields_=[
        ("spload",LOADELM),
        ("spspeed", LOADELM)
    ]

#################
# ==================== 数据读取函数 ====================
def read_cnc_id():
    """
    读取CNC设备ID

    Raises:
        Exception: 读取失败时抛出异常
    """
    cnc_ids = (ctypes.c_uint32 * 4)()
    ret = focas.cnc_rdcncid(libh, cnc_ids)
    if ret != 0:
        raise Exception(f"Failed to read cnc id ({ret})")
    machine_id = "-".join([f"{cnc_ids[i]:08x}" for i in range(4)])
    cnc_data["machine_id"] = machine_id

def read_param():
    """
    读取CNC参数（零件计数）

    Raises:
        Exception: 读取失败时抛出异常
    """
    iodbpsd = IODBPSD()

    ret = focas.cnc_rdparam(libh, PART_COUNT_PARAMETER, 0, 4 + MAX_AXIS, byref(iodbpsd))

    if ret != 0:
        raise Exception(f"Failed to read param ({ret})")
    cnc_data["part_count"] = iodbpsd.u.ldata

def read_dynamic2():
    """
    读取CNC动态数据（坐标、程序号、速度等）

    注意：坐标值需要除以1000转换为实际单位

    Raises:
        Exception: 读取失败时抛出异常
    """
    buf = ODBDY2()

    ret = focas.cnc_rddynamic2(libh, -1, sizeof(buf), byref(buf))

    if ret != 0:
        raise Exception(f"Failed to read dynamic2 ({ret})")

    # 使用列表推导式优化坐标转换性能 (替代map函数)
    # 修正：原代码索引错误，relative使用了absolute[32:35]，machine使用了[16:19]
    # 应该都从0开始取前3个轴的对应坐标
    cnc_data["absolute"] = [x / 1000.0 for x in buf.pos.faxis.absolute[0:3]]
    cnc_data["relative"] = [x / 1000.0 for x in buf.pos.faxis.relative[0:3]]
    cnc_data["machine"] = [x / 1000.0 for x in buf.pos.faxis.machine[0:3]]

    cnc_data["acts"] = buf.acts
    cnc_data["actf"] = buf.actf

    cnc_data["prgnum"] = buf.prgnum
    cnc_data["prgmnum"] = buf.prgmnum
    cnc_data["seqnum"] = buf.seqnum

def read_timer():
    """
    读取CNC计时器数据

    计时器类型:
    0: Power on time  - 通电时间
    1: Operating time - 运行时间
    2: Cutting time   - 切削时间
    3: Cycle time     - 循环时间
    4: Free purpose   - 自由用途

    Raises:
        Exception: 读取失败时抛出异常
    """
    # 0: Power on time
    # 1: Operating time
    # 2: Cutting time
    # 3: Cycle time
    # 4: Free purpose
    cnc_data["timer"] = {}
    timer = IODBTIME()

    ret = focas.cnc_rdtimer(libh, 0, byref(timer))

    if ret != 0:
        raise Exception(f"Failed to read timer ! ({ret})")
    cnc_data["timer"]["powerOnTimer"] = timer.minute

    ret = focas.cnc_rdtimer(libh, 1, byref(timer))

    if ret != 0:
        raise Exception(f"Failed to read timer ! ({ret})")
    cnc_data["timer"]["operatingTimer"] = timer.minute

    ret = focas.cnc_rdtimer(libh, 2, byref(timer))

    if ret != 0:
        raise Exception(f"Failed to read timer ! ({ret})")
    cnc_data["timer"]["cuttingTimer"] = timer.minute

def read_statinfo():
    """
    读取CNC状态信息

    包括:
    - auto: 自动/手动模式
    - emergency: 急停状态
    - run: 运行状态
    - alarm: 报警状态

    注意：当急停按下时，run状态强制置为1(STOP)

    Raises:
        Exception: 读取失败时抛出异常
    """
    statinfo = ODBST()

    ret = focas.cnc_statinfo(libh, byref(statinfo))

    if ret != 0:
        raise Exception(f"Failed to read statinfo ! ({ret})")

    cnc_data["statinfo"] = {}
    cnc_data["statinfo"]['auto'] = statinfo.auto
    cnc_data["statinfo"]['emergency'] = statinfo.emergency
    # cnc_data["statinfo"]['run'] = statinfo.run
    if statinfo.emergency == 1:  # 急停按下，run状态强制置1（Stop）
        cnc_data["statinfo"]['run'] = 1
    else:
        cnc_data["statinfo"]['run'] = statinfo.run
    cnc_data["statinfo"]['alarm'] = statinfo.alarm

# ==================== 信号处理和清理函数 ====================
def signal_handler(sig, frame):
    """
    处理终止信号，确保资源正确释放

    Args:
        sig: 信号编号
        frame: 当前栈帧
    """
    global running
    print('\n程序正在安全退出...')
    running = False

def cleanup():
    """
    清理资源：断开MQTT和CNC连接
    """
    try:
        if mqttclient:
            mqttclient.loop_stop()
            mqttclient.disconnect()
            logging.info("MQTT连接已断开")
    except Exception as e:
        logging.error(f"MQTT断开连接时出错: {e}")

    try:
        ret = focas.cnc_freelibhndl(libh)
        if ret != 0:
            logging.error(f"Failed to free library handle! ({ret})")
        else:
            logging.info("CNC连接已断开")
    except Exception as e:
        logging.error(f"CNC断开连接时出错: {e}")

############## 主程序 #############
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('fanuc-su.log'),
            logging.StreamHandler()
        ]
    )

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 1. 连接CNC
        print(f"正在连接到设备 {device_ip}:{CNC_PORT}...")
        ret = focas.cnc_allclibhndl3(device_ip.encode(), CNC_PORT, CNC_TIMEOUT, ctypes.byref(libh))
        if ret != 0:
            raise Exception(f"机床连接失败 ({ret})")
        print(f"【CNC {device_ip} 连接成功】")

        cnc_data['device_name'] = device_name

        # 2. 连接MQTT
        if connect_mqtt(mqtt_ip):
            print(f"【MQTT {mqtt_ip} 连接成功】")
        else:
            logging.warning("MQTT连接失败，但程序将继续运行")

        # 3. 主循环 - 数据采集和发送
        ii = 0
        logging.info("开始数据采集...")

        while running:
            try:
                # 使用模ulo运算符优化循环逻辑
                # 每1000次(约1分钟)采集一次低频数据
                if ii % LOW_FREQ_INTERVAL == 0:
                    read_param()
                    part_count = cnc_data["part_count"]

                    read_dynamic2()
                    absolute = cnc_data["absolute"]
                    relative = cnc_data["relative"]
                    machine = cnc_data["machine"]

                    read_timer()
                    timer = cnc_data["timer"]

                    read_statinfo()
                    statinfo = cnc_data["statinfo"]
                else:
                    # 高频采集：只采集坐标信息
                    read_dynamic2()
                    # 使用缓存的低频数据
                    cnc_data["timer"] = timer
                    cnc_data["part_count"] = part_count
                    cnc_data["statinfo"] = statinfo

                ii += 1

                # 发送MQTT消息
                mqtt_msg = json.dumps(cnc_data)
                result = mqttclient.publish(mqtt_topic, payload=mqtt_msg, qos=MQTT_QOS)

                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    logging.debug(f"MQTT数据发送成功 topic:{mqtt_topic}")
                else:
                    logging.warning(f"MQTT数据发送失败 rc:{result.rc}")

                time.sleep(cycle)

            except Exception as e:
                logging.error(f"数据采集或发送错误: {e}")
                # 发生错误时暂停一会儿再继续
                time.sleep(1)

    except KeyboardInterrupt:
        print("\n用户中断程序")
    except Exception as e:
        logging.error(f"程序错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup()
        print("程序已退出")
        sys.exit(0)
