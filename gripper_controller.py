import minimalmodbus
import serial

# --- 夹爪控制类 (基于手册 Modbus 协议) ---
class ChangingTekGripper:
    def __init__(self, port='COM4', slave_id=1):
        self.instrument = minimalmodbus.Instrument(port, slave_id)
        self.instrument.serial.baudrate = 115200
        self.instrument.serial.bytesize = 8
        self.instrument.serial.stopbits = 1
        self.instrument.serial.parity = serial.PARITY_NONE
        self.instrument.serial.timeout = 0.1
        
        # 上电使能 
        try:
            self.instrument.write_register(0x0100, 1)
            print("夹爪已使能")
        except Exception as e:
            print(f"夹爪初始化失败: {e}")

    def move(self, pos, speed=100, force=40):
        """
        pos: 目标位置
        speed/force: 0-100 百分比 
        """
        try:
            # 写入位置 (32位，分为高低寄存器) 
            self.instrument.write_register(0x0102, (pos >> 16) & 0xFFFF)
            self.instrument.write_register(0x0103, pos & 0xFFFF)
            # 写入速度和力矩 
            self.instrument.write_register(0x0104, speed)
            self.instrument.write_register(0x0105, force)
            # 触发运动 
            self.instrument.write_register(0x0108, 1)
        except Exception as e:
            print(f"夹爪移动失败: {e}")
            pass

    def get_status(self):
        """读取当前位置和力矩数据 """
        try:
            pos_h = self.instrument.read_register(0x0102)
            pos_l = self.instrument.read_register(0x0103)
            current = self.instrument.read_register(0x060C)
            actual_pos = (pos_h << 16) | pos_l
            return actual_pos, current
        except Exception:
            return 0, 0