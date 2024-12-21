import machine, utime

class LED():
    # LED Pin Configurations
    GREEN_LED = 4
    RED_LED = 3
    BLUE_LED = 6
    WHITE_LED = 8

    def __init__(self, pin):
        self.led = machine.Pin(pin, machine.Pin.OUT)

    def on(self):
        self.led.on()
        print('LED on')

    def off(self):
        self.led.off()

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


class Main:
    NATURAL_WIND = 1
    SLEEP_WIND = 2
    NORMAL_WIND = 0

    def __init__(self):
        self.green_led = LED(LED.GREEN_LED)
        self.red_led = LED(LED.RED_LED)
        self.blue_led = LED(LED.BLUE_LED)
        self.white_led = LED(LED.WHITE_LED)
        self.keyboard = Keyboard()   
        self.motor = Motor_ctrl()

        self.key_motor_map = {
                         '1': lambda : (self.motor.set_duty(30), self.white_led.on(), self.blue_led.off(), self.green_led.off(), self.red_led.off()),
                         '2': lambda : (self.motor.set_duty(60), self.white_led.off(), self.blue_led.on(), self.green_led.off(), self.red_led.off()),
                         '3': lambda : (self.motor.set_duty(80), self.white_led.off(), self.blue_led.off(), self.green_led.on(), self.red_led.off()),
                         'A': lambda : (self.motor.set_duty(100), self.white_led.off(), self.blue_led.off(), self.green_led.off(), self.red_led.on()),
                         '4': lambda : (self.change_wind(self.NATURAL_WIND)),
                         '5': lambda : (self.change_wind(self.SLEEP_WIND)),
                         '6': lambda : (self.change_wind(self.NORMAL_WIND)),
                         'D': lambda : (self.motor.set_duty(0), self.white_led.off(), self.blue_led.off(), self.green_led.off(), self.red_led.off())        
                         }   
        
    def change_wind(self, wind_type):
        while self.key != None:
            if self.key == '4' or self.key == '5' or self.key == '6':
                self.motor.start()
                utime.sleep(wind_type)
            else:
                break

    def run(self):
        while True:
            self.motor.start()
            self.key = self.keyboard.get_key()
            if self.key in self.key_motor_map:
                self.key_motor_map[self.key]()   
            
                
        
if __name__ == '__main__':
    main = Main()
    main.run()

