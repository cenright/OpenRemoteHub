""" keyboard.py """
import threading
import evdev
from evdev import InputDevice
from evdev.ecodes import EV_KEY

class KeyEvent:
    def __init__(self):
        self.keycode = 0
        self.scancode = 0
        self.keyvalue = 0


class Keyboard:
    """main class"""

    def __init__(self, input_device_path, grab, command_queue):
        self.input_device_path = input_device_path
        self.command_queue = command_queue
        self.long_press_limit = 1.0
        self.keyboard = InputDevice(self.input_device_path)
        if grab:
            self.keyboard.grab()
        self.lastval = 0
        self.lastEvent = None
    
    def start(self):
        """start"""
        key_press_time = None
        long_press_timer = None

        for event in self.keyboard.read_loop():

            if(event.code == 4 and event.type == 4):
                lastval = event.value
                lastEvent = event

            # read_loop will return all types of input,
            # so we want to only look at keyboard presses
            if event.type == EV_KEY:
               
               
                cat = evdev.categorize(event)
                keycode = cat.keycode
                #event.keycode = keycode
                #event.scancode = event.value
                keyEvent = KeyEvent
                keyEvent.keycode = keycode
                keyEvent.scancode = event.code
                keyEvent.keyvalue = event.code
                
                if(event.timestamp() == lastEvent.timestamp()):
                    keyEvent.scancode = lastEvent.value
                
                if event.value == 1:
                    #event.keystate = "down"
                    keyEvent.keystate = "down"
                    key_press_time = event.timestamp()
                    long_press_timer = threading.Timer(
                        #self.long_press_limit, self.handle_long_press, args=[event.code]
                        self.long_press_limit, self.handle_long_press_event, args=[keyEvent]
                    )
                    
                    self.command_queue.put(
                            #{"scancode": event.code, "keystate": "down", "long_press": False}
                            self.getcommand(keyEvent.keycode, keyEvent.keystate, keyEvent.keyvalue, False, keyEvent.scancode)
                        )
                    
                    long_press_timer.start()
                            
                elif event.value == 0:
                    #event.keystate = "up"
                    keyEvent.keystate = "up"
                           
                    if key_press_time is not None:
                        key_release_time = event.timestamp()
                        time_elapsed = key_release_time - key_press_time
                        if long_press_timer and long_press_timer.is_alive():
                            long_press_timer.cancel()
                        if time_elapsed < self.long_press_limit:
                            self.command_queue.put(
                                #{"scancode": event.code, "keystate": "up", "long_press": False}
                                #self.getcommand(event.keycode, event.keystate, event.value, False, event.scancode)
                                self.getcommand(keyEvent.keycode, keyEvent.keystate, keyEvent.keyvalue, False, keyEvent.scancode)
                            )
                    key_press_time = None
                    long_press_timer = None

    def handle_long_press(self, code, long_press=True):
        """handle long press"""
        self.command_queue.put({"scancode": code, "keystate": "up", "long_press": long_press})

    def handle_long_press_event(self, event, keystate = "up", long_press=True):
        """handle long press"""
        self.command_queue.put(
                    self.getcommand(event.keycode, keystate, event.keyvalue, long_press, event.scancode)
                           # self.getcommand(keyEvent.keycode, keyEvent.keystate, keyEvent.keyvalue, False, keyEvent.scancode)
                            )

    def getcommand(self, keycode, keystate, keyvalue, long_press, scancode):
        return {"keycode": keycode, "keystate": keystate, "keyvalue": keyvalue, "long_press": long_press, "scancode": scancode}


    def stop(self):
        """stop"""
        self.keyboard.close()
        
        
import queue
from command_processor import CommandProcessor

command_queue = queue.Queue()

command_processor = CommandProcessor(
    #command_queue, "common.json", "scripts/plugins", 60
    command_queue, "common.json", "plugins", 60
)

keyboard = Keyboard("/dev/input/event1", True, command_queue)

keyboard_thread = threading.Thread(target=keyboard.start)
keyboard_thread.start()

keyboard2 = Keyboard("/dev/input/event2", True, command_queue)

keyboard_thread2 = threading.Thread(target=keyboard2.start)
keyboard_thread2.start()


command_processor_thread = threading.Thread(target=command_processor.start)
command_processor_thread.start()

keyboard_thread.join()
keyboard_thread2.join()
command_processor_thread.join()

        