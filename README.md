# 節能公車站牌系統｜Energy-Saving Smart Bus Stop

> 有人才亮燈，智慧節能感測系統  
> Intelligent display system that activates only when people are present

---

## 專案簡介｜Project Overview

節能公車站牌系統結合 IoT 感測器與 AWS 雲端服務，當偵測到有人靠近時自動拍照並上傳至雲端儲存。系統透過 PIR 紅外線感測器偵測人流，使用光敏電阻調整 OLED 顯示亮度，並模擬太陽能儲電機制，實現智慧節能的公車站牌顯示系統。

This project integrates IoT sensors with AWS cloud services to create a smart bus stop system. When motion is detected via PIR sensor, the system automatically captures photos and uploads them to cloud storage. The system adjusts OLED brightness based on ambient light and simulates solar energy storage for energy efficiency.

---

## 系統架構｜System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Raspberry Pi                              │
│  ┌──────────┐  ┌────────┐  ┌──────────┐  ┌────────────────┐   │
│  │ PIR      │  │ Camera │  │  OLED    │  │ Light Sensor   │   │
│  │ Sensor   │  │  (V2)  │  │ Display  │  │ (BH1750)       │   │
│  └──────────┘  └────────┘  └──────────┘  └────────────────┘   │
│         │           │            │               │              │
│         └───────────┴────────────┴───────────────┘              │
│                          │                                       │
│                   iot/main.py                                    │
│                   (AWSIoTPythonSDK)                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │ MQTT over TLS
                            │ (每 15 秒更新 Shadow)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AWS IoT Core                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Thing: MyThing-113065528                                 │  │
│  │  Shadow State:                                            │  │
│  │    - presence (bool)                                      │  │
│  │    - light (string)                                       │  │
│  │    - electricity (int, 0-100)                             │  │
│  │    - oled.power (on/off)                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                     │
│              ┌─────────────┴──────────────┐                     │
│              ▼                            ▼                     │
│  ┌─────────────────────┐      ┌─────────────────────┐         │
│  │ Topic Rule 1        │      │ Topic Rule 2        │         │
│  │ PresenceDetected    │      │ CaptureImageToS3    │         │
│  │                     │      │                     │         │
│  │ Trigger: Shadow     │      │ Trigger: MQTT       │         │
│  │ presence false→true │      │ device/camera/image │         │
│  └─────────────────────┘      └─────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
              │                            │
              │                            │
              ▼                            ▼
┌─────────────────────┐        ┌─────────────────────┐
│ AWS Lambda          │        │ AWS Lambda          │
│ busstop-            │        │ busstop-            │
│ PresenceTov2        │        │ v2Base64toS3        │
│                     │        │                     │
│ Action:             │        │ Action:             │
│ Publish MQTT        │        │ Decode base64       │
│ command to          │        │ Upload to S3        │
│ my/subscribetopic   │        │                     │
└─────────────────────┘        └─────────────────────┘
              │                            │
              │                            │
              ▼                            ▼
       (Back to Pi)              ┌─────────────────────┐
      Take photo & send          │     AWS S3          │
                                 │  busstop-images-*   │
                                 │  photos/            │
                                 │  NTHU-{time}.jpg    │
                                 └─────────────────────┘
