# coding: utf-8
import hashlib
import re
from datetime import datetime

import requests
from PyQt5.QtCore import QVersionNumber, QObject, pyqtSignal, QSettings

from app.config import VERSION


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

    def getLatestVersionInfo(self):
        """获取最新版本信息"""
        url = "https://vc.bkfeng.top/api/version"
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # 解析 JSON
        data = response.json()

        # 解析版本
        version = data.get('version', self.currentVersion)
        match = self.versionPattern.search(version)
        if not match:
            version = self.currentVersion

        self.latestVersion = version
        self.forceUpdate = data.get('force_update', False)
        self.updateInfo = data.get('update_info', '')
        self.downloadURL = data.get('download_url', '')
        self.announcement = data.get('announcement', {})
        self.history = data.get('history', [])

        return data

    def hasNewVersion(self):
        """检查是否有新版本"""
        try:
            version_data = self.getLatestVersionInfo()
        except requests.RequestException:
            return False  # 网络错误时不提示更新

        # 检查历史版本中当前版本是否可用
        current_version_available = True
        for version_info in self.history:
            if version_info['version'].lstrip('v') == self.currentVersion.lower():
                current_version_available = version_info.get('available', True)
                break

        # 如果当前版本不可用，强制更新
        if not current_version_available:
            self.forceUpdate = True

        latest_ver_num = QVersionNumber.fromString(self.latestVersion.lstrip('v'))
        current_ver_num = QVersionNumber.fromString(self.currentVersion.lstrip('v'))

        if latest_ver_num > current_ver_num or self.forceUpdate:
            self.newVersionAvailable.emit(
                self.latestVersion,
                self.forceUpdate,
                self.updateInfo,
                self.downloadURL
            )
            return True
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
                return
            start_date = datetime.strptime(ann.get('start_date'), "%Y-%m-%d").date()
            end_date = datetime.strptime(ann.get('end_date'), "%Y-%m-%d").date()
            today = datetime.today().date()
            if start_date <= today <= end_date:
                content = ann.get('content', '')
                # 标记该公告已显示
                self.settings.setValue(f'announcement/shown_announcement_{announcement_id}', True)
                self.announcementAvailable.emit(content)

    def performCheck(self):
        """执行版本和公告检查"""
        self.hasNewVersion()
        self.checkAnnouncement()
        self.checkCompleted.emit()
