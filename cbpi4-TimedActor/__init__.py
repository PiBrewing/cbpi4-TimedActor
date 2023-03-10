import asyncio
import logging
from unittest.mock import MagicMock, patch

from cbpi.api import *


logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
except Exception:
    logger.warning("Failed to load RPi.GPIO. Using Mock instead")
    MockRPi = MagicMock()
    modules = {
        "RPi": MockRPi,
        "RPi.GPIO": MockRPi.GPIO
    }
    patcher = patch.dict("sys.modules", modules)
    patcher.start()
    import RPi.GPIO as GPIO

mode = GPIO.getmode()
if (mode == None):
    GPIO.setmode(GPIO.BCM)

@parameters([Property.Select(label="GPIO", options=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27]), 
             Property.Select(label="Inverted", options=["Yes", "No"],description="No: Active on high; Yes: Active on low"),
             Property.Number(label="OnTime", description="Time in seconds for Actor onTime (Default:5)"),
             Property.Number(label="OffTime", description="Time in seconds for Actor offTime (Default:5)")])
class TimedActor(CBPiActor):

    # Custom property which can be configured by the user
    #@action("Set Power", parameters=[Property.Number(label="Power", configurable=True,description="Power Setting [0-100]")])
    #async def setpower(self,Power = 100 ,**kwargs):
    #    self.power=int(Power)
    #    if self.power < 0:
    #        self.power = 0
    #    if self.power > 100:
    #        self.power = 100           
    #    await self.set_power(self.power)      

    def get_GPIO_state(self, state):
        # ON
        if state == 1:
            return 1 if self.inverted == False else 0
        # OFF
        if state == 0:
            return 0 if self.inverted == False else 1

    async def on_start(self):
        self.power = None
        self.gpio = self.props.GPIO
        self.inverted = True if self.props.get("Inverted", "No") == "Yes" else False
        self.onTime = int(self.props.get("OnTime", 5))
        self.offTime = int(self.props.get("OffTime", 5))
        GPIO.setup(self.gpio, GPIO.OUT)
        GPIO.output(self.gpio, self.get_GPIO_state(0))
        self.state = False
        self.ActorRunning=False

    async def on(self, power = None):
        #if power is not None:
        #    self.power = power
        #else: 
        #    self.power = 100
#        await self.set_power(self.power)

        logger.warning("ACTOR %s ON - GPIO %s " %  (self.id, self.gpio))
        GPIO.output(self.gpio, self.get_GPIO_state(1))  
        self.state = True
        self.ActorRunning=True


    async def off(self):
        logger.warning("ACTOR %s OFF - GPIO %s " % (self.id, self.gpio))
        GPIO.output(self.gpio, self.get_GPIO_state(0))
        self.state = False
        self.ActorRunning=False

    def get_state(self):
        return self.state
    
    async def run(self):
        while self.running == True:
            if self.ActorRunning == True:
                if self.onTime > 0:
                    GPIO.output(self.gpio, self.get_GPIO_state(1))
                    self.state=True
                    await self.cbpi.actor.ws_actor_update()
                    await asyncio.sleep(self.onTime)
                if self.offTime > 0:
                    GPIO.output(self.gpio, self.get_GPIO_state(0))
                    self.state = False
                    await self.cbpi.actor.ws_actor_update()
                    await asyncio.sleep(self.offTime)
            else:
                await asyncio.sleep(1)

    async def set_power(self, power):
        self.power = power
        await self.cbpi.actor.actor_update(self.id,power)
        pass
            

def setup(cbpi):

    '''
    This method is called by the server during startup 
    Here you need to register your plugins at the server
    
    :param cbpi: the cbpi core 
    :return: 
    '''

    cbpi.plugin.register("TimedActor", TimedActor)
    