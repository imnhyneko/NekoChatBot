import unittest
from unittest.mock import AsyncMock, patch
import sys
import os
import asyncio
from dotenv import load_dotenv

# Ensure the bot.py module is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'NekoAPI')))
from bot import bot  # Import the bot instance

class TestBot(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Load environment variables from .env.test
        dotenv_path = os.path.join(os.path.dirname(__file__), '.env.test')
        load_dotenv(dotenv_path=dotenv_path)
        
        # Start the bot with the token from the environment
        self.bot_task = asyncio.create_task(bot.start(os.getenv("DISCORD_BOT_TOKEN")))

    async def execute_command(self, command, ctx):
        """Helper function to execute a bot command."""
        message = await self.create_mock_message(command, ctx)
        await bot.process_commands(message)
    
    async def test_command_ping(self):
        """Test the ping command returns the correct response."""
        ctx = AsyncMock()
        ctx.send = AsyncMock()
        ctx.author.id = 12345
        ctx.guild.id = 67890
        ctx.channel.id = 1234567890
        
        # Simulate invoking the ping command
        await self.execute_command("!ping", ctx)

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
      await self.execute_command(f"!echo {test_content}", ctx)

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
        # Clean up by canceling the bot task
        self.bot_task.cancel()

if __name__ == "__main__":
    unittest.main()
