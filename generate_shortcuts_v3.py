#!/usr/bin/env python3
"""
iPhone 照片自動清理系統 — 捷徑生成器 (v3)
======================================
只保留 3 個捷徑：
1. 1_切換自動刪除模式 (Control Center Switch - 自動初始化，顯示當前狀態)
2. 2_自動標記新照片 (自動初始化，預設 7 天)
3. 3_執行自動刪除清理 (定期清理已到期照片)
"""

import plistlib
import os
import uuid

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output_v3")

def make_uuid():
    return str(uuid.uuid4()).upper()

def attachment(variable_name, output_uuid=None, agg_type=None, output_name=None):
    if output_uuid:
        att = {
            "OutputUUID": output_uuid,
            "Type": "ActionOutput"
        }
        if output_name:
            att["OutputName"] = output_name
        return att
    else:
        att = {
            "Type": "Variable",
            "VariableName": variable_name,
        }
        if agg_type:
            att["Aggrandizements"] = [{"Type": "WFCoercionVariableAggrandizement", "CoercionItemClass": agg_type}]
        return att

def variable_parameter(variable_name, output_uuid=None, agg_type=None, output_name=None):
    return {
        "Value": attachment(variable_name, output_uuid, agg_type, output_name),
        "WFSerializationType": "WFTextTokenAttachment"
    }

def text_token_string(text):
    return {
        "Value": {
            "string": text,
            "attachmentsByRange": {}
        },
        "WFSerializationType": "WFTextTokenString"
    }

def text_token_attachment(variable_name, output_uuid=None, prefix="", suffix="", output_name=None):
    att = attachment(variable_name, output_uuid, output_name=output_name)
    token = f"{prefix}\uFFFC{suffix}"
    return {
        "Value": {
            "string": token,
            "attachmentsByRange": {
                f"{{{len(prefix)}, 1}}": att
            }
        },
        "WFSerializationType": "WFTextTokenString"
    }

def shortcut_base(name, icon_glyph=61440, icon_color=-1263359489):
    return {
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowMinimumClientVersionString": "900",
        "WFWorkflowClientVersion": "2602.0.5",
        "WFWorkflowClientRelease": "2602.0.5",
        "WFWorkflowIcon": {
            "WFWorkflowIconStartColor": icon_color,
            "WFWorkflowIconGlyphNumber": icon_glyph,
        },
        "WFWorkflowTypes": ["NCWidget", "WatchKit"],
        "WFWorkflowInputContentItemClasses": [
            "WFAppStoreAppContentItem",
            "WFArticleContentItem",
            "WFContactContentItem",
            "WFDateContentItem",
            "WFEmailAddressContentItem",
            "WFGenericFileContentItem",
            "WFImageContentItem",
            "WFiTunesProductContentItem",
            "WFLocationContentItem",
            "WFDCMapsLinkContentItem",
            "WFAVAssetContentItem",
            "WFPDFContentItem",
            "WFPhoneNumberContentItem",
            "WFRichTextContentItem",
            "WFSafariWebPageContentItem",
            "WFStringContentItem",
            "WFURLContentItem"
        ],
        "WFWorkflowActions": [],
        "WFWorkflowImportQuestions": [],
        "WFWorkflowName": name,
    }

# ─── Action Builders ─────────────────────────────────────────────────

def action_get_file(path, error_if_not_found=False):
    uid = make_uuid()
    return uid, {
        "WFWorkflowActionIdentifier": "is.workflow.actions.documentpicker.open",
        "WFWorkflowActionParameters": {
            "WFGetFilePath": text_token_string(path),
            "WFFileErrorIfNotFound": error_if_not_found,
            "WFShowFilePicker": False,
            "UUID": uid,
        }
    }

def action_save_file(path, input_uuid, overwrite=True, input_name="Text"):
    uid = make_uuid()
    return uid, {
        "WFWorkflowActionIdentifier": "is.workflow.actions.documentpicker.save",
        "WFWorkflowActionParameters": {
            "WFFilePath": text_token_string(path),
            "WFOverwriteFile": overwrite,
            "WFAskWhereToSave": False,
            "WFInput": variable_parameter("", output_uuid=input_uuid, output_name=input_name),
            "UUID": uid,
        }
    }