```

### 運作流程｜Workflow

1. **感測與回報：** Raspberry Pi 每 15 秒偵測 PIR 人流、光照強度，並更新 AWS IoT Thing Shadow
2. **觸發拍照：** 當 `presence` 從 `false` 變為 `true`，IoT Rule 觸發 Lambda 函式 `busstop-PresenceTov2`
3. **發送指令：** Lambda 發布 MQTT 訊息 `{"action": "take_picture"}` 到 `my/subscribetopic`
4. **拍照上傳：** Raspberry Pi 收到指令後拍照，將 base64 編碼圖片發送至 `device/camera/image` topic
5. **儲存至雲端：** IoT Rule 觸發 `busstop-v2Base64toS3` Lambda，解碼圖片並上傳至 S3 bucket

---

## 硬體元件｜Hardware Components

| 元件 | 型號/規格 | 用途 |
|------|----------|------|
| **Raspberry Pi** | Pi 3/4 | 主控制器，執行 IoT 程式 |
| **Camera Module** | Picamera2 (V2) | 拍攝公車站牌照片 |
| **PIR Sensor** | HC-SR501 | 偵測人體紅外線，判斷是否有人靠近 |
| **OLED Display** | SSD1306 (128×64, I2C) | 顯示公車資訊與電量狀態 |
| **Light Sensor** | BH1750 (I2C) | 偵測環境光照，調整螢幕亮度 |

### GPIO 接腳配置

- **PIR Sensor:** GPIO 26 (BCM)
- **OLED Display:** I2C (SDA/SCL, address: 0x3C)
- **Light Sensor:** I2C (address: 0x23)

---

## AWS 服務架構｜AWS Services

| 服務 | 資源名稱 | 用途 |
|------|---------|------|
| **AWS IoT Core** | Thing: `MyThing-113065528` | 裝置連線、Shadow 狀態管理、MQTT 訊息路由 |
| **IoT Topic Rules** | `busstop_PresenceDetected`<br>`busstop_CaptureImageToS3` | 自動化事件處理，觸發 Lambda 函式 |
| **AWS Lambda** | `busstop-PresenceTov2`<br>`busstop-v2Base64toS3` | 無伺服器運算：發送拍照指令、上傳圖片至 S3 |
| **Amazon S3** | `busstop-images-*` | 儲存拍攝的公車站牌照片 |
| **AWS IAM** | `busstop-lambda-exec-role` | Lambda 函式執行權限（IoT Publish, S3 PutObject, CloudWatch Logs） |

**本專案不使用：** DynamoDB, API Gateway, Cognito, SNS

---

## 專案結構｜Repository Structure

```
cloud-programming-energy-saving-bus-stop/
├── README.md                           # 專案說明文件（本檔案）
│
├── iot/                                # Raspberry Pi IoT 裝置程式
│   └── main.py                         # 主程式：感測器控制、MQTT 通訊、Shadow 更新
│
├── backend/
│   ├── lambda_functions/               # Lambda 函式原始碼
│   │   ├── PresenceTov2.py            # 偵測到人流時發送拍照指令
│   │   └── v2Base64toS3.py            # 接收 base64 圖片並上傳 S3
│   └── api_gateway/                    # (預留，目前未使用)
│
├── deployment/
│   ├── lambda/                         # Lambda 部署用 ZIP 檔案
│   │   ├── PresenceTov2.zip
│   │   └── v2Base64toS3.zip
│   │
│   └── infra/                          # Terraform 基礎設施定義
│       ├── main.tf                     # AWS Provider 設定
│       ├── variables.tf                # 輸入變數（region, S3 bucket name）
│       ├── outputs.tf                  # 輸出值（IoT endpoint, Thing name）
│       ├── iam.tf                      # Lambda 執行角色與權限
│       ├── lambda.tf                   # Lambda 函式資源
│       ├── s3.tf                       # S3 bucket 資源
│       ├── iot.tf                      # IoT Thing、Topic Rules、Device Policy
│       └── terraform.tfvars.example    # 變數範本檔案
│
├── docs/
│   └── deployment_guide.md             # 詳細部署指南
│
├── web/                                # 前端網頁（預留，目前未使用）
│
└── config/                             # IoT 憑證與設定檔（本地存放，不上傳 Git）
    ├── AmazonRootCA1.pem               # AWS IoT Root CA
    ├── {cert-id}-certificate.pem       # 裝置憑證
    └── private.pem.key                 # 私鑰
```

---

## 快速開始｜Quick Start

### 前置需求

- AWS 帳號（具備管理員權限）
- Terraform >= 1.0
- AWS CLI v2
- Python 3.9+
- Raspberry Pi (已連接 PIR、Camera、OLED、Light Sensor)

### 部署步驟

完整部署指南請參閱 **[docs/deployment_guide.md](docs/deployment_guide.md)**

簡易流程：

```bash
# 1. Clone 專案
git clone https://github.com/Iris6636/cloud-programming-energy-saving-bus-stop.git
cd cloud-programming-energy-saving-bus-stop

# 2. 設定 Terraform 變數
cd deployment/infra
cp terraform.tfvars.example terraform.tfvars
# 編輯 terraform.tfvars，設定 S3 bucket 名稱（必須全球唯一）

# 3. 部署 AWS 基礎設施
terraform init
terraform plan
terraform apply

# 4. 記錄輸出的 IoT endpoint
terraform output iot_endpoint

