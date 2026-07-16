# iPhone 照片自動清理系統 (iPhone Photo Auto-Delete System)

本系統為基於 iOS 內建「捷徑（Shortcuts）」與「個人自動化」建構之照片自動清理方案。啟用後，系統將自動掃描新拍攝的照片、影片或螢幕截圖，並於 7 天（10080 分鐘）後自動移入相簿之「最近刪除」檔案夾，以達照片自動化整理之目的。

本方案無需使用任何第三方應用程式或伺服器，所有狀態與待刪除清單均儲存於使用者個人的 iCloud 雲碟中，確保隱私安全。

---

## 核心功能
* **狀態無感切換**：可直接於 iOS 18 控制中心背景切換啟用狀態，並彈出系統通知，免除任何交互確認選單。
* **增量自動標記**：相機關閉時自動觸發，精確識別自上次標記時間後的新增照片，計算到期時間並寫入隊列。
* **定時背景清理**：可配置每週自動執行，比對隊列時間並自動清理已過期照片。
* **零配置初始化**：系統支援自動初始化，首次導入執行即可自動在 iCloud 建立所需之資料夾結構。

---

## 系統架構與資料流

```
[控制中心/使用者] ──(觸發切換)──> 1_切換自動刪除模式 ──(讀寫狀態)──> iCloud (status.txt)
                                                                 │
[關閉相機自動化] ───────────────> 2_自動標記新照片 ───────────────┤ (讀取狀態)
                                   │                             │
                            (寫入待刪除清單)                      v
                                   └───────────────────────> iCloud (pending_list.json)
                                                                 ▲
[定時清理自動化] ───────────────> 3_執行自動刪除清理 ───────────────┘ (讀取過期並刪除)
                                   │
                                   └───────────────────────> iOS 相片庫 (最近刪除)
```

---

## 安裝與配置步驟

### 1. 導入捷徑檔案
自桌面「iPhone自動刪除捷徑」資料夾中，將以下三個已簽署之 `.shortcut` 檔案透過 AirDrop 傳送至 iPhone 並完成導入：
* `1_切換自動刪除模式.shortcut`
* `2_自動標記新照片.shortcut`
* `3_執行自動刪除清理.shortcut`

### 2. 設置 iOS 自動化觸發器

#### 2.1 新照片標記觸發器 (相機關閉時執行)
1. 開啟「捷徑」App，切換至「自動化」分頁，點擊「+」新增自動化。
2. 選擇「App」作為觸發條件，App 選擇「相機」。
3. 勾選「已關閉」，並取消勾選「已開啟」。
4. 選擇「立即執行」，並關閉「執行時通知」。
5. 動作選擇執行捷徑 `2_自動標記新照片`。

#### 2.2 定期清理觸發器 (每週背景清理)
1. 於「自動化」分頁點擊「+」新增自動化，選擇「特定時間」。
2. 設定執行頻率為「每週」，並指定特定時間（例如：每週日 02:00）。
3. 選擇「立即執行」，並關閉「執行時通知」。
4. 動作選擇執行捷徑 `3_執行自動刪除清理`。

### 3. 配置隱私權限
為實現無感背景刪除，必須授權清理捷徑照片刪除權限：
1. 開啟「捷徑」App，進入 `3_執行自動刪除清理` 捷徑的編輯畫面。
2. 點擊螢幕底部的「資訊 (i)」圖示，切換至「隱私」分頁。
3. 於「照片」權限項，將其設定為「允許存取」，並將「刪除不詢問」開關開啟。

### 4. (選配) 控制中心開關配置 (iOS 18)
1. 下拉開啟「控制中心」，長按空白處進入編輯模式，點擊「新增控制項目」。
2. 選擇「捷徑」控制項，並將其指定為 `1_切換自動刪除模式`。

---

## 常見問題與排查

#### Q1: 清理時依然跳出確認刪除彈窗？
原因為「刪除不詢問」權限未成功啟用。請依據「步驟 3」確認該隱私開關已確實開啟。

#### Q2: 關閉相機後未發送「新照片已標記」通知？
1. 確認 `status.txt` 內容為 `開啟`（若為 `關閉` 則會直接跳過標記）。
2. 確認捷徑 App 的系統通知權限已啟用（可至系統「設定」>「通知」>「捷徑」中確認）。

#### Q3: 若於到期前手動刪除了相片，系統是否會報錯？
不會。系統內建容錯機制，若尋找不到相片會直接跳過並從 `pending_list.json` 隊列中清除該筆記錄。

#### Q4: 如何完全移除系統？
1. 執行 `1_切換自動刪除模式` 將狀態切換為 `關閉`。
2. 於捷徑 App 中刪除對應的自動化觸發器。
3. 刪除 iCloud 雲碟中 `Shortcuts/AutoDeletePhotos` 目錄。

========================================================================

