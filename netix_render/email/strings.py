"""Chrome phrases per locale; body copy always comes from the caller's contract, never from here."""

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "hello": "Hello",
        "regards": "Regards",
        "automated_note": "This is an automated message — please do not reply.",
        "verification_code": "Your verification code",
        "code_expires": "This code expires in {minutes} minutes.",
        "code_ignore": "If you did not request this code, you can safely ignore this email.",
        "report_ready": "Your report is ready",
        "download": "Download",
        "report_pack_intro": "The following files were generated and are attached or available below.",
        "alarm_triggered": "Alarm triggered",
        "asset": "Asset",
        "triggered_at": "Triggered at",
        "feedback_intro": "We would appreciate your feedback.",
        "reference": "Reference",
    },
    "ar": {
        "hello": "مرحباً",
        "regards": "مع التحية",
        "automated_note": "هذه رسالة آلية — يرجى عدم الرد.",
        "verification_code": "رمز التحقق الخاص بك",
        "code_expires": "تنتهي صلاحية هذا الرمز خلال {minutes} دقيقة.",
        "code_ignore": "إذا لم تطلب هذا الرمز، يمكنك تجاهل هذه الرسالة.",
        "report_ready": "تقريرك جاهز",
        "download": "تنزيل",
        "report_pack_intro": "تم إنشاء الملفات التالية وهي مرفقة أو متاحة أدناه.",
        "alarm_triggered": "تم تفعيل الإنذار",
        "asset": "الأصل",
        "triggered_at": "وقت التفعيل",
        "feedback_intro": "نقدّر ملاحظاتك.",
        "reference": "المرجع",
    },
    "es": {
        "hello": "Hola",
        "regards": "Saludos",
        "automated_note": "Este es un mensaje automático — por favor no responda.",
        "verification_code": "Su código de verificación",
        "code_expires": "Este código caduca en {minutes} minutos.",
        "code_ignore": "Si no solicitó este código, puede ignorar este correo.",
        "report_ready": "Su informe está listo",
        "download": "Descargar",
        "report_pack_intro": "Se generaron los siguientes archivos; están adjuntos o disponibles abajo.",
        "alarm_triggered": "Alarma activada",
        "asset": "Activo",
        "triggered_at": "Activada a las",
        "feedback_intro": "Agradeceríamos sus comentarios.",
        "reference": "Referencia",
    },
}


def translator(locale: str):
    """Returns t(key, **kwargs) bound to locale, falling back to English for missing keys."""
    table = STRINGS.get(locale, STRINGS["en"])

    def translate(key: str, **kwargs: object) -> str:
        template = table.get(key) or STRINGS["en"][key]
        return template.format(**kwargs) if kwargs else template

    return translate
