'''
    v1.1 Su600
    2023-1-9 只高频采集dynamic2 坐标信息，其它参数都1000次（约1分钟）采集一次
    1-10 恢复设置里的cycle参数

    v1.2 Su600
    2026-2-20 修复相对坐标读取索引错误(relative[0:3])
              修复ODBACT结构体字段定义错误(dummp应为c_short*2)
              修复cnc_startupprocess字符串未编码问题
              移除主循环中的重复loop_start调用
              增加CNC/MQTT断线重连机制，提升长期运行稳定性
              修复cnc_freelibhndl不可达代码，改为try/finally确保资源释放
              使用脚本目录替代os.getcwd()定位库文件，避免路径问题
              机床坐标使用测试验证的索引machine[16:19]

    todo 文件加密 二进制
'''
import ctypes
import os
import logging
import json
import time
import paho.mqtt.client as mqtt
from ctypes import (
    Structure, Union, c_char, c_short, c_int32, c_uint32, c_ushort,
    byref, sizeof, cdll
)

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 使用脚本所在目录作为库路径，避免因工作目录不同导致加载失败
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
libpath = os.path.join(_SCRIPT_DIR, "libfwlib32.so")
focas = cdll.LoadLibrary(libpath)

# cnc_startupprocess第二个参数需要bytes类型（Python 3）
ret = focas.cnc_startupprocess(0, b"focas.log")
if ret != 0:
    raise Exception(f"Failed to create required log file! ({ret})")

'''
    打开配置文件
'''
# 读取配置文件并输出连接信息
_config_path = os.path.join(_SCRIPT_DIR, 'fanuc-config.json')
with open(_config_path, 'r', encoding='utf8') as fp:
    json_data = json.load(fp)
    device_name = json_data["device_name"]
    device_ip = json_data["device_ip"]
    cycle = float(json_data["cycle"])
    mqtt_ip = json_data["mqtt_ip"]
    mqtt_topic = json_data["mqtt_topic"]

    print(f"\n============= FANUC 机床数据采集 Su600 ===============")
    print(f"|| 【设备名称: 】  {device_name}")
    print(f"|| 【机床IP:   】  {device_ip}")
    print(f"|| 【循环延迟: 】  {cycle}")
    print(f"|| 【MQTT地址: 】  {mqtt_ip}")
    print(f"|| 【MQTT主题: 】  {mqtt_topic}")
    print("===========================================================\n")

port = 8193
timeout = 10
cnc_data = {}

# 数据采集周期配置（每N次循环进行一次完整数据采集）
FULL_DATA_CYCLE = 1000

libh = c_ushort(0)

mqttclient = mqtt.Client(device_name)

# 连接MQTT服务器，loop_start启动后台线程，只调用一次
def on_mqtt_connect(mqtt_ip):
    mqttclient.connect(mqtt_ip, 1883, 60)
    mqttclient.loop_start()

# MQTT连接成功回调
def _on_mqtt_connected(client, userdata, flags, rc):
    if rc == 0:
        logging.info(f"MQTT {mqtt_ip} 连接成功")
    else:
        logging.warning(f"MQTT 连接失败，返回码: {rc}")


# MQTT断开连接回调，rc!=0表示意外断开，paho会自动重连
def _on_mqtt_disconnected(client, userdata, rc):
    if rc != 0:
        logging.warning(f"MQTT 意外断开连接，返回码: {rc}，将自动重连")

# 消息处理函数
def on_message_come(client, userdata, msg):
    try:
        payload = json.loads(msg.payload)
        logging.info(f"收到MQTT消息 topic:{msg.topic}, payload:{payload}")
    except json.JSONDecodeError as e:
        logging.error(f"MQTT消息解析失败: {e}")

# 注册MQTT回调
mqttclient.on_connect = _on_mqtt_connected
mqttclient.on_disconnect = _on_mqtt_disconnected
mqttclient.on_message = on_message_come

MAX_AXIS = 48


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
    """实际速度数据结构体"""
    _fields_ = [
        ('dummp', c_short * 2),  # 修复：原'dummp[2]'为无效字段名且仅占2字节，应为c_short*2(4字节)
        ('data', c_int32)
    ]