def action_text(content, is_token_string=False):
    uid = make_uuid()
    params = {"UUID": uid}
    if is_token_string:
        params["WFTextActionText"] = content
    else:
        params["WFTextActionText"] = text_token_string(content)
    return uid, {
        "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
        "WFWorkflowActionParameters": params,
    }

def action_list(items):
    uid = make_uuid()
    return uid, {
        "WFWorkflowActionIdentifier": "is.workflow.actions.list",
        "WFWorkflowActionParameters": {
            "WFItems": items,
            "UUID": uid,
        }
    }

def action_set_variable(name, input_uuid, input_name="Text"):
    return make_uuid(), {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": name,
            "WFInput": variable_parameter("", output_uuid=input_uuid, output_name=input_name),
        }
    }

def action_get_variable(name):
    uid = make_uuid()
    return uid, {
        "WFWorkflowActionIdentifier": "is.workflow.actions.getvariable",
        "WFWorkflowActionParameters": {
            "WFVariable": variable_parameter(name),
            "UUID": uid,
        }
    }

def action_if_begin(input_uuid, condition, value=None, input_is_variable=False, input_name="Text"):
    group_id = make_uuid()
    if input_is_variable:
        wf_input = {
            "Type": "Variable",
            "Variable": {
                "Value": attachment(input_uuid),
                "WFSerializationType": "WFTextTokenAttachment"
            }
        }
    else:
        wf_input = {
            "Type": "Variable",
            "Variable": {
                "Value": attachment("", output_uuid=input_uuid, output_name=input_name),
                "WFSerializationType": "WFTextTokenAttachment"
            }
        }
    params = {
        "GroupingIdentifier": group_id,
        "WFControlFlowMode": 0,
        "WFInput": wf_input,
        "WFCondition": condition,
    }
    if value is not None:
        params["WFConditionalActionString"] = str(value)
        params["WFConditionValue"] = value
    return group_id, {
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": params,
    }

def action_if_otherwise(group_id):
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": group_id,
            "WFControlFlowMode": 1,
        }
    }

def action_if_end(group_id):
    uid = make_uuid()
    return uid, {
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": group_id,
            "WFControlFlowMode": 2,
            "UUID": uid,
        }
    }

def action_create_folder(path):
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.file.createfolder",
        "WFWorkflowActionParameters": {
            "WFFilePath": path,
        }
    }

def action_show_notification(title, body):
    return make_uuid(), {
        "WFWorkflowActionIdentifier": "is.workflow.actions.notification",
        "WFWorkflowActionParameters": {
            "WFNotificationActionTitle": text_token_string(title),
            "WFNotificationActionBody": text_token_string(body) if isinstance(body, str) else body,
        }
    }

def action_choose_from_list(prompt, input_uuid):
    uid = make_uuid()
    return uid, {
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefromlist",
        "WFWorkflowActionParameters": {
            "WFChooseFromListActionPrompt": prompt,
            "WFInput": variable_parameter("", output_uuid=input_uuid),
            "UUID": uid,
        }
    }

def action_dictionary(items):
    uid = make_uuid()
    wf_items = []
    for key, val, vtype in items:
        item = {
            "WFKey": text_token_string(key),
            "WFItemType": vtype,
            "WFValue": text_token_string(str(val)) if isinstance(val, str) else val,
        }
        wf_items.append(item)
    return uid, {
        "WFWorkflowActionIdentifier": "is.workflow.actions.dictionary",
        "WFWorkflowActionParameters": {
            "WFItems": {
                "Value": {"WFDictionaryFieldValueItems": wf_items},
                "WFSerializationType": "WFDictionaryFieldValue",
            },
            "UUID": uid,
        }
    }

