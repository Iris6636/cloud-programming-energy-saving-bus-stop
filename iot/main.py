# ? ??????????????????????? MQTT ????

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient, AWSIoTMQTTShadowClient
import time
import json
import base64
import board
import adafruit_ssd1306
import smbus2
from PIL import Image, ImageDraw, ImageFont
from picamera2 import Picamera2
import traceback
import RPi.GPIO as GPIO
import threading

# --- PIR Sensor ---
PIR_PIN = 26
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)

camera_lock = threading.Lock()

# ??? Picamera2??????
picam2 = Picamera2()
picam2.configure(picam2.create_still_configuration(main={"size": (640, 480)}))
picam2.start()
time.sleep(2)
print("Camera initialized")

def take_and_send_photo_via_mqtt():
    if not camera_lock.acquire(blocking=False):
        print("Camera is busy, skipping photo.")
        return

    try:
        timestamp = int(time.time())
        filename = f"/tmp/NTHU-{timestamp}.jpg"
        mqtt_topic = "device/camera/image"

        picam2.capture_file(filename)
        print(f"Photo captured: {filename}")

        with open(filename, "rb") as image_file:
            image_bytes = image_file.read()
            encoded_image = base64.b64encode(image_bytes).decode('utf-8')

        payload = {
            "filename": f"NTHU-{timestamp}.jpg",
            "image_data": encoded_image
        }

        myMQTTClient.publish(mqtt_topic, json.dumps(payload), 1)
        print(f"Image published to topic: {mqtt_topic}")

    except Exception as e:
        print(f"Camera or publish error: {e}")
        traceback.print_exc()

    finally:
        camera_lock.release()

# --- OLED ?? ---
i2c = board.I2C()
I2C_ADDR = 0x3C
bus = smbus2.SMBus(1)
oled = None

try:
    oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=I2C_ADDR)
except RuntimeError as e:
    print(f"OLED initialization failed: {e}")

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
    if oled is None:
        return
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        print("Font not found, using default.")
        font = ImageFont.load_default()
    image = Image.new('1', (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    draw.text((x, y), text, 1, font=font)
    oled.image(image)
    oled.show()

def clear_oled():
    if oled is not None:
        oled.fill(0)
        oled.show()

last_displayed_text = None
def display_text_if_changed(new_text):
    global last_displayed_text
    if new_text != last_displayed_text:
        clear_oled()
        display_text_on_oled(new_text, 0, 10)
        last_displayed_text = new_text

# --- ??????? ---
battery = 50
def detect_light():
    return True

def update_battery(light_detected):
    global battery
    battery = min(100, battery + 1) if light_detected else max(0, battery - 1)
    return battery

DEVICE_ADDRESS = 0x23
ONE_TIME_HIGH_RES_MODE_1 = 0x20
bus = smbus2.SMBus(1)

def read_light(addr=DEVICE_ADDRESS):
    data = bus.read_i2c_block_data(addr, ONE_TIME_HIGH_RES_MODE_1, 2)
    count = (data[1] + (256 * data[0])) / 1.2
    return count

def map_light_to_brightness(lux):
    if lux > 800: return 255
    if lux > 500: return 180
    if lux > 200: return 120
    if lux > 50:  return 80
    return 10

def set_oled_brightness(brightness):
    try:
        bus.write_byte_data(I2C_ADDR, 0x00, 0x81)
        bus.write_byte_data(I2C_ADDR, 0x00, brightness)
        print(f"OLED brightness set to: {brightness}")
    except Exception as e:
        print(f"Brightness setting failed: {e}")

# --- AWS IoT ?? ---
endpoint = "a1ebcaquqh9vk4-ats.iot.us-east-1.amazonaws.com"
rootCAPath = "/home/team6/Downloads/CP/AmazonRootCA1.pem"
certificatePath = "/home/team6/Downloads/CP/099829d333d212702545ca498091208c3dd6b5480fd0583505c71836e8566736-certificate.pem"
privateKeyPath = "/home/team6/Downloads/CP/private.pem.key"
thingName = "MyThing-113065528"
subscribeTopic = "my/subscribetopic"

myMQTTClient = AWSIoTMQTTClient("myMQTTClientID")
myMQTTClient.configureEndpoint(endpoint, 8883)
myMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)
myMQTTClient.configureConnectDisconnectTimeout(10)
myMQTTClient.configureMQTTOperationTimeout(10)

myShadowClient = AWSIoTMQTTShadowClient("myShadowClientID")
myShadowClient.configureEndpoint(endpoint, 8883)
myShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)
myShadowClient.configureConnectDisconnectTimeout(10)
myShadowClient.configureMQTTOperationTimeout(10)