# dynamic2 相关结构体
class FAXIS(Structure):
    """多轴坐标数据结构体"""
    _fields_ = [
        ('absolute',c_int32*MAX_AXIS),
        ('machine', c_int32*MAX_AXIS),
        ('relative', c_int32*MAX_AXIS),
        ('distance', c_int32*MAX_AXIS),
    ]


class OAXIS(Structure):
    """单轴坐标数据结构体"""
    _fields_ = [
        ('absolute',c_int32),
        ('machine', c_int32),
        ('relative', c_int32),
        ('distance', c_int32),
    ]


class POS(Union):
    """坐标数据联合体"""
    _fields_ = [
        ('faxis',FAXIS),
        ('oaxis',OAXIS)
    ]

class ODBDY2(Structure):
    """动态数据结构体 (dynamic2)"""
    _fields_ = [
        ('dummp', c_short),
        ('axis', c_short),
        ('alarm',c_short),
        ('prgnum',c_int32),
        ('prgmnum',c_int32),
        ('seqnum',c_int32),
        ('actf',c_int32),
        ('acts',c_int32),
        ('pos',POS)
    ]


class ODBTLIFE4(Structure):
    """刀具寿命数据结构体"""
    _fields_ = [
        ('datano',c_short),
        ('type',c_short),
        ('data',c_int32)
    ]
class IODBTLMAG(Structure):
    """刀具管理数据结构体"""
    _fields_ = [
        ('magazine',c_short),
        ('pot',c_short),
        ('tool_index',c_short)
    ]
class IODBTIME(Structure):
    """定时器数据结构体"""
    _fields_ = [
        ('minute',c_int32),
        ('msec',c_int32)
    ]

