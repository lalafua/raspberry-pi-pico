import machine, utime

class LED():
    # LED Pin Configurations
    GREEN_LED = 3
    RED_LED = 4
    BLUE_LED = 6

    def __init__(self, pin):
        self.led = machine.Pin(pin, machine.Pin.OUT)

    def on(self):
        self.led.on()

    def off(self):
        self.led.off()

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
        self.cols = [machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP) for pin in col_pins]
        
        # Define keymap
        self.keymap = [
            ['1', '2', '3', 'A'],
            ['4', '5', '6', 'B'],
            ['7', '8', '9', 'C'],
            ['*', '0', '#', 'D']
        ]
        self.debounce_time = debounce_time  
        self.last_press_time = 0
        
    def scan(self):
        key = None
        current_time = utime.ticks_ms()
        
        # Debounce
        if utime.ticks_ms() - self.last_press_time < self.debounce_time:
            return None
        
        # Scan
        for i, row in enumerate(self.rows):
            row.on()
            for j, col in enumerate(self.cols):
                if col.value():
                    self.last_press_time = current_time
                    row.off()
                    key = self.keymap[i][j]
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

        self.keyboard = Keyboard(Keyboard.ROW_PINS, Keyboard.COL_PINS, Keyboard.DEBOUNCE_TIME)   

    def run(self):
        while True:
            print(self.keyboard.get_key())
            utime.sleep(0.1)
            if self.keyboard.get_key() == '1':
                self.green_led.on()
                self.blue_led.off()
                self.red_led.off()
            elif self.keyboard.get_key() == '2':
                self.green_led.off()
                self.blue_led.on()
                self.red_led.off()
            elif self.keyboard.get_key() == '3':
                self.green_led.off()
                self.blue_led.off()
                self.red_led.on()
            elif self.keyboard.get_key() == None:
                self.green_led.off()
                self.blue_led.off()
                self.red_led.off()
            else:
                self.green_led.off()
                self.blue_led.off()
                self.red_led.off()
                
                
        
if __name__ == '__main__':
    main = Main()
    main.run()

