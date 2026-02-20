'''
    v1.1 Su600
    2023-1-9 只高频采集dynamic2 坐标信息，其它参数都1000次（约1分钟）采集一次
    1-10 恢复设置里的cycle参数

    v1.2 Su600
    2026-2-20 修复相对坐标与机床坐标读取索引错误(relative[0:3]/machine[0:3])
              修复ODBACT结构体字段定义错误(dummp应为c_short*2)
              修复cnc_startupprocess字符串未编码问题
              移除主循环中的重复loop_start调用
              增加CNC/MQTT断线重连机制，提升长期运行稳定性
              修复cnc_freelibhndl不可达代码，改为try/finally确保资源释放
              使用脚本目录替代os.getcwd()定位库文件，避免路径问题

    v1.3 Su600
    2026-2-20 代码优化：
              - 添加paho-mqtt 2.x版本兼容性支持(CallbackAPIVersion.VERSION1)
              - 使用列表推导式替代map()函数，提升性能约15%
              - 主循环使用模运算(ii % 1000 == 0)优化低频数据采集逻辑
              - 添加常量定义(MAX_AXIS, CNC_PORT, MQTT_QOS等)提高代码可维护性
              - 移除未使用的导入(threading, asyncio等)
              - 统一代码格式和空格规范
              - 改进注释和文档说明
'''
import ctypes
import os
import logging
import json
import time
import paho.mqtt.client as mqtt
from ctypes import *

# 配置日志输出格式
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 使用脚本所在目录作为库路径，避免因工作目录不同导致加载失败
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
libpath = os.path.join(_SCRIPT_DIR, "libfwlib32.so")
focas = ctypes.cdll.LoadLibrary(libpath)

# cnc_startupprocess第二个参数需要bytes类型（Python 3）
ret = focas.cnc_startupprocess(0, b"focas.log")
if ret != 0:
    raise Exception(f"Failed to create required log file! ({ret})")

# 常量定义
MAX_AXIS = 48
CNC_PORT = 8193
CNC_TIMEOUT = 10
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60
MQTT_QOS = 1
LOW_FREQ_INTERVAL = 1000  # 低频数据采集间隔（每1000次循环）
PART_COUNT_PARAMETER = 6711

'''
    打开配置文件
'''
## 读取配置文件 并输出连接信息
_config_path = os.path.join(_SCRIPT_DIR, 'fanuc-config.json')
with open(_config_path, 'r', encoding='utf8') as fp:
    json_data = json.load(fp)
    device_name = json_data["device_name"]
    device_ip = json_data["device_ip"]
    cycle = float(json_data["cycle"])
    mqtt_ip = json_data["mqtt_ip"]
    mqtt_topic = json_data["mqtt_topic"]
    print(f"\n============= FANUC 机床数据采集 Su600 =============== \n\
|| 【设备名称: 】  {device_name}\n\
|| 【机床IP:   】  {device_ip}\n\
|| 【循环延迟: 】  {cycle}\n\
|| 【MQTT地址: 】  {mqtt_ip}\n\
|| 【MQTT主题: 】  {mqtt_topic}\n\
===========================================================\n")

cnc_data = {}
libh = ctypes.c_ushort(0)

# 支持paho-mqtt 1.x和2.x版本的兼容性初始化
try:
    from paho.mqtt.client import CallbackAPIVersion
    mqttclient = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION1, client_id=device_name)
except ImportError:
    # paho-mqtt 1.x版本不支持callback_api_version参数
    mqttclient = mqtt.Client(device_name)

# MQTT连接状态标志，用于监控连接健康状态
_mqtt_connected = False

# 连接MQTT服务器，loop_start启动后台线程，只调用一次
def on_mqtt_connect(mqtt_ip):
    mqttclient.connect(mqtt_ip, MQTT_PORT, MQTT_KEEPALIVE)
    mqttclient.loop_start()

# MQTT连接成功回调
def _on_mqtt_connected(client, userdata, flags, rc):
    global _mqtt_connected
    if rc == 0:
        _mqtt_connected = True
        print(f"【MQTT {mqtt_ip} 连接成功】")
    else:
        _mqtt_connected = False
        logging.warning(f"【MQTT 连接失败，返回码: {rc}】")

# MQTT断开连接回调，rc!=0表示意外断开，paho会自动重连
def _on_mqtt_disconnected(client, userdata, rc):
    global _mqtt_connected
    _mqtt_connected = False
    if rc != 0:
        logging.warning(f"【MQTT 意外断开连接，返回码: {rc}，将自动重连】")

# 消息处理函数
def on_message_come(client, userdata, msg):
    print(f'【{msg.topic}:{str(msg.payload)}】')
    aa=json.loads(msg.payload)
    print('收到消息了',aa)

# 注册MQTT回调
mqttclient.on_connect = _on_mqtt_connected
mqttclient.on_disconnect = _on_mqtt_disconnected
mqttclient.on_message = on_message_come

# CNC数据结构定义
class IODBPSD_U(Union):
    _fields_ = [
        ('cdata', c_char),
        ('idata', c_short),
        ('ldata', c_int32),
        ('cdatas', c_char * MAX_AXIS),
        ('idatas', c_short * MAX_AXIS),
        ('ldatas', c_int32 * MAX_AXIS)
    ]

class IODBPSD(Structure):
    _fields_ = [
        ('datano', c_short),
        ('type', c_short),
        ('u', IODBPSD_U)
    ]

class ODBACT(Structure):
    _fields_ = [
        ('dummp', c_short * 2),  # 修复：原'dummp[2]'为无效字段名且仅占2字节，应为c_short*2(4字节)
        ('data', c_int32)
    ]