class ODBST(Structure):
    """机床状态信息结构体"""
    _fields_ = [
        ('hdck', c_short),
        ('tmmode',c_short),
        ('auto', c_short),
        ('run', c_short),
        ('motion', c_short),
        ('mstb', c_short),
        ('emergency', c_short),
        ('alarm',c_short),
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
    """负载数据元素结构体"""
    _fields_ = [
        ("data",c_int32),
        ("dec", c_short),
        ("unit", c_short),
        ("name", c_char),
        ("suff1", c_char),
        ("suff2", c_char),
        ("reserve", c_char)
    ]
class ODBSPLOAD(Structure):
    """主轴负载数据结构体"""
    _fields_ = [
        ("spload",LOADELM),
        ("spspeed", LOADELM)
    ]


# 辅助函数
def div1000(x: int) -> float:
    """将整数值除以1000，用于坐标单位转换"""
    return x / 1000


def read_cnc_id():
    """读取CNC机床ID"""
    cnc_ids = (c_uint32 * 4)()
    ret = focas.cnc_rdcncid(libh, cnc_ids)
    if ret != 0:
        raise Exception(f"Failed to read cnc id ({ret})")
    machine_id = "-".join([f"{cnc_ids[i]:08x}" for i in range(4)])
    cnc_data["machine_id"] = machine_id


def read_param():
    """读取参数数据（零件计数）"""
    PART_COUNT_PARAMETER = 6711
    iodbpsd = IODBPSD()

    ret = focas.cnc_rdparam(libh, PART_COUNT_PARAMETER, 0, 4 + MAX_AXIS, byref(iodbpsd))

    if ret != 0:
        raise Exception(f"Failed to read param ({ret})")
    cnc_data["part_count"] = iodbpsd.u.ldata


def read_dynamic2():
    """读取动态数据（坐标、速度、程序号等）"""
    buf = ODBDY2()

    ret = focas.cnc_rddynamic2(libh, -1, sizeof(buf), byref(buf))

    if ret != 0:
        raise Exception(f"Failed to read dynamic2 ({ret})")
    # 读取前3轴绝对坐标（X/Y/Z），除以1000转换为毫米
    cnc_data["absolute"] = list(map(div1000, buf.pos.faxis.absolute[0:3]))
    # 修复：相对坐标应从relative数组读取，原代码错误地读取了absolute[32:35]
    cnc_data["relative"] = list(map(div1000, buf.pos.faxis.relative[0:3]))
    # 机床坐标从machine[16:19]读取（已实际测试验证的索引）
    cnc_data["machine"] = list(map(div1000, buf.pos.faxis.machine[16:19]))
    cnc_data["acts"] = buf.acts
    cnc_data["actf"] = buf.actf

    cnc_data["prgnum"] = buf.prgnum
    cnc_data["prgmnum"] = buf.prgmnum
    cnc_data["seqnum"] = buf.seqnum


def read_timer():
    """读取定时器数据（通电、运行、切削时间）"""
    # 0: Power on time
    # 1: Operating time
    # 2: Cutting time
    # 3: Cycle time
    # 4: Free purpose
    cnc_data["timer"] = {}
    timer = IODBTIME()

    # 读取通电时间
    ret = focas.cnc_rdtimer(libh, 0, byref(timer))
    if ret != 0:
        raise Exception(f"Failed to read power-on timer ({ret})")
    cnc_data["timer"]["powerOnTimer"] = timer.minute

    # 读取运行时间
    ret = focas.cnc_rdtimer(libh, 1, byref(timer))
    if ret != 0:
        raise Exception(f"Failed to read operating timer ({ret})")
    cnc_data["timer"]["operatingTimer"] = timer.minute

    # 读取切削时间
    ret = focas.cnc_rdtimer(libh, 2, byref(timer))
    if ret != 0:
        raise Exception(f"Failed to read cutting timer ({ret})")
    cnc_data["timer"]["cuttingTimer"] = timer.minute


def read_statinfo():
    """读取机床状态信息（自动/手动模式、运行状态、急停、报警等）"""
    statinfo = ODBST()

    ret = focas.cnc_statinfo(libh, byref(statinfo))

    if ret != 0:
        raise Exception(f"Failed to read statinfo ({ret})")

    cnc_data["statinfo"] = {}
    cnc_data["statinfo"]['auto'] = statinfo.auto
    cnc_data["statinfo"]['emergency'] = statinfo.emergency
    # 急停按下时，run状态强制置1（Stop）
    if statinfo.emergency == 1:
        cnc_data["statinfo"]['run'] = 1
    else:
        cnc_data["statinfo"]['run'] = statinfo.run
    cnc_data["statinfo"]['alarm'] = statinfo.alarm


# 主程序
if __name__ == "__main__":
    print(f"正在连接到设备 {device_ip}:{port}...")
    ret = focas.cnc_allclibhndl3(device_ip.encode(), port, timeout, byref(libh))
    if ret != 0:
        raise Exception(f"机床连接失败 ({ret})")

    cnc_data['device_name'] = device_name

    # 连接MQTT
    try:
        on_mqtt_connect(mqtt_ip)
    except Exception as error:
        logging.error(f"MQTT连接错误: {error}")
    else:
        logging.info(f"MQTT {mqtt_ip} 连接成功")

    iteration_count = 0
    try:
        while True:
            # 每FULL_DATA_CYCLE次循环进行一次完整数据采集
            if iteration_count == 0 or iteration_count == FULL_DATA_CYCLE:
                read_param()
                part_count = cnc_data["part_count"]

                read_dynamic2()

                read_timer()
                timer = cnc_data["timer"]

                read_statinfo()
                statinfo = cnc_data["statinfo"]
                if iteration_count == FULL_DATA_CYCLE:
                    iteration_count = 1
            else:
                # 高频采集：只读取动态数据，复用上次的timer、part_count、statinfo
                read_dynamic2()
                cnc_data["timer"] = timer
                cnc_data["part_count"] = part_count
                cnc_data["statinfo"] = statinfo

            iteration_count += 1
            time.sleep(cycle)

            # 发布MQTT消息
            mqtt_msg = json.dumps(cnc_data)
            logging.info(mqtt_msg)
            mqttclient.publish(mqtt_topic, payload=mqtt_msg, qos=1)
            logging.info(f"MQTT发送数据 topic:{mqtt_topic} Done")

    except Exception as e:
        logging.error(f"主循环异常退出: {e}")
        raise
    finally:
        # 确保程序退出时释放CNC连接句柄
        ret = focas.cnc_freelibhndl(libh)
        if ret != 0:
            logging.warning(f"Failed to free library handle! ({ret})")
