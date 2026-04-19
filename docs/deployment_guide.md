# Deployment Guide｜部署指南

本指南說明如何使用 Terraform 從零開始部署節能公車站牌系統的 AWS 基礎設施。

---

## Prerequisites｜前置需求

### 必要工具

在開始部署前，請確認已安裝以下工具：

| 工具 | 最低版本 | 用途 |
|------|---------|------|
| **AWS CLI** | v2.x | 管理 AWS 憑證與資源 |
| **Terraform** | >= 1.0 | 基礎設施即程式碼部署 |
| **Python** | >= 3.9 | Lambda 函式開發與測試 |
| **Git** | 任意版本 | 版本控制 |

### Windows 使用者安裝說明

在 Windows 環境下，建議使用套件管理工具安裝：

**使用 Chocolatey:**
```bash
choco install awscli terraform python git
```

**使用 winget:**
```bash
winget install Amazon.AWSCLI
winget install Hashicorp.Terraform
winget install Python.Python.3.12
winget install Git.Git
```

### AWS 帳號設定

1. 確認擁有 AWS 帳號並具備管理員權限
2. 配置 AWS CLI 憑證：

```bash
aws configure
```

輸入您的 Access Key ID、Secret Access Key、預設區域（建議 `us-east-1`）

---

## Architecture Overview｜架構總覽

### Terraform 檔案結構

```
deployment/infra/
├── main.tf                 # AWS Provider 設定
├── variables.tf            # 輸入變數定義（region, S3 bucket name）
├── outputs.tf              # 輸出值（IoT endpoint, Thing name, S3 bucket）
├── iam.tf                  # Lambda 執行角色與權限
├── lambda.tf               # 2 個 Lambda 函式定義
├── s3.tf                   # S3 影像儲存桶
├── iot.tf                  # IoT Thing + 2 條 Topic Rules + Device Policy
└── terraform.tfvars.example # 變數範本檔案
```

### 系統運作流程

```
Raspberry Pi
    ↓ (每 15 秒更新 Shadow)
AWS IoT Core (Thing Shadow)
    ↓ (presence: false→true)
IoT Topic Rule: busstop_PresenceDetected
    ↓
Lambda: busstop-PresenceTov2
    ↓ (publish MQTT: {"action": "take_picture"})
Raspberry Pi
    ↓ (拍照並發送 base64 圖片到 device/camera/image)
IoT Topic Rule: busstop_CaptureImageToS3
    ↓
Lambda: busstop-v2Base64toS3
    ↓
S3 Bucket (photos/NTHU-{timestamp}.jpg)
```

---

## Step-by-Step Deployment｜逐步部署

### Step 1: 準備 Lambda 函式壓縮檔

確認 `deployment/lambda/` 目錄下已有兩個 Lambda 函式的 ZIP 檔：

```bash
ls deployment/lambda/
```

應該看到：
- `PresenceTov2.zip` (包含 `lambda_function.py`)
- `v2Base64toS3.zip` (包含 `v2Base64toS3.py`)

如果檔案不存在，請手動建立：

```bash
# PresenceTov2.zip — 內部檔名必須是 lambda_function.py（handler: lambda_function.lambda_handler）
cp backend/lambda_functions/PresenceTov2.py /tmp/lambda_function.py
cd /tmp && zip PresenceTov2.zip lambda_function.py
cp /tmp/PresenceTov2.zip deployment/lambda/PresenceTov2.zip

# v2Base64toS3.zip — 內部檔名必須是 v2Base64toS3.py（handler: v2Base64toS3.lambda_handler）
cp backend/lambda_functions/v2Base64toS3.py /tmp/v2Base64toS3.py
cd /tmp && zip v2Base64toS3.zip v2Base64toS3.py
cp /tmp/v2Base64toS3.zip deployment/lambda/v2Base64toS3.zip
```

> **重要：** ZIP 檔案名稱必須與 handler 對應。`PresenceTov2.zip` 內部必須包含 `lambda_function.py`（handler 為 `lambda_function.lambda_handler`）；`v2Base64toS3.zip` 內部必須包含 `v2Base64toS3.py`（handler 為 `v2Base64toS3.lambda_handler`）。

### Step 2: 設定 Terraform 變數

複製範本檔案並編輯：

```bash
cd deployment/infra
cp terraform.tfvars.example terraform.tfvars
```

編輯 `terraform.tfvars`：

```hcl
aws_region        = "us-east-1"
s3_bucket_images  = "busstop-images-yourname-20260409"  # 必須全球唯一
```

> **提示：** S3 bucket 名稱必須全球唯一，建議加上日期或隨機字串。

### Step 3: 初始化 Terraform

```bash
terraform init
```

此步驟會下載 AWS provider 並初始化工作目錄。

### Step 4: 檢視部署計畫

```bash
terraform plan
```

