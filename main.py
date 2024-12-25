import machine, utime, _thread

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
import framebuf
import micropython

# Constants
SET_CONTRAST = micropython.const(0x81)
SET_ENTIRE_ON = micropython.const(0xA4)
SET_NORM_INV = micropython.const(0xA6)
SET_DISP = micropython.const(0xAE)
SET_MEM_ADDR = micropython.const(0x20)
SET_COL_ADDR = micropython.const(0x21)
SET_PAGE_ADDR = micropython.const(0x22)
SET_DISP_START_LINE = micropython.const(0x40)
SET_SEG_REMAP = micropython.const(0xA0)
SET_MUX_RATIO = micropython.const(0xA8)
SET_COM_OUT_DIR = micropython.const(0xC0)
SET_DISP_OFFSET = micropython.const(0xD3)
SET_COM_PIN_CFG = micropython.const(0xDA)
SET_DISP_CLK_DIV = micropython.const(0xD5)
SET_PRECHARGE = micropython.const(0xD9)
SET_VCOM_DESEL = micropython.const(0xDB)
SET_CHARGE_PUMP = micropython.const(0x8D)

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


# DHT11 Sensor Driver
import array

class InvalidChecksum(Exception):
    pass
 
class InvalidPulseCount(Exception):
    pass
 
MAX_UNCHANGED = const(100)
MIN_INTERVAL_US = const(200000)
HIGH_LEVEL = const(50)
EXPECTED_PULSES = const(84)
 
class DHT11:
    _temperature: float
    _humidity: float
 
    def __init__(self, pin):
        self._pin = pin
        self._last_measure = utime.ticks_us()
        self._temperature = -1
        self._humidity = -1
 
    def measure(self):
        current_ticks = utime.ticks_us()
        if utime.ticks_diff(current_ticks, self._last_measure) < MIN_INTERVAL_US and (
            self._temperature > -1 or self._humidity > -1
        ):
            # Less than a second since last read, which is too soon according
            # to the datasheet
            return
 
        self._send_init_signal()
        pulses = self._capture_pulses()
        buffer = self._convert_pulses_to_buffer(pulses)
        self._verify_checksum(buffer)
 
        self._humidity = buffer[0] + buffer[1] / 10
        self._temperature = buffer[2] + buffer[3] / 10
        self._last_measure = utime.ticks_us()
 
    @property
    def humidity(self):
        self.measure()
        return self._humidity
 
    @property
    def temperature(self):
        self.measure()
        return self._temperature
 
    def _send_init_signal(self):
        self._pin.init(machine.Pin.OUT, machine.Pin.PULL_DOWN)
        self._pin.value(1)
        utime.sleep_ms(50)
        self._pin.value(0)
        utime.sleep_ms(18)
 
    @micropython.native
    def _capture_pulses(self):
        pin = self._pin
        pin.init(machine.Pin.IN, machine.Pin.PULL_UP)
 
        val = 1
        idx = 0
        transitions = bytearray(EXPECTED_PULSES)
        unchanged = 0
        timestamp = utime.ticks_us()
 
        while unchanged < MAX_UNCHANGED:
            if val != pin.value():
                if idx >= EXPECTED_PULSES:
                    raise InvalidPulseCount(
                        "Got more than {} pulses".format(EXPECTED_PULSES)
                    )
                now = utime.ticks_us()
                transitions[idx] = now - timestamp
                timestamp = now
                idx += 1
 
                val = 1 - val
                unchanged = 0
            else:
                unchanged += 1
        pin.init(machine.Pin.OUT, machine.Pin.PULL_DOWN)
        if idx != EXPECTED_PULSES:
            raise InvalidPulseCount(
                "Expected {} but got {} pulses".format(EXPECTED_PULSES, idx)
            )
        return transitions[4:]
 
    def _convert_pulses_to_buffer(self, pulses):
        """Convert a list of 80 pulses into a 5 byte buffer
        The resulting 5 bytes in the buffer will be:
            0: Integral relative humidity data
            1: Decimal relative humidity data
            2: Integral temperature data
            3: Decimal temperature data
            4: Checksum
        """
        # Convert the pulses to 40 bits
        binary = 0
        for idx in range(0, len(pulses), 2):
            binary = binary << 1 | int(pulses[idx] > HIGH_LEVEL)
 
        # Split into 5 bytes
        buffer = array.array("B")
        for shift in range(4, -1, -1):
            buffer.append(binary >> shift * 8 & 0xFF)
        return buffer
 
    def _verify_checksum(self, buffer):
        # Calculate checksum
        checksum = 0
        for buf in buffer[0:4]:
            checksum += buf
        if checksum & 0xFF != buffer[4]:
            raise InvalidChecksum()

class Main:
    NATURAL_WIND = 1
    SLEEP_WIND = 2
    NORMAL_WIND = 0

    TEMP_THRESHOLD = 0

    def __init__(self):
        self.keyboard = Keyboard()   
        self.motor = Motor_ctrl()
      
        self.current_speed = 0
        self.wind_type = None
        self.running = True

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
            '7': lambda: self.set_temp_threshold(30),
            '8': lambda: self.set_temp_threshold(50),
        }

        _thread.start_new_thread(self.wind_control_thread, ())

    def change_speed(self, speed):
        self.current_speed = speed
        if self.wind_type is None:
            self.motor.set_duty(speed)
            

    def change_wind_type(self, wind_type):
        self.wind_type = wind_type
        
    
    def wind_control_thread(self):
        while True:
            self.oled.fill(0)
            self.oled.rect(0, 0, 128, 64, 1)
            self.oled.text('WindSpeed:' + str(self.current_speed), 0, 16, 1)
            self.oled.text('WindType:', 0, 32, 1)
            if self.wind_type == self.NATURAL_WIND:
                print('Natural wind')
                self.oled.text('WindType:Natural', 0, 32, 1)
                # Natural wind pattern
                speeds = [self.current_speed, 0]
                for speed in speeds:
                    if self.wind_type != self.NATURAL_WIND:
                        break
                    self.motor.set_duty(int(speed))
                    utime.sleep(1)
            elif self.wind_type == self.SLEEP_WIND:
                print('Sleep wind')
                self.oled.text('WindType:Sleep', 0, 32, 1)
                # Sleep wind pattern
                speeds = [self.current_speed, 0]
                for speed in speeds:
                    if self.wind_type != self.SLEEP_WIND:
                        break
                    self.motor.set_duty(int(speed))
                    utime.sleep(2)
            elif self.wind_type == self.NORMAL_WIND:
                print('Normal wind')
                self.oled.text('WindType:Normal', 0, 32, 1)
                self.motor.set_duty(self.current_speed)
            self.oled.show()
        
    def set_temp_threshold(self, temp):
        self.TEMP_THRESHOLD = temp

    def overheating_protection(self):
        

    def main(self):
        while True:
            self.motor.start()
            self.key = self.keyboard.get_key()
            if self.key in self.key_motor_map:
                self.key_motor_map[self.key]()   
            
                
        
if __name__ == '__main__':
    prog = Main()
    prog.main()

