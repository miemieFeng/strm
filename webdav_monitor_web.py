#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import threading
import time
import logging
import argparse
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
import webdav_monitor_mt as monitor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("webdav_monitor_web.log"),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

# 全局变量
webdav_monitor = None
monitor_thread = None
config_file = "webdav_config.json"
config = {
    "webdav_url": "",
    "username": "",
    "password": "",
    "local_dir": "./downloads",
    "remote_dir": "/",
    "check_interval": 600,
    "max_workers": 10,
    "replace_ip": "",
    "post_command": "",
    "web_port": 8080
}

# 日志记录
log_entries = []
MAX_LOG_ENTRIES = 100

class LogHandler(logging.Handler):
    def emit(self, record):
        log_entry = {
            'time': datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S'),
            'level': record.levelname,
            'message': record.getMessage()
        }
        log_entries.append(log_entry)
        # 保持日志数量限制
        while len(log_entries) > MAX_LOG_ENTRIES:
            log_entries.pop(0)

# 添加自定义日志处理器
log_handler = LogHandler()
logging.getLogger().addHandler(log_handler)

def load_config():
    """加载配置文件"""
    global config, config_file
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                saved_config = json.load(f)
                # 更新配置，保留默认值
                for key in saved_config:
                    if key in config:
                        config[key] = saved_config[key]
            logging.info("配置已从文件加载")
        else:
            save_config()
            logging.info("已创建默认配置文件")
    except Exception as e:
        logging.error(f"加载配置文件时出错: {e}")

def save_config():
    """保存配置到文件"""
    try:
        # 不保存密码到配置文件，如果是更新配置则保留原密码
        save_data = config.copy()
        
        with open(config_file, 'w') as f:
            json.dump(save_data, f, indent=2)
        logging.info("配置已保存到文件")
    except Exception as e:
        logging.error(f"保存配置文件时出错: {e}")

def start_monitor():
    """启动监控线程"""
    global webdav_monitor, monitor_thread
    
    if monitor_thread and monitor_thread.is_alive():
        logging.warning("监控已经在运行")
        return False
    
    try:
        webdav_monitor = monitor.WebdavMonitor(
            webdav_url=config["webdav_url"],
            username=config["username"],
            password=config["password"],
            local_dir=config["local_dir"],
            remote_dir=config["remote_dir"],
            check_interval=config["check_interval"],
            max_workers=config["max_workers"],
            post_download_command=config["post_command"],
            replace_ip=config["replace_ip"]
        )
        
        monitor_thread = threading.Thread(target=webdav_monitor.monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        logging.info("监控已启动")
        return True
    except Exception as e:
        logging.error(f"启动监控时出错: {e}")
        return False

def stop_monitor():
    """停止监控线程"""
    global webdav_monitor, monitor_thread
    
    if webdav_monitor:
        try:
            webdav_monitor.stop()
            if monitor_thread and monitor_thread.is_alive():
                monitor_thread.join(timeout=5)
            logging.info("监控已停止")
            return True
        except Exception as e:
            logging.error(f"停止监控时出错: {e}")
    return False

@app.route('/')
def index():
    """网页首页"""
    monitor_status = "运行中" if monitor_thread and monitor_thread.is_alive() else "已停止"
    
    stats = {
        "status": monitor_status,
        "local_dir": config["local_dir"],
        "remote_dir": config["remote_dir"],
        "interval": config["check_interval"]
    }
    
    if webdav_monitor:
        # 添加一些运行时统计信息
        stats["download_count"] = getattr(webdav_monitor, "download_count", 0)
        stats["processed_count"] = getattr(webdav_monitor, "processed_count", 0)
        stats["error_count"] = getattr(webdav_monitor, "error_count", 0)
    
    # 反向显示日志，最新的在前面
    recent_logs = list(reversed(log_entries[-20:]))
    
    return render_template('index.html', stats=stats, logs=recent_logs, config=config)

@app.route('/api/start', methods=['POST'])
def api_start():
    """API: 启动监控"""
    success = start_monitor()
    return jsonify({"success": success})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    """API: 停止监控"""
    success = stop_monitor()
    return jsonify({"success": success})

@app.route('/api/save_config', methods=['POST'])
def api_save_config():
    """API: 保存配置"""
    global config
    
    # 从请求中获取配置
    for key in config:
        if key in request.form:
            # 转换数值类型
            if key in ["check_interval", "max_workers", "web_port"]:
                try:
                    config[key] = int(request.form[key])
                except:
                    pass
            else:
                config[key] = request.form[key]
    
    # 保存到文件
    save_config()
    
    # 如果监控正在运行，提示需要重启
    needs_restart = monitor_thread and monitor_thread.is_alive()
    
    return jsonify({"success": True, "needs_restart": needs_restart})

@app.route('/api/logs')
def api_logs():
    """API: 获取日志"""
    return jsonify(list(reversed(log_entries)))

@app.route('/api/status')
def api_status():
    """API: 获取状态"""
    monitor_status = "running" if monitor_thread and monitor_thread.is_alive() else "stopped"
    
    stats = {
        "status": monitor_status,
        "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    if webdav_monitor:
        stats["download_count"] = getattr(webdav_monitor, "download_count", 0)
        stats["processed_count"] = getattr(webdav_monitor, "processed_count", 0)
        stats["error_count"] = getattr(webdav_monitor, "error_count", 0)
        
        # 获取最近下载的文件
        downloaded_files = getattr(webdav_monitor, "downloaded_files", [])
        stats["recent_files"] = downloaded_files[-10:] if downloaded_files else []
    
    return jsonify(stats)

@app.route('/api/restart', methods=['POST'])
def api_restart():
    """API: 重启监控"""
    stop_monitor()
    time.sleep(1)
    success = start_monitor()
    return jsonify({"success": success})

def main():
    """主函数"""
    global config_file
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="WebDAV监控Web界面")
    parser.add_argument("--config-dir", default=".", help="配置文件目录路径")
    parser.add_argument("--port", type=int, default=8080, help="Web服务监听端口")
    args = parser.parse_args()
    
    # 设置配置文件路径
    config_file = os.path.join(args.config_dir, "webdav_config.json")
    
    # 加载配置
    load_config()
    
    # 更新Web端口
    config["web_port"] = args.port
    
    # 自动启动监控
    if config["webdav_url"] and config["username"] and config["password"]:
        start_monitor()
    
    # 启动Web服务
    app.run(host='0.0.0.0', port=config["web_port"], debug=False)

if __name__ == "__main__":
    main() 