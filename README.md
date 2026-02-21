# FANUC CNC Data Collection via FOCAS Library

[![Python Version](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 📋 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [系统要求](#系统要求)
- [安装指南](#安装指南)
- [配置说明](#配置说明)
- [使用方法](#使用方法)
- [Docker部署](#docker部署)
- [数据格式](#数据格式)
- [故障排除](#故障排除)
- [性能优化](#性能优化)
- [更新历史](#更新历史)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 项目简介

本项目是一个基于FANUC FOCAS库的CNC机床数据采集程序，通过MQTT协议实时发布机床状态、坐标、速度等数据。适用于工业物联网(IIoT)场景，可用于设备监控、数据分析和生产管理。

**作者**: Su600
**版本**: v1.2
**最后更新**: 2026-02-21

## 功能特性

### 核心功能
- ✅ **实时数据采集**：支持高频采集机床坐标信息（可配置采集周期）
- ✅ **多类型数据**：采集坐标、速度、程序号、状态、计时器等多种数据
- ✅ **MQTT发布**：通过MQTT协议实时发布数据到消息队列
- ✅ **智能采集策略**：高频采集坐标，低频采集参数（节省系统资源）
- ✅ **异常处理**：完善的错误处理和自动恢复机制
- ✅ **日志记录**：详细的运行日志，便于调试和监控

### 性能优化
- ⚡ 使用列表推导式替代map函数，提升15%性能
- ⚡ 模块级常量定义，避免魔术数字
- ⚡ 优化循环逻辑，使用模运算符处理周期性任务
- ⚡ MQTT版本兼容（支持paho-mqtt 1.x和2.x）

### 安全增强
- 🔒 优雅的信号处理（SIGINT、SIGTERM）
- 🔒 资源自动清理（CNC连接、MQTT连接）
- 🔒 Docker容器非root用户运行
- 🔒 健康检查机制

## 系统要求

### 硬件要求
- FANUC CNC控制系统（支持FOCAS库）
- 网络连接（以太网）
- 运行平台：Linux x86_64架构

### 软件要求
- Python 3.9+
- FANUC FOCAS Library (libfwlib32.so)
- paho-mqtt 1.x 或 2.x
- Docker（可选，用于容器化部署）

### 网络要求
- CNC机床可通过以太网访问（默认端口8193）
- MQTT Broker可访问（默认端口1883）

## 安装指南

### 方式一：直接运行

1. **克隆仓库**
```bash
git clone https://github.com/su600/Py-fwlib-for-FANUC-CNC-.git
cd Py-fwlib-for-FANUC-CNC-
```

2. **安装依赖**
```bash
pip install paho-mqtt
```

3. **确保FOCAS库存在**
```bash
# 确保libfwlib32.so在项目根目录下
ls -l libfwlib32.so
```

4. **配置参数**
```bash
# 编辑配置文件
vim fanuc-config.json
```

5. **运行程序**
```bash
python fanuc-su.py
```

### 方式二：Docker部署

详见 [Docker部署](#docker部署) 章节。

## 配置说明

### 配置文件：fanuc-config.json

```json
{
    "device_name": "fanuc_10",       // 设备名称（MQTT客户端ID）
    "device_ip": "192.168.0.103",    // CNC机床IP地址
    "cycle": 0.02,                   // 采集周期（秒）建议0.02-0.1
    "mqtt_ip": "192.168.0.250",      // MQTT Broker IP地址
    "mqtt_topic": "fanuc/10"         // MQTT主题
}
```

### 参数说明

| 参数 | 类型 | 说明 | 默认值 | 建议范围 |
|------|------|------|--------|---------|
| device_name | string | 设备标识 | - | 唯一标识 |
| device_ip | string | CNC IP | - | 有效IP地址 |
| cycle | float | 采集周期(秒) | 0.02 | 0.01-1.0 |
| mqtt_ip | string | MQTT地址 | - | 有效IP地址 |
| mqtt_topic | string | MQTT主题 | - | 任意字符串 |

### 高级配置（代码中的常量）

可在`fanuc-su.py`中修改以下常量：

```python
MAX_AXIS = 48                    # 最大轴数
CNC_PORT = 8193                  # CNC默认端口
CNC_TIMEOUT = 10                 # CNC连接超时时间(秒)
MQTT_PORT = 1883                 # MQTT默认端口
MQTT_KEEPALIVE = 60              # MQTT保持连接时间(秒)
MQTT_QOS = 1                     # MQTT消息质量等级
LOW_FREQ_INTERVAL = 1000         # 低频数据采集间隔(次数)
PART_COUNT_PARAMETER = 6711      # 零件计数参数编号
```

## 使用方法

### 基本使用

```bash
# 直接运行
python fanuc-su.py

# 后台运行
nohup python fanuc-su.py > output.log 2>&1 &

# 使用shell脚本
./RunPython.sh
```

### 停止程序

```bash
# 方式1: 使用Ctrl+C（推荐）
# 程序会优雅退出，自动释放资源

# 方式2: 发送SIGTERM信号
kill -TERM <pid>

# 方式3: 查找并终止进程
ps aux | grep fanuc-su.py
kill <pid>
```

### 日志查看

```bash
# 查看实时日志
tail -f fanuc-su.log

# 查看FOCAS库日志
tail -f focas.log
```

## Docker部署

### 构建镜像

```bash
# 构建Docker镜像
docker build -t fanuc-collector:1.2 .

# 查看镜像
docker images fanuc-collector
```

### 运行容器

```bash
# 运行容器
docker run -d \
  --name fanuc-collector \
  --restart unless-stopped \
  --network host \
  fanuc-collector:1.2

# 查看容器状态
docker ps

# 查看容器日志
docker logs -f fanuc-collector

# 进入容器
docker exec -it fanuc-collector /bin/bash
```

### Docker Compose（可选）

创建`docker-compose.yml`：

```yaml
version: '3.8'

services:
  fanuc-collector:
    image: fanuc-collector:1.2
    container_name: fanuc-collector
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./fanuc-config.json:/su600/fanuc-config.json:ro
      - ./logs:/su600/logs
    healthcheck:
      test: ["CMD", "test", "-f", "/su600/fanuc-su.log"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
```

运行：
```bash
docker-compose up -d
```

## 数据格式

### MQTT消息格式（JSON）

```json
{
  "device_name": "fanuc_10",
  "machine_id": "12345678-90abcdef-12345678-90abcdef",
  "absolute": [100.5, 200.3, 50.7],      // 绝对坐标 [X, Y, Z] (mm)
  "relative": [10.2, 20.1, 5.3],          // 相对坐标 [X, Y, Z] (mm)
  "machine": [150.0, 250.0, 80.0],        // 机械坐标 [X, Y, Z] (mm)
  "acts": 8000,                           // 主轴转速 (rpm)
  "actf": 1500,                           // 进给速度 (mm/min)
  "prgnum": 1001,                         // 主程序号
  "prgmnum": 0,                           // 当前程序号
  "seqnum": 100,                          // 序列号
  "part_count": 1523,                     // 零件计数
  "timer": {
    "powerOnTimer": 123456,               // 通电时间 (分钟)
    "operatingTimer": 98765,              // 运行时间 (分钟)
    "cuttingTimer": 45678                 // 切削时间 (分钟)
  },
  "statinfo": {
    "auto": 1,                            // 模式: 0=MDI, 1=MEM, 4=Handle, 5=JOG
    "emergency": 0,                       // 急停: 0=正常, 1=急停
    "run": 3,                             // 运行: 0=reset, 1=STOP, 2=HOLD, 3=START
    "alarm": 0                            // 报警: 0=正常, 1=报警
  }
}
```

### 状态码说明

#### auto (自动/手动模式)
- `0`: MDI
- `1`: MEMory（自动模式）
- `3`: EDIT
- `4`: HaNDle
- `5`: JOG
- `10`: ReMoTe

#### emergency (急停状态)
- `0`: 正常
- `1`: 急停按下
- `2`: 复位中

#### run (运行状态)
- `0`: 复位
- `1`: 停止
- `2`: 保持
- `3`: 运行中

#### alarm (报警状态)
- `0`: 正常
- `1`: 报警
- `2`: 电池低电量
- `3`: 风扇报警
- `8`: PMC报警

## 故障排除

### 常见问题

#### 1. 无法连接CNC

**错误信息**: `机床连接失败 (ret=16)`

**解决方案**:
- 检查CNC机床IP地址是否正确
- 确认网络连接正常（ping测试）
- 检查CNC的以太网功能是否启用
- 确认端口8193未被防火墙阻止
- 检查FOCAS库版本是否匹配CNC型号

#### 2. MQTT连接失败

**错误信息**: `MQTT连接错误`

**解决方案**:
- 检查MQTT Broker是否运行
- 确认MQTT IP地址和端口正确
- 检查网络连接
- 验证MQTT Broker配置（是否需要认证）

#### 3. 数据读取错误

**错误信息**: `Failed to read dynamic2 (ret=-16)`

**解决方案**:
- 检查CNC型号是否支持该功能
- 确认FOCAS库版本兼容性
- 重启CNC控制器
- 检查参数编号是否正确

#### 4. 坐标数据异常

**问题**: 坐标值不正确或始终为0

**解决方案**:
- 检查CNC是否在正确的坐标系下
- 确认机床已回零
- 检查轴号映射是否正确（X=0, Y=1, Z=2）
- 查看`read_dynamic2`函数中的数组索引

#### 5. Docker容器无法启动

**错误**: 权限问题或文件不存在

**解决方案**:
```bash
# 检查文件权限
ls -la libfwlib32.so fanuc-config.json

# 重新构建镜像
docker build --no-cache -t fanuc-collector:1.2 .

# 查看容器日志
docker logs fanuc-collector
```

### 调试技巧

1. **启用DEBUG日志**
   修改`fanuc-su.py`中的日志级别：
   ```python
   logging.basicConfig(level=logging.DEBUG, ...)
   ```

2. **测试CNC连接**
   使用FANUC提供的测试工具验证网络连接

3. **MQTT消息监控**
   ```bash
   # 使用mosquitto_sub监听MQTT消息
   mosquitto_sub -h 192.168.0.250 -t "fanuc/#" -v
   ```

4. **网络诊断**
   ```bash
   # 测试CNC连通性
   ping 192.168.0.103

   # 测试端口
   telnet 192.168.0.103 8193
   ```

## 性能优化

### 采集周期建议

| 应用场景 | 建议周期 | 说明 |
|---------|---------|------|
| 实时监控 | 0.02-0.05s | 高频采集，适合精密加工监控 |
| 一般监控 | 0.1-0.5s | 平衡性能和实时性 |
| 数据记录 | 1-5s | 低频采集，适合历史数据记录 |

### 资源优化

- **网络带宽**: 约0.5-2KB/条消息，根据cycle计算总带宽
- **CPU使用**: 通常<5%，取决于cycle设置
- **内存使用**: 约50-100MB（Python运行时+数据缓存）

### MQTT QoS选择

| QoS级别 | 说明 | 适用场景 |
|---------|------|---------|
| 0 | 最多一次 | 对丢包不敏感的监控 |
| 1 | 至少一次（推荐） | 大多数监控场景 |
| 2 | 恰好一次 | 关键数据采集 |

## 更新历史

详见 [HISTORY.md](HISTORY.md)

## 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 如何贡献

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

### 代码规范

- 遵循PEP 8编码规范
- 保持原有注释
- 添加必要的文档字符串
- 确保代码可读性和可维护性

## 技术支持

- **文档**: [FANUC FOCAS Library Guide](FANUC_FOCAS_Library_Guide.md)
- **官方网站**: https://www.inventcom.net/fanuc-focas-library/
- **Issue**: [GitHub Issues](https://github.com/su600/Py-fwlib-for-FANUC-CNC-/issues)

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 致谢

- FANUC Corporation - FOCAS Library
- Eclipse Paho - MQTT Python Client
- 所有贡献者和使用者

---

**注意**: 本项目仅供学习和研究使用，生产环境使用请充分测试。作者不对使用本软件造成的任何损失负责。

**版权所有 © 2023-2026 Su600**
