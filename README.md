# cloud-programming-energy-saving-bus-stop
節能公車站牌系統，透過 IoT 感測與 AWS 雲端整合，根據人流與光照智慧調整看板顯示狀態並模擬太陽能儲電。 A smart bus stop system combining IoT sensors and AWS services, designed to display information only when people are nearby, and simulate solar energy storage via light detection.

# 節能公車站牌系統｜Energy-Saving Smart Bus Stop

> 有人才亮燈，感測也節能！  
> Energy-efficient smart signage triggered by real-world presence and sunlight.


---

## 📘 專案簡介｜Project Introduction

節能公車站牌是一款結合 IoT 感測與 AWS 雲端服務的智慧看板系統。透過紅外線與光敏電阻感測器偵測人流與光照，自動控制 OLED 顯示開關與亮度，並模擬太陽能儲電。後台管理員可透過網頁即時查看電量與運作狀態。

This is a smart signage system that only activates when people approach. It integrates IoT sensors and AWS cloud services to dynamically adjust display brightness and simulate solar energy storage. A backend dashboard provides real-time monitoring.

---

## 🧱 系統架構圖｜System Architecture

![System Diagram](architecture/system_architecture.png)

---

## 🧑‍💻 系統流程｜System Workflow

1. 每 15 秒感測一次光照與人流，並將資料上傳 AWS  
   Sensing is done every 15 seconds and sent to AWS.
2. 若有人靠近，開啟 OLED 並顯示資訊  
   OLED lights up with info when people are detected.
3. 根據光強調整螢幕亮度並模擬電量變化  
   Light intensity affects brightness & battery simulation.
4. 管理員可透過網站查看即時狀態  
   Admin can check status via frontend.
---

## 🔧 使用技術｜Tech Stack

### 🎯 AWS 雲端服務｜AWS Services
- IoT Core（設備通訊 / Device Communication）
- Lambda（邏輯處理 / Business Logic）
- DynamoDB（狀態儲存 / State Storage）
- S3（影像儲存 / Image Upload）
- API Gateway（前後端連接 / API Access）


### 📦 IoT 裝置與硬體｜IoT & Hardware
- Raspberry Pi 3 / 4
- V2 Camera 模組
- 震動感測器 SW-420
- 電磁閥 DS-0420S

### 💻 前端技術｜Frontend
- HTML / CSS / JavaScript
- S3 Static Hosting + Cognito Login

---

## 🚀 如何使用本專案｜Getting Started

### ✅ 下載專案｜Clone the Repo

```bash
git clone https://github.com/your-account/smart-washer-project.git
cd smart-washer-project
```

或下載 ZIP → 解壓縮  
Or download the ZIP and extract it.

---

### ✅ 執行 IoT 裝置程式｜Run IoT Device Code

```bash
cd iot/
python3 main.py
```

請事先連接感測器與相機，並於 `config/` 中放置 IoT 憑證與設定檔。  
Connect the sensors and camera, and ensure your AWS IoT certificates and config file are placed under `config/`.

---

### ✅ 部署 Lambda 函式｜Deploy Lambda Functions

進入 `backend/lambda_functions/`，依功能部署下列程式碼：  
Go to `backend/lambda_functions/` and deploy the following Lambda functions:

| 檔案 File | 功能 Function |
|-----------|----------------|
| `process_image.py` | 拍照上傳 + Rekognition 辨識<br>Upload image & recognize time |
| `update_status.py` | 更新洗衣狀態至 DB<br>Update washer status to DB |
| `send_notification.py` | 傳送 SNS 通知<br>Send user notification |
| `schedule_checker.py` | 檢查預約是否過期<br>Check if reservation expired |


---

## 📁 專案結構｜Project Structure

```
cloud-programming-energy-saving-bus-stop/
├── README.md                  
├── iot/                  
├── backend/                    
├── web/                        
├── docs/         
```

```

---

## 👥 團隊成員｜Team Members

雲端程式設計 第6組  
Group 6 — Cloud Programming Project  

- 吳君慧 Peggy Wu  
- 何佳穎 Chia-Ying Ho  
- 簡宏諭 Hung-Yu Chien  
- 邱子洋 Tzu-Yang Chiu

---


## 🔗 相關連結

- 🎥 [系統 Demo 影片](https://youtu.be/your-video-link)
- 🖼️ [簡報 PDF 下載](docs/final_presentation.pdf)

---


## 📎 注意事項｜Notes

- `config/` 資料夾請手動建立並放入憑證與設定檔。  
  請勿將 `.pem`、`.json` 等敏感檔案上傳 GitHub。  
  → Create `config/` and place certificates locally. Do NOT upload secrets to GitHub.

- 若需詳細安裝流程，請見 [`docs/setup_guide.md`](docs/setup_guide.md)  
  For detailed setup, see `docs/setup_guide.md`
