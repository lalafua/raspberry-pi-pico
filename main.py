import component
from config import *


class Main:
    def __init__(self):
        self.green_led = component.LED(GREEN_LED)
        self.red_led = component.LED(RED_LED)
        self.blue_led = component.LED(BLUE_LED)

        self.keyboard = component.Keyboard(ROW_PINS, COL_PINS, DEBOUNCE_TIME)   

    def run(self):
        while True:
            self.blue_led.on()
                
        
if __name__ == '__main__':
    main = Main()
    main.run()