#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import webdav3.client as wc
import logging
import argparse
import urllib.parse
from datetime import datetime
import threading
import queue
import concurrent.futures
import subprocess
import shlex
import re
import socket
import sys
import ssl
import sqlite3

# 禁用所有潜在的代理配置
if 'http_proxy' in os.environ:
    del os.environ['http_proxy']
if 'https_proxy' in os.environ:
    del os.environ['https_proxy']
if 'HTTP_PROXY' in os.environ:
    del os.environ['HTTP_PROXY']
if 'HTTPS_PROXY' in os.environ:
    del os.environ['HTTPS_PROXY']

# 配置IPv6支持
socket.setdefaulttimeout(30)  # 设置较长的超时时间

# 从环境变量获取日志级别
log_level_name = os.environ.get('LOG_LEVEL', 'INFO')
log_level = getattr(logging, log_level_name.upper(), logging.INFO)

# 配置日志
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("webdav_monitor.log"),
        logging.StreamHandler()
    ]
)

# 创建结果报告器 - 用于确保扫描耗时和新增文件数量始终显示，即使日志级别设置为WARNING
class ResultReporter:
    @staticmethod
    def report(message):
        # 使用ERROR级别确保消息始终显示，但实际是INFO信息
        logging.log(logging.ERROR if log_level > logging.INFO else logging.INFO, message)

reporter = ResultReporter()

# 打印系统和网络信息
logging.info("=== 系统和网络信息 ===")
logging.info(f"Python版本: {sys.version}")
logging.info(f"系统平台: {sys.platform}")
try:
    # 尝试获取和显示本机IP地址
    hostname = socket.gethostname()
    ips = socket.getaddrinfo(hostname, None)
    logging.info(f"主机名: {hostname}")
    for ip in ips:
        logging.info(f"IP地址: {ip[4][0]} (类型: {ip[0]})")
except Exception as e:
    logging.warning(f"获取系统网络信息失败: {e}")

# 尝试解析WebDAV服务器IP
try:
    domain = "hu.miemiejun.me"
    ips = socket.getaddrinfo(domain, None)
    logging.info(f"WebDAV服务器域名 {domain} 解析结果:")
    for ip in ips:
        logging.info(f"  - {ip[4][0]} (类型: {ip[0]})")
except Exception as e:
    logging.warning(f"解析WebDAV服务器IP失败: {e}")

def fix_path(parent_dir, path_item):
    """修复路径，确保使用正确格式"""
    # 如果路径已经是绝对路径，直接返回
    if path_item.startswith('/'):
        return path_item
    
    # 否则，拼接父目录和子项目
    if parent_dir.endswith('/'):
        return parent_dir + path_item
    else:
        return parent_dir + '/' + path_item

def process_strm_content(file_path, replace_ip_with_domain=None):
    """处理STRM文件内容，替换IP为域名"""
    if not replace_ip_with_domain:
        return False
        
    try:
        # 读取STRM文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则表达式替换IP地址为域名
        # 匹配形如 http://192.168.1.1:8080/ 或 http://10.0.0.1/ 的IP地址
        ip_pattern = r'http://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(:\d+)?/'
        
        # 检查是否有匹配
        if re.search(ip_pattern, content):
            # 替换IP为域名，保留端口号(如果有)
            new_content = re.sub(ip_pattern, f'http://{replace_ip_with_domain}\\2/', content)
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            # 只记录文件所在目录，而不是完整路径
            file_dir = os.path.dirname(file_path)
            # 日志改为调试级别
            # logging.debug(f"已处理STRM文件: {os.path.basename(file_path)}")
            return True
        else:
            logging.debug(f"STRM文件中未找到需要替换的IP: {os.path.basename(file_path)}")
            return False
            
    except Exception as e:
        logging.error(f"处理STRM文件内容时出错: {os.path.basename(file_path)}, {e}")
        return False