def action_get_dictionary_value(dict_uuid, key=None, get_type="Value", dict_name="Text"):
    uid = make_uuid()
    params = {
        "WFInput": variable_parameter("", output_uuid=dict_uuid, output_name=dict_name),
        "UUID": uid,
    }
    if get_type == "All Keys":
        params["WFGetDictionaryValueType"] = "All Keys"
    elif get_type == "All Values":
        params["WFGetDictionaryValueType"] = "All Values"
    else:
        params["WFGetDictionaryValueType"] = "Value"
        if key:
            params["WFDictionaryKey"] = text_token_string(key) if isinstance(key, str) else key
    return uid, {
        "WFWorkflowActionIdentifier": "is.workflow.actions.getvalueforkey",
        "WFWorkflowActionParameters": params,
    }

def action_find_photos(sort_by="Date Taken", order="Latest First", limit=None, filter_filename_uuid=None, filter_filename_name="Dictionary Value"):
    uid = make_uuid()
    params = {
        "WFContentItemSortProperty": sort_by,
        "WFContentItemSortOrder": order,
        "UUID": uid,
    }
    if limit is not None:
        params["WFContentItemLimitEnabled"] = True
        params["WFContentItemLimitNumber"] = limit
    if filter_filename_uuid:
        params["WFContentItemFilter"] = {
            "Value": {
                "WFActionParameterFilterPrefix": 1,
                "WFActionParameterFilterTemplates": [
                    {
                        "Property": "Filename",
                        "Operator": 4,  # is
                        "VariableOverrides": {},
                        "String": variable_parameter("", output_uuid=filter_filename_uuid, output_name=filter_filename_name),
                        "Unit": 4,
                    }
                ]
            },
            "WFSerializationType": "WFContentPredicateTableTemplate",
        }
    return uid, {
        "WFWorkflowActionIdentifier": "is.workflow.actions.filter.photos",
        "WFWorkflowActionParameters": params,
    }

def action_get_photo_detail(photo_uuid, detail="Filename", photo_name="Photos"):
    uid = make_uuid()
    return uid, {
        "WFWorkflowActionIdentifier": "is.workflow.actions.properties.photos",
        "WFWorkflowActionParameters": {
            "WFInput": variable_parameter("", output_uuid=photo_uuid, output_name=photo_name),
            "WFContentItemPropertyName": detail,
            "UUID": uid,
        }
    }

def action_delete_photos(photos_uuid, photos_name="Photos"):
    return make_uuid(), {
        "WFWorkflowActionIdentifier": "is.workflow.actions.deletephotos",
        "WFWorkflowActionParameters": {
            "WFInput": variable_parameter("", output_uuid=photos_uuid, output_name=photos_name),
        }
    }

def action_current_date():
    uid = make_uuid()
    return uid, {
        "WFWorkflowActionIdentifier": "is.workflow.actions.date",
        "WFWorkflowActionParameters": {
            "WFDateActionMode": "Current Date",
            "UUID": uid,
        }
    }

def action_adjust_date(date_uuid, magnitude_variable, unit="Minutes", operation="Add", date_name="Date"):
    uid = make_uuid()
    return uid, {
        "WFWorkflowActionIdentifier": "is.workflow.actions.adjustdate",
        "WFWorkflowActionParameters": {
            "WFDate": variable_parameter("", output_uuid=date_uuid, output_name=date_name),
            "WFDateActionMode": operation,
            "WFDuration": {
                "Value": {
                    "Unit": unit,
                    "Magnitude": variable_parameter(magnitude_variable),
                },
                "WFSerializationType": "WFQuantityFieldValue",
            },
            "UUID": uid,
        }
    }

def action_format_date(date_uuid, format_type="ISO 8601", date_name="Date"):
    uid = make_uuid()
    return uid, {
        "WFWorkflowActionIdentifier": "is.workflow.actions.format.date",
        "WFWorkflowActionParameters": {
            "WFDate": variable_parameter("", output_uuid=date_uuid, output_name=date_name),
            "WFDateFormatStyle": format_type,
            "UUID": uid,
        }
    }

def action_number(value):
    uid = make_uuid()
    return uid, {
        "WFWorkflowActionIdentifier": "is.workflow.actions.number",
        "WFWorkflowActionParameters": {
            "WFNumberActionNumber": value,
            "UUID": uid,
        }
    }

