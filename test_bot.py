import unittest
from unittest.mock import AsyncMock, patch
import sys
import os
import asyncio

# Ensure the bot.py module is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'NekoAPI')))
from NekoAPI.bot import bot  # Import the bot instance

class TestBot(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # You don't need to create a separate Bot instance. We will test the existing bot.
        # Setup mock environment variables here if needed
        os.environ['DISCORD_BOT_TOKEN'] = "TEST_TOKEN" # Replace with mock token
        os.environ['GOOGLE_GEMINI_API_KEY'] = "TEST_GEMINI_KEY" # Mock Gemini API
        os.environ['GOOGLE_API_KEY'] = "TEST_GOOGLE_API" # Mock Search API
        os.environ['GOOGLE_CSE_ID'] = "TEST_CSE_ID" # Mock Search Engine ID
        os.environ['GITHUB_TOKEN'] = "TEST_GITHUB_TOKEN" # Mock GitHub Token
        os.environ['CUSTOM_CHANNELS'] = "1234567890"
        
    async def test_command_ping(self):
        """Test the ping command returns the correct response."""
        ctx = AsyncMock()
        ctx.send = AsyncMock()
        ctx.author.id = 12345
        ctx.guild.id = 67890
        ctx.channel.id = 1234567890
        
        # Simulate invoking the ping command
        await bot.invoke(await self.create_mock_message("!ping", ctx))

        ctx.send.assert_called_once_with("Pong!")
    
    async def test_command_echo(self):
      """Test the echo command returns the correct content."""
      ctx = AsyncMock()
      ctx.send = AsyncMock()
      ctx.author.id = 12345
      ctx.guild.id = 67890
      ctx.channel.id = 1234567890

      test_content = "Hello, Neko!"
      # Simulate invoking the echo command
      await bot.invoke(await self.create_mock_message(f"!echo {test_content}", ctx))

      ctx.send.assert_called_once_with(test_content)
    
    async def create_mock_message(self, content, ctx):
        """Create a mock message object."""
        message = AsyncMock()
        message.content = content
        message.channel = ctx
        message.author = ctx.author
        message.guild = ctx.guild
        return message

    def tearDown(self):
        # Clean up environment variables
        del os.environ['DISCORD_BOT_TOKEN']
        del os.environ['GOOGLE_GEMINI_API_KEY']
        del os.environ['GOOGLE_API_KEY']
        del os.environ['GOOGLE_CSE_ID']
        del os.environ['GITHUB_TOKEN']
        del os.environ['CUSTOM_CHANNELS']


if __name__ == "__main__":
    unittest.main()