# iPhone Photo Auto-Delete System

This system is an automated photo cleanup solution built on iOS native Shortcuts and Personal Automations. Once enabled, the system automatically scans newly taken photos, videos, or screenshots, and moves them to the "Recently Deleted" folder in the Photos app after 7 days (10,080 minutes) to achieve automated organization.

This solution does not require any third-party applications or servers. All state data and queue details are stored in the user's personal iCloud Drive, ensuring data privacy and security.

---

## Core Features
* **Seamless State Toggle**: Allows enabling or disabling the system directly from the iOS 18 Control Center in the background, showing notifications without interactive menus.
* **Incremental Auto-Tagging**: Triggered when the Camera app is closed. Identifies new photos taken since the last tagging timestamp, calculates expiration dates, and appends them to the queue.
* **Scheduled Background Cleanup**: Configurable weekly automation that compares queue timestamps and deletes expired photos.
* **Zero-Configuration Initialization**: Supports automatic folder structure initialization in iCloud upon the first execution.

---

## System Architecture & Data Flow

```
[Control Center/User] ─(Toggle Status)─> 1_Toggle Auto-Delete Mode ──(Read/Write Status)──> iCloud (status.txt)
                                                                                            │
[Camera Close Trigger] ────────────────> 2_Auto Tag New Photos ─────────────────────────────┤ (Read Status)
                                            │                                               │
                                     (Append to Queue)                                      v
                                            └─────────────────────────────────────────> iCloud (pending_list.json)
                                                                                            ▲
[Scheduled Cleanup Trigger] ───────────> 3_Run Auto-Delete Cleanup ─────────────────────────┘ (Read/Delete Expired)
                                            │
                                            └─────────────────────────────────────────> iOS Photos (Recently Deleted)
```

---

## Installation & Configuration Steps

### 1. Import Shortcut Files
From the "iPhone自動刪除捷徑" folder on your Desktop, AirDrop the following three signed `.shortcut` files to your iPhone and import them:
* `1_切換自動刪除模式.shortcut` (1_Toggle Auto-Delete Mode)
* `2_自動標記新照片.shortcut` (2_Auto Tag New Photos)
* `3_執行自動刪除清理.shortcut` (3_Run Auto-Delete Cleanup)

### 2. Setup iOS Personal Automations

#### 2.1 Photo Tagging Trigger (Triggered when Camera app is closed)
1. Open the "Shortcuts" app, switch to the "Automation" tab, and tap "+" to add a new automation.
2. Choose "App" as the trigger condition, and select "Camera" as the app.
3. Check "Is Closed", and uncheck "Is Opened".
4. Select "Run Immediately", and turn off "Notify When Run".
5. Set the action to run the shortcut `2_自動標記新照片`.

#### 2.2 Scheduled Cleanup Trigger (Weekly background cleanup)
1. Tap "+" in the "Automation" tab to add a new automation, and select "Time of Day".
2. Set the frequency to "Weekly" and specify a time (e.g., Sunday at 02:00 AM).
3. Select "Run Immediately", and turn off "Notify When Run".
4. Set the action to run the shortcut `3_執行自動刪除清理`.

### 3. Configure Privacy Permissions
To enable background deletion without prompts, you must grant the cleanup shortcut delete permissions:
1. Open the "Shortcuts" app, and tap "..." on `3_執行自動刪除清理` to edit it.
2. Tap the "Info (i)" icon at the bottom of the screen, and switch to the "Privacy" tab.
3. Under the "Photos" permission section, set it to "Allow Access", and enable "Delete without asking".

### 4. (Optional) Control Center Toggle Configuration (iOS 18)
1. Swipe down to open the "Control Center", long-press any empty space to enter edit mode, and tap "Add a Control".
2. Choose "Shortcut" as the control item, and assign it to the `1_切換自動刪除模式` shortcut.

---

## FAQ & Troubleshooting

#### Q1: Deletion still prompts a confirmation dialog?
This occurs if the "Delete without asking" permission is not enabled. Follow "Step 3" to ensure that the privacy toggle is enabled.

#### Q2: No "New Photos Tagged" notification is received after closing the Camera?
1. Ensure the content of `status.txt` is `開啟` (if set to `關閉`, tagging is skipped).
2. Confirm that system notification permissions for the Shortcuts app are enabled under "Settings" > "Notifications" > "Shortcuts".

#### Q3: Will the system encounter errors if a photo is manually deleted before expiration?
No. The system has built-in error handling. If a photo is not found, the shortcut will skip it and remove the record from `pending_list.json`.

#### Q4: How do I completely uninstall the system?
1. Run `1_切換自動刪除模式` to toggle the status to `關閉`.
2. Delete the associated automation triggers in the Shortcuts app.
3. Delete the `Shortcuts/AutoDeletePhotos` directory in iCloud Drive.