def action_count(input_uuid, input_name="Variable"):
    uid = make_uuid()
    return uid, {
        "WFWorkflowActionIdentifier": "is.workflow.actions.count",
        "WFWorkflowActionParameters": {
            "Input": variable_parameter("", output_uuid=input_uuid, output_name=input_name),
            "UUID": uid,
        }
    }

def action_repeat_each_begin(input_uuid, input_name="Variable"):
    group_id = make_uuid()
    return group_id, {
        "WFWorkflowActionIdentifier": "is.workflow.actions.repeat.each",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": group_id,
            "WFControlFlowMode": 0,
            "WFInput": variable_parameter("", output_uuid=input_uuid, output_name=input_name),
        }
    }

def action_repeat_each_end(group_id):
    uid = make_uuid()
    return uid, {
        "WFWorkflowActionIdentifier": "is.workflow.actions.repeat.each",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": group_id,
            "WFControlFlowMode": 2,
            "UUID": uid,
        }
    }

def action_add_to_variable(name, input_uuid, input_name="Dictionary"):
    return make_uuid(), {
        "WFWorkflowActionIdentifier": "is.workflow.actions.appendvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": name,
            "WFInput": variable_parameter("", output_uuid=input_uuid, output_name=input_name),
        }
    }

def action_get_dates_from(input_uuid, input_name="Text"):
    uid = make_uuid()
    return uid, {
        "WFWorkflowActionIdentifier": "is.workflow.actions.detect.date",
        "WFWorkflowActionParameters": {
            "WFInput": variable_parameter("", output_uuid=input_uuid, output_name=input_name),
            "UUID": uid,
        }
    }

# ═══════════════════════════════════════════════════════════════════════
#  SHORTCUT 1: 1_切換自動刪除模式 (含狀態顯示與自動初始化)
# ═══════════════════════════════════════════════════════════════════════

def build_toggle_shortcut():
    sc = shortcut_base("1_切換自動刪除模式", icon_glyph=59511, icon_color=4282601983)
    actions = sc["WFWorkflowActions"]

    # 1. 取得 status.txt
    file_uid, a = action_get_file("AutoDeletePhotos/status.txt", error_if_not_found=False)
    actions.append(a)
    
    # 存入變數
    _, a = action_set_variable("StatusFile", file_uid, input_name="File")
    actions.append(a)

    # 2. 將檔案轉為文字 (若檔案不存在，此文字為空)
    text_uid, a = action_text("placeholder")
    a["WFWorkflowActionParameters"]["WFTextActionText"] = text_token_attachment("StatusFile")
    actions.append(a)
    
    # 存入變數
    _, a = action_set_variable("StatusText", text_uid, input_name="Text")
    actions.append(a)

    # 3. 判斷狀態是否為「開啟」
    g_check, a = action_if_begin("StatusText", 4, "開啟", input_is_variable=True)
    actions.append(a)

    # 3a. 目前為「開啟」 -> 切換為「關閉」
    new_off_uid, a = action_text("關閉")
    actions.append(a)
    _, a = action_save_file("AutoDeletePhotos/status.txt", new_off_uid, overwrite=True)
    actions.append(a)
    _, a = action_show_notification("自動刪除模式", "🔴 自動刪除模式已關閉")
    actions.append(a)

    actions.append(action_if_otherwise(g_check))

    # 3b. 目前為「關閉」或不存在 -> 切換為「開啟」
    new_on_uid, a = action_text("開啟")
    actions.append(a)
    _, a = action_save_file("AutoDeletePhotos/status.txt", new_on_uid, overwrite=True)
    actions.append(a)
    _, a = action_show_notification("自動刪除模式", "🟢 自動刪除模式已開啟 (7天自動刪除)")
    actions.append(a)

    _, a = action_if_end(g_check)
    actions.append(a)

    return sc

# ═══════════════════════════════════════════════════════════════════════
#  SHORTCUT 2: 2_自動標記新照片 (自動初始化，預設 7 天)
# ═══════════════════════════════════════════════════════════════════════