# 5. 更新 Raspberry Pi 程式碼中的 endpoint
# 編輯 iot/main.py 第 162 行，填入新的 IoT endpoint

# 6. 在 AWS Console 產生新的 IoT 憑證並下載
# 將憑證上傳至 Raspberry Pi 的 /home/team6/Downloads/CP/

# 7. 在 Raspberry Pi 上執行 IoT 程式
cd iot
python3 main.py
```

---

## 核心功能｜Key Features

### 智慧人流偵測
- 使用 PIR 紅外線感測器偵測人體移動
- 偵測到人流時自動觸發拍照功能
- Shadow state 每 15 秒更新一次，即時反映裝置狀態

### 自動拍照上傳
- 當 `presence` 從 false 變為 true 時自動觸發
- 使用 Picamera2 拍攝 640×480 解析度照片
- Base64 編碼後透過 MQTT 傳輸至雲端
- Lambda 自動解碼並儲存至 S3

### 環境感知亮度調整
- BH1750 光感測器即時偵測環境光照（單位：lux）
- 自動調整 OLED 顯示亮度（10-255），節省電力
- 光照映射邏輯：
  - > 800 lux → 255 (最亮)
  - 500-800 lux → 180
  - 200-500 lux → 120
  - 50-200 lux → 80
  - < 50 lux → 10 (最暗)

### 模擬太陽能儲電
- 模擬電池電量（0-100%）
- 偵測到光照時充電（+1% per cycle）
- 無光照時放電（-1% per cycle）
- 電量狀態透過 Shadow 回報至雲端

---

## 技術特點｜Technical Highlights

### Infrastructure as Code
- 完整使用 Terraform 管理所有 AWS 資源
- 可重複部署，易於遷移至不同 AWS 帳號
- 版本控制，追蹤基礎設施變更歷史

### Serverless Architecture
- 無需管理伺服器，Lambda 自動擴展
- 按使用量計費，低成本運行
- 高可用性，AWS 自動處理容錯

### Event-Driven Design
- IoT Shadow state change 觸發 Lambda
- MQTT pub/sub 實現裝置與雲端解耦
- 非同步處理，即時回應感測事件

### Security Best Practices
- IoT 裝置使用 X.509 憑證認證
- TLS 1.2 加密 MQTT 通訊
- IAM 最小權限原則，Lambda 僅授予必要權限
- S3 server-side encryption (AES256)

---

## 團隊成員｜Team Members

**雲端程式設計 第6組**  
Cloud Programming - Group 6

- 吳君慧 **Peggy Wu**
- 何佳穎 **Chia-Ying Ho**
- 簡宏諭 **Hung-Yu Chien**
- 邱子洋 **Tzu-Yang Chiu**

---

## 開發環境｜Development Environment

- **Pi OS:** Raspberry Pi OS (Debian-based)
- **Python Version:** 3.9+
- **Key Libraries:**
  - `AWSIoTPythonSDK` - MQTT 通訊與 Shadow 管理
  - `Picamera2` - 相機控制
  - `adafruit-circuitpython-ssd1306` - OLED 顯示控制
  - `smbus2` - I2C 裝置通訊
  - `RPi.GPIO` - GPIO 控制
  - `Pillow` - 圖片處理
- **AWS Region:** us-east-1
- **Terraform Version:** >= 1.0
- **Lambda Runtime:** Python 3.13

---

## 相關資源｜Resources

- [部署指南](docs/deployment_guide.md) - 完整的 Terraform 部署步驟
- [AWS IoT Device SDK for Python](https://github.com/aws/aws-iot-device-sdk-python)
- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

---

## 授權｜License

本專案為雲端程式設計課程作業，僅供學習與展示用途。

This is a course project for educational purposes only.

---

## 注意事項｜Important Notes

- **請勿上傳敏感資料：** `config/` 目錄中的 AWS IoT 憑證檔案（`.pem`, `.key`）不應上傳至 GitHub
- **S3 Bucket 命名：** 部署時需使用全球唯一的 bucket 名稱
- **憑證更新：** 遷移至新 AWS 帳號時，必須重新產生 IoT 憑證並更新 Raspberry Pi 上的檔案
- **成本控制：** 雖然專案使用量小，但建議定期檢查 AWS 帳單，避免非預期費用

---

**專案版本：** v1.0 (2026-04-09)
