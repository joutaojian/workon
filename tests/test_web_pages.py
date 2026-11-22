# coding: utf-8
"""首页、登录页与工作台的轻量回归测试。"""
import unittest
from html.parser import HTMLParser

from workon.web import create_app


class _ExternalResourceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.resources = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and attrs.get("src"):
            self.resources.append(attrs["src"])
        if tag == "link" and attrs.get("href"):
            self.resources.append(attrs["href"])
        if tag == "img" and attrs.get("src", "").startswith(("http://", "https://")):
            self.resources.append(attrs["src"])


class TestWebPages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = create_app().test_client()

    @staticmethod
    def _html(response):
        # Flask 的默认 test_client 编码不用于校验中文内容。
        return response.data.decode("utf-8")

    def test_home_explains_product_and_actions(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = self._html(response)
        for text in ("AI 只做一次", "好结果，随时复现", "MIT", "Python 3.9+", "打开工作台"):
            self.assertIn(text, html)
        for anchor in ('id="how"', 'id="features"', 'id="start"'):
            self.assertIn(anchor, html)

    def test_pages_have_no_external_assets(self):
        for path in ("/", "/login"):
            parser = _ExternalResourceParser()
            parser.feed(self._html(self.client.get(path)))
            self.assertEqual(parser.resources, [])

    def test_login_form_and_workbench_auth_are_preserved(self):
        html = self._html(self.client.get("/login"))
        self.assertIn('method="post"', html)
        self.assertIn('name="password"', html)
        self.assertNotIn("__ERROR_MSG__", html)
        self.assertEqual(self.client.get("/workbench").status_code, 302)


if __name__ == "__main__":
    unittest.main()
