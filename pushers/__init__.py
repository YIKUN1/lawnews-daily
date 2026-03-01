from .base import BasePusher
from .pushplus import PushPlusPusher
from .wechat_work import WeChatWorkPusher
from .wechat_group import WechatGroupPusher

__all__ = ['BasePusher', 'PushPlusPusher', 'WeChatWorkPusher', 'WechatGroupPusher', 'create_pusher']


def create_pusher(config: dict):
    """创建推送器实例"""
    from .wechaty_ipad import WechatyPusher
    
    method = config.get('method', 'pushplus')
    
    pushers = {
        'pushplus': PushPlusPusher,
        'wechat_work': WeChatWorkPusher,
        'wechaty': WechatyPusher,
        'wechat_group': WechatGroupPusher,
    }
    
    pusher_class = pushers.get(method, PushPlusPusher)
    return pusher_class(config.get(method, {}))
