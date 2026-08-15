from email.message import EmailMessage

import aiosmtplib

from src.core.config import settings


class EmailProvider:
    def __init__(self) -> None:
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
        self.use_tls = settings.SMTP_USE_TLS

    async def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        *,
        html: bool = False,
    ) -> None:
        if not self.host:
            raise RuntimeError("SMTP_HOST não configurado")

        if not self.from_email:
            raise RuntimeError("SMTP_FROM_EMAIL não configurado")

        message = EmailMessage()

        message["From"] = (
            f"{self.from_name} <{self.from_email}>"
            if self.from_name
            else self.from_email
        )
        message["To"] = recipient
        message["Subject"] = subject

        if html:
            message.add_alternative(body, subtype="html")
        else:
            message.set_content(body)

        await aiosmtplib.send(
            message,
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            start_tls=self.use_tls,
        )