Terraform 會顯示即將建立的資源清單。請仔細檢查：
- 2 個 Lambda 函式
- 1 個 S3 bucket
- 1 個 IoT Thing
- 2 條 IoT Topic Rules
- 1 個 IoT Device Policy
- 1 個 IAM role 及相關 policy

### Step 5: 執行部署

```bash
terraform apply
```

輸入 `yes` 確認部署。部署時間約 1-2 分鐘。

### Step 6: 記錄重要輸出值

部署完成後，記錄以下輸出值（後續設定 Raspberry Pi 時需要）：

```bash
terraform output
```

輸出範例：
```
iot_endpoint      = "a1bc2def3ghijk-ats.iot.us-east-1.amazonaws.com"
iot_thing_name    = "MyThing-113065528"
s3_bucket_images  = "busstop-images-yourname-20260409"
```

**請將 `iot_endpoint` 值複製並保存，稍後需要更新到 Raspberry Pi 程式碼中。**

---

## Lambda Functions｜Lambda 函式說明

### Lambda 1: busstop-PresenceTov2

**觸發條件：** 當 IoT Thing Shadow 的 `presence` 欄位從 `false` 變為 `true`

**功能：** 發送 MQTT 訊息到 `my/subscribetopic`，指示 Raspberry Pi 拍照

**Handler:** `lambda_function.lambda_handler`

**Runtime:** Python 3.13

**Timeout:** 10 秒

**環境變數：** 無

### Lambda 2: busstop-v2Base64toS3

**觸發條件：** 接收到 `device/camera/image` topic 的 MQTT 訊息

**功能：** 解碼 base64 圖片並上傳至 S3 bucket 的 `photos/` 目錄

**Handler:** `v2Base64toS3.lambda_handler`

**Runtime:** Python 3.13

**Timeout:** 10 秒

**環境變數：**

| 變數名稱 | 說明 | 範例值 |
|---------|------|--------|
| `S3_BUCKET_IMAGES` | S3 儲存桶名稱 | `busstop-images-yourname-20260409` |

---

## IAM Permissions｜權限摘要

### Lambda Execution Role: `busstop-lambda-exec-role`

此角色授予 Lambda 函式以下權限：

| 權限類別 | Actions | 用途 |
|---------|---------|------|
| **CloudWatch Logs** | `logs:CreateLogGroup`<br>`logs:CreateLogStream`<br>`logs:PutLogEvents` | 寫入執行日誌 |
| **IoT Publish** | `iot:Publish` | 發送 MQTT 訊息至所有 topics |
| **S3 Object** | `s3:PutObject`<br>`s3:GetObject` | 上傳與讀取圖片檔案 |
| **S3 Bucket** | `s3:ListBucket` | 列出 bucket 內容 |

---

## IoT Topic Rules｜IoT 規則說明

| Rule Name | SQL 語句 | 觸發條件 | 動作 |
|-----------|---------|---------|------|
| **busstop_PresenceDetected** | `SELECT * FROM '$aws/things/MyThing-113065528/shadow/update/documents' WHERE current.state.reported.presence = true AND previous.state.reported.presence = false` | Shadow 中 `presence` 從 false 變 true | 觸發 `busstop-PresenceTov2` Lambda |
| **busstop_CaptureImageToS3** | `SELECT * FROM 'device/camera/image'` | 接收到 `device/camera/image` topic 的訊息 | 觸發 `busstop-v2Base64toS3` Lambda |

---

## Post-Deployment Configuration｜部署後設定

### 更新 Raspberry Pi 程式碼

部署完成後，必須更新 Raspberry Pi 上的 `iot/main.py`：

1. 取得新的 IoT endpoint（從 `terraform output iot_endpoint` 取得）

2. 編輯 `iot/main.py` 的第 162 行：

```python
# 原本（舊帳號）
endpoint = "a1ebcaquqh9vk4-ats.iot.us-east-1.amazonaws.com"

# 改為新的 endpoint（從 terraform output 取得）
endpoint = "a1bc2def3ghijk-ats.iot.us-east-1.amazonaws.com"
```

3. 儲存檔案並重新部署到 Raspberry Pi

### 產生並安裝新的 IoT 憑證

舊憑證無法在新 AWS 帳號中使用，必須重新產生：

**在 AWS Console 中：**

1. 進入 **IoT Core** → **Security** → **Certificates**
2. 點擊 **Create certificate**
3. 選擇 **Auto-generate a new certificate**
4. 下載以下三個檔案：
   - Device certificate (`.pem.crt`)
   - Private key (`.pem.key`)
   - Amazon Root CA 1 (`AmazonRootCA1.pem`)

**在 Raspberry Pi 上：**

1. 將憑證檔案上傳至 `/home/team6/Downloads/CP/`
2. 更新 `iot/main.py` 中的憑證路徑（第 163-165 行）：

