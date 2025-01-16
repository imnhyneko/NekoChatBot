import unittest
from unittest.mock import AsyncMock, patch
import sys
import os

# Đảm bảo module bot.py trong thư mục NekoAPI được import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'NekoAPI')))
from bot import Bot  # Giả sử trong bot.py có lớp Bot

class TestBot(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Mock token và các cài đặt cần thiết cho bot
        self.mock_token = "TEST_TOKEN"
        self.bot = Bot(command_prefix="!")

    async def test_command_ping(self):
        """Kiểm tra lệnh ping trả về phản hồi đúng."""
        with patch("discord.ext.commands.Bot.invoke") as mock_invoke:
            mock_invoke.return_value = None  # Không thực sự gọi API Discord
            
            ctx = AsyncMock()
            ctx.send = AsyncMock()  # Mock send method

            # Giả sử bot.py có hàm ping(ctx)
            await self.bot.ping(ctx)
            ctx.send.assert_called_once_with("Pong!")

    async def test_command_echo(self):
        """Kiểm tra lệnh echo trả về nội dung chính xác."""
        with patch("discord.ext.commands.Bot.invoke") as mock_invoke:
            mock_invoke.return_value = None
            
            ctx = AsyncMock()
            ctx.send = AsyncMock()

            # Giả sử bot.py có hàm echo(ctx, *, content)
            test_content = "Hello, Neko!"
            await self.bot.echo(ctx, content=test_content)
            ctx.send.assert_called_once_with(test_content)

    def tearDown(self):
        # Xóa bot sau khi test
        del self.bot

if __name__ == "__main__":
    unittest.main()