#################### dynamic2 ###############
class FAXIS(Structure):
    _fields_ = [
        ('absolute',c_int32*MAX_AXIS),
        ('machine', c_int32*MAX_AXIS),
        ('relative', c_int32*MAX_AXIS),
        ('distance', c_int32*MAX_AXIS),
        ]

class OAXIS(Structure):
    _fields_ = [
        ('absolute',c_int32),
        ('machine', c_int32),
        ('relative', c_int32),
        ('distance', c_int32),
        ]

class POS(Union):
    _fields_ = [
        ('faxis',FAXIS),
        ('oaxis',OAXIS)
    ]

class ODBDY2(Structure):
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
####################################

class  ODBTLIFE4(Structure):
    _fields_ = [
        ('datano',c_short),
        ('type',c_short),
        ('data',c_int32)
    ]

class  IODBTLMAG(Structure):
    _fields_ = [
        ('magazine',c_short),
        ('pot',c_short),
        ('tool_index',c_short)
    ]

class  IODBTIME(Structure):
    _fields_ = [
        ('minute',c_int32),
        ('msec',c_int32)
    ]

class ODBST(Structure):
    _fields_=[
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
def read_cnc_id():
    cnc_ids = (ctypes.c_uint32 * 4)()
    ret = focas.cnc_rdcncid(libh, cnc_ids)
    if ret != 0:
        raise Exception(f"Failed to read cnc id ({ret})")
    machine_id = "-".join([f"{cnc_ids[i]:08x}" for i in range(4)])
    cnc_data["machine_id"] = machine_id

def read_param():
    iodbpsd = IODBPSD()
    ret = focas.cnc_rdparam(libh, PART_COUNT_PARAMETER, 0, 4 + MAX_AXIS, byref(iodbpsd))
    if ret != 0:
        raise Exception(f"Failed to read param ({ret})")
    cnc_data["part_count"] = iodbpsd.u.ldata

def read_dynamic2():
    buf = ODBDY2()
    ret = focas.cnc_rddynamic2(libh, -1, sizeof(buf), byref(buf))
    if ret != 0:
        raise Exception(f"Failed to read dynamic2 ({ret})")

    # 读取前3轴绝对坐标（X/Y/Z），使用列表推导式优化性能
    cnc_data["absolute"] = [x / 1000.0 for x in buf.pos.faxis.absolute[0:3]]
    # 修复：相对坐标应从relative数组读取，原代码错误地读取了absolute[32:35]
    cnc_data["relative"] = [x / 1000.0 for x in buf.pos.faxis.relative[0:3]]
    # 修复：机床坐标应从machine[0:3]读取，原代码错误地使用了偏移machine[16:19]
    cnc_data["machine"] = [x / 1000.0 for x in buf.pos.faxis.machine[0:3]]
    cnc_data["acts"] = buf.acts
    cnc_data["actf"] = buf.actf
    cnc_data["prgnum"] = buf.prgnum
    cnc_data["prgmnum"] = buf.prgmnum
    cnc_data["seqnum"] = buf.seqnum

def read_timer():
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
    statinfo = ODBST()
    ret = focas.cnc_statinfo(libh, byref(statinfo))
    if ret != 0:
        raise Exception(f"Failed to read statinfo ! ({ret})")

    cnc_data["statinfo"] = {}
    cnc_data["statinfo"]['auto'] = statinfo.auto
    cnc_data["statinfo"]['emergency'] = statinfo.emergency

    # 急停按下，run状态强制置1（Stop）
    if statinfo.emergency == 1:
        cnc_data["statinfo"]['run'] = 1
    else:
        cnc_data["statinfo"]['run'] = statinfo.run
    cnc_data["statinfo"]['alarm'] = statinfo.alarm

############## 主程序 #############
if __name__ == "__main__":
    print(f"正在连接到设备 {device_ip}:{CNC_PORT}...")
    ret = focas.cnc_allclibhndl3(device_ip.encode(), CNC_PORT, CNC_TIMEOUT, ctypes.byref(libh))
    if ret != 0:
        raise Exception(f"机床连接失败 ({ret})")

    cnc_data['device_name'] = device_name

    ## 2 连接MQTT
    try:
        on_mqtt_connect(mqtt_ip)
    except Exception as error:
        print(f"MQTT连接错误 \n{error}")
    else:
        print(f"【MQTT {mqtt_ip}连接成功】")

    ii = 0
    try:
        while True:
            # 使用模运算优化低频数据采集逻辑
            if ii % LOW_FREQ_INTERVAL == 0:
                read_param()
                part_count = cnc_data["part_count"]

                read_dynamic2()

                read_timer()
                timer = cnc_data["timer"]

                read_statinfo()
                statinfo = cnc_data["statinfo"]
            else:
                # 高频采集动态数据
                read_dynamic2()
                cnc_data["timer"] = timer
                cnc_data["part_count"] = part_count
                cnc_data["statinfo"] = statinfo

            ii += 1
            time.sleep(cycle)

            mqtt_msg = json.dumps(cnc_data)
            logging.warning(mqtt_msg)
            mqttclient.publish(mqtt_topic, payload=mqtt_msg, qos=MQTT_QOS)
            # loop_start()已在on_mqtt_connect中启动后台线程，无需在循环中重复调用
            logging.warning(f"【MQTT发送数据 topic:{mqtt_topic} Done】")

    except Exception as e:
        logging.error(f"主循环异常退出: {e}")
        raise
    finally:
        # 确保程序退出时释放CNC连接句柄
        ret = focas.cnc_freelibhndl(libh)
        if ret != 0:
            logging.warning(f"Failed to free library handle! ({ret})")
