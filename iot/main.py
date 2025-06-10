
# This version can successfully control OLED power ON/OFF via AWS IoT Shadow
# 0505: Brightness control added

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import time
import json
import base64
import board
import adafruit_ssd1306
import smbus2
from PIL import Image, ImageDraw, ImageFont

from picamera2 import Picamera2
import boto3

# --- Take photo and upload to S3 ---
def take_and_send_photo_via_mqtt():
    timestamp = int(time.time())
    filename = f"/tmp/NTHU-{timestamp}.jpg"
    mqtt_topic = "device/camera/image"

    try:
        # 拍照存檔
        picam2 = Picamera2()
        picam2.start()
        time.sleep(2)
        picam2.capture_file(filename)
        print(f"Photo captured: {filename}")
        picam2.close()

        # 讀檔並轉 base64
        with open(filename, "rb") as image_file:
            image_bytes = image_file.read()
            encoded_image = base64.b64encode(image_bytes).decode('utf-8')

        # 組成 MQTT payload
        payload = {
            "filename": f"NTHU-{timestamp}.jpg",
            "image_data": encoded_image
        }

        # 發送 MQTT 到新的 topic
        myMQTTClient.publish(mqtt_topic, json.dumps(payload), 1)
        print(f"Image published to topic: {mqtt_topic}")

    except Exception as e:
        print(f"Camera or publish error: {e}")
        return




# --- OLED Configuration ---
i2c = board.I2C()
I2C_ADDR = 0x3C
bus = smbus2.SMBus(1)
oled = None
try:
    oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=I2C_ADDR)
except RuntimeError as e:
    print(f"OLED initialization failed: {e}. Check I2C connection and address.")

def turn_on_oled_display():
    try:
        bus.write_byte_data(I2C_ADDR, 0x00, 0xAF)
        print("OLED ON command sent")
    except Exception as e:
        print(f"Error turning OLED ON: {e}")

def turn_off_oled_display():
    try:
        bus.write_byte_data(I2C_ADDR, 0x00, 0xAE)
        print("OLED OFF command sent")
    except Exception as e:
        print(f"Error turning OLED OFF: {e}")

def read_oled_status():
    try:
        bus.write_byte_data(I2C_ADDR, 0x00, 0x00)
        time.sleep(0.01)
        response = bus.read_byte(I2C_ADDR)
        print(f"OLED status: {bin(response)} (0x{response:02X})")
        return response
    except Exception as e:
        print(f"Error reading OLED status: {e}")
        return None

font_path = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'

def display_text_on_oled(text, x, y, font_size=16, font_path=font_path):
    global oled
    if oled is None:
        return
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        print(f"Font {font_path} not found, using default.")
        font = ImageFont.load_default()
    image = Image.new('1', (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    draw.text((x, y), text, 1, font=font)
    oled.image(image)
    oled.show()

def clear_oled():
    global oled
    if oled is not None:
        oled.fill(0)
        oled.show()

last_displayed_text = None

def display_text_if_changed(new_text):
    global last_displayed_text
    if new_text != last_displayed_text:
        clear_oled()
        display_text_on_oled(new_text, 0, 10, font_size=16)
        last_displayed_text = new_text

# --- Simulated Battery ---
battery = 50

def detect_light():
    return True

def update_battery(light_detected):
    global battery
    if light_detected:
        battery = min(100, battery + 1)
    else:
        battery = max(0, battery - 1)
    return battery

# --- Light Sensor ---
import smbus
DEVICE_ADDRESS = 0x23
ONE_TIME_HIGH_RES_MODE_1 = 0x20
bus = smbus.SMBus(1)

def read_light(addr=DEVICE_ADDRESS):
    data = bus.read_i2c_block_data(addr, ONE_TIME_HIGH_RES_MODE_1, 2)
    count = (data[1] + (256 * data[0])) / 1.2
    return count

def map_light_to_brightness(lux_value):
    if lux_value > 800:
        return 255
    elif lux_value > 500:
        return 180
    elif lux_value > 200:
        return 120
    elif lux_value > 50:
        return 80
    else:
        return 10

def set_oled_brightness(brightness):
    try:
        bus.write_byte_data(I2C_ADDR, 0x00, 0x81)
        bus.write_byte_data(I2C_ADDR, 0x00, brightness)
        print(f"OLED brightness set to: {brightness}")
    except Exception as e:
        print(f"Brightness setting failed: {e}")

# --- AWS IoT Setup ---
endpoint = "a1ebcaquqh9vk4-ats.iot.us-east-1.amazonaws.com"
rootCAPath = "/home/team6/Downloads/CP/AmazonRootCA1.pem"
certificatePath = "/home/team6/Downloads/CP/099829d333d212702545ca498091208c3dd6b5480fd0583505c71836e8566736-certificate.pem"
privateKeyPath = "/home/team6/Downloads/CP/private.pem.key"
thingName = "MyThing-113065528"

# MQTT ??
publishTopic = "my/publishtopic"
subscribeTopic = "my/subscribetopic"



myMQTTClient = AWSIoTMQTTClient("myMQTTClientID")
myMQTTClient.configureEndpoint(endpoint, 8883)
myMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)
myMQTTClient.configureConnectDisconnectTimeout(10)
myMQTTClient.configureMQTTOperationTimeout(5)

myShadowClient = AWSIoTMQTTShadowClient("myShadowClientID")
myShadowClient.configureEndpoint(endpoint, 8883)
myShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)
myShadowClient.configureConnectDisconnectTimeout(10)
myShadowClient.configureMQTTOperationTimeout(5)

