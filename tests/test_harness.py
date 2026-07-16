"""
iPhone Auto-Delete Photos Shortcuts - Python Simulation & Test Harness
"""

import os
import json
import tempfile
import shutil
import unittest
from datetime import datetime, timedelta

# ==========================================
# 1. Helper Functions
# ==========================================

def parse_time(t):
    if isinstance(t, datetime):
        return t
    if isinstance(t, str):
        if t.endswith('Z'):
            t = t[:-1]
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(t, fmt)
            except ValueError:
                continue
    raise ValueError(f"Cannot parse time: {t}")

# ==========================================
# 2. Simulation Environment Class
# ==========================================

class ShortcutsSimulator:
    def __init__(self, icloud_dir, photo_library=None):
        self.icloud_dir = icloud_dir
        self.shortcuts_dir = os.path.join(icloud_dir, "Shortcuts")
        
        # Initialize photo library
        # Structure: { photo_id: { "id": photo_id, "type": "photo"/"video"/"screenshot", "creation_time": datetime, "status": "active", "favorite": False } }
        self.photo_library = photo_library if photo_library is not None else {}
        
        # Simulation control settings
        self.has_photo_permission = True
        self.delete_without_asking = True
        self.user_confirm_delete_response = "allow" # "allow" or "deny"
        self.storage_full = False  # If True, simulate storage full by raising OSError on write

    def _get_status_path(self):
        return os.path.join(self.shortcuts_dir, "auto_delete_status.txt")

    def _get_timer_path(self):
        return os.path.join(self.shortcuts_dir, "auto_delete_timer.txt")

    def _get_pending_path(self):
        return os.path.join(self.shortcuts_dir, "pending_delete.json")

    def _check_storage_full(self):
        if self.storage_full:
            raise OSError("檔案儲存失敗，請檢查 iCloud 空間")

    def toggle_shortcut(self):
        self._check_storage_full()
        os.makedirs(self.shortcuts_dir, exist_ok=True)
        status_path = self._get_status_path()
        
        # Read status
        current_status = None
        if os.path.exists(status_path):
            try:
                with open(status_path, 'r', encoding='utf-8') as f:
                    current_status = f.read().strip()
            except Exception:
                pass
        
        # Toggle logic
        if current_status == "開啟":
            new_status = "關閉"
            notification = "自動刪除模式已關閉"
        else:
            new_status = "開啟"
            notification = "自動刪除模式已開啟"
            
        with open(status_path, 'w', encoding='utf-8') as f:
            f.write(new_status)
            
        return notification

    def timer_setting_shortcut(self, option):
        self._check_storage_full()
        os.makedirs(self.shortcuts_dir, exist_ok=True)
        timer_path = self._get_timer_path()
        
        options_map = {
            "30分鐘": 30,
            "1小時": 60,
            "2小時": 120,
            "4小時": 240,
            "6小時": 360,
            "12小時": 720,
            "24小時": 1440
        }
        
        if option not in options_map:
            raise ValueError("無效的選項")
            
        minutes = options_map[option]
        with open(timer_path, 'w', encoding='utf-8') as f:
            f.write(str(minutes))

    def photo_tagging_trigger(self, photo_id, creation_time):
        if not self.has_photo_permission:
            raise PermissionError("無法取得照片資訊，請檢查隱私權限設定")
            
        status_path = self._get_status_path()
        timer_path = self._get_timer_path()
        pending_path = self._get_pending_path()
        
        # Read status - default to "關閉" if missing/corrupted
        status = "關閉"
        if os.path.exists(status_path):
            try:
                with open(status_path, 'r', encoding='utf-8') as f:
                    status = f.read().strip()
            except Exception:
                pass
                
        if status != "開啟":
            return
            
        # Read timer - default to 60 minutes if missing/corrupted
        timer_minutes = 60
        if os.path.exists(timer_path):
            try:
                with open(timer_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    timer_minutes = int(content)
            except Exception:
                timer_minutes = 60
                
        # Parse creation_time
        dt_creation = parse_time(creation_time)
        dt_expiration = dt_creation + timedelta(minutes=timer_minutes)
        expiration_str = dt_expiration.isoformat()
        
        # Read pending list
        pending_list = []
        if os.path.exists(pending_path):
            try:
                with open(pending_path, 'r', encoding='utf-8') as f:
                    pending_list = json.load(f)
                if not isinstance(pending_list, list):
                    pending_list = []
            except json.JSONDecodeError:
                pending_list = []
                
        # Append new item
        pending_list.append({
            "id": photo_id,
            "delete_time": expiration_str
        })
        
        self._check_storage_full()
        os.makedirs(self.shortcuts_dir, exist_ok=True)
        with open(pending_path, 'w', encoding='utf-8') as f:
            json.dump(pending_list, f, ensure_ascii=False, indent=2)

    def cleanup_automation_shortcut(self, current_time):
        if not self.has_photo_permission:
            raise PermissionError("無法存取相簿，請檢查隱私設定。")
            
        pending_path = self._get_pending_path()
        
        if not os.path.exists(pending_path):
            return
            
        pending_list = []
        corrupted_reset = False
        try:
            with open(pending_path, 'r', encoding='utf-8') as f:
                pending_list = json.load(f)
            if not isinstance(pending_list, list):
                corrupted_reset = True
        except json.JSONDecodeError:
            corrupted_reset = True
            
        if corrupted_reset:
            pending_list = []
            self._check_storage_full()
            with open(pending_path, 'w', encoding='utf-8') as f:
                json.dump(pending_list, f, ensure_ascii=False, indent=2)
            return "待刪除清單已損毀，已自動重置。"
            
        dt_current = parse_time(current_time)
        
        # Identify expired and unexpired items
        expired_items = []
        unexpired_items = []
        
        for item in pending_list:
            try:
                dt_delete = parse_time(item["delete_time"])
                if dt_delete <= dt_current:
                    expired_items.append(item)
                else:
                    unexpired_items.append(item)
            except Exception:
                # If timestamp is unparseable, treat as expired to be robust
                expired_items.append(item)
                
        if not expired_items:
            return
            
        # Check permissions/confirmation for expired items
        # Filter out items that are already deleted from the library manually (TC-B4-03)
        actual_expired_in_library = []
        for item in expired_items:
            photo_id = item["id"]
            if photo_id in self.photo_library:
                photo_info = self.photo_library[photo_id]
                if photo_info.get("status") == "active":
                    actual_expired_in_library.append(photo_info)
                    
        # Check if confirmation is required
        needs_prompt = False
        if not self.delete_without_asking:
            needs_prompt = True
        else:
            # Check if any actual expired photo is a favorite
            for photo in actual_expired_in_library:
                if photo.get("favorite", False):
                    needs_prompt = True
                    break
                    
        if needs_prompt:
            if self.user_confirm_delete_response == "deny":
                # Abort deletion, keep all items in pending list
                return "拒絕刪除"
                
        # If allowed or no confirmation needed, delete them
        for photo in actual_expired_in_library:
            photo["status"] = "recently_deleted"
            photo["deleted_at"] = dt_current.isoformat()
            
        # Update pending list to only contain unexpired items
        self._check_storage_full()
        with open(pending_path, 'w', encoding='utf-8') as f:
            json.dump(unexpired_items, f, ensure_ascii=False, indent=2)


# ==========================================
# 3. Global Shortcut Functions Delegate
# ==========================================

_simulator = None

def get_simulator():
    global _simulator
    if _simulator is None:
        # Fallback default temp dir
        temp_dir = tempfile.mkdtemp()
        _simulator = ShortcutsSimulator(icloud_dir=temp_dir)
    return _simulator

def set_simulator(sim):
    global _simulator
    _simulator = sim

def toggle_shortcut():
    return get_simulator().toggle_shortcut()

def timer_setting_shortcut(option):
    return get_simulator().timer_setting_shortcut(option)

def photo_tagging_trigger(photo_id, creation_time):
    return get_simulator().photo_tagging_trigger(photo_id, creation_time)

def cleanup_automation_shortcut(current_time):
    return get_simulator().cleanup_automation_shortcut(current_time)


# ==========================================
# 4. Unittest Suite
# ==========================================

class TestShortcutsSystem(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.photo_library = {}
        self.sim = ShortcutsSimulator(icloud_dir=self.temp_dir, photo_library=self.photo_library)
        set_simulator(self.sim)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        set_simulator(None)

    # ---------------------------------------------------------
    # Tier 1: Functional Coverage
    # ---------------------------------------------------------
    
    # Feature 1: Control Center Toggle Mode
    def test_tc_f1_01_toggle_initial_no_status_file(self):
        # Initial: no status file
        status_path = self.sim._get_status_path()
        self.assertFalse(os.path.exists(status_path))
        
        notification = toggle_shortcut()
        self.assertEqual(notification, "自動刪除模式已開啟")
        self.assertTrue(os.path.exists(status_path))
        with open(status_path, 'r', encoding='utf-8') as f:
            self.assertEqual(f.read().strip(), "開啟")

    def test_tc_f1_02_toggle_from_open_to_closed(self):
        # Setup: status file is "開啟"
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        with open(self.sim._get_status_path(), 'w', encoding='utf-8') as f:
            f.write("開啟")
            
        notification = toggle_shortcut()
        self.assertEqual(notification, "自動刪除模式已關閉")
        with open(self.sim._get_status_path(), 'r', encoding='utf-8') as f:
            self.assertEqual(f.read().strip(), "關閉")

    def test_tc_f1_03_toggle_from_closed_to_open(self):
        # Setup: status file is "關閉"
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        with open(self.sim._get_status_path(), 'w', encoding='utf-8') as f:
            f.write("關閉")
            
        notification = toggle_shortcut()
        self.assertEqual(notification, "自動刪除模式已開啟")
        with open(self.sim._get_status_path(), 'r', encoding='utf-8') as f:
            self.assertEqual(f.read().strip(), "開啟")

    def test_tc_f1_04_toggle_cycle(self):
        # Setup: initial no status file. Run toggle 3 times.
        notifications = []
        notifications.append(toggle_shortcut()) # -> 關閉 to 開啟
        notifications.append(toggle_shortcut()) # -> 開啟 to 關閉
        notifications.append(toggle_shortcut()) # -> 關閉 to 開啟
        
        self.assertEqual(notifications, [
            "自動刪除模式已開啟",
            "自動刪除模式已關閉",
            "自動刪除模式已開啟"
        ])

    # Feature 2: Timer Setting
    def test_tc_f2_01_timer_setting_30_minutes(self):
        timer_setting_shortcut("30分鐘")
        with open(self.sim._get_timer_path(), 'r', encoding='utf-8') as f:
            self.assertEqual(f.read().strip(), "30")

    def test_tc_f2_02_timer_setting_2_hours(self):
        timer_setting_shortcut("2小時")
        with open(self.sim._get_timer_path(), 'r', encoding='utf-8') as f:
            self.assertEqual(f.read().strip(), "120")

    def test_tc_f2_03_timer_setting_24_hours(self):
        timer_setting_shortcut("24小時")
        with open(self.sim._get_timer_path(), 'r', encoding='utf-8') as f:
            self.assertEqual(f.read().strip(), "1440")

    def test_tc_f2_05_timer_setting_initial_no_timer_file(self):
        # Timer file does not exist initially
        timer_path = self.sim._get_timer_path()
        self.assertFalse(os.path.exists(timer_path))
        
        timer_setting_shortcut("4小時")
        self.assertTrue(os.path.exists(timer_path))
        with open(timer_path, 'r', encoding='utf-8') as f:
            self.assertEqual(f.read().strip(), "240")

    # Feature 3: Photo Tagging Trigger
    def test_tc_f3_01_photo_tagging_enabled(self):
        # Setup status = 開啟, timer = 30
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        with open(self.sim._get_status_path(), 'w', encoding='utf-8') as f:
            f.write("開啟")
        with open(self.sim._get_timer_path(), 'w', encoding='utf-8') as f:
            f.write("30")
            
        creation_time = "2026-07-16T12:00:00"
        photo_tagging_trigger("PHOTO_001", creation_time)
        
        # Verify JSON
        pending_path = self.sim._get_pending_path()
        self.assertTrue(os.path.exists(pending_path))
        with open(pending_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["id"], "PHOTO_001")
            self.assertEqual(data[0]["delete_time"], "2026-07-16T12:30:00")

    def test_tc_f3_02_video_tagging_enabled(self):
        # Setup status = 開啟, timer = 60
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        with open(self.sim._get_status_path(), 'w', encoding='utf-8') as f:
            f.write("開啟")
        with open(self.sim._get_timer_path(), 'w', encoding='utf-8') as f:
            f.write("60")
            
        creation_time = "2026-07-16T12:00:00"
        photo_tagging_trigger("VIDEO_001", creation_time)
        
        # Verify JSON
        pending_path = self.sim._get_pending_path()
        with open(pending_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["id"], "VIDEO_001")
            self.assertEqual(data[0]["delete_time"], "2026-07-16T13:00:00")

    def test_tc_f3_03_screenshot_tagging_enabled(self):
        # Setup status = 開啟, timer = 30
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        with open(self.sim._get_status_path(), 'w', encoding='utf-8') as f:
            f.write("開啟")
        with open(self.sim._get_timer_path(), 'w', encoding='utf-8') as f:
            f.write("30")
            
        creation_time = "2026-07-16T12:00:00"
        photo_tagging_trigger("SCREENSHOT_001", creation_time)
        
        # Verify JSON
        pending_path = self.sim._get_pending_path()
        with open(pending_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["id"], "SCREENSHOT_001")
            self.assertEqual(data[0]["delete_time"], "2026-07-16T12:30:00")

    def test_tc_f3_04_photo_tagging_disabled(self):
        # Setup status = 關閉
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        with open(self.sim._get_status_path(), 'w', encoding='utf-8') as f:
            f.write("關閉")
            
        creation_time = "2026-07-16T12:00:00"
        photo_tagging_trigger("PHOTO_002", creation_time)
        
        # Verify JSON does not exist or is empty
        pending_path = self.sim._get_pending_path()
        self.assertFalse(os.path.exists(pending_path))

    def test_tc_f3_05_photo_tagging_disabled_keeps_existing(self):
        # Setup existing item in JSON
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        existing_list = [{"id": "PHOTO_OLD", "delete_time": "2026-07-16T12:30:00"}]
        with open(self.sim._get_pending_path(), 'w', encoding='utf-8') as f:
            json.dump(existing_list, f, ensure_ascii=False)
            
        # Status = 關閉
        with open(self.sim._get_status_path(), 'w', encoding='utf-8') as f:
            f.write("關閉")
            
        photo_tagging_trigger("PHOTO_NEW", "2026-07-16T12:00:00")
        
        # Verify JSON still has only the old item
        with open(self.sim._get_pending_path(), 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["id"], "PHOTO_OLD")

    # Feature 4: Cleanup Automation
    def test_tc_f4_01_cleanup_single_expired(self):
        # Setup mock library
        self.photo_library["PHOTO_001"] = {
            "id": "PHOTO_001",
            "type": "photo",
            "creation_time": datetime(2026, 7, 16, 12, 0, 0),
            "status": "active"
        }
        # Setup pending delete with expired item
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        pending_list = [{"id": "PHOTO_001", "delete_time": "2026-07-16T12:30:00"}]
        with open(self.sim._get_pending_path(), 'w', encoding='utf-8') as f:
            json.dump(pending_list, f, ensure_ascii=False)
            
        cleanup_automation_shortcut("2026-07-16T12:35:00")
        
        # Verify photo library status
        self.assertEqual(self.photo_library["PHOTO_001"]["status"], "recently_deleted")
        # Verify JSON is empty
        with open(self.sim._get_pending_path(), 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(len(data), 0)

    def test_tc_f4_02_cleanup_unexpired(self):
        self.photo_library["PHOTO_002"] = {
            "id": "PHOTO_002",
            "type": "photo",
            "creation_time": datetime(2026, 7, 16, 12, 0, 0),
            "status": "active"
        }
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        pending_list = [{"id": "PHOTO_002", "delete_time": "2026-07-16T12:30:00"}]
        with open(self.sim._get_pending_path(), 'w', encoding='utf-8') as f:
            json.dump(pending_list, f, ensure_ascii=False)
            
        cleanup_automation_shortcut("2026-07-16T12:20:00")
        
        self.assertEqual(self.photo_library["PHOTO_002"]["status"], "active")
        with open(self.sim._get_pending_path(), 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(len(data), 1)

    def test_tc_f4_03_cleanup_batch_expired(self):
        for pid in ("P1", "P2", "P3"):
            self.photo_library[pid] = {
                "id": pid,
                "type": "photo",
                "creation_time": datetime(2026, 7, 16, 12, 0, 0),
                "status": "active"
            }
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        pending_list = [
            {"id": "P1", "delete_time": "2026-07-16T12:30:00"},
            {"id": "P2", "delete_time": "2026-07-16T12:30:00"},
            {"id": "P3", "delete_time": "2026-07-16T12:30:00"}
        ]
        with open(self.sim._get_pending_path(), 'w', encoding='utf-8') as f:
            json.dump(pending_list, f, ensure_ascii=False)
            
        cleanup_automation_shortcut("2026-07-16T12:40:00")
        
        for pid in ("P1", "P2", "P3"):
            self.assertEqual(self.photo_library[pid]["status"], "recently_deleted")
        with open(self.sim._get_pending_path(), 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(len(data), 0)

    # Feature 5: Delete Without Asking
    def test_tc_f5_01_cleanup_silent_with_delete_without_asking(self):
        self.sim.delete_without_asking = True
        self.photo_library["P_SILENT"] = {
            "id": "P_SILENT",
            "type": "photo",
            "creation_time": datetime(2026, 7, 16, 12, 0, 0),
            "status": "active"
        }
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        pending_list = [{"id": "P_SILENT", "delete_time": "2026-07-16T12:30:00"}]
        with open(self.sim._get_pending_path(), 'w', encoding='utf-8') as f:
            json.dump(pending_list, f, ensure_ascii=False)
            
        cleanup_automation_shortcut("2026-07-16T12:35:00")
        self.assertEqual(self.photo_library["P_SILENT"]["status"], "recently_deleted")

    def test_tc_f5_02_cleanup_prompt_when_not_delete_without_asking(self):
        self.sim.delete_without_asking = False
        self.sim.user_confirm_delete_response = "allow"
        self.photo_library["P_PROMPT"] = {
            "id": "P_PROMPT",
            "type": "photo",
            "creation_time": datetime(2026, 7, 16, 12, 0, 0),
            "status": "active"
        }
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        pending_list = [{"id": "P_PROMPT", "delete_time": "2026-07-16T12:30:00"}]
        with open(self.sim._get_pending_path(), 'w', encoding='utf-8') as f:
            json.dump(pending_list, f, ensure_ascii=False)
            
        cleanup_automation_shortcut("2026-07-16T12:35:00")
        self.assertEqual(self.photo_library["P_PROMPT"]["status"], "recently_deleted")

    def test_tc_f5_04_cleanup_user_denies(self):
        self.sim.delete_without_asking = False
        self.sim.user_confirm_delete_response = "deny"
        self.photo_library["P_DENIED"] = {
            "id": "P_DENIED",
            "type": "photo",
            "creation_time": datetime(2026, 7, 16, 12, 0, 0),
            "status": "active"
        }
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        pending_list = [{"id": "P_DENIED", "delete_time": "2026-07-16T12:30:00"}]
        with open(self.sim._get_pending_path(), 'w', encoding='utf-8') as f:
            json.dump(pending_list, f, ensure_ascii=False)
            
        cleanup_automation_shortcut("2026-07-16T12:35:00")
        self.assertEqual(self.photo_library["P_DENIED"]["status"], "active")
        with open(self.sim._get_pending_path(), 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(len(data), 1)

    def test_tc_f5_05_cleanup_permission_error(self):
        self.sim.has_photo_permission = False
        with self.assertRaises(PermissionError) as context:
            cleanup_automation_shortcut("2026-07-16T12:35:00")
        self.assertEqual(str(context.exception), "無法存取相簿，請檢查隱私設定。")

    # Feature 6: Traditional Chinese UI & Data Persistence
    def test_tc_f6_01_traditional_chinese_notifications(self):
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        with open(self.sim._get_status_path(), 'w', encoding='utf-8') as f:
            f.write("關閉")
        n1 = toggle_shortcut()
        self.assertEqual(n1, "自動刪除模式已開啟")
        
        n2 = toggle_shortcut()
        self.assertEqual(n2, "自動刪除模式已關閉")

    def test_tc_f6_02_traditional_chinese_options(self):
        options = ["30分鐘", "1小時", "2小時", "4小時", "6小時", "12小時", "24小時"]
        expected_minutes = ["30", "60", "120", "240", "360", "720", "1440"]
        for opt, val in zip(options, expected_minutes):
            timer_setting_shortcut(opt)
            with open(self.sim._get_timer_path(), 'r', encoding='utf-8') as f:
                self.assertEqual(f.read().strip(), val)

    def test_tc_f6_03_icloud_file_paths_exist(self):
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        status_path = self.sim._get_status_path()
        timer_path = self.sim._get_timer_path()
        pending_path = self.sim._get_pending_path()
        
        self.assertEqual(os.path.basename(status_path), "auto_delete_status.txt")
        self.assertEqual(os.path.basename(timer_path), "auto_delete_timer.txt")
        self.assertEqual(os.path.basename(pending_path), "pending_delete.json")
        self.assertTrue(os.path.dirname(status_path).endswith("Shortcuts"))

    def test_tc_f6_04_json_schema_validation(self):
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        with open(self.sim._get_status_path(), 'w', encoding='utf-8') as f:
            f.write("開啟")
        with open(self.sim._get_timer_path(), 'w', encoding='utf-8') as f:
            f.write("60")
            
        photo_tagging_trigger("PHOTO_SCHEMA_TEST", "2026-07-16T12:00:00")
        
        with open(self.sim._get_pending_path(), 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 1)
            item = data[0]
            self.assertIn("id", item)
            self.assertIn("delete_time", item)
            self.assertIsInstance(item["id"], str)
            self.assertIsInstance(item["delete_time"], str)
            dt = datetime.fromisoformat(item["delete_time"])
            self.assertEqual(dt.year, 2026)

    # ---------------------------------------------------------
    # Tier 2: Boundary & Corner Cases
    # ---------------------------------------------------------

    def test_tc_b1_01_toggle_status_corrupted(self):
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        with open(self.sim._get_status_path(), 'w', encoding='utf-8') as f:
            f.write("錯誤狀態123")
            
        notification = toggle_shortcut()
        self.assertEqual(notification, "自動刪除模式已開啟")
        with open(self.sim._get_status_path(), 'r', encoding='utf-8') as f:
            self.assertEqual(f.read().strip(), "開啟")

    def test_tc_b1_03_icloud_storage_full(self):
        self.sim.storage_full = True
        with self.assertRaises(OSError) as context:
            toggle_shortcut()
        self.assertEqual(str(context.exception), "檔案儲存失敗，請檢查 iCloud 空間")

    def test_tc_b2_03_timer_corrupted_fallback(self):
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        with open(self.sim._get_timer_path(), 'w', encoding='utf-8') as f:
            f.write("無效文字")
        with open(self.sim._get_status_path(), 'w', encoding='utf-8') as f:
            f.write("開啟")
            
        photo_tagging_trigger("P_FALLBACK", "2026-07-16T12:00:00")
        
        with open(self.sim._get_pending_path(), 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(data[0]["delete_time"], "2026-07-16T13:00:00")

    def test_tc_b2_04_timer_setting_invalid_option(self):
        with self.assertRaises(ValueError):
            timer_setting_shortcut("無效的選項")

    def test_tc_b3_01_photo_tagging_burst_mode(self):
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        with open(self.sim._get_status_path(), 'w', encoding='utf-8') as f:
            f.write("開啟")
        with open(self.sim._get_timer_path(), 'w', encoding='utf-8') as f:
            f.write("30")
            
        creation_time = "2026-07-16T12:00:00"
        for i in range(1, 11):
            photo_tagging_trigger(f"BURST_{i:03d}", creation_time)
            
        with open(self.sim._get_pending_path(), 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(len(data), 10)
            self.assertEqual(data[0]["id"], "BURST_001")
            self.assertEqual(data[9]["id"], "BURST_010")

    def test_tc_b3_03_photo_tagging_live_photo(self):
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        with open(self.sim._get_status_path(), 'w', encoding='utf-8') as f:
            f.write("開啟")
        with open(self.sim._get_timer_path(), 'w', encoding='utf-8') as f:
            f.write("30")
            
        self.photo_library["LIVE_001"] = {
            "id": "LIVE_001",
            "type": "live_photo",
            "creation_time": datetime(2026, 7, 16, 12, 0, 0),
            "status": "active"
        }
        
        photo_tagging_trigger("LIVE_001", "2026-07-16T12:00:00")
        cleanup_automation_shortcut("2026-07-16T12:45:00")
        
        self.assertEqual(self.photo_library["LIVE_001"]["status"], "recently_deleted")

    def test_tc_b3_05_photo_tagging_permission_error(self):
        self.sim.has_photo_permission = False
        with self.assertRaises(PermissionError) as context:
            photo_tagging_trigger("P_PERM_ERROR", "2026-07-16T12:00:00")
        self.assertEqual(str(context.exception), "無法取得照片資訊，請檢查隱私權限設定")

    def test_tc_b4_01_cleanup_json_corrupted(self):
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        with open(self.sim._get_pending_path(), 'w', encoding='utf-8') as f:
            f.write("非JSON格式的字串")
            
        msg = cleanup_automation_shortcut("2026-07-16T12:35:00")
        self.assertEqual(msg, "待刪除清單已損毀，已自動重置。")
        
        with open(self.sim._get_pending_path(), 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(data, [])

    def test_tc_b4_02_cleanup_large_batch(self):
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        pending_list = []
        for i in range(500):
            pid = f"BATCH_{i}"
            self.photo_library[pid] = {
                "id": pid,
                "type": "photo",
                "creation_time": datetime(2026, 7, 16, 12, 0, 0),
                "status": "active"
            }
            pending_list.append({"id": pid, "delete_time": "2026-07-16T12:30:00"})
            
        with open(self.sim._get_pending_path(), 'w', encoding='utf-8') as f:
            json.dump(pending_list, f, ensure_ascii=False)
            
        cleanup_automation_shortcut("2026-07-16T12:35:00")
        
        for i in range(500):
            self.assertEqual(self.photo_library[f"BATCH_{i}"]["status"], "recently_deleted")
        with open(self.sim._get_pending_path(), 'r', encoding='utf-8') as f:
            self.assertEqual(json.load(f), [])

    def test_tc_b4_03_cleanup_manually_deleted_by_user(self):
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        pending_list = [
            {"id": "PHOTO_USER_DEL", "delete_time": "2026-07-16T12:30:00"},
            {"id": "PHOTO_REMAIN", "delete_time": "2026-07-16T12:30:00"}
        ]
        self.photo_library["PHOTO_REMAIN"] = {
            "id": "PHOTO_REMAIN",
            "type": "photo",
            "creation_time": datetime(2026, 7, 16, 12, 0, 0),
            "status": "active"
        }
        with open(self.sim._get_pending_path(), 'w', encoding='utf-8') as f:
            json.dump(pending_list, f, ensure_ascii=False)
            
        cleanup_automation_shortcut("2026-07-16T12:35:00")
        
        self.assertEqual(self.photo_library["PHOTO_REMAIN"]["status"], "recently_deleted")
        with open(self.sim._get_pending_path(), 'r', encoding='utf-8') as f:
            self.assertEqual(json.load(f), [])

    def test_tc_b4_04_cleanup_exact_expiry_time(self):
        self.photo_library["P_EXACT"] = {
            "id": "P_EXACT",
            "type": "photo",
            "creation_time": datetime(2026, 7, 16, 12, 0, 0),
            "status": "active"
        }
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        pending_list = [{"id": "P_EXACT", "delete_time": "2026-07-16T12:30:00"}]
        with open(self.sim._get_pending_path(), 'w', encoding='utf-8') as f:
            json.dump(pending_list, f, ensure_ascii=False)
            
        cleanup_automation_shortcut("2026-07-16T12:30:00")
        self.assertEqual(self.photo_library["P_EXACT"]["status"], "recently_deleted")

    def test_tc_b4_05_cleanup_empty_json(self):
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        with open(self.sim._get_pending_path(), 'w', encoding='utf-8') as f:
            json.dump([], f)
            
        cleanup_automation_shortcut("2026-07-16T12:35:00")

    def test_tc_b5_01_cleanup_favorite_photo_prompt(self):
        self.sim.delete_without_asking = True
        self.sim.user_confirm_delete_response = "deny"
        
        self.photo_library["P_FAV"] = {
            "id": "P_FAV",
            "type": "photo",
            "creation_time": datetime(2026, 7, 16, 12, 0, 0),
            "status": "active",
            "favorite": True
        }
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        pending_list = [{"id": "P_FAV", "delete_time": "2026-07-16T12:30:00"}]
        with open(self.sim._get_pending_path(), 'w', encoding='utf-8') as f:
            json.dump(pending_list, f, ensure_ascii=False)
            
        msg = cleanup_automation_shortcut("2026-07-16T12:35:00")
        self.assertEqual(msg, "拒絕刪除")
        self.assertEqual(self.photo_library["P_FAV"]["status"], "active")

    # ---------------------------------------------------------
    # Tier 3: Cross-Feature Combinations
    # ---------------------------------------------------------

    def test_tc_c_01_cross_toggle_and_tag(self):
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        with open(self.sim._get_status_path(), 'w', encoding='utf-8') as f:
            f.write("關閉")
            
        photo_tagging_trigger("PHOTO_A", "2026-07-16T12:00:00")
        toggle_shortcut()
        photo_tagging_trigger("PHOTO_B", "2026-07-16T12:00:00")
        
        with open(self.sim._get_pending_path(), 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["id"], "PHOTO_B")

    def test_tc_c_02_cross_timer_change_and_tag(self):
        timer_setting_shortcut("30分鐘")
        with open(self.sim._get_status_path(), 'w', encoding='utf-8') as f:
            f.write("開啟")
            
        photo_tagging_trigger("PHOTO_A", "2026-07-16T12:00:00")
        timer_setting_shortcut("2小時")
        photo_tagging_trigger("PHOTO_B", "2026-07-16T12:05:00")
        
        with open(self.sim._get_pending_path(), 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]["delete_time"], "2026-07-16T12:30:00")
            self.assertEqual(data[1]["delete_time"], "2026-07-16T14:05:00")

    def test_tc_c_03_cross_timer_and_cleanup_precision(self):
        self.photo_library["P1"] = {"id": "P1", "status": "active"}
        self.photo_library["P2"] = {"id": "P2", "status": "active"}
        
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        pending_list = [
            {"id": "P1", "delete_time": "2026-07-16T12:30:00"},
            {"id": "P2", "delete_time": "2026-07-17T12:01:00"}
        ]
        with open(self.sim._get_pending_path(), 'w', encoding='utf-8') as f:
            json.dump(pending_list, f)
            
        cleanup_automation_shortcut("2026-07-16T12:35:00")
        
        self.assertEqual(self.photo_library["P1"]["status"], "recently_deleted")
        self.assertEqual(self.photo_library["P2"]["status"], "active")
        with open(self.sim._get_pending_path(), 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["id"], "P2")

    def test_tc_c_04_cross_toggle_disabled_does_not_affect_cleanup(self):
        self.photo_library["P_OLD"] = {"id": "P_OLD", "status": "active"}
        
        os.makedirs(self.sim.shortcuts_dir, exist_ok=True)
        with open(self.sim._get_status_path(), 'w', encoding='utf-8') as f:
            f.write("關閉")
        pending_list = [{"id": "P_OLD", "delete_time": "2026-07-16T12:30:00"}]
        with open(self.sim._get_pending_path(), 'w', encoding='utf-8') as f:
            json.dump(pending_list, f)
            
        cleanup_automation_shortcut("2026-07-16T12:35:00")
        self.assertEqual(self.photo_library["P_OLD"]["status"], "recently_deleted")

    def test_tc_c_06_cross_cleanup_json_missing(self):
        pending_path = self.sim._get_pending_path()
        self.assertFalse(os.path.exists(pending_path))
        
        cleanup_automation_shortcut("2026-07-16T12:35:00")

    # ---------------------------------------------------------
    # Tier 4: Real-World Scenarios
    # ---------------------------------------------------------

    def test_scenario_tc_r_01_shopping_receipt(self):
        toggle_shortcut()
        timer_setting_shortcut("2小時")
        
        self.photo_library["RECEIPT_001"] = {
            "id": "RECEIPT_001",
            "type": "photo",
            "creation_time": datetime(2026, 7, 16, 12, 0, 0),
            "status": "active"
        }
        photo_tagging_trigger("RECEIPT_001", "2026-07-16T12:00:00")
        
        with open(self.sim._get_pending_path(), 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(data[0]["delete_time"], "2026-07-16T14:00:00")
            
        cleanup_automation_shortcut("2026-07-16T14:05:00")
        
        self.assertEqual(self.photo_library["RECEIPT_001"]["status"], "recently_deleted")
        with open(self.sim._get_pending_path(), 'r', encoding='utf-8') as f:
            self.assertEqual(json.load(f), [])

    def test_scenario_tc_r_02_social_screenshot(self):
        toggle_shortcut()
        timer_setting_shortcut("30分鐘")
        
        self.photo_library["SCREENSHOT_002"] = {
            "id": "SCREENSHOT_002",
            "type": "screenshot",
            "creation_time": datetime(2026, 7, 16, 12, 0, 0),
            "status": "active"
        }
        photo_tagging_trigger("SCREENSHOT_002", "2026-07-16T12:00:00")
        
        cleanup_automation_shortcut("2026-07-16T12:35:00")
        self.assertEqual(self.photo_library["SCREENSHOT_002"]["status"], "recently_deleted")

    def test_scenario_tc_r_03_travel_photo_protection(self):
        timer_setting_shortcut("12小時")
        toggle_shortcut()
        
        self.photo_library["MAP_PHOTO_A"] = {
            "id": "MAP_PHOTO_A",
            "type": "photo",
            "creation_time": datetime(2026, 7, 16, 12, 0, 0),
            "status": "active"
        }
        photo_tagging_trigger("MAP_PHOTO_A", "2026-07-16T12:00:00")
        
        toggle_shortcut()
        
        self.photo_library["LANDSCAPE_B"] = {
            "id": "LANDSCAPE_B",
            "type": "photo",
            "creation_time": datetime(2026, 7, 16, 12, 5, 0),
            "status": "active"
        }
        photo_tagging_trigger("LANDSCAPE_B", "2026-07-16T12:05:00")
        
        cleanup_automation_shortcut("2026-07-17T01:05:00")
        
        self.assertEqual(self.photo_library["MAP_PHOTO_A"]["status"], "recently_deleted")
        self.assertEqual(self.photo_library["LANDSCAPE_B"]["status"], "active")

    def test_scenario_tc_r_04_classroom_slides(self):
        timer_setting_shortcut("12小時")
        toggle_shortcut()
        
        for i in range(1, 16):
            pid = f"SLIDE_{i:03d}"
            self.photo_library[pid] = {
                "id": pid,
                "type": "photo",
                "creation_time": datetime(2026, 7, 16, 9, 0, 0),
                "status": "active"
            }
            photo_tagging_trigger(pid, "2026-07-16T09:00:00")
            
        with open(self.sim._get_pending_path(), 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(len(data), 15)
            
        cleanup_automation_shortcut("2026-07-16T21:05:00")
        
        for i in range(1, 16):
            self.assertEqual(self.photo_library[f"SLIDE_{i:03d}"]["status"], "recently_deleted")
        with open(self.sim._get_pending_path(), 'r', encoding='utf-8') as f:
            self.assertEqual(json.load(f), [])

    def test_scenario_tc_r_05_low_storage_video_assets(self):
        timer_setting_shortcut("4小時")
        toggle_shortcut()
        
        for i in range(1, 6):
            pid = f"VIDEO_ASSET_{i}"
            self.photo_library[pid] = {
                "id": pid,
                "type": "video",
                "creation_time": datetime(2026, 7, 16, 12, 0, 0),
                "status": "active"
            }
            photo_tagging_trigger(pid, "2026-07-16T12:00:00")
            
        cleanup_automation_shortcut("2026-07-16T16:05:00")
        
        for i in range(1, 6):
            self.assertEqual(self.photo_library[f"VIDEO_ASSET_{i}"]["status"], "recently_deleted")


if __name__ == "__main__":
    unittest.main()