try:
    myMQTTClient.connect()
    myShadowClient.connect()
    print("Connected to AWS IoT Core & Shadow")
except Exception as e:
    print(f"MQTT/Shadow connection failed: {e}")
    exit()

def customCallback(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode('utf-8'))
        if payload.get("action") == "take_picture":
            take_and_send_photo_via_mqtt()
    except Exception as e:
        print(f"customCallback error: {e}")

myMQTTClient.subscribe(subscribeTopic, 1, customCallback)

def shadowUpdateCallback(payload, responseStatus, token):
    print(f"[shadowUpdate] Status: {responseStatus}")
    if responseStatus == "accepted":
        print(json.dumps(json.loads(payload), indent=2))

def shadowGetCallback(payload, responseStatus, token):
    if responseStatus == "accepted":
        parsed = json.loads(payload)
        motion = GPIO.input(PIR_PIN)
        if oled and "text" in parsed.get("state", {}).get("desired", {}).get("oled", {}):
            if motion:
                display_text_if_changed(parsed["state"]["desired"]["oled"]["text"])
        if oled and "power" in parsed.get("state", {}).get("desired", {}).get("oled", {}):
            power = parsed["state"]["desired"]["oled"]["power"]
            turn_on_oled_display() if power == "on" else turn_off_oled_display()

def shadowDeltaCallback(payload, responseStatus, token):
    parsed = json.loads(payload)
    motion = GPIO.input(PIR_PIN)
    if oled and "text" in parsed.get("state", {}).get("oled", {}):
        if motion:
            display_text_if_changed(parsed["state"]["oled"]["text"])
    if oled and "power" in parsed.get("state", {}).get("oled", {}):
        power = parsed["state"]["oled"]["power"]
        turn_on_oled_display() if power == "on" else turn_off_oled_display()

deviceShadowHandler = myShadowClient.createShadowHandlerWithName(thingName, True)
deviceShadowHandler.shadowRegisterDeltaCallback(shadowDeltaCallback)

# --- Main Loop ---
try:
    while True:
        motion = GPIO.input(PIR_PIN)
        print(f"[PIR] Motion: {motion}")

        oled_raw_status = read_oled_status()
        oled_power = "on" if oled_raw_status and oled_raw_status != 0x44 else "off"

        if motion and oled_power == "on":
            take_and_send_photo_via_mqtt()
        else:
            print("Skip photo")

        lux = read_light()
        set_oled_brightness(map_light_to_brightness(lux))

        battery = update_battery(detect_light())
        print(f"[SIM] Battery: {battery}")

        shadowPayload = json.dumps({
            "state": {
                "reported": {
                    "presence": bool(motion),
                    "light": "true",
                    "electricity": battery,
                    "oled": {
                        "power": oled_power,
                    }
                }
            }
        })
        deviceShadowHandler.shadowUpdate(shadowPayload, shadowUpdateCallback, 5)
        deviceShadowHandler.shadowGet(shadowGetCallback, 5)

        time.sleep(15)

except KeyboardInterrupt:
    print("Interrupted by user")

finally:
    GPIO.cleanup()