def build_tag_shortcut():
    sc = shortcut_base("2_自動標記新照片", icon_glyph=59470, icon_color=-16728321)
    actions = sc["WFWorkflowActions"]

    # ── 1. 讀取狀態 ──
    file_uid, a = action_get_file("AutoDeletePhotos/status.txt", error_if_not_found=False)
    actions.append(a)
    
    _, a = action_set_variable("StatusFile", file_uid, input_name="File")
    actions.append(a)

    # 2. 將檔案轉為文字 (若檔案不存在，此文字為空)
    status_text_uid, a = action_text("placeholder")
    a["WFWorkflowActionParameters"]["WFTextActionText"] = text_token_attachment("StatusFile")
    actions.append(a)
    
    _, a = action_set_variable("StatusText", status_text_uid, input_name="Text")
    actions.append(a)

    # ── 2. 如果狀態為「開啟」 ──
    g2, a = action_if_begin("StatusText", 4, "開啟", input_is_variable=True)
    actions.append(a)

    # ── 3. 預設刪除時間為 7 天 (10080 分鐘) ──
    dur_uid, a = action_number(10080)
    actions.append(a)
    _, a = action_set_variable("Duration", dur_uid, input_name="Number")
    actions.append(a)

    # ── 4. 讀取上次標記時間 last_tag_time.txt ──
    last_tag_uid, a = action_get_file("AutoDeletePhotos/last_tag_time.txt", error_if_not_found=False)
    actions.append(a)
    
    _, a = action_set_variable("LastTagFile", last_tag_uid, input_name="File")
    actions.append(a)
    
    # 將上次標記時間轉為文字
    last_tag_text_uid, a = action_text("placeholder")
    a["WFWorkflowActionParameters"]["WFTextActionText"] = text_token_attachment("LastTagFile")
    actions.append(a)
    
    _, a = action_set_variable("LastTagText", last_tag_text_uid, input_name="Text")
    actions.append(a)

    # ── 5. 取得目前日期 ──
    now_uid, a = action_current_date()
    actions.append(a)
    _, a = action_set_variable("Now", now_uid, input_name="Date")
    actions.append(a)

    # ── 6. 讀取現有待刪除清單 ──
    list_file_uid, a = action_get_file("AutoDeletePhotos/pending_list.json", error_if_not_found=False)
    actions.append(a)
    
    _, a = action_set_variable("ListFile", list_file_uid, input_name="File")
    actions.append(a)
    
    list_text_uid, a = action_text("placeholder")
    a["WFWorkflowActionParameters"]["WFTextActionText"] = text_token_attachment("ListFile")
    actions.append(a)
    
    _, a = action_set_variable("ListText", list_text_uid, input_name="Text")
    actions.append(a)
    
    g_list, a = action_if_begin("ListText", 100, input_is_variable=True)
    actions.append(a)
    
    existing_vals_uid, a = action_get_dictionary_value(list_text_uid, get_type="All Values", dict_name="Text")
    actions.append(a)
    
    _, a = action_set_variable("PhotoList", existing_vals_uid, input_name="Dictionary Value")
    actions.append(a)
    
    actions.append(action_if_otherwise(g_list))
    _, a = action_if_end(g_list)
    actions.append(a)

    # ── 7. 尋找相片 ──
    g_last, a = action_if_begin("LastTagText", 100, input_is_variable=True)
    actions.append(a)

    last_date_uid, a = action_get_dates_from(last_tag_text_uid, input_name="Text")
    actions.append(a)
    _, a = action_set_variable("LastTagDate", last_date_uid, input_name="Dates")
    actions.append(a)

    # 最新 20 張（避免大量相片效能差）
    photos_multi_uid, a = action_find_photos(sort_by="Date Taken", order="Latest First", limit=20)
    actions.append(a)
    _, a = action_set_variable("AllRecentPhotos", photos_multi_uid, input_name="Photos")
    actions.append(a)

    actions.append(action_if_otherwise(g_last))

    # 首次執行，僅處理最新 1 張以利安全初始化
    photos_single_uid, a = action_find_photos(sort_by="Date Taken", order="Latest First", limit=1)
    actions.append(a)
    _, a = action_set_variable("AllRecentPhotos", photos_single_uid, input_name="Photos")
    actions.append(a)

    _, a = action_if_end(g_last)
    actions.append(a)

    # ── 8. 計算到期日期 ──
    delete_at_uid, a = action_adjust_date(now_uid, "Duration", unit="Minutes", operation="Add")
    actions.append(a)
    _, a = action_set_variable("DeleteAt", delete_at_uid, input_name="Adjusted Date")
    actions.append(a)

    delete_at_iso_uid, a = action_format_date(delete_at_uid, "ISO 8601", date_name="Adjusted Date")
    actions.append(a)
    _, a = action_set_variable("DeleteAtISO", delete_at_iso_uid, input_name="Formatted Date")
    actions.append(a)

    now_iso_uid, a = action_format_date(now_uid, "ISO 8601")
    actions.append(a)
    _, a = action_set_variable("NowISO", now_iso_uid, input_name="Formatted Date")
    actions.append(a)

    # ── 9. 迴圈檢查新拍攝的相片 ──
    photos_var_uid, a = action_get_variable("AllRecentPhotos")
    actions.append(a)

    loop_gid, a = action_repeat_each_begin(photos_var_uid)
    actions.append(a)

    repeat_item_dict = {
        "Value": {"Type": "Variable", "VariableName": "Repeat Item"},
        "WFSerializationType": "WFTextTokenAttachment",
    }

    taken_date_uid, a = action_get_photo_detail(make_uuid(), "Date Taken")
    a["WFWorkflowActionParameters"]["WFInput"] = repeat_item_dict
    actions.append(a)
    _, a = action_set_variable("PhotoDate", taken_date_uid, input_name="Photo Detail")
    actions.append(a)

    g_check_time, a = action_if_begin("LastTagText", 100, input_is_variable=True)
    actions.append(a)

    # 照片拍攝時間晚於上次標記時間 -> 標記新照片 (直接比對變數 PhotoDate)
    g_new_photo, a = action_if_begin("PhotoDate", 3, input_is_variable=True) # 3 = is after
    a["WFWorkflowActionParameters"]["WFDate"] = variable_parameter("LastTagDate")
    actions.append(a)

    fname_uid, a = action_get_photo_detail(make_uuid(), "Filename")
    a["WFWorkflowActionParameters"]["WFInput"] = repeat_item_dict
    actions.append(a)
    _, a = action_set_variable("PhotoID", fname_uid, input_name="Photo Detail")
    actions.append(a)

    entry_dict_uid, a = action_dictionary([
        ("id", text_token_attachment("PhotoID"), 0),
        ("captured_at", text_token_attachment("NowISO"), 0),
        ("delete_at", text_token_attachment("DeleteAtISO"), 0),
    ])
    actions.append(a)

    _, a = action_add_to_variable("PhotoList", entry_dict_uid)
    actions.append(a)

    _, a = action_add_to_variable("NewTags", entry_dict_uid)
    actions.append(a)

    _, a = action_if_end(g_new_photo)
    actions.append(a)

    # 首次執行，直接標記
    actions.append(action_if_otherwise(g_check_time))

    fname_uid2, a = action_get_photo_detail(make_uuid(), "Filename")
    a["WFWorkflowActionParameters"]["WFInput"] = repeat_item_dict
    actions.append(a)
    _, a = action_set_variable("PhotoID", fname_uid2, input_name="Photo Detail")
    actions.append(a)

    entry_dict_uid2, a = action_dictionary([
        ("id", text_token_attachment("PhotoID"), 0),
        ("captured_at", text_token_attachment("NowISO"), 0),
        ("delete_at", text_token_attachment("DeleteAtISO"), 0),
    ])
    actions.append(a)

    _, a = action_add_to_variable("PhotoList", entry_dict_uid2)
    actions.append(a)

    _, a = action_add_to_variable("NewTags", entry_dict_uid2)
    actions.append(a)

    _, a = action_if_end(g_check_time)
    actions.append(a)

    _, a = action_repeat_each_end(loop_gid)
    actions.append(a)

    # ── 10. 儲存更新後的 pending_list.json ──
    photo_list_var_uid, a = action_get_variable("PhotoList")
    actions.append(a)
    _, a = action_save_file("AutoDeletePhotos/pending_list.json", photo_list_var_uid, overwrite=True, input_name="Variable")
    actions.append(a)

    # ── 11. 儲存更新後的 last_tag_time ──
    now_iso_var_uid, a = action_get_variable("NowISO")
    actions.append(a)
    _, a = action_save_file("AutoDeletePhotos/last_tag_time.txt", now_iso_var_uid, overwrite=True, input_name="Variable")
    actions.append(a)

    # ── 12. 發送通知 ──
    new_tags_var_uid, a = action_get_variable("NewTags")
    actions.append(a)
    
    new_tags_count_uid, a = action_count(new_tags_var_uid)
    actions.append(a)
    _, a = action_set_variable("NewTagsCount", new_tags_count_uid, input_name="Count")
    actions.append(a)
    
    # 只有當有新標記的照片時才發通知，減少日常干擾 (2 = is greater than)
    g_notify, a = action_if_begin("NewTagsCount", 2, 0, input_is_variable=True)
    actions.append(a)

    _, a = action_show_notification(
        "新照片已標記",
        text_token_attachment("NewTagsCount", prefix="📸 已排程 ", suffix=" 張照片，將在 7 天後刪除"),
    )
    actions.append(a)
    
    _, a = action_if_end(g_notify)
    actions.append(a)

    actions.append(action_if_otherwise(g2))
    _, a = action_if_end(g2)
    actions.append(a)

    return sc

