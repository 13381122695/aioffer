# -*- coding:utf-8 -*-
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, make_msgid, formatdate
import random

# ==================== 【请在此处填写你的配置】====================
# 发信地址（必须是阿里云邮件推送中已验证的发信地址）
username = 'noreply@coursefinder.com.cn'  # ←←← 修改这里！

# SMTP密码（在阿里云控制台「邮件推送」-「发信地址」中生成）
password = 'NOreply1234'                # ←←← 修改这里！

# 收件人邮箱（可改为用户输入的邮箱）
to_email = '875401@qq.com'                  # ←←← 修改这里！或从用户输入获取

# 回信地址（可选，一般设为和发信地址一致或客服邮箱）
reply_to = 'noreply@coursefinder.com.cn'               # ←←← 可选修改

# 验证码位数（默认6位数字）
code_length = 6
# =============================================================

# 生成随机验证码
verification_code = ''.join([str(random.randint(0, 9)) for _ in range(code_length)])

# 构建邮件内容
msg = MIMEMultipart('alternative')
msg['Subject'] = Header('【验证码】您的验证码是：' + verification_code, 'utf-8')
msg['From'] = formataddr(["系统通知", username])
msg['To'] = to_email
msg['Reply-to'] = reply_to
msg['Message-id'] = make_msgid()
msg['Date'] = formatdate()

# HTML 邮件正文（可自定义样式）
html_body = f"""
<html>
  <body>
    <p>您好！</p>
    <p><曼彻斯特大学研究生专业入学评估系统>向您发送的验证码为：<strong style="color: #d32f2f; font-size: 24px;">{verification_code}</strong></p>
    <p>该验证码5分钟内有效，请勿泄露给他人。</p>
    <p>—— 曼彻斯特大学研究生专业入学评估系统自动发送，请勿回复</p>
  </body>
</html>
"""
msg.attach(MIMEText(html_body, 'html', 'utf-8'))

# 发送邮件
try:
    # 使用阿里云邮件推送 SMTP（端口 80 或 465）
    client = smtplib.SMTP('smtpdm.aliyun.com', 80)
    client.set_debuglevel(0)  # 设为1可查看调试信息
    client.login(username, password)
    
    # 注意：sendmail 的第二个参数必须是列表
    client.sendmail(username, [to_email], msg.as_string())
    client.quit()
    
    print(f"✅ 验证码邮件已发送至 {to_email}，验证码为：{verification_code}")
    # 实际使用时不要打印验证码！此处仅用于测试
except Exception as e:
    print("❌ 邮件发送失败:", str(e))