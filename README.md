# UR10 夹爪轨迹录制与复现

本项目包含 UR10 机器人夹爪轨迹的录制与复现控制程序，适用于参考机器人轨迹记录、夹爪控制和回放实现。

## 主要功能

- `record.py`：开启 teachMode、允许人工拖动机械臂录制轨迹，通过 RTDE 采集机器人状态并保存为 CSV，同时记录夹爪开合命令（键盘触发）
- `replay.py`：读取 CSV，使用 `moveJ + servoJ` 回放关节轨迹，并同步控制夹爪（含一个带力控补偿的回放函数）
- `teach.py`：仅开启 teachMode 和夹爪键盘控制小工具（不记录数据）
- `gripper_controller.py`：夹爪 Modbus 控制类

## 环境与依赖

- Python 3.9+
- 依赖包见 `requirements.txt`：
  - `ur-rtde`
  - `minimalmodbus`
  - `pyserial`
  - `pynput`

此外需要：
- UR 机器人开启 RTDE（脚本通过 `rtde_control` / `rtde_receive` 与机器人通讯）
- 夹爪可通过 Modbus RTU 串口访问（脚本默认 `COM4`，波特率 115200，可根据实际情况修改）

安装依赖：

```bash
python -m pip install -r requirements.txt
```

## 使用说明

运行前需要改两处配置：
- **机器人 IP**：`record.py` / `replay.py` 里的 `ip_address`（当前示例是 `192.168.192.200`）
- **夹爪串口**：`record.py` / `replay.py` / `teach.py` 里 `ChangingTekGripper(port='COM4')`

可选择更改的配置：
- **输入输出文件名**：`record.py` 里的 `filename`（当前示例是 `assembly_data.csv`），`replay.py`里的 `filename` 和 `log_filename`（当前示例是 `assembly_data.csv` 和 `replay_log.csv`）
- **复现时的控制方式**：通过在 `replay.py` 中更改 `replay` 函数的 `force_compensate_mode` 为 `True` 或 `False`，可以选择是否开启复现力控的模式（默认关闭）

### 录制轨迹（生成 CSV）

`record.py` 会进入 UR 的 `teachMode()`，并以约 100Hz 写入 CSV（默认 `assembly_data.csv`）。

```bash
python record.py
```

键盘控制：
- 按 `o`：夹爪打开（脚本里用 `gripper.move(6000)`，可根据夹爪开合角度和夹取力度需求调整参数）
- 按 `c`：夹爪关闭（脚本里用 `gripper.move(9000)`，可根据夹爪开合角度和夹取力度需求调整参数）
- `Ctrl+C`：结束录制并退出 teachMode

输出文件：
- `assembly_data.csv`：录制数据（时间戳、关节角、电流、TCP 位姿、TCP 力、夹爪指令）

### 回放轨迹（读取 CSV）

```bash
python replay.py
```

说明：
- 默认读取 `assembly_data.csv`
- 会先 `moveJ` 到起始关节角，然后循环 `servoJ` 回放
- 复现过程的数据默认记录到 `replay_log.csv` 中

### 仅改变机械臂和夹爪状态（不录制轨迹）

```bash
python teach.py
```

### 备注

该代码基于可运行版本经过较多的结构修改得到，因此并非经过测试的最终可用版本。若运行时遇到问题，请尝试自行分析和解决错误，或者直接丢给 AI 让它纠错。。。

目前怀疑控制夹爪的时候进行串口通信，可能会导致录制时数据采集频率局部低于100Hz，正在考虑之后引入线程、让 servoJ 用 timestamp 而非固定频率来复现轨迹