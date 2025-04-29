#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 临时脚本，用于禁用代理并运行原始脚本

import os
import sys
import subprocess

# 禁用所有代理
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('all_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('ALL_PROXY', None)

# 确认代理已禁用
print("代理设置已禁用")
for key in os.environ:
    if 'proxy' in key.lower():
        print(f"{key} = {os.environ[key]}")

# 构建命令参数
cmd = [
    "python3", "webdav_monitor_mt.py",
    "--url", "http://hu.miemiejun.me:5005",
    "--username", "19965027242",
    "--password", "zhao131496",
    "--remote-dir", "/links/影视",
    "--local-dir", "./downloads",
    "--threads", "2",
    "--interval", "10",
    "--replace-ip", "121.36.197.33",
    "--verbose"
]

# 运行原始脚本
print("开始运行WebDAV监控脚本...")
subprocess.run(cmd) 