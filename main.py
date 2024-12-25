import machine, utime, _thread
import framebuf
from micropython import const
import dht


class Motor_ctrl():
    MOTOR_PWM = 15
    MOTOR_CTRL_AIN1 = 14
    MOTOR_CTRL_AIN2 = 13

    def __init__(self, motor_pwm = MOTOR_PWM, motor_ain1 = MOTOR_CTRL_AIN1, motor_ain2 = MOTOR_CTRL_AIN2):    
        self.motor_pwm = machine.PWM(machine.Pin(motor_pwm))
        self.motor_pwm.freq(10000)
        self.motor_pwm.duty_u16(0)

        self.motor_ctrl_ain1 = machine.Pin(motor_ain1, machine.Pin.OUT)
        self.motor_ctrl_ain1.on()
        self.motor_ctrl_ain2 = machine.Pin(motor_ain2, machine.Pin.OUT)
        self.motor_ctrl_ain2.off()

    def set_duty(self, duty):
        duty = int(duty/100*65535)
        self.motor_pwm.duty_u16(duty)
        print('Motor speed: ', duty)

    def stop(self):
        self.motor_ctrl_ain1.off()
        self.motor_ctrl_ain2.off()
    
    def start(self):
        self.motor_ctrl_ain1.on()
        self.motor_ctrl_ain2.off()

class Keyboard():
    # Keyboard Matrix Configuration
    ROW_PINS = [16, 17, 18, 19]
    COL_PINS = [20, 21, 22, 26]

    # Timing Configuration
    DEBOUNCE_TIME = 20

    def __init__(self, row_pins = ROW_PINS, col_pins = COL_PINS, debounce_time = DEBOUNCE_TIME):
        # Initialize rows for output
        self.rows = [machine.Pin(pin, machine.Pin.OUT) for pin in row_pins] 
        # Initialize columns for input with pull-up
        self.cols = [machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_DOWN) for pin in col_pins]
        
        # Define keymap
        self.keymap = [
            ['D', '#', '0', '*'],
            ['C', '9', '8', '7'],
            ['B', '6', '5', '4'],
            ['A', '3', '2', '1']
        ]
        self.debounce_time = debounce_time  
        self.last_press_time = 0
        
    def scan(self):
        key = None
        current_time = utime.ticks_ms()
        
        # Debounce
        if utime.ticks_ms() - self.last_press_time < self.debounce_time:
            return 0
        # Scan
        for i, row in enumerate(self.rows):
            row.on()
            for j, col in enumerate(self.cols):
                if col.value():
                    key = self.keymap[i][j]
                    self.last_press_time = current_time
                    row.off()
                    return key
            row.off()
    
    def get_key(self):
        key = self.scan()
        if key:
            return key
        return None

# ssd1306 OLED Driver 

# Constants
SET_CONTRAST = const(0x81)
SET_ENTIRE_ON = const(0xA4)
SET_NORM_INV = const(0xA6)
SET_DISP = const(0xAE)
SET_MEM_ADDR = const(0x20)
SET_COL_ADDR = const(0x21)
SET_PAGE_ADDR = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP = const(0xA0)
SET_MUX_RATIO = const(0xA8)
SET_COM_OUT_DIR = const(0xC0)
SET_DISP_OFFSET = const(0xD3)
SET_COM_PIN_CFG = const(0xDA)
SET_DISP_CLK_DIV = const(0xD5)
SET_PRECHARGE = const(0xD9)
SET_VCOM_DESEL = const(0xDB)
SET_CHARGE_PUMP = const(0x8D)

class SSD1306_I2C(framebuf.FrameBuffer):
    def __init__(self, width, height, i2c, addr=0x3C):
        self.i2c = i2c
        self.addr = addr
        self.width = width
        self.height = height
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()
        
    def init_display(self):
        for cmd in [
            SET_DISP | 0x00,  # off
            SET_MEM_ADDR, 0x00,  # horizontal
            SET_DISP_START_LINE | 0x00,
            SET_SEG_REMAP | 0x01,  # rotate screen 180
            SET_MUX_RATIO, self.height - 1,
            SET_COM_OUT_DIR | 0x08,
            SET_DISP_OFFSET, 0x00,
            SET_COM_PIN_CFG, 0x02 if self.height == 32 else 0x12,
            SET_DISP_CLK_DIV, 0x80,
            SET_PRECHARGE, 0x22,
            SET_VCOM_DESEL, 0x30,
            SET_CONTRAST, 0xFF,
            SET_ENTIRE_ON,
            SET_NORM_INV,
            SET_CHARGE_PUMP, 0x14,
            SET_DISP | 0x01]:  # on
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def write_cmd(self, cmd):
        self.i2c.writeto(self.addr, bytes([0x80, cmd]))

    def write_data(self, buf):
        self.i2c.writeto(self.addr, b'\x40' + buf)

    def show(self):
        x0 = 0
        x1 = self.width - 1
        if self.width == 64:
            # displays with width of 64 pixels are shifted by 32
            x0 += 32
            x1 += 32
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_data(self.buffer)