class WebdavMonitor:
    def __init__(self, webdav_url, username, password, local_dir, remote_dir='/', check_interval=300, max_workers=5, post_download_command=None, replace_ip=None, pool_connections=20, pool_maxsize=30):
        """
        初始化WebDAV监控器
        
        :param webdav_url: WebDAV服务器地址
        :param username: WebDAV账号
        :param password: WebDAV密码
        :param local_dir: 本地存储目录
        :param remote_dir: 远程扫描目录，默认为根目录
        :param check_interval: 检查间隔(秒)，默认5分钟
        :param max_workers: 最大并行下载线程数
        :param post_download_command: 下载完成后执行的命令，可包含{local_path}占位符
        :param replace_ip: 下载后替换STRM文件中的IP为指定域名
        :param pool_connections: 连接池初始连接数
        :param pool_maxsize: 连接池最大连接数
        """
        self.local_dir = local_dir
        self.remote_dir = remote_dir
        self.check_interval = check_interval
        self.max_workers = max_workers
        self.post_download_command = post_download_command
        self.replace_ip = replace_ip
        self.pool_connections = pool_connections
        self.pool_maxsize = pool_maxsize
        
        # 确保本地目录存在
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)
            
        # 配置WebDAV客户端
        self.client_options = {
            'webdav_hostname': webdav_url,
            'webdav_login': username,
            'webdav_password': password,
            'disable_check': True,
            'webdav_timeout': 30,  # 设置较长的超时时间
            'verbose': logging.getLogger().level <= logging.DEBUG,  # 根据日志级别自动设置WebDAV的verbose
            'pool_connections': self.pool_connections,  # 连接池初始连接数
            'pool_maxsize': self.pool_maxsize      # 连接池最大连接数
        }
        
        # 确保域名解析工作正常
        try:
            import socket
            hostname = webdav_url.split('//')[1].split(':')[0]
            logging.info(f"尝试解析WebDAV主机名 {hostname}")
            ips = socket.getaddrinfo(hostname, None)
            for ip in ips:
                logging.info(f"WebDAV主机名解析: {ip[4][0]} (类型: {ip[0]})")
        except Exception as e:
            logging.warning(f"WebDAV主机名解析失败: {e}")
        
        # 创建客户端并测试连接
        self.client = self._create_client_with_retry(max_retries=3)
        
        # 使用SQLite数据库记录已处理的文件
        self.file_tracker = os.path.join(local_dir, '.processed_files.db')
        self.processed_files = self._load_processed_files()
        
        # 上次扫描时间记录
        self.last_scan_file = os.path.join(local_dir, '.last_scan_time')
        self.last_scan_time = self._load_last_scan_time()
        
        # 下载队列和线程池
        self.download_queue = queue.Queue()
        self.stop_flag = threading.Event()
        
        # 下载统计
        self.download_count = 0
        self.error_count = 0
        self.processed_count = 0
        self.dir_stats = {}  # 按目录统计下载和处理的文件
        self.stats_lock = threading.Lock()
        
        # 数据库操作队列和批处理
        self.db_queue = queue.Queue()
        self.db_batch_size = 50  # 批量处理大小
        self.pending_files = []  # 待处理的文件路径列表
        self.db_batch_lock = threading.Lock()
        self.db_last_flush_time = time.time()
        self.db_flush_interval = 30  # 30秒自动刷新一次
        
        # 启动数据库工作线程
        self.db_worker_thread = threading.Thread(target=self._db_worker, daemon=True)
        self.db_worker_thread.start()
        logging.info("数据库工作线程已启动，批处理大小: %d, 自动刷新间隔: %d秒", self.db_batch_size, self.db_flush_interval)
    
    def _create_client_with_retry(self, max_retries=3):
        """创建WebDAV客户端并尝试连接，失败时重试"""
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                client = wc.Client(self.client_options)
                # 测试连接
                logging.info(f"测试WebDAV连接 (尝试 {retry_count+1}/{max_retries})...")
                client.check(self.remote_dir)
                logging.info("WebDAV连接成功！")
                return client
            except Exception as e:
                retry_count += 1
                last_error = e
                logging.warning(f"WebDAV连接失败: {e}, 重试 ({retry_count}/{max_retries})")
                time.sleep(2 * retry_count)  # 递增等待时间
        
        # 如果所有重试都失败
        logging.error(f"无法连接到WebDAV服务器，最后错误: {last_error}")
        # 返回客户端，即使未通过测试
        return wc.Client(self.client_options)
    
    def _load_processed_files(self):
        """加载已处理文件记录"""
        processed_files = set()
        if os.path.exists(self.file_tracker):
            try:
                # 使用数据库而不是文本文件来存储已处理文件
                conn = sqlite3.connect(self.file_tracker)
                cursor = conn.cursor()
                # 确保表存在
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed_files (
                    path TEXT PRIMARY KEY
                )''')
                conn.commit()
                
                # 读取所有记录
                cursor.execute("SELECT path FROM processed_files")
                for row in cursor.fetchall():
                    processed_files.add(row[0])
                conn.close()
                return processed_files
            except Exception as e:
                logging.warning(f"从数据库加载处理记录失败: {e}，尝试从文本文件加载")
                # 如果数据库读取失败，尝试从旧格式的文本文件读取
                try:
                    with open(self.file_tracker, 'r') as f:
                        return set(line.strip() for line in f.readlines())
                except Exception as e2:
                    logging.error(f"加载处理记录失败: {e2}")
                    return set()
        return processed_files
    
    def _save_processed_file(self, file_path):
        """将文件记录请求添加到队列"""
        # 立即更新内存中的集合，不需要等待数据库操作
        self.processed_files.add(file_path)
        # 添加到数据库队列
        self.db_queue.put({'type': 'save_file', 'file_path': file_path})
    
    def _load_last_scan_time(self):
        """加载上次扫描时间"""
        if os.path.exists(self.last_scan_file):
            with open(self.last_scan_file, 'r') as f:
                try:
                    return float(f.read().strip())
                except:
                    return 0
        return 0
        
    def _save_last_scan_time(self):
        """保存当前扫描时间"""
        current_time = time.time()
        with open(self.last_scan_file, 'w') as f:
            f.write(str(current_time))
        self.last_scan_time = current_time
    
    def _is_file_new(self, file_path):
        """检查文件是否为新文件"""
        # 使用哈希表查找效率高
        return file_path not in self.processed_files
    
    def _encode_path(self, path):
        """编码路径，处理中文字符问题"""
        try:
            # 只编码路径部分，不编码基本URL结构
            parts = path.split('/')
            encoded_parts = []
            for part in parts:
                if part:  # 跳过空部分
                    # 只对非ASCII字符进行编码
                    if any(ord(c) > 127 for c in part):
                        encoded_parts.append(urllib.parse.quote(part))
                    else:
                        encoded_parts.append(part)
            
            encoded_path = '/'.join(encoded_parts)
            if path.startswith('/'):
                encoded_path = '/' + encoded_path
            if path.endswith('/'):
                encoded_path = encoded_path + '/'
                
            return encoded_path
        except Exception as e:
            logging.error(f"编码路径 {path} 时出错: {e}")
            return path
    
    def _download_file(self, remote_path):
        """下载文件到本地"""
        try:
            # 创建相对路径，保持目录结构
            relative_path = remote_path.lstrip('/')
            local_path = os.path.join(self.local_dir, relative_path)
            
            # 确保目标目录存在
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # 下载文件
            success = False
            retry_count = 0
            max_retries = 3
            last_error = None
            
            while retry_count < max_retries and not success:
                try:
                    self.client.download_file(remote_path, local_path)
                    success = True
                except Exception as e:
                    last_error = e
                    retry_count += 1
                    logging.error(f"下载文件时出错: {e}, 重试 ({retry_count}/{max_retries})")
                    
                    # 如果是连接池满的错误，等待较长时间后重试
                    if "Connection pool is full" in str(e):
                        logging.warning(f"连接池已满，等待后重试...")
                        time.sleep(5)  # 等待更长时间
                    else:
                        time.sleep(1)
                        
                    # 如果达到最大重试次数，尝试使用编码后的路径
                    if retry_count == max_retries and not success:
                        encoded_path = self._encode_path(remote_path)
                        if encoded_path != remote_path:
                            try:
                                logging.debug(f"尝试使用编码路径: {encoded_path}")
                                self.client.download_file(encoded_path, local_path)
                                success = True
                            except Exception as e2:
                                logging.error(f"使用编码路径下载文件时出错: {e2}")
            
            if success:
                # 添加到已处理文件列表
                self._save_processed_file(remote_path)
                
                # 获取文件所在的远程目录
                remote_dir = os.path.dirname(remote_path)
                if not remote_dir:
                    remote_dir = '/'
                
                # 更新下载统计
                with self.stats_lock:
                    self.download_count += 1
                    # 记录下载的文件
                    self.downloaded_files.append(remote_path)
                    
                    # 更新目录统计
                    if remote_dir not in self.dir_stats:
                        self.dir_stats[remote_dir] = {'downloads': 0, 'processed': 0}
                    self.dir_stats[remote_dir]['downloads'] += 1
                
                # 处理STRM文件内容，替换IP为域名
                if self.replace_ip and local_path.lower().endswith('.strm'):
                    processed = process_strm_content(local_path, self.replace_ip)
                    if processed:
                        with self.stats_lock:
                            self.processed_count += 1
                            self.dir_stats[remote_dir]['processed'] += 1
                
                # 执行下载后命令
                if self.post_download_command:
                    self._execute_post_download(local_path)
                
                return True
            else:
                # 更新错误统计
                with self.stats_lock:
                    self.error_count += 1
                return False
                
        except Exception as e:
            logging.error(f"处理下载文件 {remote_path} 时出错: {e}")
            # 更新错误统计
            with self.stats_lock:
                self.error_count += 1
            return False
    
    def _execute_post_download(self, local_path):
        """执行下载后命令"""
        try:
            if not self.post_download_command:
                return
                
            # 替换命令中的占位符
            cmd = self.post_download_command.replace('{local_path}', local_path)
            
            # 执行命令
            logging.debug(f"执行下载后命令")
            process = subprocess.Popen(
                shlex.split(cmd), 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                logging.debug(f"命令执行成功")
            else:
                logging.error(f"命令执行失败")
                
        except Exception as e:
            logging.error(f"执行下载后命令时出错")
    
    def _download_worker(self, item):
        """下载工作线程，由线程池调用"""
        remote_path = item
        if self._is_file_new(remote_path):
            return self._download_file(remote_path)
        return False
    
    def _find_and_download_files(self, directory=None):
        """递归查找所有文件并立即添加到下载线程池"""
        if directory is None:
            directory = self.remote_dir
        
        # 重置本次扫描的统计信息
        self.download_count = 0
        self.error_count = 0
        self.processed_count = 0
        self.dir_stats = {}  # 重置目录统计
        # 记录新增的文件列表
        self.downloaded_files = []
        
        # 创建线程池
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 开始查找和下载过程
            self._find_files(directory, executor, futures=None, depth=0)
            
            # 等待所有下载任务完成
            executor.shutdown(wait=True)
        
        return self.download_count, self.error_count, self.processed_count, self.downloaded_files
    
    def _find_files(self, directory, executor, futures=None, depth=0):
        """递归查找文件并提交到线程池下载"""
        if futures is None:
            futures = []
            
        try:
            try:
                # 获取目录列表
                files = self.client.list(directory)
                # 直接批量处理目录中的文件
                new_files = []
                
                # 收集所有文件和目录
                directories = []
                for file_name in files:
                    # 跳过当前目录
                    if file_name == directory or file_name == "./":
                        continue
                    
                    # 构建完整路径
                    file_path = fix_path(directory, file_name)
                    
                    try:
                        is_dir = self.client.is_dir(file_path)
                    except Exception as e:
                        logging.warning(f"检查路径是否为目录时出错")
                        # 尝试通过路径判断
                        is_dir = file_path.endswith('/')
                    
                    if is_dir:
                        # 收集目录待后续处理
                        directories.append(file_path)
                    else:
                        # 收集所有可能需要下载的文件
                        if self._is_file_new(file_path):
                            new_files.append(file_path)
                
                # 批量提交文件下载任务
                if new_files:
                    for file_path in new_files:
                        future = executor.submit(self._download_worker, file_path)
                        futures.append(future)
                
                # 处理完所有文件后再递归处理子目录，减少并行递归深度
                for dir_path in directories:
                    try:
                        self._find_files(dir_path, executor, futures, depth + 1)
                    except Exception as e:
                        logging.warning(f"递归查找目录时出错")
                
            except Exception as e:
                logging.error(f"列出目录 {directory} 时出错: {e}")
                # 尝试使用编码后的路径
                encoded_directory = self._encode_path(directory)
                if encoded_directory != directory:
                    logging.debug(f"尝试使用编码后的路径: {encoded_directory}")
                    try:
                        files = self.client.list(encoded_directory)
                    except Exception as e2:
                        logging.error(f"使用编码路径 {encoded_directory} 列出目录时出错: {e2}")
                        return futures
                else:
                    return futures
            
            return futures
        except Exception as e:
            logging.error(f"查找文件时出错: {e}")
            return futures
    
    def _process_existing_strm_files(self):
        """处理已下载的STRM文件内容"""
        if not self.replace_ip:
            return 0
            
        processed_count = 0
        # 使用字典来跟踪每个目录中处理的文件数量
        dir_stats = {}
        
        try:
            logging.info(f"开始处理已下载的STRM文件内容...")
            
            # 遍历本地目录
            for root, dirs, files in os.walk(self.local_dir):
                for file in files:
                    if file.lower().endswith('.strm'):
                        file_path = os.path.join(root, file)
                        if process_strm_content(file_path, self.replace_ip):
                            processed_count += 1
                            
                            # 记录目录统计信息
                            rel_dir = os.path.relpath(root, self.local_dir)
                            if rel_dir == '.':
                                rel_dir = '根目录'
                            if rel_dir not in dir_stats:
                                dir_stats[rel_dir] = 0
                            dir_stats[rel_dir] += 1
            
            # 按照处理的文件数量排序并显示每个目录的统计信息
            if dir_stats:
                logging.info(f"按目录统计处理的STRM文件:")
                for dir_path, count in sorted(dir_stats.items(), key=lambda x: x[1], reverse=True):
                    logging.info(f"  - {dir_path}: {count}个文件")
                    
            logging.info(f"已处理 {processed_count} 个已下载的STRM文件内容")
            return processed_count
        except Exception as e:
            logging.error(f"处理已下载的STRM文件内容时出错: {e}")
            return processed_count
    
    def monitor(self):
        """开始监控WebDAV服务器"""
        logging.info(f"开始监控WebDAV服务器的 {self.remote_dir} 目录，将检查新的文件 (间隔: {self.check_interval}秒)")
        logging.info(f"使用 {self.max_workers} 个线程进行并行下载")
        
        if self.replace_ip:
            logging.info(f"下载后将自动处理STRM文件内容，替换IP为: {self.replace_ip}")
            # 首先处理已下载的文件
            processed_count = self._process_existing_strm_files()
            if processed_count > 0:
                logging.info(f"已处理 {processed_count} 个已存在的STRM文件")
        
        try:
            scan_count = 0
            client_rebuild_interval = 5  # 每 5 次扫描重建一次客户端
            
            while not self.stop_flag.is_set():
                start_time = time.time()
                scan_count += 1
                logging.info(f"开始扫描... (第 {scan_count} 次)")
                
                # 定期重建客户端以释放连接资源
                if scan_count % client_rebuild_interval == 0:
                    logging.debug("定期重建WebDAV客户端以释放连接资源...")
                    self.client = self._create_client_with_retry(max_retries=3)
                
                # 检查远程目录是否存在
                try:
                    exists = self.client.check(self.remote_dir)
                    if not exists:
                        logging.error(f"远程目录 {self.remote_dir} 不存在")
                        time.sleep(self.check_interval)
                        continue
                except Exception as e:
                    logging.error(f"检查远程目录 {self.remote_dir} 是否存在时出错: {e}")
                    # 如果出现连接错误，尝试重建客户端
                    if "Connection pool is full" in str(e):
                        logging.warning("连接池已满，重建WebDAV客户端...")
                        self.client = self._create_client_with_retry(max_retries=3)
                    time.sleep(self.check_interval)
                    continue
                
                # 查找所有文件并立即下载
                download_count, error_count, processed_count, downloaded_files = self._find_and_download_files()
                
                # 更新上次扫描时间
                self._save_last_scan_time()
                
                elapsed_time = time.time() - start_time
                
                # 记录扫描结果 - 使用专用报告器确保即使在警告级别下也会显示
                reporter.report(f"扫描完成 - 耗时: {elapsed_time:.2f}秒，新增文件: {download_count}个，失败: {error_count}个")
                
                # 如果有新增文件，输出文件列表，但保持在INFO级别
                if download_count > 0 and logging.getLogger().level <= logging.INFO:
                    logging.info(f"新增文件列表:")
                    for file_path in downloaded_files:
                        logging.info(f"  - {file_path}")
                
                logging.info(f"等待 {self.check_interval} 秒后再次检查...")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logging.info("监控已停止")
            self.stop_flag.set()
        except Exception as e:
            logging.error(f"监控过程中发生错误: {e}")
            # 尝试重新启动监控
            if not self.stop_flag.is_set():
                logging.info("尝试重新启动监控...")
                time.sleep(10)
                self.monitor()
    
    def stop(self):
        """停止监控和下载"""
        logging.info("正在停止监控...")
        self.stop_flag.set()
        
        # 刷新剩余的待处理文件
        self.db_queue.put({'type': 'flush'})
        
        # 等待数据库队列处理完成
        logging.info("等待数据库操作完成...")
        try:
            self.db_queue.join()
            self.db_worker_thread.join(timeout=30)
        except:
            pass
            
        logging.info("监控器已停止")

    def _db_worker(self):
        """数据库工作线程，处理所有数据库写入操作，使用批处理提高效率"""
        while not self.stop_flag.is_set() or not self.db_queue.empty():
            try:
                # 检查是否需要刷新批处理
                current_time = time.time()
                if current_time - self.db_last_flush_time > self.db_flush_interval:
                    with self.db_batch_lock:
                        if self.pending_files:
                            self._db_flush_batch()
                
                # 从队列获取任务，短超时以便定期检查刷新
                try:
                    task = self.db_queue.get(timeout=2)
                except queue.Empty:
                    continue
                
                # 处理任务
                try:
                    if task['type'] == 'save_file':
                        with self.db_batch_lock:
                            self.pending_files.append(task['file_path'])
                            # 如果达到批处理大小，立即刷新
                            if len(self.pending_files) >= self.db_batch_size:
                                self._db_flush_batch()
                    elif task['type'] == 'flush':
                        with self.db_batch_lock:
                            self._db_flush_batch()
                except Exception as e:
                    logging.error(f"处理数据库任务出错: {e}")
                
                # 标记任务完成
                self.db_queue.task_done()
                
            except Exception as e:
                logging.error(f"数据库工作线程异常: {e}")
                time.sleep(1)  # 出错后暂停一下
    
    def _db_flush_batch(self):
        """将待处理的文件批量写入数据库"""
        if not self.pending_files:
            return
        
        current_batch = self.pending_files.copy()
        self.pending_files = []
        self.db_last_flush_time = time.time()
        
        # 批量写入数据库
        try:
            conn = sqlite3.connect(self.file_tracker, timeout=60)  # 增加超时时间
            cursor = conn.cursor()
            # 确保表存在
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_files (
                path TEXT PRIMARY KEY
            )''')
            
            # 使用批量插入
            cursor.executemany(
                "INSERT OR IGNORE INTO processed_files (path) VALUES (?)", 
                [(path,) for path in current_batch]
            )
            conn.commit()
            conn.close()
            
            logging.info(f"已批量保存 {len(current_batch)} 个文件记录到数据库")
        except Exception as e:
            logging.error(f"批量保存记录到数据库失败: {e}")
            # 备用文本文件存储
            try:
                with open(self.file_tracker + ".txt", 'a') as f:
                    for path in current_batch:
                        f.write(f"{path}\n")
            except Exception as e2:
                logging.error(f"批量保存记录到文本文件也失败: {e2}")

