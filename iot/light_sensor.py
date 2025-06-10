from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import RPi.GPIO as GPIO
import time
import json

# === Light Sensor (Digital Output) ===
LIGHT_PIN = 27
GPIO.setmode(GPIO.BCM)
GPIO.setup(LIGHT_PIN, GPIO.IN)

# === AWS IoT Core Configuration ===
endpoint = "a1ebcaquqh9vk4-ats.iot.us-east-1.amazonaws.com"
rootCAPath = "/home/team6/Downloads/CP/AmazonRootCA1.pem"
certificatePath = "/home/team6/Downloads/CP/099829d333d212702545ca498091208c3dd6b5480fd0583505c71836e8566736-certificate.pem"
privateKeyPath = "/home/team6/Downloads/CP/private.pem.key"
clientId = "lightSensorClient"
thingName = "MyThing-113065528"
topic = "113065528/light"

# === Initialize MQTT Client ===
mqttClient = AWSIoTMQTTClient(clientId)
mqttClient.configureEndpoint(endpoint, 8883)
mqttClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)
mqttClient.configureConnectDisconnectTimeout(10)
mqttClient.configureMQTTOperationTimeout(5)

# === Connect to AWS IoT Core ===
try:
    mqttClient.connect()
    print("Connected to AWS IoT Core")
except Exception as e:
    print(f"Connection failed: {e}")
    exit()

# === Light Monitoring Loop ===
try:
    while True:
        light_value = GPIO.input(LIGHT_PIN)
        light_state = "bright" if light_value == 1 else "dark"

        payload = {
            "thing": thingName,
            "timestamp": time.time(),
            "light": light_state
        }

        mqttClient.publish(topic, json.dumps(payload), 1)
        print(f"Published to {topic}: {payload}")

        time.sleep(3)
except KeyboardInterrupt:
    print("Stopped by user")
finally:
    GPIO.cleanup()
