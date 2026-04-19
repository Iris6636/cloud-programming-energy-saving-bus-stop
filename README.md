# 節能智慧公車站牌系統｜Energy-Saving Smart Bus Stop

有人才亮，無人即暗——偵測到人流時自動拍照上傳，結合 IoT 感測與 AWS 雲端實現節能顯示系統。

Presence-driven smart display: automatically captures and uploads photos when people are detected, powered by IoT sensors and AWS cloud.

本 repo 為 113-2 國立清華大學雲端程式設計課程第 6 組黑客松小專案。課程結束後補全 Terraform IaC，使部署環境可在任意 AWS 帳號重現。

This repo is a hackathon mini-project from Group 6 of the NTHU 113-2 *Cloud Programming* course. Terraform IaC was added post-course to make the deployment fully reproducible on any AWS account.

📑 [簡報 Slides](https://drive.google.com/file/d/19yguSur3Kxkcy-BVKRJPZeOC-JerOW-N/view?usp=sharing) ・ 🎥 [專案介紹 + Demo 影片](https://drive.google.com/file/d/1zG8NVtIvkOJWsTG3smMxXWGzzYL0mKia/view?usp=sharing)

---

## 系統架構圖｜System Architecture

```
┌──────────────────────────────────────────────┐
│                Raspberry Pi                   │
│                                               │
│  PIR Sensor ──► 偵測人流                      │
│  Camera     ──► 拍照                          │
│  BH1750     ──► 偵測光照 → 調整 OLED 亮度     │
│  OLED       ──► 顯示資訊                      │
│                                               │
│  iot/main.py（每 15 秒更新 Shadow）            │
└───────────────┬──────────────────────────────┘
                │ MQTT over TLS (port 8883)
                ▼
┌──────────────────────────────────────────────┐
│              AWS IoT Core                     │
│                                               │
│  Thing Shadow：                               │
│    presence / light / electricity / oled      │
│                                               │
│  Topic Rule 1：presence false → true          │
│    └─► Lambda: busstop-PresenceTov2           │
│          └─► Publish MQTT: take_picture       │
│                └─► Pi 收到指令、拍照           │
│                      └─► MQTT: device/camera/image
│                                               │
│  Topic Rule 2：device/camera/image            │
│    └─► Lambda: busstop-v2Base64toS3           │
│          └─► 解碼 base64 → S3 上傳            │
└──────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────┐
│              Amazon S3                        │
│  photos/NTHU-{timestamp}.jpg                  │
└──────────────────────────────────────────────┘
```

---

## 系統亮點｜Highlights

### 1. Shadow 狀態轉換觸發，而非輪詢

IoT Rule 監聽的是 Shadow update document，只在 `presence` 從 `false` 變 `true` 的瞬間觸發 Lambda，而不是每次上報都觸發。這樣即使 Pi 每 15 秒更新一次，也不會在有人持續停留時反覆發送拍照指令。

### 2. 雙跳 MQTT 拍照指令鏈

「偵測到人」到「照片存進 S3」中間有一段雙向 MQTT：
Lambda 先 publish 指令給 Pi → Pi 拍照 → Pi publish 圖片回雲端 → Lambda 上傳 S3。
這個設計讓相機控制邏輯留在裝置端（減少傳輸量），雲端只負責儲存。

### 3. 邊緣運算節能邏輯

OLED 亮度調整完全在 Pi 本地完成（BH1750 光照 → lux mapping → I2C 寫入亮度值），不依賴雲端回路。電量模擬也在本地計算後才上報 Shadow，減少不必要的雲端呼叫。

### 4. 完整 IaC，一鍵重現

所有 AWS 資源（IoT Thing、Topic Rules、Lambda、S3、IAM）由 Terraform 管理，`terraform apply` 即可在新帳號重建完整環境，不需要手動在 Console 點選。

---

## 技術選型｜Tech Stack

### AWS 服務

| 服務 | 用途 | 選用原因 |
|------|------|---------|
| **AWS IoT Core** | 裝置 MQTT 通訊、Thing Shadow 狀態管理 | 原生支援 Shadow state change 事件觸發，不需自建 MQTT broker |
| **AWS Lambda** | 發送拍照指令、解碼圖片上傳 S3 | Serverless，無需管理伺服器；事件驅動，只在觸發時計費 |
| **Amazon S3** | 儲存拍攝的站牌照片 | 低成本持久儲存；可直接對接 Lambda |
| **AWS IAM** | Lambda 執行角色權限控管 | 最小權限原則，只開放必要的 iot:Publish 與 s3:PutObject |
| **Terraform** | 基礎設施即程式碼 | 可重複部署，版本控制，遷移帳號不需重新手動設定 |

### 裝置端

| 元件 | 規格 | 用途 |
|------|------|------|
| Raspberry Pi | 3 / 4 | 主控制器 |
| PIR Sensor | HC-SR501，GPIO 26 | 人流偵測 |
| Camera Module | Picamera2 V2，640×480 | 拍攝站牌畫面 |
| OLED Display | SSD1306，128×64，I2C 0x3C | 顯示資訊 |
| Light Sensor | BH1750，I2C 0x23 | 偵測環境光照 |

---

## 快速開始｜Quick Start

```bash
git clone https://github.com/Iris6636/cloud-programming-energy-saving-bus-stop.git
cd cloud-programming-energy-saving-bus-stop/deployment/infra
cp terraform.tfvars.example terraform.tfvars   # 填入你的 S3 bucket 名稱
terraform init && terraform apply
```

部署完成後，將 `terraform output iot_endpoint` 的值更新至 `iot/main.py`，並在 AWS Console 產生新憑證上傳至 Pi。

完整步驟請見 **[docs/deployment_guide.md](docs/deployment_guide.md)**

---

## 專案結構｜Project Structure

```
cloud-programming-energy-saving-bus-stop/
├── iot/
│   └── main.py                    # Pi 主程式：感測器、MQTT、Shadow 更新
├── backend/
│   └── lambda_functions/
│       ├── PresenceTov2.py        # 偵測到人流 → 發送拍照指令
│       └── v2Base64toS3.py        # 接收 base64 圖片 → 上傳 S3
├── deployment/
│   ├── infra/                     # Terraform（terraform apply 即部署）
│   └── lambda/                    # Lambda .zip 部署包
├── docs/
│   └── deployment_guide.md        # 完整部署指南
└── config/                        # IoT 憑證（請勿上傳 Git）
```

---

## 相關文件｜Documentation

| 文件 | 說明 |
|------|------|
| [docs/deployment_guide.md](docs/deployment_guide.md) | Terraform 部署、Pi 憑證設定、驗證與疑難排解 |

---

## 團隊成員｜Team Members

雲端程式設計 第6組｜NTHU Cloud Programming — Group 6

- 吳君慧 Peggy Wu
- 何佳穎 Chia-Ying Ho
- 簡宏諭 Hung-Yu Chien
- 邱子洋 Tzu-Yang Chiu
