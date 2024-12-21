import machine, utime

class LED():
    # LED Pin Configurations
    GREEN_LED = 3
    RED_LED = 4
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
    MOTOR = 15
    def __init__(self, pin):
        self.motor = machine.PWM(machine.Pin(pin))
        self.motor.freq(10000)
        self.motor.duty_u16(0)

    def set_duty(self, duty):
        duty = int(duty/100*65535)
        self.motor.duty_u16(duty)
        print('Motor speed: ', duty)

class Keyboard():
    # Keyboard Matrix Configuration
    ROW_PINS = [16, 17, 18, 19]
    COL_PINS = [20, 21, 22, 26]

    # Timing Configuration
    DEBOUNCE_TIME = 20

    def __init__(self, row_pins, col_pins, debounce_time):
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
    def __init__(self):
        self.green_led = LED(LED.GREEN_LED)
        self.red_led = LED(LED.RED_LED)
        self.blue_led = LED(LED.BLUE_LED)
        self.white_led = LED(LED.WHITE_LED)
        self.keyboard = Keyboard(Keyboard.ROW_PINS, Keyboard.COL_PINS, Keyboard.DEBOUNCE_TIME)   
        self.motor = Motor_ctrl(Motor_ctrl.MOTOR)

        self.key_motor_map = {
                         '1': lambda : (self.motor.set_duty(30) and self.white_led.on() and self.blue_led.off() and self.green_led.off()  and self.red_led.off()),
                         '2': lambda : (self.motor.set_duty(60) and self.white_led.off() and self.blue_led.on() and self.green_led.off()  and self.red_led.off()),
                         '3': lambda : (self.motor.set_duty(80) and self.white_led.off() and self.blue_led.off() and self.green_led.on()  and self.red_led.off()),
                         'A': lambda : (self.motor.set_duty(100) and self.white_led.off() and self.blue_led.off() and self.green_led.off()  and self.red_led.on()),
                         }   

    # def natural_wind(self, duty):
    #     self.motor.set_duty(duty)
    #     utime.sleep(1)
    #     self.motor.set_duty(0)
    #     utime.sleep(1)

    # def sleep_wind(self, duty):
    #     self.motor.set_duty(duty)
    #     utime.sleep(2)
    #     self.motor.set_duty(0)
    #     utime.sleep(2)

    # def normal_wind(self, duty):
    #     self.motor.set_duty(duty)

    def run(self):
        while True:
            key = self.keyboard.get_key()
            print(key)

            # Control the motor speed
            if key in self.key_motor_map:
                self.key_motor_map[key]()
            
            
                
        
if __name__ == '__main__':
    main = Main()
    main.run()

