from .base import BasePusher
from .pushplus import PushPlusPusher
from .wechat_work import WeChatWorkPusher
from .wechat_group import WechatGroupPusher

__all__ = ['BasePusher', 'PushPlusPusher', 'WeChatWorkPusher', 'WechatGroupPusher', 'create_pusher']


def create_pusher(config: dict):
    """创建推送器实例"""
    method = config.get('method', 'pushplus')
    
    pushers = {
        'pushplus': PushPlusPusher,
        'wechat_work': WeChatWorkPusher,
        'wechat_group': WechatGroupPusher,
    }
    
    # 延迟导入 wechaty（仅在需要时）
    if method == 'wechaty':
        try:
            from .wechaty_ipad import WechatyPusher
            pushers['wechaty'] = WechatyPusher
        except ImportError:
            raise ImportError("请安装 wechaty: pip install wechaty")
    
    pusher_class = pushers.get(method, PushPlusPusher)
    return pusher_class(config.get(method, {}))
