"""Independent current-snapshot audit for Interface Modernization Stage 4.

Audits the visible reference top toolbar, its native menus, compatibility action
identity, compact/desktop modes, geometry and duplicate visual commands.
"""
from __future__ import annotations
import argparse, hashlib, json, os, platform, subprocess, sys, re
from pathlib import Path
from typing import Any, cast
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut
from PySide6.QtWidgets import QApplication, QLineEdit, QToolButton, QWidgetAction
from scripts.audit_ui_capture import AuditConfig
from src.core.commands import CommandManager
from src.models.scene import Scene
from src.ui.main_window import MainWindow
from src.ui.theme_qss import QSS
ROOT=Path(__file__).resolve().parents[1]
HOST_PATH_RE=re.compile(r"(?i)[A-Z]:[\\/](?:Users|Documents and Settings)[\\/][^\r\n\"<>]+")
RESOLUTIONS={"1280x720":(1280,720),"1366x768":(1366,768),"1920x1080":(1920,1080)}

def sha256(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
def git(*args:str)->str:
    return subprocess.run(["git",*args],cwd=ROOT,check=True,capture_output=True,text=True,encoding="utf-8").stdout.strip()
def rect(widget:Any)->list[int]:
    g=widget.geometry(); return [g.x(),g.y(),g.width(),g.height()]
def safe(text:str)->str:return HOST_PATH_RE.sub("<host-path-redacted>",text)
def run(command:list[str],cwd:Path,log:Path)->dict[str,Any]:
    result=subprocess.run(command,cwd=cwd,capture_output=True,text=True,encoding="utf-8",errors="replace",check=False)
    log.write_text(safe(result.stdout+result.stderr),encoding="utf-8",newline="\n")
    return {"command":[".venv/Scripts/python.exe" if x==sys.executable else x for x in command],"returncode":result.returncode,"log":log.name}
def menu_texts(button:QToolButton)->list[str]:
    return [action.text() for action in button.menu().actions()] if button.menu() else []
def action_record(action:Any,button:Any|None=None)->dict[str,Any]:
    return {"text":action.text(),"tooltip":action.toolTip(),"accessible_name":action.property("accessibleName"),"icon_key":action.property("iconKey"),"icon_null":action.icon().isNull(),"button":None if button is None else {"object_name":button.objectName(),"accessible_name":button.accessibleName(),"focus_policy":button.focusPolicy().name,"geometry":rect(button)}}

def contract()->dict[str,Any]:
    app=QApplication.instance() or QApplication(sys.argv); cast(Any,app).setStyleSheet(QSS)
    failures:list[str]=[]; resolutions:dict[str,Any]={}; duplicate_check:dict[str,Any]={}; menus:dict[str,Any]={}
    for label,(width,height) in RESOLUTIONS.items():
        scene=Scene(); scene.cmd=CommandManager(); window=MainWindow(scene,AuditConfig()); window.resize(width,height); window.show(); app.processEvents()
        toolbar=window.reference_top_toolbar
        expected_style="ToolButtonIconOnly" if width<1450 else "ToolButtonTextBesideIcon"
        if toolbar.objectName()!="reference_top_toolbar": failures.append(f"{label}: visible toolbar object name drifted")
        if not toolbar.isVisibleTo(window): failures.append(f"{label}: visible top toolbar hidden")
        if toolbar.isMovable() or toolbar.isFloatable(): failures.append(f"{label}: visible top toolbar movable/floatable")
        if toolbar.toolButtonStyle().name!=expected_style: failures.append(f"{label}: style {toolbar.toolButtonStyle().name} != {expected_style}")
        if sum(a.isSeparator() for a in toolbar.actions())!=5: failures.append(f"{label}: expected five native visible group boundaries")
        out=[]; metadata={}
        for action in toolbar.actions():
            if action.isSeparator(): continue
            button=action.defaultWidget() if isinstance(action,QWidgetAction) else toolbar.widgetForAction(action)
            if button is None: failures.append(f"{label}: no widget for visible toolbar item {action.text()}"); continue
            if not button.isVisibleTo(window) and button.objectName() not in {"reference_command_search"}: continue
            g=button.geometry(); inside=g.left()>=0 and g.top()>=0 and g.right()<toolbar.width() and g.bottom()<toolbar.height()
            if button.objectName()!="qt_toolbar_ext_button" and not inside:
                out.append(button.objectName()); failures.append(f"{label}: visible control clips {button.objectName()}")
            if isinstance(button,QToolButton) and button.objectName()!="qt_toolbar_ext_button":
                if not button.accessibleName(): failures.append(f"{label}: accessible name missing {button.objectName()}")
                if button.focusPolicy()==Qt.FocusPolicy.NoFocus: failures.append(f"{label}: focus disabled {button.objectName()}")
                if button.icon().isNull() and button.objectName() != "reference_menu_button": failures.append(f"{label}: icon missing {button.objectName()}")
            metadata[button.objectName()]={"text":button.text() if hasattr(button,"text") else "","accessible_name":button.accessibleName() if hasattr(button,"accessibleName") else "","focus_policy":button.focusPolicy().name if hasattr(button,"focusPolicy") else None,"geometry":rect(button)}
        search=window.reference_command_search
        if not search.isVisibleTo(window) and width>=1450: failures.append(f"{label}: command search hidden in desktop mode")
        if search.isVisibleTo(window):
            g=search.geometry()
            if g.left()<0 or g.top()<0 or g.right()>=toolbar.width() or g.bottom()>=toolbar.height(): failures.append(f"{label}: command search clips")
            if not search.accessibleName() or search.placeholderText()!="Ctrl+K": failures.append(f"{label}: command search metadata drifted")
        resolutions[label]={"window_size":[width,height],"toolbar_geometry":rect(toolbar),"style":toolbar.toolButtonStyle().name,"separator_count":sum(a.isSeparator() for a in toolbar.actions()),"clipped":out,"controls":metadata,"overflow_visible":bool(toolbar.findChild(QToolButton,"qt_toolbar_ext_button") and toolbar.findChild(QToolButton,"qt_toolbar_ext_button").isVisible())}
        if label=="1280x720":
            fit=window.tool_palette.navigation_actions["fit_view"]; focus=window.tool_palette.navigation_actions["focus_selected"]; move=window.tool_palette.navigation_actions["move_viewport"]; select=window.tool_palette._tool_actions["selection"]
            visible_ids={"fit":id(fit),"focus":id(focus),"pan":id(move),"select":id(select)}
            duplicate_check={"canonical_action_ids":visible_ids,"fit_shared_with_rail":toolbar.widgetForAction(fit) is not None and window.reference_tool_palette.widgetForAction(fit) is not None,"focus_shared_with_rail":toolbar.widgetForAction(focus) is not None and window.reference_tool_palette.widgetForAction(focus) is not None,"pan_shared_with_rail":toolbar.widgetForAction(move) is not None and window.reference_tool_palette.widgetForAction(move) is not None,"select_shared_with_rail":toolbar.widgetForAction(select) is not None and window.reference_tool_palette.widgetForAction(select) is not None}
            if not all(duplicate_check[k] for k in duplicate_check if k.endswith("shared_with_rail")): failures.append("visible duplicate navigation controls are not backed by the canonical shared actions")
            direct_expected=[fit,window.act_100,focus,move,select,window.undo_action,window.redo_action]
            if not all(toolbar.widgetForAction(a) is not None for a in direct_expected): failures.append("one or more required direct top actions are not materialized")
            required_menus={"view":(window.act_grid,window.act_snap),"render":(window.act_lit,window.act_xray1,window.act_xray2,window.act_xray3,window.mask_viewer_action),"collision":(window.collision_overlay_action,window.act_export_collision_json,window.act_export_collision_txt),"edit":(window.act_clean,window.settings_action)}
            for name,items in required_menus.items():
                button=getattr(window,f"reference_{name}_button")
                actual=tuple(button.menu().actions())
                menus[name]={"button":button.objectName(),"actions":[a.text() for a in actual]}
                if actual!=items: failures.append(f"visible {name} menu membership/order drifted")
            file_actions=(window.open_project_action,window.open_image_action,window.save_project_action,window.act_export)
            if not all(toolbar.widgetForAction(a) is not None for a in file_actions): failures.append("File group is missing a visible required action")
            if window.act_fit in window.view_menu.actions() and window.act_fit is fit: failures.append("Fit action unexpectedly duplicated by identity in canonical migration")
            shortcut_keys={shortcut.key().toString() for shortcut in window.findChildren(QShortcut)}
            if "Ctrl+K" not in shortcut_keys: failures.append("Ctrl+K command palette shortcut missing")
            identities=(fit,focus,move,select,window.undo_action,window.redo_action,window.act_clean,window.settings_action)
            window.set_language("pt"); app.processEvents()
            if identities!=(fit,focus,move,select,window.undo_action,window.redo_action,window.act_clean,window.settings_action): failures.append("action identity changed during translation")
        window.close(); app.processEvents()
    return {"status":"PASS" if not failures else "FAIL","failure_count":len(failures),"failures":failures,"resolutions":resolutions,"duplicate_check":duplicate_check,"menus":menus}

def main()->int:
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path,required=True); args=parser.parse_args(); output=args.output.resolve(); output.mkdir(parents=True,exist_ok=True); raw=output/"raw-captures"; visual=output/"visual-audit"; raw.mkdir(exist_ok=True); visual.mkdir(exist_ok=True)
    capture=run([sys.executable,"scripts/audit_ui_capture.py","--output",str(raw)],ROOT,output/"capture.log")
    visual_run=run([sys.executable,"scripts/audit_visual_artifacts.py","--input",str(raw),"--output",str(visual)],ROOT,output/"visual-audit.log")
    visual_report=json.loads((visual/"visual-audit-report.json").read_text(encoding="utf-8")) if (visual/"visual-audit-report.json").is_file() else {"status":"MISSING","finding_count":None}
    live=contract(); report={"schema":"neoeng.stage4-contract-audit","schema_version":1,"stage":4,"stage_name":"Barra superior agrupada","source_state":{"commit":git("rev-parse","HEAD"),"branch":git("rev-parse","--abbrev-ref","HEAD"),"worktree_clean":not bool(git("status","--porcelain"))},"environment":{"platform":platform.platform(),"python":platform.python_version(),"qt_platform":os.environ.get("QT_QPA_PLATFORM"),"resolutions":["1280x720","1366x768","1920x1080"]},"commands":{"capture":capture,"visual_audit":visual_run},"checks":{"capture_status":"PASS" if capture["returncode"]==0 else "FAIL","visual_status":visual_report.get("status"),"visual_finding_count":visual_report.get("finding_count"),"live_contract":live},"historical_reference":{"path":"docs/evidence/artifacts/ui-modernization-stage4-20260822/stage4-top-toolbar-report.json","classification":"HISTORICAL_ONLY"},"limitations":["Offscreen captures prove current Qt geometry and automated visual invariants; native Windows DPI capture remains separately environment-specific.","Menus and command palette are intentional alternate access paths to the same QAction objects, not duplicate command implementations.","Viewport HUD, gizmo, lateral panels and scenario editor remain outside Stage 4 and are not counted as evidence here."]}
    report["status"]="PASS" if capture["returncode"]==0 and visual_run["returncode"]==0 and visual_report.get("status")=="PASS" and live["status"]=="PASS" else "FAIL"
    (output/"stage4-contract-audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    (output/"stage4-contract-audit.md").write_text("\n".join(["# Auditoria atual da Etapa 4","",f"- Status: `{report['status']}`",f"- Commit: `{report['source_state']['commit']}`",f"- Captura: `{report['checks']['capture_status']}`",f"- Auditor visual: `{report['checks']['visual_status']}` com `{report['checks']['visual_finding_count']}` achados",f"- Contrato live: `{live['status']}` com `{live['failure_count']}` achados","","Acesso por menus/command palette foi classificado por identidade de QAction; controles visuais duplicados são tratados como falha."]) + "\n",encoding="utf-8",newline="\n")
    entries={}
    for item in sorted(output.rglob("*")):
        if item.is_file() and item.name!="stage4-artifact-index.json": entries[item.relative_to(output).as_posix()]={"bytes":item.stat().st_size,"sha256":sha256(item)}
    (output/"stage4-artifact-index.json").write_text(json.dumps({"schema":"neoeng.stage4-artifact-index","schema_version":1,"files":entries},indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps({"status":report["status"],"live":live["status"],"visual":visual_report.get("status"),"failures":live["failure_count"]},sort_keys=True)); return 0 if report["status"]=="PASS" else 1
if __name__=="__main__": raise SystemExit(main())
