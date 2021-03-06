# coding:utf-8
from app.cache import system_status_cache, hot_post_cache, topic_category_cache

from custor.handlers.basehandler import BaseRequestHandler
from custor.utils import get_cleaned_post_data, get_cleaned_json_data, json_result
from custor.decorators import login_required_json, login_required

from db.mysql_model.common import Notification
from db.mysql_model.post import Post, PostReply, PostTopic, CollectPost

# 换种注释方式

# 帖子详情
class PostDetailHandler(BaseRequestHandler):
    def get(self, post_id, *args, **kwargs):
        post = Post.get(Post.id == post_id)
        post.up_visit()
        post_detail = post
        post_replys = PostReply.list_all(post)
        self.render('post/post_detail.html',
                    post_detail=post_detail,
                    post_replys=post_replys,
                    is_collect=CollectPost.is_collect(post, self.current_user),
                    hot_post_cache=hot_post_cache,
                    topic_category_cache=topic_category_cache)


# 添加帖子
class PostAddHandler(BaseRequestHandler):

    @login_required
    def get(self, *args, **kwargs):
        self.render('post/post_new.html',
                    topic_category_cache=topic_category_cache)

    @login_required
    def post(self, *args, **kwargs):
        post_data = get_cleaned_post_data(self, ['title', 'content', 'topic'])
        try:
            topic = PostTopic.get(PostTopic.str == post_data['topic'])
        except PostTopic.DoesNotExist:
            self.write(json_result(1, '请选择正确主题'))
            return
        post = Post.create(
            topic=topic,
            title=post_data['title'],
            content=post_data['content'],
            user=self.current_user
        )
        #添加通知, 通知给其他关注的用户
        Notification.new_post(post)
        self.write(json_result(0, {'post_id': post.id}))


# 添加回复
class PostReplyAddHandler(BaseRequestHandler):

    @login_required
    def post(self, *args, **kwargs):
        post_data = get_cleaned_post_data(self, ['post', 'content'])
        try:
            post = Post.get(Post.id == post_data['post'])
        except PostTopic.DoesNotExist:
            self.write(json_result(1, '请选择正确post'))
            return
        postreply = PostReply.create(
            post=post,
            user=self.current_user,
            content=post_data['content'],
        )
        post.update_latest_reply(postreply)
        Notification.new_reply(postreply, post)
        self.write(json_result(0, {'post_id': post.id}))

# 帖子相关操作, 类似API的方式, 需要有opt,data参数(统一格式)
class PostReplyOptHandler(BaseRequestHandler):

    @login_required_json(-3, 'login failed.') # 要求登录, 否则返回(错误码, 错误信息)
    def post(self, *args, **kwargs):
        json_data = get_cleaned_json_data(self, ['opt', 'data'])
        data = json_data['data']
        opt = json_data['opt']
        # 支持某个回复
        if opt == 'support-postreply':
            try:
                postreply = PostReply.get(PostReply.id == data['postreply'])
            except:
                self.write(json_result(1, '请输入正确的回复'))
                return
            postreply.up_like()
            self.write(json_result(0, 'success'))
        # 收藏该主题
        elif opt == 'collect-post':
            try:
                post = Post.get(Post.id == data['post'])
            except:
                self.write(json_result(1, '请输入正确的Post'))
                return
            CollectPost.create(post=post, user=self.current_user)
            self.write(json_result(0, 'success'))
        # 取消收藏该主题
        elif opt == 'cancle-collect-post':
            try:
                post = Post.get(Post.id == data['post'])
            except:
                self.write(json_result(1, 'CollectPost不正确'))
                return
            collectpost = CollectPost.get(post=post, user=self.current_user)
            collectpost.delete_instance()
            self.write(json_result(0, 'success'))
        else:
            self.write(json_result(1, 'opt不支持'))

