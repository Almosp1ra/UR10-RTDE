import rtde_control, rtde_receive
import csv
import time

from gripper_controller import ChangingTekGripper

# --- 复现主程序 ---
def replay(filename="assembly_data.csv",
           ip_address="127.0.0.1",
           log_filename="replay_log.csv",
           force_compensate_mode = False
    ):
    rtde_r = rtde_receive.RTDEReceiveInterface(ip_address)
    rtde_c = rtde_control.RTDEControlInterface(ip_address)
    
    # 初始化夹爪
    gripper = ChangingTekGripper(port='COM4')

    # 1. 加载录制好的轨迹数据
    data = []
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
            
    first_q = [float(data[0][f'q{i}']) for i in range(6)]

    # 准备复现时的日志文件
    header = ["timestamp", 
              "q0", "q1", "q2", "q3", "q4", "q5", 
              "curr0", "curr1", "curr2", "curr3", "curr4", "curr5", 
              "x", "y", "z", "rx", "ry", "rz",
              "fx", "fy", "fz", "mx", "my", "mz",
              "gripper_command"]
    
    log_file = open(log_filename, mode='w', newline='')
    writer = csv.writer(log_file)
    writer.writerow(header)

    # 2. 移动到起始点 
    print("正在移动到起始点...")
    rtde_c.moveJ(first_q, 0.5, 0.5)
    time.sleep(1)

    print("开始轨迹回放...")
    last_gripper_command = None

    # 3. 设置力控参数
    task_frame = [0, 0, 0, 0, 0, 0]        # 基座坐标系
    selection_vector = [1, 1, 1, 0, 0, 0]  # 在 X、Y、Z 轴开启力控
    force_type = 2
    limits = [2, 2, 1.5, 1, 1, 1]          # 允许的轴向最大速度

    try:
        for row in data:
            start_time = time.time()
            
            q_target = [float(row[f'q{i}']) for i in range(6)]
            gripper_command = row["gripper_command"]
            recorded_f = [float(row['fx']), float(row['fy']), float(row['fz']), 0, 0, 0]

            # 更新力控：将录制时的力作为当前的目标力
            if force_compensate_mode:
                rtde_c.forceMode(task_frame, selection_vector, recorded_f, force_type, limits)
            
            # 使用 servoJ 执行轨迹流
            rtde_c.servoJ(q_target, 0, 0, 0.01, 0.1, 400)

            # --- 实时获取当前状态 (记录内容) ---
            t_now = rtde_r.getTimestamp()
            q_now = rtde_r.getActualQ()
            cur_now = rtde_r.getActualCurrent()     # 获取电流
            p_now = rtde_r.getActualTCPPose()
            f_now = rtde_r.getActualTCPForce()      # 获取实际 TCP 力

            # --- 写入 CSV ---
            log_row = [t_now] + q_now + cur_now + p_now + f_now + [gripper_command]
            writer.writerow(log_row)

            # 夹爪控制 
            if gripper_command == 'open' and last_gripper_command != 'open':
                gripper.move(6000) # 打开
                last_gripper_command = 'open'
            elif gripper_command == 'close' and last_gripper_command != 'close':
                gripper.move(9000) # 关闭
                last_gripper_command = 'close'
                # gripper.move(g_pos)
                # last_g_pos = g_pos

            # 控制 100Hz 频率
            elapsed = time.time() - start_time
            if elapsed < 0.01:
                time.sleep(0.01 - elapsed)

    except Exception as e:
        print(f"复现中断: {e}")
    finally:
        # 停止力控并停止运动
        if force_compensate_mode:
            rtde_c.forceModeStop()
        rtde_c.servoStop()
        log_file.close() # 记得关闭文件
        print("复现完成")

if __name__ == "__main__":
    replay(ip_address="192.168.192.200")