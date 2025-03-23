from http import HTTPStatus
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from posts.models import Post, Group, Comment

User = get_user_model()


class BaseAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='regular_user',
                                             password='testpass')
        self.another_user = User.objects.create_user(username='another_user',
                                                     password='testpass')
        self.group = Group.objects.create(title='Group 1', slug='group-1',
                                          description='Test group')
        self.post_without_group = Post.objects.create(text='Post without group',
                                                      author=self.user)
        self.post_with_group = Post.objects.create(text='Post with group',
                                                   author=self.user, group=self.group)
        self.comment = Comment.objects.create(text='Test comment',
                                              author=self.user,
                                              post=self.post_with_group)
        self.user_client = APIClient()
        self.user_client.force_authenticate(user=self.user)
        self.another_client = APIClient()
        self.another_client.force_authenticate(user=self.another_user)

    def url_for_post_list(self):
        return '/api/v1/posts/'

    def url_for_post_detail(self, post_id):
        return f'/api/v1/posts/{post_id}/'

    def url_for_comment_list(self, post_id):
        return f'/api/v1/posts/{post_id}/comments/'

    def url_for_comment_detail(self, post_id, comment_id):
        return f'/api/v1/posts/{post_id}/comments/{comment_id}/'


class PostAPITests(BaseAPITest):
    def test_posts_unauthenticated_get(self):
        client = APIClient()
        response = client.get(self.url_for_post_list())
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    def test_posts_authenticated_get(self):
        response = self.user_client.get(self.url_for_post_list())
        self.assertEqual(response.status_code, HTTPStatus.OK)
        posts = response.json()
        self.assertIsInstance(posts, list)
        if posts:
            post = posts[0]
            for field in ("id",
                          "text",
                          "author",
                          "pub_date",
                          "image",
                          "group"):
                self.assertIn(field, post)

    def test_post_create_without_group(self):
        data = {"text": "New post without group"}
        response = self.user_client.post(self.url_for_post_list(), data=data)
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        response_data = response.json()
        self.assertEqual(response_data.get("author"), self.user.username)
        self.assertEqual(response_data.get("text"), data["text"])
        self.assertIsNone(response_data.get("group"))

    def test_post_update_not_author(self):
        data = {"text": "Changed text"}
        url = self.url_for_post_detail(self.post_with_group.id)
        response = self.another_client.patch(url, data=data)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_post_delete_by_author(self):
        url = self.url_for_post_detail(self.post_without_group.id)
        response = self.user_client.delete(url)
        self.assertEqual(response.status_code, HTTPStatus.NO_CONTENT)
        self.assertFalse(
            Post.objects.filter(id=self.post_without_group.id).exists())


class CommentAPITests(BaseAPITest):
    def test_comments_unauthenticated_get(self):
        client = APIClient()
        url = self.url_for_comment_list(self.post_with_group.id)
        response = client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    def test_comment_create(self):
        url = self.url_for_comment_list(self.post_with_group.id)
        data = {"text": "New comment"}
        response = self.user_client.post(url, data=data)
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        response_data = response.json()
        self.assertEqual(response_data.get("author"), self.user.username)
        self.assertEqual(response_data.get("text"), data["text"])
        self.assertEqual(response_data.get("post"), self.post_with_group.id)

    def test_comment_update_not_author(self):
        url = self.url_for_comment_detail(self.post_with_group.id,
                                          self.comment.id)
        data = {"text": "Hacked comment text"}
        response = self.another_client.patch(url, data=data)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_comment_delete_unauthenticated(self):
        client = APIClient()
        url = self.url_for_comment_detail(self.post_with_group.id,
                                          self.comment.id)
        response = client.delete(url)
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)
        self.assertTrue(Comment.objects.filter(id=self.comment.id).exists())
