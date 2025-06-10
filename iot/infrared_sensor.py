from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient, AWSIoTMQTTShadowClient
import RPi.GPIO as GPIO
import time
import json

# === PIR Sensor Setup ===
PIR_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)

# === AWS IoT Config ===
endpoint = "a1ebcaquqh9vk4-ats.iot.us-east-1.amazonaws.com"
rootCAPath = "/home/team6/Downloads/CP/AmazonRootCA1.pem"
certificatePath = "/home/team6/Downloads/CP/099829d333d212702545ca498091208c3dd6b5480fd0583505c71836e8566736-certificate.pem"
privateKeyPath = "/home/team6/Downloads/CP/private.pem.key"
thingName = "MyThing-113065528"
clientId = "pirShadowClient"

# === Init MQTT Client ===
mqttClient = AWSIoTMQTTClient(clientId)
mqttClient.configureEndpoint(endpoint, 8883)
mqttClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)
mqttClient.configureConnectDisconnectTimeout(10)
mqttClient.configureMQTTOperationTimeout(5)

# === Init Shadow Client ===
shadowClient = AWSIoTMQTTShadowClient(clientId + "Shadow")
shadowClient.configureEndpoint(endpoint, 8883)
shadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)
shadowClient.configureConnectDisconnectTimeout(10)
shadowClient.configureMQTTOperationTimeout(5)

# === Connect to AWS ===
try:
    mqttClient.connect()
    print("Connected to AWS IoT Core")
    shadowClient.connect()
    print("Connected to AWS IoT Shadow")
except Exception as e:
    print(f"Connection failed: {e}")
    GPIO.cleanup()
    exit()

# === Create Shadow Handler ===
deviceShadowHandler = shadowClient.createShadowHandlerWithName(thingName, True)

# === Shadow Delta Callback (not used, but good practice) ===
def shadowDeltaCallback(payload, responseStatus, token):
    print("Received delta update:")
    print(json.dumps(json.loads(payload), indent=2))

# === Shadow Update Callback ===
def shadowUpdateCallback(payload, responseStatus, token):
    if responseStatus == "accepted":
        print("Shadow update successful")
    elif responseStatus == "rejected":
        print("Shadow update rejected")
    elif responseStatus == "timeout":
        print("Shadow update timeout")

# Register delta (optional)
deviceShadowHandler.shadowRegisterDeltaCallback(shadowDeltaCallback)

# === Main Loop: Read PIR & Update Shadow ===
try:
    while True:
        motion = bool(GPIO.input(PIR_PIN))
        payload = {
            "state": {
                "reported": {
                    "presence": motion
                }
            }
        }
        shadowJSON = json.dumps(payload)
        print(f"Updating shadow: {shadowJSON}")
        deviceShadowHandler.shadowUpdate(shadowJSON, shadowUpdateCallback, 5)
        time.sleep(5)

except KeyboardInterrupt:
    print("Stopped by user.")
finally:
    GPIO.cleanup()
