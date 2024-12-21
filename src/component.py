import machine, utime

RED_LED = 4
BLUE_LED = 6

class LED():
    def __init__(self, pin):
        self.led = machine.Pin(pin, machine.Pin.OUT)

    def on(self):
        self.led.on()

    def off(self):
        self.led.off()

class Keyboard():
    def __init__(self, row_pins=[16,17,18,19], col_pins=[20,21,22,26]):
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

        # To debounce the keys
        self.debounce_time = 20
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