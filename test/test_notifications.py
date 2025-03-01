import logging
import unittest
from unittest.mock import patch, Mock

from src.notifications import SendTelegramMessage


class TestSendTelegramMessage(unittest.TestCase):
    @patch('os.getenv')
    @patch('requests.post')
    def test_send_telegram_message_success(self, mock_post, mock_getenv):
        mock_getenv.side_effect = lambda key: {
            'TelegramAPIKeyRelease': 'fake_api_key',
            'TelegramChatIDRelease': 'fake_chat_id',
        }.get(key)

        # set up the mocking
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_post.return_value.__enter__.return_value = mock_resp  # support context manager

        # perform the actual test
        result = SendTelegramMessage('Test Message')
        self.assertTrue(result)

        # validate the expected parameters were passed
        mock_post.assert_called_once_with(
            'https://api.telegram.org/botfake_api_key/sendMessage',
            params={'chat_id': 'fake_chat_id', 'text': 'Test Message'}
        )

    @patch('os.getenv')
    def test_missing_api_key(self, mock_getenv):
        mock_getenv.side_effect = lambda key: None if key == 'TelegramAPIKeyRelease' else 'fake_chat_id'

        # verify the expect log message is present
        with self.assertLogs(logging.getLogger(), level='ERROR') as log:
            result = SendTelegramMessage('Test Message')
            self.assertFalse(result)
            self.assertIn('Missing TelegramAPIKey environment variable', log.output[0])

    @patch('os.getenv')
    def test_missing_chat_id(self, mock_getenv):
        mock_getenv.side_effect = lambda key: 'fake_api_key' if key == 'TelegramAPIKeyRelease' else None

        # verify the expect log message is present
        with self.assertLogs(logging.getLogger(), level='ERROR') as log:
            result = SendTelegramMessage('Test Message')
            self.assertFalse(result)
            self.assertIn('Missing TelegramChatID environment variable', log.output[0])

    @patch('os.getenv')
    @patch('requests.post')
    def test_http_error(self, mock_post, mock_getenv):
        mock_getenv.side_effect = lambda key: {
            'TelegramAPIKeyRelease': 'fake_api_key',
            'TelegramChatIDRelease': 'fake_chat_id',
        }.get(key)

        # set up the mocking
        mock_resp = Mock()
        mock_resp.status_code = 400
        mock_post.return_value.__enter__.return_value = mock_resp

        # verify the expect log message is present
        with self.assertLogs(logging.getLogger(), level='ERROR') as log:
            result = SendTelegramMessage('Test Message')
            self.assertFalse(result)
            self.assertIn('Log Review Telegram Notification Failed: Response Code 400', log.output[0])

        # validate the expected parameters were passed
        mock_post.assert_called_once_with(
            'https://api.telegram.org/botfake_api_key/sendMessage',
            params={'chat_id': 'fake_chat_id', 'text': 'Test Message'}
        )


if __name__ == '__main__':
    unittest.main()
