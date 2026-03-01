from typing import Dict, List
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from pushers.base import BasePusher
from utils.logger import get_logger

logger = get_logger(__name__)


class WechatGroupPusher(BasePusher):
    """微信群推送器（使用itchat-uos）"""
    
    name = "wechat_group"
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.group_names = config.get('group_names', [])  # 群名称列表
        self._itchat = None
        self._logged_in = False
    
    def _login(self) -> bool:
        """登录微信"""
        if self._logged_in:
            return True
        
        try:
            import itchat
            import os
            
            logger.info("正在登录微信，请扫描二维码...")
            
            # 确保data目录存在
            os.makedirs('data', exist_ok=True)
            
            # 登录（使用热重载避免重复扫码）
            itchat.auto_login(
                hotReload=True,
                statusStorageDir='data/itchat.pkl',
                enableCmdQR=2  # 在命令行显示二维码
            )
            
            self._itchat = itchat
            self._logged_in = True
            logger.info("微信登录成功")
            return True
            
        except Exception as e:
            logger.error(f"微信登录失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def send(self, content: str, title: str = "") -> Dict:
        """
        发送消息到微信群。
        
        Args:
            content: 消息内容
            title: 消息标题
        
        Returns:
            发送结果
        """
        if not self.group_names:
            logger.error("未配置群名称列表")
            return {
                'success': False,
                'message': '未配置群名称列表',
                'pushed_at': datetime.now().isoformat()
            }
        
        # 登录
        if not self._login():
            return {
                'success': False,
                'message': '微信登录失败',
                'pushed_at': datetime.now().isoformat()
            }
        
        # 构建消息
        full_content = f"【{title}】\n\n{content}" if title else content
        
        success_count = 0
        failed_groups = []
        
        for group_name in self.group_names:
            try:
                # 搜索群聊
                chatrooms = self._itchat.search_chatrooms(name=group_name)
                
                if not chatrooms:
                    logger.warning(f"未找到群: {group_name}")
                    failed_groups.append(group_name)
                    continue
                
                # 发送消息
                chatroom = chatrooms[0]
                self._itchat.send(full_content, toUserName=chatroom['UserName'])
                logger.info(f"已发送到群: {group_name}")
                success_count += 1
                
            except Exception as e:
                logger.error(f"发送到群 {group_name} 失败: {e}")
                failed_groups.append(group_name)
        
        result = {
            'success': success_count > 0,
            'message': f'成功发送到 {success_count}/{len(self.group_names)} 个群',
            'pushed_at': datetime.now().isoformat()
        }
        
        if failed_groups:
            result['failed_groups'] = failed_groups
        
        return result
    
    def get_chatrooms(self) -> List[Dict]:
        """获取所有群聊列表"""
        if not self._login():
            return []
        
        try:
            chatrooms = self._itchat.get_chatrooms(update=True)
            return [{'name': c['NickName'], 'member_count': c.get('MemberCount', 0)} for c in chatrooms]
        except Exception as e:
            logger.error(f"获取群聊列表失败: {e}")
            return []
    
    def logout(self) -> None:
        """退出登录"""
        if self._itchat:
            try:
                self._itchat.logout()
                logger.info("微信已退出登录")
            except:
                pass
            self._logged_in = False