def main():
    parser = argparse.ArgumentParser(description='多线程监控WebDAV服务器并下载文件')
    parser.add_argument('--url', required=True, help='WebDAV服务器地址')
    parser.add_argument('--username', required=True, help='WebDAV账号')
    parser.add_argument('--password', required=True, help='WebDAV密码')
    parser.add_argument('--local-dir', default='./downloads', help='本地保存目录，默认为./downloads')
    parser.add_argument('--remote-dir', default='/links/影视', help='远程扫描目录，默认为/links/影视')
    parser.add_argument('--interval', type=int, default=600, help='检查间隔(秒)，默认600秒(10分钟)')
    parser.add_argument('--threads', type=int, default=10, help='下载线程数，默认10个')
    parser.add_argument('--post-command', help='下载完成后执行的命令，可使用{local_path}占位符')
    parser.add_argument('--replace-ip', help='替换STRM文件中的IP为指定域名，例如: hu.miemiejun.me')
    parser.add_argument('--verbose', action='store_true', help='显示详细日志')
    parser.add_argument('--pool-connections', type=int, default=20, help='连接池初始连接数，默认20个')
    parser.add_argument('--pool-maxsize', type=int, default=30, help='连接池最大连接数，默认30个')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 初始化监控器
    monitor = WebdavMonitor(
        webdav_url=args.url,
        username=args.username,
        password=args.password,
        local_dir=args.local_dir,
        remote_dir=args.remote_dir,
        check_interval=args.interval,
        max_workers=args.threads,
        post_download_command=args.post_command,
        replace_ip=args.replace_ip,
        pool_connections=args.pool_connections,
        pool_maxsize=args.pool_maxsize
    )
    
    try:
        monitor.monitor()
    except KeyboardInterrupt:
        logging.info("收到用户中断，正在停止监控...")
        monitor.stop()

if __name__ == "__main__":
    main() 