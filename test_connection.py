#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import sys
import socket

# 确保清除所有代理设置
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None) 
os.environ.pop('all_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('ALL_PROXY', None)

# 创建一个没有代理的会话
session = requests.Session()
session.trust_env = False  # 不使用环境变量中的代理

# WebDAV服务器信息
hostname = "hu.miemiejun.me"
url = f"http://{hostname}:5005/links/影视/"
username = "19965027242"
password = "zhao131496"

print(f"测试连接到WebDAV服务器: {url}")
print(f"使用用户名: {username}")

# 首先尝试解析域名
try:
    print(f"尝试解析域名 {hostname}...")
    ip = socket.gethostbyname(hostname)
    print(f"解析结果: {hostname} -> {ip}")
except socket.gaierror as e:
    print(f"域名解析失败: {e}")
    print("这意味着您的系统无法将域名转换为IP地址")
    print("可能的原因: 1) 域名不存在 2) DNS服务器不可用 3) 域名只在特定网络环境中可用")
    sys.exit(1)

try:
    # 发送PROPFIND请求(WebDAV协议用于列出目录内容)
    headers = {
        'Depth': '1',
        'Content-Type': 'application/xml',
    }
    response = session.request(
        'PROPFIND', 
        url, 
        headers=headers,
        auth=(username, password),
        timeout=10
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 207:  # 207是WebDAV的成功状态码
        print("连接成功！可以访问WebDAV服务器")
        print(f"响应内容长度: {len(response.content)} 字节")
    else:
        print(f"连接失败，响应: {response.text}")
        
except Exception as e:
    print(f"连接错误: {e}")
    
print("\n现在尝试普通的HTTP GET请求...")
try:
    response = session.get(url, auth=(username, password), timeout=10)
    print(f"GET状态码: {response.status_code}")
    print(f"GET响应: {response.text[:200] if response.text else '无响应内容'}")
except Exception as e:
    print(f"GET请求错误: {e}") 