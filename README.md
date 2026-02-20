# Py-fwlib for FANUC CNC

基于 FANUC FOCAS 库（fwlib32.so）的 Python CNC 数据采集工具，通过以太网连接 FANUC 数控系统，实时采集机床状态并通过 MQTT 发布。

> 作者：Su600  
> 参考文档：[FANUC FOCAS Library Guide](./FANUC_FOCAS_Library_Guide.md)  
> 数据源：https://www.inventcom.net/fanuc-focas-library/

---

## 功能特性

- **高频坐标采集**：每个循环（默认 20ms）读取绝对坐标、相对坐标、机床坐标、进给速度、主轴转速、程序号等动态数据
- **低频状态采集**：每 1000 次循环（约 1 分钟）读取零件计数、各类计时器、机床状态等参数
- **MQTT 实时发布**：采集数据序列化为 JSON 并发布到指定 MQTT 主题
- **MQTT 自动重连**：通过 paho-mqtt 内建机制在断线后自动恢复连接
- **Docker 容器部署**：提供 Dockerfile，可快速容器化部署

---

## 采集数据字段说明

| 字段 | 说明 | 单位 |
|------|------|------|
| `device_name` | 设备名称（来自配置） | - |
| `absolute` | 前 3 轴绝对坐标 [X, Y, Z] | mm |
| `relative` | 前 3 轴相对坐标 [X, Y, Z] | mm |
| `machine` | 前 3 轴机床坐标 [X, Y, Z] | mm |
| `actf` | 实际进给速度（F 值） | mm/min |
| `acts` | 实际主轴转速（S 值） | rpm |
| `prgnum` | 当前程序号 | - |
| `prgmnum` | 主程序号 | - |
| `seqnum` | 当前序列号 | - |
| `part_count` | 零件计数（参数 6711） | 件 |
| `timer.powerOnTimer` | 通电时间 | 分钟 |
| `timer.operatingTimer` | 运行时间 | 分钟 |
| `timer.cuttingTimer` | 切削时间 | 分钟 |
| `statinfo.auto` | 自动/手动模式 | - |
| `statinfo.run` | 自动运行状态 | - |
| `statinfo.emergency` | 急停状态 | - |
| `statinfo.alarm` | 报警状态 | - |

---

## 环境要求

- Python 3.9+
- Linux x86（需匹配 `libfwlib32.so` 的目标架构）
- FANUC 数控系统支持 FOCAS2 以太网连接（端口 8193）
- MQTT Broker（如 Mosquitto）

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/su600/Py-fwlib-for-FANUC-CNC-.git
cd Py-fwlib-for-FANUC-CNC-
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 修改配置文件

编辑 `fanuc-config.json`：

```json
{
    "device_name": "fanuc_10",
    "device_ip": "192.168.0.103",
    "cycle": 0.02,
    "mqtt_ip": "192.168.0.250",
    "mqtt_topic": "fanuc/10"
}
```

| 参数 | 说明 |
|------|------|
| `device_name` | 设备唯一名称，同时作为 MQTT 客户端 ID |
| `device_ip` | FANUC 机床 IP 地址 |
| `cycle` | 高频采集间隔（秒），默认 0.02（50Hz） |
| `mqtt_ip` | MQTT Broker IP 地址 |
| `mqtt_topic` | 数据发布的 MQTT 主题 |

### 4. 运行

```bash
python fanuc-su.py
```

或使用启动脚本：

```bash
chmod +x RunPython.sh
./RunPython.sh
```

---

## Docker 部署

### 构建镜像

```bash
docker build -t fanuc-collector .
```

### 运行容器

```bash
docker run -d --name fanuc-collector fanuc-collector
```

### 查看日志

```bash
docker logs -f fanuc-collector
```

---

## 文件结构

```
.
├── fanuc-su.py              # 主程序
├── fanuc-config.json        # 配置文件
├── libfwlib32.so            # FANUC FOCAS2 共享库（Linux x86）
├── FANUC_FOCAS_Library_Guide.md  # FOCAS 函数参考文档
├── requirements.txt         # Python 依赖
├── Dockerfile               # Docker 镜像构建文件
├── RunPython.sh             # 启动脚本
└── README.md                # 本文档
```

---

## 变更历史

### v1.2（2026-02-20）

- **修复**：`read_dynamic2()` 中相对坐标错误读取 `absolute[32:35]`，修正为 `relative[0:3]`
- **修复**：`read_dynamic2()` 中机床坐标错误偏移 `machine[16:19]`，修正为 `machine[0:3]`
- **修复**：`ODBACT` 结构体字段 `'dummp[2]'` 无效且尺寸错误，修正为 `('dummp', c_short * 2)`
- **修复**：`cnc_startupprocess` 第二参数字符串未编码，改为 `b"focas.log"`（Python 3 bytes 要求）
- **修复**：`cnc_freelibhndl` 位于 `while 1:` 之后为不可达代码，改为 `try/finally` 确保资源释放
- **修复**：主循环中重复调用 `mqttclient.loop_start()` 导致多余后台线程，移至 `on_mqtt_connect` 中仅调用一次
- **改进**：库文件与配置文件路径改用脚本所在目录（`__file__`），避免工作目录不同时加载失败
- **改进**：注册 MQTT `on_connect`、`on_disconnect`、`on_message` 回调，监控连接状态，意外断开时自动重连
- **改进**：主循环加 `try/except/finally`，未捕获异常记录日志并保证句柄释放
- **新增**：`requirements.txt` 依赖文件
- **新增**：`README.md` 使用文档
- **更新**：`Dockerfile` 升级基础镜像至 `python:3.11-slim-bookworm`，改用 `requirements.txt` 安装依赖

### v1.1（2023-01-10）

- 只高频采集 `cnc_rddynamic2` 坐标信息，其它参数每 1000 次（约 1 分钟）采集一次
- 恢复配置文件中的 `cycle` 参数
