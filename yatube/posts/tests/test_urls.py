from http import HTTPStatus

from django.urls import reverse
from django.test import TestCase, Client

from posts.models import Post, Group, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.auth_user = User.objects.create_user(username='auth_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client.force_login(PostURLTests.auth_user)
        self.authorized_client_author.force_login(self.author)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{self.group.slug}/',
            'posts/profile.html': f'/profile/{self.author.username}/',
            'posts/post_detail.html': f'/posts/{self.post.id}/',
            'posts/post_create.html': '/create/',
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/',
        }
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_exists_at_desired_location(self):
        """Доступность страниц в приложении Posts."""
        url_names = (
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.author.username}/',
            f'/posts/{self.post.id}/',
        )
        for address in url_names:
            with self.subTest():
                response = self.client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_exists_at_desired_location(self):
        """Страница доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_exists_at_desired_location_for_author(self):
        """Страница доступна автору."""
        response = self.authorized_client_author.get(
            f'/posts/{self.post.id}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_redirect_anonymous_on_admin_login(self):
        """Страница /create/ перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.client.get(reverse('posts:post_create'))
        adress = reverse('posts:post_create')
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=' + adress
        )

    def test_post_edit_url_redirect_anonymous_on_admin_login(self):
        """Страница post_edit перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.client.get(
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            )
        )
        adress = reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=' + adress
        )

    def test_page_404(self):
        """Запрос к несуществующей странице."""
        response = self.client.get('/page_404')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_redirect_not_author(self):
        """Редирект при попытке редактирования чужого поста."""
        self.editor = User.objects.create_user(username='User')
        self.editor_client = Client()
        self.editor_client.force_login(self.editor)
        new_data = {
            'text': 'Отредактированный текст'
        }
        response = self.editor_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=new_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )

    def test_unixisting_page(self):
        """Страница 404 отдает кастомный шаблон."""
        response = self.client.get('/page_404')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
