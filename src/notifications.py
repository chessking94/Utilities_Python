import logging
import os

import requests


def SendTelegramMessage(message: str, chat_id: int = None) -> bool:
    """Sends a message via Telegram

    Parameters
    ----------
    message : str
        The text of the message to send
    chat_id : int (default None)
        The ID value of the user to send the message to

    Returns
    -------
    bool : If the message was sent successfully

    """
    api_key = os.getenv('TelegramAPIKeyRelease')
    if api_key is None:
        logging.error('Missing TelegramAPIKey environment variable')
        return False

    if chat_id is None:
        chat_id = os.getenv('TelegramChatIDRelease')
        if chat_id is None:
            logging.error('Missing TelegramChatID environment variable')
            return False

    url = f'https://api.telegram.org/bot{api_key}/sendMessage'
    params = {'chat_id': chat_id, 'text': message}
    with requests.post(url, params=params) as resp:
        cde = resp.status_code
        if cde != 200:
            logging.error(f'Log Review Telegram Notification Failed: Response Code {cde}')
            return False
        else:
            return True