# ═══════════════════════════════════════════════════════════════════════
#  SHORTCUT 3: 3_執行自動刪除清理 (定期清理已到期照片)
# ═══════════════════════════════════════════════════════════════════════

def build_cleanup_shortcut():
    sc = shortcut_base("3_執行自動刪除清理", icon_glyph=59946, icon_color=-7257601)
    actions = sc["WFWorkflowActions"]

    # 1. 取得待刪除清單
    file_uid, a = action_get_file("AutoDeletePhotos/pending_list.json", error_if_not_found=False)
    actions.append(a)
    
    _, a = action_set_variable("ListFile", file_uid, input_name="File")
    actions.append(a)

    json_text_uid, a = action_text("placeholder")
    a["WFWorkflowActionParameters"]["WFTextActionText"] = text_token_attachment("ListFile")
    actions.append(a)

    entries_uid, a = action_get_dictionary_value(json_text_uid, get_type="All Values", dict_name="Text")
    actions.append(a)
    _, a = action_set_variable("AllEntries", entries_uid, input_name="Dictionary Value")
    actions.append(a)

    # 取得目前日期
    now_uid, a = action_current_date()
    actions.append(a)
    _, a = action_set_variable("Now", now_uid, input_name="Date")
    actions.append(a)

    # 迴圈檢查每一個項目
    loop_gid, a = action_repeat_each_begin(entries_uid, input_name="Dictionary Value")
    actions.append(a)

    repeat_item_dict = {
        "Value": {"Type": "Variable", "VariableName": "Repeat Item"},
        "WFSerializationType": "WFTextTokenAttachment",
    }

    del_at_str_uid, a = action_get_dictionary_value(make_uuid(), key="delete_at")
    a["WFWorkflowActionParameters"]["WFInput"] = repeat_item_dict
    actions.append(a)

    del_at_date_uid, a = action_get_dates_from(del_at_str_uid, input_name="Dictionary Value")
    actions.append(a)
    _, a = action_set_variable("DeleteAtDate", del_at_date_uid, input_name="Dates")
    actions.append(a)

    # 如果日期解析成功
    g_parse, a = action_if_begin(del_at_date_uid, 100, input_name="Dates")
    actions.append(a)

    # 如果目前時間晚於或等於刪除時間 (Now >= DeleteAtDate) (直接比對變數 Now)
    g_expired, a = action_if_begin("Now", 3, input_is_variable=True) # 3 = is after
    a["WFWorkflowActionParameters"]["WFDate"] = variable_parameter("DeleteAtDate")
    actions.append(a)

    photo_id_uid, a = action_get_dictionary_value(make_uuid(), key="id")
    a["WFWorkflowActionParameters"]["WFInput"] = repeat_item_dict
    actions.append(a)

    found_uid, a = action_find_photos(filter_filename_uuid=photo_id_uid, filter_filename_name="Dictionary Value")
    actions.append(a)

    g_found, a = action_if_begin(found_uid, 100, input_name="Photos")
    actions.append(a)

    # 自動刪除 (設定不詢問)
    _, a = action_delete_photos(found_uid, photos_name="Photos")
    actions.append(a)

    # 記錄有刪除照片
    deleted_marker_uid, a = action_number(1)
    actions.append(a)
    _, a = action_add_to_variable("DeletedItems", deleted_marker_uid, input_name="Number")
    actions.append(a)

    actions.append(action_if_otherwise(g_found))
    _, a = action_if_end(g_found)
    actions.append(a)

    # 未到期 -> 保留並寫回 KeepList
    actions.append(action_if_otherwise(g_expired))

    keep_item_uid, a = action_get_variable("Repeat Item")
    a["WFWorkflowActionParameters"]["WFVariable"] = repeat_item_dict
    actions.append(a)
    _, a = action_add_to_variable("KeepList", keep_item_uid, input_name="Variable")
    actions.append(a)

    _, a = action_if_end(g_expired)
    actions.append(a)

    # 解析失敗 -> 保留
    actions.append(action_if_otherwise(g_parse))

    keep_safe_uid, a = action_get_variable("Repeat Item")
    a["WFWorkflowActionParameters"]["WFVariable"] = repeat_item_dict
    actions.append(a)
    _, a = action_add_to_variable("KeepList", keep_safe_uid, input_name="Variable")
    actions.append(a)

    _, a = action_if_end(g_parse)
    actions.append(a)

    _, a = action_repeat_each_end(loop_gid)
    actions.append(a)

    # 儲存 KeepList 回 pending_list.json
    keep_var_uid, a = action_get_variable("KeepList")
    actions.append(a)
    _, a = action_save_file("AutoDeletePhotos/pending_list.json", keep_var_uid, overwrite=True, input_name="Variable")
    actions.append(a)

    # 檢查是否有刪除照片並發送通知
    deleted_items_uid, a = action_get_variable("DeletedItems")
    actions.append(a)
    
    deleted_count_uid, a = action_count(deleted_items_uid, input_name="Variable")
    actions.append(a)
    _, a = action_set_variable("DeletedCount", deleted_count_uid, input_name="Count")
    actions.append(a)
    
    # 只有當 DeletedCount 大於 0 時才發送通知 (2 = is greater than)
    g_notify, a = action_if_begin("DeletedCount", 2, 0, input_is_variable=True)
    actions.append(a)
    
    _, a = action_show_notification(
        "自動清理完成",
        text_token_attachment("DeletedCount", prefix="🗑️ 已清理 ", suffix=" 張已到期的過期照片。"),
    )
    actions.append(a)
    
    _, a = action_if_end(g_notify)
    actions.append(a)

    return sc

# ═══════════════════════════════════════════════════════════════════════
#  Main: Generate all v3 .shortcut files
# ═══════════════════════════════════════════════════════════════════════

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    shortcuts = [
        ("1_切換自動刪除模式.shortcut", build_toggle_shortcut()),
        ("2_自動標記新照片.shortcut", build_tag_shortcut()),
        ("3_執行自動刪除清理.shortcut", build_cleanup_shortcut()),
    ]

    for filename, data in shortcuts:
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "wb") as f:
            plistlib.dump(data, f, fmt=plistlib.FMT_BINARY)
        print(f"✅ 已生成 v3: {filepath}")

    print(f"\n🎉 v3 捷徑檔案生成完畢，輸出至: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