```python
rootCAPath = "/home/team6/Downloads/CP/AmazonRootCA1.pem"
certificatePath = "/home/team6/Downloads/CP/{YOUR-CERT-ID}-certificate.pem"
privateKeyPath = "/home/team6/Downloads/CP/private.pem.key"
```

**在 AWS Console 中附加 Policy 到憑證：**

1. 回到 **Certificates** 頁面，選擇剛建立的憑證
2. 點擊 **Attach policy**
3. 選擇 `busstop-DevicePolicy`
4. 點擊 **Attach things**，選擇 `MyThing-113065528`

---

## Verify Deployment｜驗證部署

### 1. 檢查 Lambda 函式

```bash
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `busstop-`)].FunctionName'
```

應該看到：
```json
[
    "busstop-PresenceTov2",
    "busstop-v2Base64toS3"
]
```

### 2. 檢查 S3 Bucket

```bash
aws s3 ls | grep busstop
```

應該看到您建立的 bucket 名稱。

### 3. 測試 IoT 連線

在 Raspberry Pi 上執行：

```bash
cd iot
python3 main.py
```

如果成功連線，應該看到：
```
Connected to AWS IoT Core & Shadow
[PIR] Motion: ...
```

### 4. 檢查 Lambda 日誌

部署後可手動觸發測試或等待 Raspberry Pi 觸發，然後檢查 CloudWatch Logs：

```bash
aws logs tail /aws/lambda/busstop-PresenceTov2 --follow
aws logs tail /aws/lambda/busstop-v2Base64toS3 --follow
```

---

## Cleanup｜清理資源

如需移除所有部署的資源：

```bash
cd deployment/infra
terraform destroy
```

**警告：** 此操作會刪除所有資源，包括 S3 bucket 中的圖片。在執行前請確認已備份重要資料。

> **注意：** 如果 S3 bucket 內有檔案，Terraform 可能無法刪除。請先清空 bucket：
>
> ```bash
> aws s3 rm s3://YOUR-BUCKET-NAME --recursive
> ```

---

## Troubleshooting｜疑難排解

### Lambda 函式錯誤

**症狀：** Lambda 執行失敗

**檢查步驟：**

1. 查看 CloudWatch Logs：
   ```bash
   aws logs tail /aws/lambda/busstop-PresenceTov2 --since 10m
   ```

2. 常見錯誤：
   - `KeyError: 'S3_BUCKET_IMAGES'` → 檢查 Lambda 環境變數是否正確設定
   - `Permission denied` → 檢查 IAM role 權限
   - `Invalid base64` → 檢查 Raspberry Pi 傳送的資料格式

### IoT 裝置無法連線

**症狀：** Raspberry Pi 無法連接到 AWS IoT Core

**檢查清單：**

1. **IoT Endpoint 是否正確？**
   ```bash
   # 在 iot/main.py 中檢查
   endpoint = "YOUR-IOT-ENDPOINT"  # 必須與 terraform output 相符
   ```

2. **憑證檔案是否存在且路徑正確？**
   ```bash
   ls -la /home/team6/Downloads/CP/
   ```

3. **憑證是否已附加 Policy 和 Thing？**
   - 在 AWS Console 檢查：IoT Core → Security → Certificates
   - 確認憑證狀態為 **Active**
   - 確認已附加 `busstop-DevicePolicy` 和 `MyThing-113065528`

4. **Device Policy 權限是否足夠？**
   - Policy 應允許 `iot:Connect`, `iot:Publish`, `iot:Subscribe`, `iot:Receive`, `iot:UpdateThingShadow`, `iot:GetThingShadow`

### S3 上傳失敗

**症狀：** 圖片無法上傳至 S3

**檢查步驟：**

1. 確認 Lambda 環境變數 `S3_BUCKET_IMAGES` 設定正確
2. 確認 Lambda IAM role 有 `s3:PutObject` 權限
3. 檢查 bucket 名稱是否正確（不含 `s3://` 前綴）

### Terraform 部署失敗

**常見問題：**

1. **S3 bucket 名稱衝突：**
   ```
   Error: Error creating S3 bucket: BucketAlreadyExists
   ```
   → 修改 `terraform.tfvars` 中的 `s3_bucket_images`，使用唯一名稱

2. **AWS 憑證過期：**
   ```
   Error: error configuring Terraform AWS Provider: error validating provider credentials
   ```
   → 執行 `aws configure` 重新設定憑證

3. **Lambda ZIP 檔案不存在：**
   ```
   Error: error reading "deployment/lambda/PresenceTov2.zip"
   ```
   → 返回 Step 1 重新建立 ZIP 檔案

---

## Additional Resources｜相關資源

- [AWS IoT Core 官方文件](https://docs.aws.amazon.com/iot/)
- [Terraform AWS Provider 文件](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Lambda Python 執行環境](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)

---

**部署指南版本：** v1.0 (2026-04-09)
