import rtde_control
import rtde_receive
import csv
import time
from pynput import keyboard  # 用于非阻塞监听键盘控制夹爪

from gripper_controller import ChangingTekGripper

# --- 录制主程序 ---
def record(ip_address="127.0.0.1", filename = "assembly_data.csv"):
    # 初始化机器人接口
    rtde_c = rtde_control.RTDEControlInterface(ip_address)
    rtde_r = rtde_receive.RTDEReceiveInterface(ip_address)
    
    # 初始化夹爪
    gripper = ChangingTekGripper(port='COM4')
    
    # 键盘控制逻辑
    last_gripper_command = gripper_command = None # 'open', 'close'
    def on_press(key):
        nonlocal gripper_command
        try:
            if key.char == 'o': gripper_command = 'open'
            if key.char == 'c': gripper_command = 'close'
        except AttributeError: pass

    listener = keyboard.Listener(on_press=on_press)
    listener.start()
   
    # 增加力/力矩数据 (f0-f5) 和 夹爪数据 (g_pos, g_cur)
    header = ["timestamp", "q0", "q1", "q2", "q3", "q4", "q5",
              "curr0", "curr1", "curr2", "curr3", "curr4", "curr5", # 电流
              "x", "y", "z", "rx", "ry", "rz",
              "fx", "fy", "fz", "mx", "my", "mz",
              #"gripper_pos", "gripper_current"]
              "gripper_command"]

    with open(filename, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)

        print("\n[控制说明] 按 'o' 打开夹爪，按 'c' 关闭夹爪。Ctrl+C 停止。")
        rtde_c.teachMode()
        
        try:
            while True:
                # 1. 夹爪控制执行
                if gripper_command == 'open':
                    gripper.move(6000) # 假设 0 为全开
                    last_gripper_command = 'open'
                    gripper_command = None
                elif gripper_command == 'close':
                    gripper.move(9000) # 假设 9000 为全闭 [cite: 21]
                    last_gripper_command = 'close'
                    gripper_command = None

                # 2. 获取数据
                t = rtde_r.getTimestamp()
                q = rtde_r.getActualQ()
                currents = rtde_r.getActualCurrent() # 获取 6 个关节的实际电流
                p = rtde_r.getActualTCPPose()
                f_data = rtde_r.getActualTCPForce() # 获取末端 6 维力 [传感器数据无需开启 forceMode]
                # g_pos, g_cur = gripper.get_status()

                # 因为每次轨迹记录的时间瓶颈可能出现在串口上，所以改为记录夹爪操作，而不是读取并记录夹爪数据
                
                # 3. 记录与显示
                # row = [t] + q + currents + p + f_data + [g_pos, g_cur]
                row = [t] + q + currents + p + f_data + [last_gripper_command]
                writer.writerow(row)
                
                status_text = f"\r[录制中] Z:{p[2]*1000:>6.1f}mm | Fz:{f_data[2]:>5.1f}N | Gripper:{gripper_command}"
                print(status_text, end="", flush=True)
                
                time.sleep(0.01) # 100Hz 采样
                
        except KeyboardInterrupt:
            print("\n录制结束")
        finally:
            rtde_c.endTeachMode()
            listener.stop()
            
if __name__ == "__main__":
    record(ip_address="192.168.192.200", filename="assembly_data.csv")