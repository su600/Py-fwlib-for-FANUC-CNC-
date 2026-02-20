# FANUC FOCAS Library 核心机床参数函数完整指南

**文档版本**: 1.0  
**生成日期**: 2026-02-20  
**数据来源**: https://www.inventcom.net/fanuc-focas-library/

---

## 目录

1. [函数概览](#函数概览)
2. [详细函数文档](#详细函数文档)
   - [1. cnc_absolute - 读绝对坐标](#1-cnc_absolute---读绝对坐标)
   - [2. cnc_machine - 读机械坐标](#2-cnc_machine---读机械坐标)
   - [3. cnc_rdposition - 读位置信息](#3-cnc_rdposition---读位置信息)
   - [4. cnc_actf - 读进给速度](#4-cnc_actf---读进给速度)
   - [5. cnc_acts - 读主轴速度](#5-cnc_acts---读主轴速度)
   - [6. cnc_rdspeed - 读速度信息](#6-cnc_rdspeed---读速度信息)
   - [7. cnc_rdaxisdata - 读轴数据](#7-cnc_rdaxisdata---读轴数据)
   - [8. cnc_rddynamic - 读动态数据](#8-cnc_rddynamic---读动态数据)
   - [9. cnc_rdparam - 读参数](#9-cnc_rdparam---读参数)
   - [10. cnc_rdset - 读设置数据](#10-cnc_rdset---读设置数据)
3. [通用结构体定义](#通用结构体定义)
4. [Python ctypes 调用示例](#python-ctypes-调用示例)
5. [常见错误代码](#常见错误代码)
6. [使用流程指南](#使用流程指南)

---

## 函数概览

| 优先级 | 函数名 | 说明 | 可用模式 |
|------|--------|------|--------|
| 1 | `cnc_absolute` | 读绝对坐标 | 所有模式 |
| 2 | `cnc_machine` | 读机械坐标 | 所有模式 |
| 3 | `cnc_rdposition` | 读位置信息（综合） | 特定模式 |
| 4 | `cnc_actf` | 读进给速度 | 所有模式 |
| 5 | `cnc_acts` | 读主轴速度 | 所有模式 |
| 6 | `cnc_rdspeed` | 读速度信息（综合） | 特定模式 |
| 7 | `cnc_rdaxisdata` | 读轴数据（扩展） | 部分模式 |
| 8 | `cnc_rddynamic` | 读动态数据（综合） | 所有模式 |
| 9 | `cnc_rdparam` | 读参数 | 所有模式 |
| 10 | `cnc_rdset` | 读设置数据 | 所有模式 |

---

## 详细函数文档

### 1. cnc_absolute - 读绝对坐标

#### 功能描述
读取CNC指定轴的绝对位置数据。可以一次读取所有轴的绝对位置，也可以读取单个轴。

**重要说明**：
- 不同CNC系列对绝对位置的包含内容不同
- Series 30i/31i/32i: 包含刀长补偿和刀具半径补偿，不包含伺服延迟和加减速延迟
- Series 16/18/21: 包含所有补偿

#### 函数原型

```c
#include "fwlib32.h" or "fwlib64.h"

FWLIBAPI short WINAPI cnc_absolute(
    unsigned short FlibHndl,    // [in]  库句柄
    short axis,                  // [in]  轴号，-1表示所有轴
    short length,                // [in]  数据块长度
    ODBAXIS *absolute            // [out] 绝对位置数据结构体指针
);
```

#### 参数说明

| 参数名 | 类型 | 说明 | 备注 |
|-------|------|------|------|
| FlibHndl | unsigned short | 库句柄 | 见库句柄说明 |
| axis | short | 轴号 | -1(ALL_AXES)=所有轴; 1..m=各轴 |
| length | short | 数据块长度 | 单轴时: 4+4*1; 多轴时: 4+4*MAX_AXIS |
| absolute | ODBAXIS* | 输出指针 | 存储绝对位置数据 |

#### 返回值

| 返回值 | 含义 | 处理方法 |
|-------|------|--------|
| EW_OK (0) | 成功 | 数据有效 |
| EW_LENGTH (2) | 数据块长度错误 | 检查length参数 |
| EW_ATTRIB (4) | 轴号不合法 | 检查axis参数范围 |

#### 结构体定义

```c
typedef struct odbaxis {
    short dummy;           // 未使用
    short type;            // 轴号
    long data[MAX_AXIS];   // 绝对位置数据，MAX_AXIS=最大控制轴数
} ODBAXIS;
```

**data数组说明**：
- 存储各轴的绝对位置值
- 与小数点位置结合使用（由 cnc_getfigure 获取）
- 单位：与CNC设置相关（mm/inch等）

#### 使用条件和注意事项

**CNC参数要求**：
- Series 15: 2204#1=1, 7613#0=1 (必须设置)
- Series 30i/0i-D/F: 3104#6,#7 (会影响读取)

**支持CNC类型**：
- ✓ 加工中心(M): 15, 15i, 16, 18, 21, 16i系, 18i系, 21i系, 30i系, 0i-A/D/F
- ✓ 车床(T): 15i, 16i系, 18i系, 21i系, 30i系, 0i-A/D/F

**连接方式要求**：
- HSSB: 需要扩展驱动/库函数
- Ethernet: 需要以太网和扩展驱动/库函数

#### C语言示例

```c
#include "fwlib32.h"

void example_cnc_absolute(unsigned short h)
{
    ODBAXIS buf;
    short ret = cnc_absolute(h, -1, 4 + 4 * MAX_AXIS, &buf);
    
    if (ret == EW_OK) {
        // buf.data[0] = 第1轴绝对位置
        // buf.data[1] = 第2轴绝对位置
        // buf.data[2] = 第3轴绝对位置
        printf("Axis 1 absolute: %ld\n", buf.data[0]);
        printf("Axis 2 absolute: %ld\n", buf.data[1]);
        printf("Axis 3 absolute: %ld\n", buf.data[2]);
    }
}
```

---

### 2. cnc_machine - 读机械坐标

#### 功能描述
读取CNC指定轴的机械位置数据。机械位置不包含补偿值，是机械坐标系的真实位置。

**重要说明**：
- Series 30i/0i-D/F: 不包含伺服延迟和加减速延迟
- Series 16/18/21: 包含伺服延迟和加减速延迟

#### 函数原型

```c
#include "fwlib32.h" or "fwlib64.h"

FWLIBAPI short WINAPI cnc_machine(
    unsigned short FlibHndl,    // [in]  库句柄
    short axis,                  // [in]  轴号，-1表示所有轴
    short length,                // [in]  数据块长度
    ODBAXIS *machine             // [out] 机械位置数据结构体指针
);
```

#### 参数说明

| 参数名 | 类型 | 说明 | 备注 |
|-------|------|------|------|
| FlibHndl | unsigned short | 库句柄 | 见库句柄说明 |
| axis | short | 轴号 | -1(ALL_AXES)=所有轴; 1..m=各轴 |
| length | short | 数据块长度 | 单轴时: 4+4*1; 多轴时: 4+4*MAX_AXIS |
| machine | ODBAXIS* | 输出指针 | 存储机械位置数据 |

#### 返回值

| 返回值 | 含义 | 处理方法 |
|-------|------|--------|
| EW_OK (0) | 成功 | 数据有效 |
| EW_LENGTH (2) | 数据块长度错误 | 检查length参数 |
| EW_ATTRIB (4) | 轴号不合法 | 检查axis参数范围 |

#### 结构体定义

```c
typedef struct odbaxis {
    short dummy;           // 未使用
    short type;            // 轴号
    long data[MAX_AXIS];   // 机械位置数据
} ODBAXIS;
```

#### 使用条件和注意事项

**CNC参数要求**：
- Series 15: 2204#1=1, 7613#0=1 (必须)
- Series 16/18/21: 3104#0 (会影响)
- Series 30i: 3104#0 (会影响)

**支持CNC类型**：与 `cnc_absolute` 相同

#### C语言示例

```c
#include "fwlib32.h"

void example_cnc_machine(unsigned short h)
{
    ODBAXIS buf;
    // 读第2轴的机械位置
    short ret = cnc_machine(h, 2, 4 + 4 * 1, &buf);
    
    if (ret == EW_OK) {
        printf("Machine position axis 2: %ld\n", buf.data[0]);
    }
}
```

---

### 3. cnc_rdposition - 读位置信息

#### 功能描述
同时读取从第1轴到指定轴号的位置信息（绝对、机械、相对、距离值）。返回的轴数可以调整。

#### 函数原型

```c
#include "fwlib32.h" or "fwlib64.h"

FWLIBAPI short WINAPI cnc_rdposition(
    unsigned short FlibHndl,    // [in]    库句柄
    short type,                  // [in]    位置数据类型
    short *data_num,             // [in/out] 轴数指针
    ODBPOS *position             // [out]   位置数据结构体指针
);
```

#### 参数说明

| 参数名 | 类型 | 说明 | 备注 |
|-------|------|------|------|
| FlibHndl | unsigned short | 库句柄 | - |
| type | short | 数据类型 | 0=绝对; 1=机械; 2=相对; 3=距离; -1=全部 |
| data_num | short* | 轴数指针 | 输入请求轴数，输出实际轴数 |
| position | ODBPOS* | 位置数据 | 数组大小=data_num |

#### 返回值

| 返回值 | 含义 |
|-------|------|
| EW_OK (0) | 成功 |
| EW_LENGTH (2) | 轴数≤0 |
| EW_ATTRIB (4) | type参数错误 |

#### 结构体定义

```c
typedef struct odbpos {
    POSELM abs;    // 绝对位置
    POSELM mach;   // 机械位置
    POSELM rel;    // 相对位置
    POSELM dist;   // 距离值
} ODBPOS;

typedef struct poselm {
    long data;     // 位置数据
    short dec;     // 小数点位置
    short unit;    // 单位 (0=mm, 1=inch, 2=degree)
    short disp;    // 显示状态 (0=未显示, 1=显示)
    char name;     // 轴号名(ASCII)
    char suff;     // 轴号后缀(ASCII)
} POSELM;
```

#### 使用条件和注意事项

- 此函数不受CNC参数影响
- 自动调整返回轴数（如果请求轴数超过实际轴数）
- 支持所有CNC模式

#### C语言示例

```c
#include "fwlib32.h"

void example_cnc_rdposition(unsigned short h)
{
    ODBPOS pos[MAX_AXIS];
    short num = MAX_AXIS;
    
    short ret = cnc_rdposition(h, 0, &num, pos);  // 读绝对位置
    
    if (ret == EW_OK) {
        for (int i = 0; i < num; i++) {
            printf("%c = %d (dec=%d)\n", 
                   pos[i].abs.name, 
                   pos[i].abs.data, 
                   pos[i].abs.dec);
        }
    }
}
```

---

### 4. cnc_actf - 读进给速度

#### 功能描述
读取CNC当前的实际进给速度(F值)。这是当前加工时的实际进给速率，反映实时进给状态。

#### 函数原型

```c
#include "fwlib32.h" or "fwlib64.h"

FWLIBAPI short WINAPI cnc_actf(
    unsigned short FlibHndl,    // [in]  库句柄
    ODBACT *actualfeed          // [out] 实际进给速度结构体指针
);
```

#### 参数说明

| 参数名 | 类型 | 说明 |
|-------|------|------|
| FlibHndl | unsigned short | 库句柄 |
| actualfeed | ODBACT* | 输出进给速度数据 |

#### 返回值

| 返回值 | 含义 | 处理方法 |
|-------|------|--------|
| EW_OK (0) | 成功 | 数据有效 |
| EW_PARAM (9) | CNC参数错误(Series 15) | 检查参数7613设置 |

#### 结构体定义

```c
typedef struct odbact {
    short dummy[2];   // 未使用
    long data;        // 实际进给速度(F值)
} ODBACT;
```

**data说明**：
- 单位为 mm/min 或 inch/min（由CNC参数决定）
- 包含实时进给修调系数

#### 使用条件和注意事项

**CNC参数要求**：
- Series 15: 7613#0=1, 7613#1=1 (必须)
- Series 16/18/21: 3107#3, 3191#0, 3191#5

**支持所有CNC模式**

#### C语言示例

```c
#include "fwlib32.h"

void example_cnc_actf(unsigned short h)
{
    ODBACT buf;
    short ret = cnc_actf(h, &buf);
    
    if (ret == EW_OK) {
        printf("Current feed rate: %ld\n", buf.data);  // 例如: 1200 = 1200mm/min
    }
}
```

---

### 5. cnc_acts - 读主轴速度

#### 功能描述
读取CNC主轴的实际转速(S值)。反映主轴当前的实时旋转速度。

#### 函数原型

```c
#include "fwlib32.h" or "fwlib64.h"

FWLIBAPI short WINAPI cnc_acts(
    unsigned short FlibHndl,    // [in]  库句柄
    ODBACT *actualfeed          // [out] 实际主轴速度结构体指针
);
```

#### 参数说明

| 参数名 | 类型 | 说明 |
|-------|------|------|
| FlibHndl | unsigned short | 库句柄 |
| actualfeed | ODBACT* | 输出主轴速度数据(注：参数名为历史遗留) |

#### 返回值

| 返回值 | 含义 |
|-------|------|
| EW_OK (0) | 成功 |
| EW_PARAM (9) | CNC参数错误 |

#### 结构体定义

```c
typedef struct odbact {
    short dummy[2];   // 未使用
    long data;        // 实际主轴速度(S值) [rpm]
} ODBACT;
```

**data说明**：
- 单位为 rpm (转/分)
- 包含主轴速度修调系数

#### 使用条件和注意事项

**CNC参数要求**：
- Series 15: 7613#0=1, 7613#2=1 (必须)
- Series 16/18/21: 3118#0,#1,#2,#3, 4001#2
- Series 30i: 3799#2, 4001#2

**不支持的CNC**：
- Loader (LC) 模式不支持
- Power Mate i-H 不支持

#### C语言示例

```c
#include "fwlib32.h"

void example_cnc_acts(unsigned short h)
{
    ODBACT buf;
    short ret = cnc_acts(h, &buf);
    
    if (ret == EW_OK) {
        printf("Current spindle speed: %ld rpm\n", buf.data);  // 例如: 2470
    }
}
```

---

### 6. cnc_rdspeed - 读速度信息

#### 功能描述
同时读取进给速度和主轴速度。包含完整的单位和小数点信息，可用于显示和数据记录。

#### 函数原型

```c
#include "fwlib32.h" or "fwlib64.h"

FWLIBAPI short WINAPI cnc_rdspeed(
    unsigned short FlibHndl,    // [in]  库句柄
    short type,                  // [in]  数据类型
    ODBSPEED *speed              // [out] 速度数据结构体指针
);
```

#### 参数说明

| 参数名 | 类型 | 说明 | 备注 |
|-------|------|------|------|
| FlibHndl | unsigned short | 库句柄 | - |
| type | short | 数据类型 | 0=进给速度; 1=主轴速度; -1=全部 |
| speed | ODBSPEED* | 速度数据 | 包含进给和主轴信息 |

#### 返回值

| 返回值 | 含义 |
|-------|------|
| EW_OK (0) | 成功 |
| EW_ATTRIB (4) | type参数错误 |

#### 结构体定义

```c
typedef struct odbspeed {
    SPEEDELM actf;    // 进给速度
    SPEEDELM acts;    // 主轴速度
} ODBSPEED;

typedef struct speedelm {
    long data;        // 速度数据
    short dec;        // 小数点位置
    short unit;       // 单位
    short reserve;    // 保留
    char name;        // 名称 ('F' 或 'S')
    char suff;        // 后缀
} SPEEDELM;
```

**unit说明**：
- 0 = mm/min (进给)
- 1 = inch/min (进给)
- 2 = rpm (主轴)
- 3 = mm/rev (进给)
- 4 = inch/rev (进给)

#### 使用条件和注意事项

- 不受CNC参数影响
- 支持多主轴控制
- 适合显示和数据采集

#### C语言示例

```c
#include "fwlib32.h"

void example_cnc_rdspeed(unsigned short h)
{
    ODBSPEED speed;
    short ret = cnc_rdspeed(h, -1, &speed);
    
    if (ret == EW_OK) {
        printf("Feed rate: %c = %d (unit=%d)\n", 
               speed.actf.name, speed.actf.data, speed.actf.unit);
        printf("Spindle speed: %c = %d (unit=%d)\n", 
               speed.acts.name, speed.acts.data, speed.acts.unit);
    }
}
```

---

### 7. cnc_rdaxisdata - 读轴数据

#### 功能描述
读取各种与伺服轴/主轴相关的数据，支持扩展轴名称。可在一次调用中读取多种数据类型（最多4种）。

**功能特点**：
- 支持位置、伺服、主轴等多种数据类型
- 可同时读取多个轴的多种数据
- 返回完整的轴信息和标志位

#### 函数原型

```c
#include "fwlib32.h" or "fwlib64.h"

FWLIBAPI short WINAPI cnc_rdaxisdata(
    unsigned short FlibHndl,    // [in]    库句柄
    short cls,                   // [in]    数据分类
    short* type,                 // [in]    数据类型数组
    short num,                   // [in]    数据类型个数
    short* len,                  // [in/out] 轴数指针
    ODBAXDT* axdata              // [out]   轴数据数组
);
```

#### 参数说明

| 参数名 | 类型 | 说明 | 备注 |
|-------|------|------|------|
| FlibHndl | unsigned short | 库句柄 | - |
| cls | short | 数据分类 | 1=位置; 2=伺服; 3=主轴; 4=选中主轴; 5=速度 |
| type | short* | 类型数组 | 根据cls取不同值 |
| num | short | 类型个数 | 最多4个，超过4返回EW_ATTRIB |
| len | short* | 轴数指针 | 输入请求数，输出实际数 |
| axdata | ODBAXDT* | 数据数组 | 大小: num × (*len) |

#### 数据类型说明

**位置数据 (cls=1)**：
- 0: 绝对位置
- 1: 机械位置
- 2: 相对位置
- 3: 距离值
- 4/5: 手轮中断
- 6/7: 程序重启起点
- 8/9: 块重启起点
- 10/11: 偏移图形屏幕位置

**伺服数据 (cls=2)**：
- 0: 伺服负载计
- 1: 负载电流(%)
- 2: 负载电流(A)

**主轴数据 (cls=3/4)**：
- 0: 主轴负载计
- 1: 主轴电机速度
- 2/3: 主轴速度
- 4/5/6: 负载计特殊值
- 7: 持续处理时间

**速度数据 (cls=5)**：
- 0: 进给速度(F)
- 1: 主轴速度(S)
- 2: 点动/空运行速度
- 3: 刀尖速度
- 4: 伺服电机转速
- 5: 进给速度(F/S)

#### 返回值

| 返回值 | 含义 |
|-------|------|
| EW_OK (0) | 成功 |
| EW_LENGTH (2) | 轴数≤0 |
| EW_NUMBER (3) | cls参数错误 |
| EW_ATTRIB (4) | type参数错误或num>4 |
| EW_NOOPT (6) | 需要的选项未配置 |

#### 结构体定义

```c
typedef struct odbaxdt {
    char name[4];      // 轴名(ASCII)，NULL结尾
    long data;         // 数据值
    short dec;         // 小数点位置
    short unit;        // 单位
    short flag;        // 标志位
    short reserve;     // 保留
} ODBAXDT;

// unit取值：
// 0=mm, 1=inch, 2=degree (位置数据)
// 3=mm/min, 4=inch/min (进给速度)
// 5=rpm (主轴速度)
// 6=mm/rev, 7=inch/rev (每转进给)
// 8=%  (负载), 9=Ampere (电流)
// 10=Second (时间)
```

**flag标志位 (cls=1 位置数据)**：
- bit0: 显示状态(1=显示, 0=不显示)
- bit1: 轴脱离(1=启用, 0=禁用)
- bit2: 联动(1=启用, 0=禁用)
- bit3: 机械锁(1=启用, 0=禁用)
- bit4: 伺服断电(1=启用, 0=禁用)
- bit5: 到位检查(1=未到位, 0=到位)
- bit6: 镜像(1=启用, 0=禁用)
- bit7: 直径/半径切换(1=切换, 0=未切换)
- bit8-11: 其他高级功能标志

#### 使用条件和注意事项

**支持的CNC**：
- 0i-D/F: 支持(O)
- 30i系列: 支持(O)
- Power Motion i-A: 支持(O)
- 不支持: 0i-A, 15, 16, 18, 21等旧系列

**CNC参数**：
- 1020, 1025, 1026 (会影响)
- 3104#0,#4,#5,#6,#7 (影响位置数据)
- 3799#2 (影响主轴速度)
- 8163#0 (影响相对和绝对位置)

#### C语言示例

```c
#include "fwlib32.h"

void example_cnc_rdaxisdata(unsigned short h)
{
    ODBAXDT pos[4 * MAX_AXIS];  // 最多4种类型，MAX_AXIS轴
    short types[4] = {0, 1, 2, 3};  // 绝对、机械、相对、距离
    short num = 4;
    short len = MAX_AXIS;
    
    short ret = cnc_rdaxisdata(h, 1, types, num, &len, pos);
    
    if (ret == EW_OK) {
        printf("ABSOLUTE POSITIONS:\n");
        for (int i = 0; i < len; i++) {
            printf("%s = %d\n", pos[i].name, pos[i].data);
        }
        printf("MACHINE POSITIONS:\n");
        for (int i = len; i < 2*len; i++) {
            printf("%s = %d\n", pos[i].name, pos[i].data);
        }
    }
}
```

---

### 8. cnc_rddynamic - 读动态数据

#### 功能描述
一次读取CNC运行时变化的多种数据：报警状态、运行程序号、序列号、进给速度、主轴速度、各轴位置信息等。极大提高了数据采集效率。

#### 函数原型

```c
#include "fwlib32.h" or "fwlib64.h"

FWLIBAPI short WINAPI cnc_rddynamic(
    unsigned short FlibHndl,    // [in]  库句柄
    short axis,                  // [in]  轴号，-1表示所有轴
    short length,                // [in]  数据块长度
    ODBDY *rddynamic             // [out] 动态数据结构体指针
);
```

#### 参数说明

| 参数名 | 类型 | 说明 | 备注 |
|-------|------|------|------|
| FlibHndl | unsigned short | 库句柄 | - |
| axis | short | 轴号 | -1(ALL_AXES)=所有轴; 1..m=单轴 |
| length | short | 数据块长度 | 见下表 |
| rddynamic | ODBDY* | 输出指针 | 见结构体说明 |

**length计算**：
- 单轴: 26 + 16*1 = 42 bytes
- 多轴: 26 + 16*MAX_AXIS bytes

#### 返回值

| 返回值 | 含义 |
|-------|------|
| EW_OK (0) | 成功 |
| EW_LENGTH (2) | length参数错误 |
| EW_ATTRIB (4) | axis参数错误 |

#### 结构体定义

**程序号4位版本** (Series 15/16/18等)：
```c
typedef struct odbdy {
    short dummy;                  // 未使用
    short axis;                   // 轴号
    short alarm;                  // 报警状态
    short prgnum;                 // 当前程序号
    short prgmnum;                // 主程序号
    long seqnum;                  // 当前序列号
    long actf;                    // 实际进给速度
    long acts;                    // 实际主轴速度
    union {
        struct {
            long absolute[MAX_AXIS];   // 绝对位置数组
            long machine[MAX_AXIS];    // 机械位置数组
            long relative[MAX_AXIS];   // 相对位置数组
            long distance[MAX_AXIS];   // 距离值数组
        } faxis;                       // 所有轴数据
        struct {
            long absolute;             // 单轴绝对位置
            long machine;              // 单轴机械位置
            long relative;             // 单轴相对位置
            long distance;             // 单轴距离值
        } oaxis;                       // 单轴数据
    } pos;
} ODBDY;
```

**程序号8位版本** (Series 16i/18i等)：
```c
typedef struct odbdy {
    short dummy;                  // 未使用
    short axis;                   // 轴号
    short alarm;                  // 报警状态
    long prgnum;                  // 当前程序号(8位)
    long prgmnum;                 // 主程序号(8位)
    long seqnum;                  // 当前序列号
    long actf;                    // 实际进给速度
    long acts;                    // 实际主轴速度
    // pos 结构同上
} ODBDY;
```

#### 报警状态位说明

**Series 30i/0i-D/F**：
- #00: 参数切换(SW)
- #01: 断电参数保存(PW)
- #02: I/O错误(IO)
- #03: 前台P/S(PS)
- #04: 超程/外部数据(OT)
- #05: 过热报警(OH)
- #06: 伺服报警(SV)
- #07: 数据I/O错误(SR)
- #08: 宏报警(MC)
- #09: 主轴报警(SP)
- #10: 其他报警(DS)
- #11: 故障预防函数相关报警(IE)
- #12: 后台P/S(BG)
- #13: 同步误差(SN)
- #15: 外部报警消息(EX)

#### 使用条件和注意事项

**Series 15i**：
- 无法读取全部报警状态，请使用 cnc_rddynamic2
- 需要API版本支持8位程序号

**支持所有CNC模式**

**连接要求**：
- HSSB: 需要扩展驱动/库函数
- Ethernet: 需要以太网+扩展驱动/库函数

#### C语言示例

```c
#include "fwlib32.h"

void example_cnc_rddynamic(unsigned short h)
{
    ODBDY buf;
    short ret = cnc_rddynamic(h, -1, sizeof(buf), &buf);
    
    if (ret == EW_OK) {
        printf("Current program: %d\n", buf.prgnum);
        printf("Main program: %d\n", buf.prgmnum);
        printf("Sequence number: %ld\n", buf.seqnum);
        printf("Feed rate: %ld\n", buf.actf);
        printf("Spindle speed: %ld\n", buf.acts);
        printf("Alarm status: %d\n", buf.alarm);
        
        // 多轴数据
        for (int i = 0; i < MAX_AXIS; i++) {
            printf("Axis %d - Abs: %ld, Mach: %ld, Rel: %ld, Dist: %ld\n",
                   i+1,
                   buf.pos.faxis.absolute[i],
                   buf.pos.faxis.machine[i],
                   buf.pos.faxis.relative[i],
                   buf.pos.faxis.distance[i]);
        }
    }
}
```

---

## 通用结构体定义

### 基础数据类型

```c
// 轴位置结构
typedef struct odbaxis {
    short dummy;           // 未使用
    short type;            // 轴号
    long data[MAX_AXIS];   // 位置数据
} ODBAXIS;

// 实际速度结构
typedef struct odbact {
    short dummy[2];        // 未使用
    long data;             // 速度值
} ODBACT;

// 位置元素结构
typedef struct poselm {
    long data;             // 位置数据
    short dec;             // 小数点位置
    short unit;            // 单位
    short disp;            // 显示状态
    char name;             // 轴名
    char suff;             // 轴名后缀
} POSELM;

// 位置总体结构
typedef struct odbpos {
    POSELM abs;            // 绝对位置
    POSELM mach;           // 机械位置
    POSELM rel;            // 相对位置
    POSELM dist;           // 距离值
} ODBPOS;

// 速度元素结构
typedef struct speedelm {
    long data;             // 速度数据
    short dec;             // 小数点位置
    short unit;            // 单位
    short reserve;         // 保留
    char name;             // 名称
    char suff;             // 后缀
} SPEEDELM;

// 速度总体结构
typedef struct odbspeed {
    SPEEDELM actf;         // 进给速度
    SPEEDELM acts;         // 主轴速度
} ODBSPEED;

// 轴数据结构
typedef struct odbaxdt {
    char name[4];          // 轴名
    long data;             // 数据值
    short dec;             // 小数点位置
    short unit;            // 单位
    short flag;            // 标志位
    short reserve;         // 保留
} ODBAXDT;
```

### 常用常量

```c
#define MAX_AXIS        32        // 最大轴数
#define ALL_AXES        (-1)      // 所有轴标记
#define EW_OK           0         // 成功
#define EW_LENGTH       2         // 长度错误
#define EW_NUMBER       3         // 数值错误
#define EW_ATTRIB       4         // 属性错误
#define EW_NOOPT        6         // 无选项
#define EW_PARAM        9         // 参数错误
```

---

## Python ctypes 调用示例

### 环境准备

```python
import ctypes
import os
from ctypes import c_short, c_long, c_char, POINTER, Structure, CDLL

# 加载 FOCAS 库 (Windows)
focas_lib = ctypes.CDLL("fwlib32.dll")  # 或 "fwlib64.dll" 64位版本

# Linux/其他系统需要适配库路径
# focas_lib = ctypes.CDLL("./libfwlib32.so")
```

### 基础结构体定义

```python
MAX_AXIS = 32

class ODBAXIS(Structure):
    """轴位置数据结构"""
    _fields_ = [
        ("dummy", c_short),
        ("type", c_short),
        ("data", c_long * MAX_AXIS),
    ]

class ODBACT(Structure):
    """实际速度数据结构"""
    _fields_ = [
        ("dummy", c_short * 2),
        ("data", c_long),
    ]

class POSELM(Structure):
    """位置元素结构"""
    _fields_ = [
        ("data", c_long),
        ("dec", c_short),
        ("unit", c_short),
        ("disp", c_short),
        ("name", c_char),
        ("suff", c_char),
    ]

class ODBPOS(Structure):
    """位置总体结构"""
    _fields_ = [
        ("abs", POSELM),
        ("mach", POSELM),
        ("rel", POSELM),
        ("dist", POSELM),
    ]

class SPEEDELM(Structure):
    """速度元素结构"""
    _fields_ = [
        ("data", c_long),
        ("dec", c_short),
        ("unit", c_short),
        ("reserve", c_short),
        ("name", c_char),
        ("suff", c_char),
    ]

class ODBSPEED(Structure):
    """速度总体结构"""
    _fields_ = [
        ("actf", SPEEDELM),
        ("acts", SPEEDELM),
    ]

class ODBAXDT(Structure):
    """轴数据结构"""
    _fields_ = [
        ("name", c_char * 4),
        ("data", c_long),
        ("dec", c_short),
        ("unit", c_short),
        ("flag", c_short),
        ("reserve", c_short),
    ]

class ODBDY(Structure):
    """动态数据结构"""
    _fields_ = [
        ("dummy", c_short),
        ("axis", c_short),
        ("alarm", c_short),
        ("prgnum", c_short),
        ("prgmnum", c_short),
        ("seqnum", c_long),
        ("actf", c_long),
        ("acts", c_long),
        # 简化版本，实际使用需根据轴数扩展
    ]

class REALPRM(Structure):
    """实数参数结构"""
    _fields_ = [
        ("prm_val", c_long),      # 参数值
        ("dec_val", c_long),      # 小数位数
    ]

class IODBPSD(Structure):
    """参数/设置数据结构"""
    _fields_ = [
        ("datano", c_short),      # 参数/设置号
        ("type", c_short),        # 类型和轴号
        ("u_cdata", c_char),      # 位/字节数据
    ]
```

### 调用示例

#### 1. 读取绝对坐标

```python
def read_absolute_position(handle, axis=-1):
    """
    读取绝对坐标
    
    Args:
        handle: 库句柄
        axis: 轴号 (-1=所有轴)
    
    Returns:
        dict: 包含返回值和位置数据
    """
    # 定义函数签名
    focas_lib.cnc_absolute.argtypes = [
        ctypes.c_ushort,  # FlibHndl
        ctypes.c_short,   # axis
        ctypes.c_short,   # length
        POINTER(ODBAXIS)  # absolute
    ]
    focas_lib.cnc_absolute.restype = ctypes.c_short
    
    # 准备数据
    buf = ODBAXIS()
    length = ctypes.sizeof(ODBAXIS)
    
    # 调用函数
    ret = focas_lib.cnc_absolute(handle, axis, length, ctypes.byref(buf))
    
    # 处理结果
    result = {
        'ret': ret,
        'ret_name': get_error_name(ret),
    }
    
    if ret == 0:  # EW_OK
        result['type'] = buf.type
        result['positions'] = [buf.data[i] for i in range(MAX_AXIS)]
    
    return result

# 调用示例
# ret = read_absolute_position(h, -1)
# print(f"Return: {ret['ret_name']}")
# print(f"Positions: {ret['positions']}")
```

#### 2. 读取实际进给速度

```python
def read_actual_feed(handle):
    """读取实际进给速度(F值)"""
    
    focas_lib.cnc_actf.argtypes = [
        ctypes.c_ushort,     # FlibHndl
        POINTER(ODBACT)      # actualfeed
    ]
    focas_lib.cnc_actf.restype = ctypes.c_short
    
    buf = ODBACT()
    ret = focas_lib.cnc_actf(handle, ctypes.byref(buf))
    
    return {
        'ret': ret,
        'feed_rate': buf.data if ret == 0 else None,
    }
```

#### 3. 读取实际主轴速度

```python
def read_actual_spindle(handle):
    """读取实际主轴速度(S值)"""
    
    focas_lib.cnc_acts.argtypes = [
        ctypes.c_ushort,     # FlibHndl
        POINTER(ODBACT)      # actualfeed
    ]
    focas_lib.cnc_acts.restype = ctypes.c_short
    
    buf = ODBACT()
    ret = focas_lib.cnc_acts(handle, ctypes.byref(buf))
    
    return {
        'ret': ret,
        'spindle_speed': buf.data if ret == 0 else None,
    }
```

#### 4. 读取速度信息

```python
def read_speed_info(handle, data_type=-1):
    """
    读取速度信息
    
    Args:
        handle: 库句柄
        data_type: 0=进给; 1=主轴; -1=全部
    """
    
    focas_lib.cnc_rdspeed.argtypes = [
        ctypes.c_ushort,      # FlibHndl
        ctypes.c_short,       # type
        POINTER(ODBSPEED)     # speed
    ]
    focas_lib.cnc_rdspeed.restype = ctypes.c_short
    
    buf = ODBSPEED()
    ret = focas_lib.cnc_rdspeed(handle, data_type, ctypes.byref(buf))
    
    result = {
        'ret': ret,
    }
    
    if ret == 0:
        result['feed'] = {
            'data': buf.actf.data,
            'unit': buf.actf.unit,
            'name': buf.actf.name.decode() if isinstance(buf.actf.name, bytes) else buf.actf.name,
        }
        result['spindle'] = {
            'data': buf.acts.data,
            'unit': buf.acts.unit,
            'name': buf.acts.name.decode() if isinstance(buf.acts.name, bytes) else buf.acts.name,
        }
    
    return result
```

#### 5. 读取位置信息

```python
def read_position(handle, data_type=0, num_axes=3):
    """
    读取位置信息
    
    Args:
        handle: 库句柄
        data_type: 0=绝对; 1=机械; 2=相对; 3=距离; -1=全部
        num_axes: 轴数
    """
    
    focas_lib.cnc_rdposition.argtypes = [
        ctypes.c_ushort,          # FlibHndl
        ctypes.c_short,           # type
        POINTER(ctypes.c_short),  # data_num
        POINTER(ODBPOS)           # position
    ]
    focas_lib.cnc_rdposition.restype = ctypes.c_short
    
    data_num = ctypes.c_short(num_axes)
    buf = (ODBPOS * num_axes)()
    
    ret = focas_lib.cnc_rdposition(
        handle, 
        data_type, 
        ctypes.byref(data_num),
        buf
    )
    
    result = {
        'ret': ret,
        'actual_axes': data_num.value,
    }
    
    if ret == 0:
        positions = []
        for i in range(data_num.value):
            pos_data = {
                'abs': buf[i].abs.data,
                'machine': buf[i].mach.data,
                'relative': buf[i].rel.data,
                'distance': buf[i].dist.data,
                'axis_name': chr(buf[i].abs.name) if buf[i].abs.name else 'X',
            }
            positions.append(pos_data)
        result['positions'] = positions
    
    return result
```

#### 6. 读取动态数据

```python
def read_dynamic_data(handle, axis=-1):
    """
    读取动态数据（综合）
    包含程序号、序列号、速度、位置等信息
    """
    
    focas_lib.cnc_rddynamic.argtypes = [
        ctypes.c_ushort,      # FlibHndl
        ctypes.c_short,       # axis
        ctypes.c_short,       # length
        POINTER(ODBDY)        # rddynamic
    ]
    focas_lib.cnc_rddynamic.restype = ctypes.c_short
    
    buf = ODBDY()
    length = ctypes.sizeof(ODBDY)
    
    ret = focas_lib.cnc_rddynamic(handle, axis, length, ctypes.byref(buf))
    
    result = {
        'ret': ret,
        'ret_name': get_error_name(ret),
    }
    
    if ret == 0:
        result.update({
            'axis': buf.axis,
            'alarm': buf.alarm,
            'program': buf.prgnum,
            'main_program': buf.prgmnum,
            'sequence': buf.seqnum,
            'feed_rate': buf.actf,
            'spindle_speed': buf.acts,
        })
    
    return result
```

#### 7. 错误代码映射

```python
ERROR_CODES = {
    0: 'EW_OK',
    2: 'EW_LENGTH',
    3: 'EW_NUMBER',
    4: 'EW_ATTRIB',
    6: 'EW_NOOPT',
    9: 'EW_PARAM',
    17: 'EW_PASSWD',
}

def get_error_name(code):
    """获取错误代码的名称"""
    return ERROR_CODES.get(code, f'UNKNOWN({code})')
```

#### 8. 读取参数数据

```python
def read_parameter(handle, param_no, axis=0):
    """
    读取参数数据
    
    Args:
        handle: 库句柄
        param_no: 参数号
        axis: 轴号 (0=无轴, 1..m=轴, -1=全轴)
    
    Returns:
        dict: 参数数据
    """
    
    focas_lib.cnc_rdparam.argtypes = [
        ctypes.c_ushort,      # FlibHndl
        ctypes.c_short,       # number
        ctypes.c_short,       # axis
        ctypes.c_short,       # length
        POINTER(IODBPSD)      # param
    ]
    focas_lib.cnc_rdparam.restype = ctypes.c_short
    
    buf = IODBPSD()
    length = ctypes.sizeof(IODBPSD)
    
    ret = focas_lib.cnc_rdparam(handle, param_no, axis, length, ctypes.byref(buf))
    
    result = {
        'ret': ret,
        'ret_name': get_error_name(ret),
        'param_no': buf.datano,
        'type': buf.type,
    }
    
    if ret == 0:
        result['data'] = buf.u_cdata
    
    return result

# 使用示例：
# ret = read_parameter(h, 1020, -1)  # 读取轴名参数
# print(f"参数号: {ret['param_no']}, 数据: {ret['data']}")
```

#### 9. 读取设置数据

```python
def read_setting(handle, set_no, axis=0):
    """
    读取设置数据
    
    Args:
        handle: 库句柄
        set_no: 设置数据号
        axis: 轴号 (0=无轴, 1..m=轴, -1=全轴)
    
    Returns:
        dict: 设置数据
    """
    
    focas_lib.cnc_rdset.argtypes = [
        ctypes.c_ushort,      # FlibHndl
        ctypes.c_short,       # number
        ctypes.c_short,       # axis
        ctypes.c_short,       # length
        POINTER(IODBPSD)      # set
    ]
    focas_lib.cnc_rdset.restype = ctypes.c_short
    
    buf = IODBPSD()
    length = ctypes.sizeof(IODBPSD)
    
    ret = focas_lib.cnc_rdset(handle, set_no, axis, length, ctypes.byref(buf))
    
    result = {
        'ret': ret,
        'ret_name': get_error_name(ret),
        'set_no': buf.datano,
        'type': buf.type,
    }
    
    if ret == 0:
        result['data'] = buf.u_cdata
    
    return result

# 使用示例：
# ret = read_setting(h, 100, 0)  # 读取设置数据
# print(f"设置号: {ret['set_no']}, 结果: {ret['ret_name']}")
```
```

#### 10. 完整使用示例

```python
def main():
    """完整使用示例"""
    
    # 假设已获得有效的库句柄 h
    h = 1  # 这里应该是真实的句柄
    
    print("=== FANUC FOCAS 库调用示例 ===\n")
    
    # 1. 读取绝对坐标
    print("1. 读取绝对坐标:")
    ret1 = read_absolute_position(h, -1)
    print(f"   结果: {ret1['ret_name']}")
    if ret1['ret'] == 0:
        print(f"   第1轴: {ret1['positions'][0] / 10000:.4f}mm")
    print()
    
    # 2. 读取进给速度
    print("2. 读取进给速度:")
    ret2 = read_actual_feed(h)
    print(f"   结果: {get_error_name(ret2['ret'])}")
    if ret2['feed_rate'] is not None:
        print(f"   进给速度: {ret2['feed_rate']} mm/min")
    print()
    
    # 3. 读取主轴速度
    print("3. 读取主轴速度:")
    ret3 = read_actual_spindle(h)
    print(f"   结果: {get_error_name(ret3['ret'])}")
    if ret3['spindle_speed'] is not None:
        print(f"   主轴速度: {ret3['spindle_speed']} rpm")
    print()
    
    # 4. 读取综合速度信息
    print("4. 读取综合速度信息:")
    ret4 = read_speed_info(h, -1)
    print(f"   结果: {get_error_name(ret4['ret'])}")
    if ret4['ret'] == 0:
        print(f"   进给: {ret4['feed']['data']} (单位:{ret4['feed']['unit']})")
        print(f"   主轴: {ret4['spindle']['data']} (单位:{ret4['spindle']['unit']})")
    print()
    
    # 5. 读取位置信息
    print("5. 读取位置信息:")
    ret5 = read_position(h, 0, 3)  # 读3轴绝对位置
    print(f"   结果: {get_error_name(ret5['ret'])}")
    print(f"   实际轴数: {ret5['actual_axes']}")
    if ret5['ret'] == 0:
        for i, pos in enumerate(ret5['positions']):
            print(f"   轴 {pos['axis_name']}: 绝对={pos['abs']}, "
                  f"机械={pos['machine']}, 相对={pos['relative']}")
    print()
    
    # 6. 读取动态数据
    print("6. 读取动态数据:")
    ret6 = read_dynamic_data(h, -1)
    print(f"   结果: {ret6['ret_name']}")
    if ret6['ret'] == 0:
        print(f"   当前程序: {ret6['program']}")
        print(f"   主程序: {ret6['main_program']}")
        print(f"   序列号: {ret6['sequence']}")
        print(f"   进给速度: {ret6['feed_rate']}")
        print(f"   主轴速度: {ret6['spindle_speed']}")
        print(f"   报警状态: {bin(ret6['alarm'])}")
    print()
    
    # 7. 读取参数数据
    print("7. 读取参数数据:")
    ret7 = read_parameter(h, 1020, -1)  # 轴名参数
    print(f"   结果: {ret7['ret_name']}")
    if ret7['ret'] == 0:
        print(f"   参数号: {ret7['param_no']}")
        print(f"   数据: {ret7['data']}")
    print()
    
    # 8. 读取设置数据
    print("8. 读取设置数据:")
    ret8 = read_setting(h, 100, 0)
    print(f"   结果: {ret8['ret_name']}")
    if ret8['ret'] == 0:
        print(f"   设置号: {ret8['set_no']}")
        print(f"   数据: {ret8['data']}")

if __name__ == '__main__':
    main()
```

---

## 常见错误代码

| 代码 | 名称 | 含义 | 解决方法 |
|------|------|------|--------|
| 0 | EW_OK | 成功 | 数据有效，可使用 |
| 2 | EW_LENGTH | 数据块长度错误 | 检查structure size和length参数 |
| 3 | EW_NUMBER | 数据编号错误 | 检查数据类型或分类参数 |
| 4 | EW_ATTRIB | 数据属性错误 | 检查参数范围和有效性 |
| 6 | EW_NOOPT | 无此选项 | 检查CNC是否安装了必要选项 |
| 9 | EW_PARAM | CNC参数错误 | 检查CNC参数设置 |

**故障排除**：
1. 检查库句柄是否有效
2. 验证CNC是否连接
3. 检查CNC参数和选项配置
4. 确保数据结构对齐正确
5. 查看CNC设备日志获取详细错误信息

---

## 使用流程指南

### 初始化流程

```
1. 初始化库 (fwlib_prolog)
   ↓
2. 获取库句柄 (ethrpc_alloc_handle 或类似)
   ↓
3. 建立连接 (cnc_startupprocess)
   ↓
4. 检查CNC状态 (cnc_sysinfo)
```

### 数据采集流程

#### 单个函数调用

```
1. 准备输入参数
   ├─ 库句柄
   ├─ 轴号 (if applicable)
   └─ 数据缓冲区
   ↓
2. 调用FOCAS函数
   ├─ cnc_absolute / cnc_machine / 其他
   └─ 检查返回值
   ↓
3. 检查结果
   ├─ if ret == EW_OK → 数据有效
   ├─ if ret != EW_OK → 处理错误
   └─ 检查CNC参数和选项
   ↓
4. 使用数据或记录日志
```

#### 高效的综合采集 (推荐)

```
使用 cnc_rddynamic 一次采集多种数据：
   ├─ 报警状态
   ├─ 程序号
   ├─ 序列号
   ├─ 实际进给速度
   ├─ 实际主轴速度
   └─ 各轴位置信息
```

### 关键参数验证清单

**调用任何函数前，检查**：

- [ ] 库句柄有效
- [ ] CNC已连接
- [ ] CNC参数正确设置
- [ ] 必要的CNC选项已安装
- [ ] 数据结构大小正确
- [ ] 轴号在有效范围内

### 常见应用场景

#### 场景1: 实时位置监测
```
推荐：cnc_rdposition 或 cnc_rdaxisdata
优点：完整的轴信息，支持扩展轴名
```

#### 场景2: 加工过程实时监控
```
推荐：cnc_rddynamic (一次调用多个数据)
优点：效率高，包含程序/序列号
```

#### 场景3: 刀具更换监测
```
推荐：cnc_rdprgnum + cnc_rdseqnum 
或使用 cnc_rddynamic 获取序列号变化
```

#### 场景4: 单个轴精密控制
```
推荐：cnc_absolute 或 cnc_rdaxisdata
优点：可获取详细的标志位信息
```

#### 场景5: 机床参数获取
```
推荐：cnc_rdparam (读取参数) / cnc_rdset (读取设置)
优点：可获取机床的所有参数和设置信息
用途：配置查询、调试、数据备份
```

#### 场景6: 数据批量采集
```
推荐：cnc_rddynamic + cnc_rdaxisdata + cnc_rdparam
优点：一次获取多种类型数据，提高效率
```

### 数据有效性检查

```python
def is_data_valid(ret_code, axis_flag=None):
    """检查返回数据是否有效"""
    
    # 检查基本返回值
    if ret_code != 0:  # EW_OK
        return False, f"函数返回错误: {ret_code}"
    
    # 检查轴标志 (来自 cnc_rdaxisdata)
    if axis_flag is not None:
        if axis_flag & 0x10:  # 伺服断电
            return False, "轴伺服已断电"
        if axis_flag & 0x20:  # 未到位
            return False, "轴未到位"
    
    return True, "数据有效"
```

---

## 附录：小数点处理示例

```python
def convert_position_data(raw_data, decimal_places):
    """
    转换原始位置数据为实际值
    
    Args:
        raw_data: 来自FOCAS的长整数数据
        decimal_places: 小数点位置 (来自cnc_getfigure)
    
    Returns:
        float: 转换后的实际值
    """
    if decimal_places >= 0:
        return raw_data / (10 ** decimal_places)
    else:
        return raw_data * (10 ** (-decimal_places))

# 使用示例：
# 假设 raw_data = 120005, decimal_places = 3
# 结果 = 120005 / 1000 = 120.005 mm
actual_position = convert_position_data(120005, 3)
print(f"Position: {actual_position:.3f} mm")
```

---

### 9. cnc_rdparam - 读参数

#### 功能描述
读取CNC指定的参数数据（由参数号和轴号指定）。参数类型多样，包括位、字节、字、双字和实数类型参数。支持有轴和无轴参数。

**重要特点**：
- 支持多种参数类型：位、字节、字、双字、实数
- 可读取有轴参数或无轴参数
- 支持一次读取所有轴的参数
- 参数属性（类型、轴）可通过 `cnc_rdparainfo` 获取

#### 函数原型

```c
#include "fwlib32.h" or "fwlib64.h"

FWLIBAPI short WINAPI cnc_rdparam(
    unsigned short FlibHndl,    // [in]  库句柄
    short number,                // [in]  参数号
    short axis,                  // [in]  轴号
    short length,                // [in]  数据块长度
    IODBPSD *param               // [out] 参数数据结构体指针
);
```

#### 参数说明

| 参数名 | 类型 | 说明 | 备注 |
|-------|------|------|------|
| FlibHndl | unsigned short | 库句柄 | - |
| number | short | 参数号 | 见CNC参数手册 |
| axis | short | 轴号 | 0=无轴; 1..m=轴号; -1(ALL_AXES)=所有轴 |
| length | short | 数据块长度 | 4+(数据大小)×(轴数) |
| param | IODBPSD* | 输出参数数据 | 见结构体说明 |

#### 返回值

| 返回值 | 含义 | 处理方法 |
|-------|------|--------|
| EW_OK (0) | 成功 | 数据有效 |
| EW_LENGTH (2) | 数据块长度错误 | 检查length计算 |
| EW_NUMBER (3) | 参数号错误 | 验证参数号是否存在 |
| EW_ATTRIB (4) | 轴号错误 | 检查轴号范围 |
| EW_PASSWD (17) | 参数被保护 | 参数无法读取 |

#### 参数类型说明

| 类型 | 含义 | 字节大小 | 说明 |
|------|------|--------|------|
| 位参数 | Bit parameter | 1 | 每位有各自定义 |
| 位参数(轴) | Bit parameter with axis | 1 | 每位有各自定义（各轴） |
| 字节参数 | Byte parameter | 1 | 1字节数据 |
| 字节参数(轴) | Byte parameter with axis | 1 | 1字节数据（各轴） |
| 字参数 | Word parameter | 2 | 2字节数据 |
| 字参数(轴) | Word parameter with axis | 2 | 2字节数据（各轴） |
| 双字参数 | 2-Word parameter | 4 | 4字节数据 |
| 双字参数(轴) | 2-Word parameter with axis | 4 | 4字节数据（各轴） |
| 实数参数 | Real parameter | 8 | 4字节值+4字节小数位 |
| 实数参数(轴) | Real parameter with axis | 8 | 4字节值+4字节小数位（各轴） |

#### 结构体定义

**基本版本** (Series 15, 16/18/21等)：
```c
typedef struct iodbpsd {
    short datano;              // 参数号
    short type;                // 类型信息
                               // 高字节: 参数类型(0=位,1=字节,2=字,3=双字,4=实数)
                               // 低字节: 轴号(0=无轴, 1..m=轴, -1=全轴)
    union {
        char cdata;            // 位/字节参数数据
        short idata;           // 字参数数据
        long ldata;            // 双字参数数据
        char cdatas[MAX_AXIS]; // 位/字节参数(轴)
        short idatas[MAX_AXIS]; // 字参数(轴)
        long ldatas[MAX_AXIS]; // 双字参数(轴)
    } u;
} IODBPSD;
```

**实数参数版本** (Series 15i, 30i, 0i-D/F, PMi-A)：
```c
typedef struct realprm {
    long prm_val;              // 参数值
    long dec_val;              // 小数位数
} REALPRM;

typedef struct iodbpsd {
    short datano;              // 参数号
    short type;                // 类型信息
    union {
        char cdata;            // 位/字节参数
        short idata;           // 字参数
        long ldata;            // 双字参数
        REALPRM rdata;         // 实数参数
        // ...数组版本
        REALPRM rdatas[MAX_AXIS]; // 实数参数(轴)
    } u;
} IODBPSD;
```

**实数参数计算**：
```
实际值 = prm_val × 10^(-dec_val)

例子：prm_val=12345, dec_val=3
实际值 = 12345 × 10^(-3) = 12.345
```

#### 使用条件和注意事项

- 位参数：无法逐位读取，必须读取整个字节（8位）
- 参数可用性：通过 `cnc_rdparainfo` 和 `cnc_rdparanum` 查询
- 参数保护：某些参数可能被保护，返回 EW_PASSWD
- 支持所有CNC模式

#### C语言示例

```c
#include "fwlib32.h"

void example_cnc_rdparam(unsigned short h)
{
    IODBPSD param;
    short ret;
    
    // 示例1: 读取轴名参数(1020=轴名，所有轴)
    ret = cnc_rdparam(h, 1020, -1, 4 + 1 * MAX_AXIS, &param);
    if (ret == EW_OK) {
        printf("Parameter No: %d\n", param.datano);
        for (int i = 0; i < 3; i++) {
            printf("Axis %d name: %c\n", i+1, param.u.cdatas[i]);
        }
    }
    
    // 示例2: 读取双字参数(3101=主轴最大速度，无轴)
    ret = cnc_rdparam(h, 3101, 0, 4 + 4, &param);
    if (ret == EW_OK) {
        printf("Spindle max speed: %ld\n", param.u.ldata);
    }
}
```

---

### 10. cnc_rdset - 读设置数据

#### 功能描述
读取CNC指定的设置数据（由设置号和轴号指定）。设置数据与参数类似，但具有"设置属性"，不能读取无设置属性的参数。

**与 cnc_rdparam 的区别**：
- 只能读取具有"设置属性"的参数
- 无法读取纯参数（无设置属性的参数）
- 其他特性基本相同

#### 函数原型

```c
#include "fwlib32.h" or "fwlib64.h"

FWLIBAPI short WINAPI cnc_rdset(
    unsigned short FlibHndl,    // [in]  库句柄
    short number,                // [in]  设置数据号
    short axis,                  // [in]  轴号
    short length,                // [in]  数据块长度
    IODBPSD *set                 // [out] 设置数据结构体指针
);
```

#### 参数说明

| 参数名 | 类型 | 说明 | 备注 |
|-------|------|------|------|
| FlibHndl | unsigned short | 库句柄 | - |
| number | short | 设置数据号 | 见CNC参数手册 |
| axis | short | 轴号 | 0=无轴; 1..m=轴号; -1(ALL_AXES)=所有轴 |
| length | short | 数据块长度 | 4+(数据大小)×(轴数) |
| set | IODBPSD* | 输出设置数据 | 见结构体说明 |

#### 返回值

| 返回值 | 含义 |
|-------|------|
| EW_OK (0) | 成功 |
| EW_LENGTH (2) | 数据块长度错误 |
| EW_NUMBER (3) | 设置数据号错误 |
| EW_ATTRIB (4) | 轴号错误 |

#### 设置数据类型说明

| 类型 | 字节大小 | 说明 |
|------|--------|------|
| 位设置数据 | 1 | 每位有各自定义 |
| 位设置数据(轴) | 1 | 每位有各自定义（各轴） |
| 字节设置数据 | 1 | 1字节数据 |
| 字节设置数据(轴) | 1 | 1字节数据（各轴） |
| 字设置数据 | 2 | 2字节数据 |
| 字设置数据(轴) | 2 | 2字节数据（各轴） |
| 双字设置数据 | 4 | 4字节数据 |
| 双字设置数据(轴) | 4 | 4字节数据（各轴） |
| 实数设置数据 | 8 | 4字节值+4字节小数位 |
| 实数设置数据(轴) | 8 | 4字节值+4字节小数位（各轴） |

#### 结构体定义

与 `cnc_rdparam` 相同，使用 `IODBPSD` 结构体：

```c
typedef struct iodbpsd {
    short datano;              // 设置数据号
    short type;                // 类型信息
    union {
        char cdata;            // 位/字节设置数据
        short idata;           // 字设置数据
        long ldata;            // 双字设置数据
        REALPRM rdata;         // 实数设置数据
        // ...数组版本
    } u;
} IODBPSD;
```

#### 使用条件和注意事项

- 只读取具有设置属性的参数
- 通过 `cnc_rdsetinfo` 和 `cnc_rdsetnum` 查询可用设置数据
- 支持所有CNC模式
- 多主轴设置在某些系列中有轴属性

#### C语言示例

```c
#include "fwlib32.h"

void example_cnc_rdset(unsigned short h)
{
    IODBPSD set;
    short ret;
    
    // 示例: 读取设置数据(无轴)
    ret = cnc_rdset(h, 100, 0, 4 + 4, &set);
    
    if (ret == EW_OK) {
        printf("Setting No: %d\n", set.datano);
        printf("Type: 0x%04x\n", set.type);
        printf("Data: %ld\n", set.u.ldata);
    } else {
        printf("Error: %d\n", ret);
    }
}
```

---

## 注意事项和最佳实践

1. **性能优化**
   - 使用 `cnc_rddynamic` 替代多个单独调用
   - 避免过于频繁的轮询（建议 100ms 以上间隔）
   - 使用中断机制而非轮询（如可用）

2. **错误处理**
   - 始终检查返回值
   - 实现重试机制（可选）
   - 记录失败的调用和错误代码

3. **内存管理**
   - 正确计算结构体大小
   - 避免缓冲区溢出
   - 及时释放资源

4. **CNC兼容性**
   - 检查目标CNC系列的支持情况
   - 验证CNC参数和选项配置
   - 参考官方文档了解系列差异

5. **数据精度**
   - 使用 `cnc_getfigure` 获取小数点位置
   - 正确处理不同单位转换
   - 考虑系统延迟（伺服、加减速）

6. **参数操作**
   - 区分参数(Parameter)和设置数据(Setting)
   - 使用 `cnc_rdparainfo` 验证参数属性
   - 某些参数受保护，只能读取不能修改

---

**文档完成**

此指南覆盖了FANUC FOCAS Library的10个核心机床参数函数的完整技术文档：
- **位置相关** (4个函数): cnc_absolute, cnc_machine, cnc_rdposition, cnc_rdaxisdata
- **速度相关** (4个函数): cnc_actf, cnc_acts, cnc_rdspeed, cnc_rddynamic
- **参数相关** (2个函数): cnc_rdparam, cnc_rdset

根据您的实际应用需求，选择合适的函数组合来实现机床数据采集、监控和控制功能。

如有任何疑问，请参考FANUC官方FOCAS库文档或咨询技术支持。
