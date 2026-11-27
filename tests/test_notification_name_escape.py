"""Check that request notification names are safe in HTML emails."""

from pathlib import Path
from unittest import TestCase

from jinja2 import Environment, FileSystemLoader
from markupsafe import escape

from invenio_requests.notifications.jinja import get_notification_user_name


class TestNotificationNameEscape(TestCase):
    def test_notification_name_escaped_only_in_html(self):
        """Treat names as text in HTML, while preserving plain-text messages."""
        templates = (
            Path(__file__).resolve().parents[1]
            / "invenio_requests/templates/semantic-ui/invenio_notifications"
        )
        env = Environment(loader=FileSystemLoader(templates), autoescape=False)
        env.globals.update(
            _=lambda text: text, get_notification_user_name=get_notification_user_name
        )
        for template_name in (
            "comment-request-event.create.jinja",
            "comment-request-event.reply.jinja",
        ):
            for name in ("<a href='https://example.org'>Click</a>", "Ada & Grace"):
                with self.subTest(template=template_name, name=name):
                    template = env.get_template(template_name)
                    ctx = template.new_context(
                        {
                            "notification": {
                                "context": {
                                    "request": {"id": "123", "title": "A request"},
                                    "request_event": {
                                        "id": "456",
                                        "created_by": {"profile": {"full_name": name}},
                                        "payload": {"content": "Hello"},
                                        "links": {"self_html": "/request"},
                                    },
                                }
                            },
                            "config": {"SITE_UI_URL": "https://example.org"},
                        }
                    )
                    list(template.root_render_func(ctx))
                    html = "".join(template.blocks["html_body"](ctx))
                    plain = "".join(template.blocks["plain_body"](ctx))
                    self.assertIn(str(escape(name)), html)
                    self.assertIn(name, plain)
                    if "<a" in name:
                        self.assertNotIn(name, html)
