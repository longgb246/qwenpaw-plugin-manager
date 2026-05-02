# -*- coding: utf-8 -*-
"""
Plugin Manager for QwenPaw/CoPaw
通过独立 HTTP 服务（端口 39149）提供插件管理 API

兼容性：
  - 自动检测配置目录：QWENPAW_WORKING_DIR > ~/.copaw > ~/.qwenpaw
  - 与 QwenPaw 源码 constant.py 中的 WORKING_DIR 逻辑保持一致
"""

import json
import os
import re
import shutil
import zipfile
import tempfile
import urllib.request
import threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

PLUGIN_ID = "plugin-manager"
SERVER_PORT = 39149

# ── 配置目录检测（兼容 .copaw 和 .qwenpaw） ──────────────────

def _detect_working_dir():
    """检测 QwenPaw/CoPaw 配置目录。

    优先级（与 QwenPaw 源码 constant.py 一致）：
      1. QWENPAW_WORKING_DIR 或 COPAW_WORKING_DIR 环境变量
      2. ~/.copaw（旧版，如果存在则沿用）
      3. ~/.qwenpaw（新版默认）
    """
    # 1. 环境变量
    explicit = os.environ.get("QWENPAW_WORKING_DIR") or os.environ.get(
        "COPAW_WORKING_DIR"
    )
    if explicit:
        return Path(explicit).expanduser().resolve()

    # 2. 旧版 ~/.copaw
    legacy = Path.home() / ".copaw"
    if legacy.exists():
        return legacy.resolve()

    # 3. 新版 ~/.qwenpaw
    return (Path.home() / ".qwenpaw").resolve()


WORKING_DIR = _detect_working_dir()
PLUGIN_DIR = WORKING_DIR / "plugins"
CONFIG_PATH = WORKING_DIR / "config.json"

# ── Helpers ────────────────────────────────────────────────────

def _get_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"plugins": {}}

def _save_config(config):
    backup = CONFIG_PATH.with_suffix(".json.bak")
    if CONFIG_PATH.exists():
        shutil.copy2(CONFIG_PATH, backup)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def _read_plugin_json(pdir):
    pj = pdir / "plugin.json"
    if pj.exists():
        with open(pj, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def _json_response(handler, data, status=200):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)

# ── Business Logic ─────────────────────────────────────────────

def list_plugins():
    config = _get_config()
    plugins_config = config.get("plugins", {})
    result = []
    seen = set()

    if PLUGIN_DIR.exists():
        for pdir in sorted(PLUGIN_DIR.iterdir()):
            if not pdir.is_dir() or pdir.name.startswith("."):
                continue
            info = _read_plugin_json(pdir)
            if not info:
                continue
            pid = info.get("id", pdir.name)
            seen.add(pid)
            enabled = plugins_config.get(pid, {}).get("enabled", True)
            result.append({
                "id": pid,
                "name": info.get("name", pid),
                "version": info.get("version", "0.0.0"),
                "description": info.get("description", ""),
                "author": info.get("author", ""),
                "enabled": enabled,
                "has_frontend": bool(info.get("entry", {}).get("frontend")),
                "has_backend": bool(info.get("entry", {}).get("backend")),
                "has_sidebar": info.get("meta", {}).get("has_sidebar", False),
                "path": str(pdir),
            })

    for pid, pconf in plugins_config.items():
        if pid not in seen:
            result.append({
                "id": pid,
                "name": pconf.get("name", pid),
                "version": pconf.get("version", "0.0.0"),
                "description": pconf.get("description", ""),
                "enabled": pconf.get("enabled", True),
                "missing": True,
                "path": "",
            })
    return result