try:
    myMQTTClient.connect()
    print("Connected to AWS IoT Core")
except Exception as e:
    print(f"MQTT connection failed: {e}")
    exit()

try:
    myShadowClient.connect()
    print("Connected to AWS IoT Shadow")
except Exception as e:
    print(f"Shadow connection failed: {e}")
    exit()


def customCallback(client, userdata, message):
    print(f"Message received from topic [{message.topic}]:")
    payload_str = message.payload.decode('utf-8')
    print("@@@@@@@@chchk here")
    print(payload_str)
    try:
        payload = json.loads(payload_str)
        if payload.get("action") == "take_picture":
            take_and_send_photo_via_mqtt()
    except Exception as e:
        print(f"error in customCallback: {e}")


myMQTTClient.subscribe(subscribeTopic, 1, customCallback)
print(f"Subscribed to: {subscribeTopic}")

def shadowUpdateCallback(payload, responseStatus, token):
    if responseStatus == "timeout":
        print("Shadow update timed out")
    elif responseStatus == "accepted":
        print("Shadow update accepted:")
        print(json.dumps(json.loads(payload), indent=2))
    elif responseStatus == "rejected":
        print("Shadow update rejected:")
        print(payload)

def shadowGetCallback(payload, responseStatus, token):
    print(f"!!!!!! shadowGetCallback is called!!!")
    if responseStatus == "timeout":
        print("Shadow GET timed out")
    elif responseStatus == "accepted":
        print("Shadow GET accepted:")
        parsed = json.loads(payload)
        print(json.dumps(parsed, indent=2))
       # ?? OLED ??

        if oled is not None and "state" in parsed and "desired" in parsed["state"] and "oled" in parsed["state"]["desired"] and "text" in parsed["state"]["desired"]["oled"]:

            print(f" Received delta, try to display text: {parsed['state']['desired']['oled']['text']}")
            display_text_if_changed(parsed["state"]["desired"]["oled"]["text"])

            
        #control the on/ off
        if oled is not None and "state" in parsed and "desired" in parsed["state"] and "oled" in parsed["state"]["desired"] and "power" in parsed["state"]["desired"]["oled"]:
            desired_state_power= parsed["state"]["desired"]["oled"]["power"]
            print(f"desired_state_power= {desired_state_power}")
            if desired_state_power == "off":
                clear_oled()
                turn_off_oled_display()
            elif desired_state_power == "on":
                turn_on_oled_display()
    elif responseStatus == "rejected":
        print("Shadow GET rejected:")
        print(payload)


def shadowDeltaCallback(payload, responseStatus, token):

    print("Delta update received:")
    parsed = json.loads(payload)
    print(json.dumps(parsed, indent=2))

    if oled is not None and "state" in parsed and "desired" in parsed["state"] and "oled" in parsed["state"]["desired"] and "text" in parsed["state"]["desired"]["oled"]:
        print(f" Received delta, try to display text: {parsed['state']['desired']['oled']['text']}")
        display_text_if_changed(parsed["state"]["desired"]["oled"]["text"])

    #control the on/ off
    if oled is not None and "state" in parsed and "desired" in parsed["state"] and "oled" in parsed["state"]["desired"] and "power" in parsed["state"]["desired"]["oled"]:
        desired_state_power= parsed["state"]["desired"]["oled"]["power"]
        print(f"desired_state_power= {desired_state_power}")

        if desired_state_power == "off":
            clear_oled()
            turn_off_oled_display()
        elif desired_state_power == "on":
            turn_on_oled_display()

deviceShadowHandler = myShadowClient.createShadowHandlerWithName(thingName, True)
deviceShadowHandler.shadowRegisterDeltaCallback(shadowDeltaCallback)



# Main loop
while True:
    message = {"message": "Hello from Raspberry Pi!", "timestamp": time.time()}
    myMQTTClient.publish(publishTopic, json.dumps(message), 1)
    print(f"Published to {publishTopic}: {message}")

    lux_value = read_light()
    brightness = map_light_to_brightness(lux_value)
    set_oled_brightness(brightness)

    light = detect_light()
    battery = update_battery(light)
    print(f"[SIM] Light: {light}, Battery: {battery}")

    deviceShadowHandler.shadowGet(shadowGetCallback, 5)

    oled_raw_status = read_oled_status()
    oled_power = "on" if oled_raw_status and oled_raw_status != 0x44 else "off"

    shadowPayload = json.dumps({
        "state": {
            "reported": {
                "presence": False,
                "light": "true",
                "electricity": battery,
                "oled": {
                    "power": oled_power,
                },
            }
        }
    })
    print("Sending shadow update:")
    print(shadowPayload)
    deviceShadowHandler.shadowUpdate(shadowPayload, shadowUpdateCallback, 5)

    time.sleep(5)



