import base64
from typing import Dict, Any

from config import settings
from utils.logger import get_logger


logger = get_logger(__name__)


def verify_alipay_sign(params: Dict[str, Any]) -> bool:
    try:
        from alipay.aop.api.util.SignatureUtils import verify_with_rsa
    except ModuleNotFoundError:
        logger.error("未安装 alipay-sdk-python，无法进行验签")
        return False

    params_copy = dict(params)

    sign = params_copy.pop("sign", None)
    sign_type = params_copy.pop("sign_type", None) or "RSA2"

    if not sign:
        logger.warning("签名为空")
        return False

    sign_str = str(sign).strip()
    if " " in sign_str and "+" not in sign_str:
        sign_str = sign_str.replace(" ", "+")

    sign_b64 = sign_str
    pad_len = (-len(sign_b64)) % 4
    if pad_len:
        sign_b64 = sign_b64 + ("=" * pad_len)

    try:
        sign_bytes = base64.b64decode(sign_b64)
    except Exception as exc:
        logger.error(f"签名 base64 解码失败: {type(exc).__name__}: {exc!r}")
        return False

    items = []
    for key in sorted(params_copy.keys()):
        value = params_copy.get(key)
        if value is not None and value != "":
            items.append(f"{key}={value}")
    content = "&".join(items)

    if not content:
        logger.warning("待签名字符串为空")
        return False

    if not settings.alipay_alipay_public_key_path:
        logger.error("支付宝公钥路径未配置")
        return False

    try:
        with open(settings.alipay_alipay_public_key_path, "r", encoding="utf-8") as f:
            alipay_public_key = f.read()
    except Exception as exc:
        logger.error(f"读取支付宝公钥失败: {exc}")
        return False

    alipay_public_key = alipay_public_key.lstrip("\ufeff").strip()
    if "BEGIN" not in alipay_public_key:
        alipay_public_key = (
            "-----BEGIN PUBLIC KEY-----\n" + alipay_public_key + "\n-----END PUBLIC KEY-----"
        )

    sign_type = str(sign_type).strip().upper() or "RSA2"

    message_bytes = content.encode("utf-8")

    try:
        import inspect

        try:
            sig = inspect.signature(verify_with_rsa)
        except (TypeError, ValueError):
            sig = None

        if sig is not None and "sign_type" in sig.parameters:
            try:
                result = verify_with_rsa(alipay_public_key, message_bytes, sign_b64, sign_type=sign_type)
            except TypeError:
                result = verify_with_rsa(alipay_public_key, message_bytes, sign_bytes, sign_type=sign_type)
        else:
            try:
                result = verify_with_rsa(alipay_public_key, message_bytes, sign_b64)
            except TypeError:
                result = verify_with_rsa(alipay_public_key, message_bytes, sign_bytes)

        if result is False:
            logger.warning("支付宝验签未通过")

        return bool(result)
    except Exception as exc:
        logger.exception(f"验证支付宝签名失败: {type(exc).__name__}: {exc!r}")
        return False
