from flask import current_app
from flask_mail import Message

from app.extensions import mail


def send_activation_email(user, activation_url):
    message = Message(
        subject="Pengaktifan Akaun Sistem Tempahan Bilik Mesyuarat",
        recipients=[user.email]
    )

    message.body = f"""
Assalamualaikum dan Salam Sejahtera,

Tuan/Puan {user.full_name},

Pendaftaran akaun anda bagi Sistem Tempahan Bilik Mesyuarat telah diterima.

Sila klik pautan berikut untuk mengaktifkan akaun anda:

{activation_url}

Pautan ini akan tamat tempoh selepas 1 jam.

Sekiranya anda tidak membuat pendaftaran ini, sila abaikan emel ini.

Terima kasih.

Sistem Tempahan Bilik Mesyuarat
"""

    mail.send(message)

    current_app.logger.info(
        "Activation email sent to %s",
        user.email
    )