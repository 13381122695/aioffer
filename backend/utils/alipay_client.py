from typing import Optional, Tuple

from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.request.AlipayTradePagePayRequest import AlipayTradePagePayRequest
from alipay.aop.api.request.AlipayTradeWapPayRequest import AlipayTradeWapPayRequest
from alipay.aop.api.domain.AlipayTradePagePayModel import AlipayTradePagePayModel
from alipay.aop.api.domain.AlipayTradeWapPayModel import AlipayTradeWapPayModel

from config import settings
from utils.logger import get_logger


logger = get_logger(__name__)

_client: Optional[DefaultAlipayClient] = None


def get_alipay_client() -> DefaultAlipayClient:
    global _client
    if _client is not None:
        return _client

    if (
        not settings.alipay_app_id
        or not settings.alipay_private_key_path
        or not settings.alipay_alipay_public_key_path
    ):
        raise RuntimeError("支付宝配置不完整")

    client_config = AlipayClientConfig()
    client_config.server_url = settings.alipay_gateway
    client_config.app_id = settings.alipay_app_id

    with open(settings.alipay_private_key_path, "r", encoding="utf-8") as f:
        client_config.app_private_key = f.read()

    with open(settings.alipay_alipay_public_key_path, "r", encoding="utf-8") as f:
        client_config.alipay_public_key = f.read()

    client_config.charset = "utf-8"
    client_config.format = "json"
    client_config.sign_type = "RSA2"

    _client = DefaultAlipayClient(client_config)
    return _client


def build_pay_url(
    *,
    out_trade_no: str,
    total_amount: str,
    subject: str,
    notify_url: str,
    return_url: str,
    client_type: str = "h5",
) -> Tuple[str, Optional[str]]:
    client = get_alipay_client()

    if client_type == "pc":
        model = AlipayTradePagePayModel()
        model.out_trade_no = out_trade_no
        model.total_amount = total_amount
        model.subject = subject
        model.product_code = "FAST_INSTANT_TRADE_PAY"

        request_obj = AlipayTradePagePayRequest(biz_model=model)
        request_obj.notify_url = notify_url
        request_obj.return_url = return_url

        pay_url = client.page_execute(request_obj, http_method="GET")
        return pay_url, None

    model = AlipayTradeWapPayModel()
    model.out_trade_no = out_trade_no
    model.total_amount = total_amount
    model.subject = subject
    model.product_code = "QUICK_WAP_WAY"

    request_obj = AlipayTradeWapPayRequest(biz_model=model)
    request_obj.notify_url = notify_url
    request_obj.return_url = return_url

    pay_url = client.page_execute(request_obj, http_method="GET")

    alipay_scheme: Optional[str] = None
    if isinstance(pay_url, str) and pay_url.startswith("http"):
        from urllib.parse import quote

        encoded_url = quote(pay_url, safe="")
        alipay_scheme = (
            f"alipays://platformapi/startapp?appId=20000067&url={encoded_url}"
        )

    return pay_url, alipay_scheme