def install_plugin(source):
    PLUGIN_DIR.mkdir(parents=True, exist_ok=True)

    if source.startswith("http://") or source.startswith("https://"):
        tmpdir = tempfile.mkdtemp()
        tmpzip = os.path.join(tmpdir, "plugin.zip")
        try:
            urllib.request.urlretrieve(source, tmpzip)
            with zipfile.ZipFile(tmpzip, "r") as zf:
                extract_dir = os.path.join(tmpdir, "extracted")
                zf.extractall(extract_dir)
                extracted = Path(extract_dir)
                # Handle nested dirs
                entries = list(extracted.iterdir())
                if len(entries) == 1 and entries[0].is_dir():
                    extracted = entries[0]
                for root, dirs, files in os.walk(str(extracted)):
                    if "plugin.json" in files:
                        extracted = Path(root)
                        break
                else:
                    return {"error": "压缩包中未找到 plugin.json"}

                info = _read_plugin_json(extracted)
                if not info:
                    return {"error": "无法解析 plugin.json"}
                pid = info.get("id")
                if not pid:
                    return {"error": "plugin.json 缺少 id"}

                dest = PLUGIN_DIR / pid
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(extracted, dest)

                config = _get_config()
                config.setdefault("plugins", {})[pid] = {
                    "name": info.get("name", pid),
                    "version": info.get("version", "0.0.0"),
                    "enabled": True,
                }
                _save_config(config)
                return {"success": True, "id": pid, "name": info.get("name"),
                        "message": f"插件 {info.get('name')} 安装成功！需重启生效。"}
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    else:
        source_path = Path(source)
        if not source_path.exists():
            return {"error": f"路径不存在: {source}"}
        if source_path.is_file() and source_path.suffix == ".zip":
            tmpdir = tempfile.mkdtemp()
            try:
                with zipfile.ZipFile(source_path, "r") as zf:
                    extract_dir = os.path.join(tmpdir, "extracted")
                    zf.extractall(extract_dir)
                    extracted = Path(extract_dir)
                    for root, dirs, files in os.walk(str(extracted)):
                        if "plugin.json" in files:
                            extracted = Path(root)
                            break
                    else:
                        return {"error": "ZIP 中未找到 plugin.json"}
                    info = _read_plugin_json(extracted)
                    if not info:
                        return {"error": "无法解析 plugin.json"}
                    pid = info.get("id")
                    dest = PLUGIN_DIR / pid
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(extracted, dest)
                    config = _get_config()
                    config.setdefault("plugins", {})[pid] = {
                        "name": info.get("name", pid),
                        "version": info.get("version", "0.0.0"),
                        "enabled": True,
                    }
                    _save_config(config)
                    return {"success": True, "id": pid, "name": info.get("name"),
                            "message": f"插件 {info.get('name')} 安装成功！需重启生效。"}
            finally:
                shutil.rmtree(tmpdir, ignore_errors=True)
        elif source_path.is_dir():
            info = _read_plugin_json(source_path)
            if not info:
                return {"error": "目录中未找到 plugin.json"}
            pid = info.get("id")
            dest = PLUGIN_DIR / pid
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(source_path, dest)
            config = _get_config()
            config.setdefault("plugins", {})[pid] = {
                "name": info.get("name", pid),
                "version": info.get("version", "0.0.0"),
                "enabled": True,
            }
            _save_config(config)
            return {"success": True, "id": pid, "name": info.get("name"),
                    "message": f"插件 {info.get('name')} 安装成功！需重启生效。"}
        return {"error": "不支持的源格式"}

def uninstall_plugin(plugin_id):
    if plugin_id == PLUGIN_ID:
        return {"error": "不能卸载插件管理器自身"}
    config = _get_config()
    if plugin_id not in config.get("plugins", {}):
        return {"error": f"插件 {plugin_id} 未安装"}
    plugin_path = PLUGIN_DIR / plugin_id
    if plugin_path.exists():
        shutil.rmtree(plugin_path)
    del config["plugins"][plugin_id]
    _save_config(config)

    # ── 清理 PROFILE.md 中的插件能力段落 ──
    _cleanup_profile_section(plugin_id)

    return {"success": True, "message": f"已卸载 {plugin_id}。需重启生效。"}