class Main:
    NATURAL_WIND = const(1)
    SLEEP_WIND = const(2)
    NORMAL_WIND = const(0)

    TEMP_THRESHOLD = 100

    def __init__(self):
        self.keyboard = Keyboard()   
        self.motor = Motor_ctrl()
      
        self.current_speed = 0
        self.wind_type = None
        self.running = True

        self.temp_read_interval = 2000
        self.last_time_read = 0
        self.sensor = dht.DHT11(machine.Pin(0))

        i2c = machine.I2C(0, scl=machine.Pin(5), sda=machine.Pin(4), freq=200000)
        # Scan for I2C devices
        print('Scanning I2C bus...')
        devices = i2c.scan()

        if len(devices) == 0:
            ("No I2C devices found")
        else:
            print('I2C devices found:', len(devices))
        for device in devices:
            print("Device address: ", hex(device))
        self.oled = SSD1306_I2C(128, 64, i2c)

        self.key_motor_map = {
            '1': lambda: self.change_speed(30),
            '2': lambda: self.change_speed(60),
            '3': lambda: self.change_speed(80),
            'A': lambda: self.change_speed(100),
            '4': lambda: self.change_wind_type(self.NATURAL_WIND),
            '5': lambda: self.change_wind_type(self.SLEEP_WIND),
            '6': lambda: self.change_wind_type(self.NORMAL_WIND),
            'D': lambda: self.change_speed(0),
            '7': lambda: self.set_temp_threshold(27),
            '8': lambda: self.set_temp_threshold(50),
        }

        _thread.start_new_thread(self.wind_control_thread, ())

    def change_speed(self, speed):
        self.current_speed = speed
        if self.wind_type is None:
            self.motor.set_duty(speed)

    def change_wind_type(self, wind_type):
        self.wind_type = wind_type
    
    def get_temp(self):
        current_time = utime.ticks_ms()
        if utime.ticks_diff(current_time, self.last_time_read) >= self.temp_read_interval:
            try:
                self.sensor.measure()
                self.temp = self.sensor.temperature()
                self.hum = self.sensor.humidity()
                print("Temperature: {}".format(self.temp))
                self.last_time_read = current_time
            except OSError as e:
                print('Failed to read sensor.')
        else:
            pass
        return self.temp

    def wind_control_thread(self):
        wind_type_text = {
            self.NATURAL_WIND: 'Natural',
            self.SLEEP_WIND: 'Sleep',
            self.NORMAL_WIND: 'Normal'
        }
        
        wind_patterns = {
            self.NATURAL_WIND: ([1, 0], 1),  # (speeds multiplier, sleep time)
            self.SLEEP_WIND: ([1, 0], 2),
            self.NORMAL_WIND: ([1], 0)
        }

        while True:
            # Update display
            self.oled.fill(0)
            self.oled.rect(0, 0, 128, 64, 1)
            self.oled.text(f'WindSpeed:{self.current_speed}', 0, 0, 1)
            self.oled.text(f'Threshold:{self.TEMP_THRESHOLD}', 0, 48, 1)
            self.oled.text(f'WindType:', 0, 16, 1)
            self.oled.text(f'Temp:{self.get_temp()}', 0, 32, 1)

            if self.get_temp() is not None and self.get_temp() < self.TEMP_THRESHOLD:    
                if self.wind_type in wind_type_text:
                    self.oled.text(f'WindType:{wind_type_text[self.wind_type]}', 0, 16, 1)
                    pattern, sleep_time = wind_patterns[self.wind_type]
                    
                    for speed_mult in pattern:
                        if self.wind_type != self.wind_type:  # Check if type changed
                            break
                        self.motor.set_duty(int(self.current_speed * speed_mult))
                        if sleep_time:
                            utime.sleep(sleep_time)
            else:
                self.oled.text(f'Temp too high !', 0, 32, 1)
                self.oled.show()
                self.motor.set_duty(0)
                utime.sleep(10)
                
            self.oled.show()
            utime.sleep_ms(100)
        
    def set_temp_threshold(self, threshold):
        self.TEMP_THRESHOLD = threshold
        
    def main(self):
        while True:
            self.motor.start()
            self.key = self.keyboard.get_key()
            if self.key in self.key_motor_map:
                self.key_motor_map[self.key]()   
                
        
if __name__ == '__main__':
    prog = Main()
    prog.main()

