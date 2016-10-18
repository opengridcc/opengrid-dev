import requests


class Slack(object):
    def __init__(self, url, username=None, channel=None, emoji=None):
        """
        Parameters
        ----------
        url : str
        username : str, optional
        channel : str, optional
        emoji : str, optional
        """
        self.url = url
        self.username = username
        self.channel = channel
        self.emoji = emoji

    def _post(self, p):
        """
        Parameters
        ----------
        p : dict
            payload

        Returns
        -------
        requests.Response
        """
        payload = p
        if self.username is not None:
            payload.update({"username": self.username})
        if self.channel is not None:
            payload.update({"channel": self.channel})
        if self.emoji is not None:
            payload.update({"icon_emoji": self.emoji})

        r = requests.post(url=self.url, json=payload, timeout=5)
        r.raise_for_status()
        return r

    def post_text(self, *text):
        """
        Parameters
        ----------
        text : str

        Returns
        -------
        requests.Response
        """
        payload = {"text": "\n".join(text)}
        return self._post(p=payload)

    def post_json(self, j):
        """
        Parameters
        ----------
        j : dict

        Returns
        -------
        requests.Response
        """
        return self._post(j)