def _cleanup_profile_section(plugin_id):
    """从 PROFILE.md 中移除指定插件的 marker 段落。

    同时检查所有可能的 workspace 目录下的 PROFILE.md。
    """
    try:
        workspaces_dir = WORKING_DIR / "workspaces"
        if not workspaces_dir.exists():
            return

        start_marker = f"<!-- PLUGIN:{plugin_id} START -->"
        end_marker = f"<!-- PLUGIN:{plugin_id} END -->"
        pattern = re.compile(
            r"\n*" + re.escape(start_marker) + r".*?" + re.escape(end_marker) + r"\n*",
            re.DOTALL,
        )

        for ws_dir in workspaces_dir.iterdir():
            if not ws_dir.is_dir():
                continue
            profile_path = ws_dir / "PROFILE.md"
            if not profile_path.exists():
                continue
            content = profile_path.read_text(encoding="utf-8")
            if start_marker not in content:
                continue
            cleaned = pattern.sub("\n", content).rstrip() + "\n"
            profile_path.write_text(cleaned, encoding="utf-8")
            print(f"[PluginManager] 已清理 {profile_path} 中 {plugin_id} 段落")
    except Exception as e:
        print(f"[PluginManager] 清理 PROFILE.md 失败: {e}")

def toggle_plugin(plugin_id, enabled):
    config = _get_config()
    if plugin_id not in config.get("plugins", {}):
        return {"error": f"插件 {plugin_id} 未找到"}
    config["plugins"][plugin_id]["enabled"] = enabled
    _save_config(config)
    s = "启用" if enabled else "禁用"
    return {"success": True, "message": f"插件 {plugin_id} 已{s}。需重启生效。"}

def get_plugin_info(plugin_id):
    plugin_path = PLUGIN_DIR / plugin_id
    if not plugin_path.exists():
        return {"error": f"插件 {plugin_id} 不存在"}
    info = _read_plugin_json(plugin_path)
    if not info:
        return {"error": "无法读取 plugin.json"}
    config = _get_config()
    files = [str(f.relative_to(plugin_path)) for f in plugin_path.rglob("*")
             if f.is_file() and "__pycache__" not in str(f)]
    return {
        "id": info.get("id"),
        "name": info.get("name"),
        "version": info.get("version"),
        "description": info.get("description", ""),
        "author": info.get("author", ""),
        "license": info.get("license", ""),
        "min_version": info.get("min_qwenpaw_version", info.get("min_version", "")),
        "dependencies": info.get("dependencies", []),
        "enabled": config.get("plugins", {}).get(plugin_id, {}).get("enabled", True),
        "entry": info.get("entry", {}),
        "meta": info.get("meta", {}),
        "files": files,
        "path": str(plugin_path),
        "config_dir": str(WORKING_DIR),
    }

# ── HTTP Server ────────────────────────────────────────────────

class PluginAPIHandler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/list":
            _json_response(self, list_plugins())
        elif path.startswith("/info/"):
            pid = path.split("/")[-1]
            _json_response(self, get_plugin_info(pid))
        elif path == "/status":
            _json_response(self, {
                "plugin_id": PLUGIN_ID,
                "config_dir": str(WORKING_DIR),
                "plugin_dir": str(PLUGIN_DIR),
                "config_path": str(CONFIG_PATH),
            })
        else:
            _json_response(self, {"error": "Not found"}, 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length > 0 else {}
        path = self.path.split("?")[0]

        if path == "/install":
            _json_response(self, install_plugin(body.get("source", "")))
        elif path == "/uninstall":
            _json_response(self, uninstall_plugin(body.get("plugin_id", "")))
        elif path == "/toggle":
            _json_response(self, toggle_plugin(
                body.get("plugin_id", ""), body.get("enabled", False)))
        else:
            _json_response(self, {"error": "Not found"}, 404)

    def log_message(self, format, *args):
        pass  # 静默

def _start_server():
    server = HTTPServer(("127.0.0.1", SERVER_PORT), PluginAPIHandler)
    print(f"[PluginManager] API server running on port {SERVER_PORT}")
    print(f"[PluginManager] Config dir: {WORKING_DIR}")
    print(f"[PluginManager] Plugin dir: {PLUGIN_DIR}")
    server.serve_forever()

# ── Plugin Registration ────────────────────────────────────────

class PluginManager:
    """插件管理器 — QwenPaw 动态插件"""

    def register(self, api):
        t = threading.Thread(target=_start_server, daemon=True)
        t.start()
        print(f"[PluginManager] Registered. API: http://127.0.0.1:{SERVER_PORT}")

plugin = PluginManager()
