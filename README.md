# 🔊 聲音照相管理系統(SwaggerAPI)
該API提供一套完整且可靠的介面，用於管理與存取聲音照相設備所產生的各項事件與感測資料。透過此開發者可輕鬆串接後端系統、儀表板或第三方應用，快速取得聲音事件與即時監測資訊。

---

## 📁 專案結構(Overview)
專案主要組成包含：
- **應用程式主程式碼**（main.py …）
- **環境依賴包**（requirements.txt）
- **環境設定檔**（如 `.env`）


---

## 🛠 系統需求(Requirements)
- Python 3.11

---

## 🚀 快速建置(Getting Start)

### 1. 下載專案
```bash
git clone <repo-url>
```
```bash
cd <project-folder>
```

### 2. 設定環境變數

專案需使用 `.env` 系統設定參數檔案，所有運行所需的連線資訊與服務設定皆在此檔案中進行管理。

以下為 `.env` 所需的參數格式（*不含實際值*）：

```env

PublicIP = XXX.XXX.XXX.XXX
Host = 192.168.X.XX\SQLEXPRESS
Port = 1433
User = <USERNAME>
Password = <PASSWORD>
Database = <DB_NAME>
Database_His = <DB_HISTORY_NAME>
Push_Time = 0.5

```


### 3. 啟動方式

本專案僅支援原始碼啟動方式(因有區域網路問題，因此採用直接連線)：


#### 本地運行

直接以程式原生方式啟動：

```bash
pip install -r requirements.txt
```
```bash
python main.py
```
> ⚠ 注意：本地運行需要自行準備對應語言環境與套件。


---

## 🌐 設定說明(API Proxy)

前端應用程式透過 Vite 的 Proxy 設定，將特定路徑的請求導向後端服務，以實現跨域通訊和模組化管理：

| 模組名稱 | 路徑 Prefix |
| :------- | :---------- |
| 站點站號清單 | `/edgesite` |
| 噪音事件維護 | `/soundphoto` |
| 校正紀錄清冊 | `/sensor` |
| 稽查紀錄彙整 | `/check` |


---

## 📚 文件與瀏覽器

若專案包含 API 文件，請參考：

* `/docs`
* `/swagger`
* `/redoc`

或啟動後的[預設網址](http://localhost:8010/docs)

