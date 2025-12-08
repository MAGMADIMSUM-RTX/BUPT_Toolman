import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr, formatdate, make_msgid
from typing import Optional, Tuple
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# SMTP 配置

SMTP_HOST = "smtp.qq.com"                # 例如: smtp.qq.com
SMTP_PORT = 465                          # 通常 SSL 端口是 465
SMTP_USER = "123@qq.com"            # 【替换】您的发件人邮箱
SMTP_PASS = "qwq"             # 【替换】您的邮箱授权码 
SMTP_SENDER = "泥邮工具人 <123@qq.com>" # 【替换】发件人显示名称 <邮箱>
SMTP_SENDER_NAME = "泥邮工具人"

# SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.exmail.qq.com")
# SMTP_PORT = int(os.environ.get("SMTP_PORT", 465))
# SMTP_USER = os.environ.get("SMTP_USER")
# SMTP_PASS = os.environ.get("SMTP_PASS")
# SMTP_SENDER = os.environ.get("SMTP_SENDER") or SMTP_USER or "noreply@example.com"
# SMTP_SENDER_NAME = os.environ.get("SMTP_SENDER_NAME", "泥邮工具人")
print(SMTP_HOST,SMTP_PORT,SMTP_USER,SMTP_PASS)

# 初始化 Jinja2 环境
TEMPLATE_DIR = Path(__file__).parent / "templates"
if HAS_JINJA2:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(['html', 'xml'])
    )
else:
    env = None
    logger.warning("Jinja2 not found. Template rendering will be limited.")

def render_template(template_name: str, **context) -> str:
    """
    渲染 HTML 邮件模板。
    如果安装了 Jinja2，使用 Jinja2 渲染；否则回退到简单的字符串替换（不推荐）。
    """
    if HAS_JINJA2 and env:
        try:
            template = env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return ""
    else:
        # 简单的回退逻辑，不支持复杂的 Jinja2 语法
        try:
            tpl_path = TEMPLATE_DIR / template_name
            tpl_text = tpl_path.read_text(encoding="utf-8")
            # 注意：这无法处理 {% if %} 等逻辑，仅作紧急回退
            return tpl_text.format(**context)
        except Exception as e:
            logger.error(f"Fallback rendering failed: {e}")
            return "<html><body><h1>Error rendering template</h1></body></html>"

def _resolve_sender() -> Tuple[str, str]:
    """
    解析发件人信息。
    返回: (Header 格式的 From 字段, SMTP envelope sender 邮箱)
    """
    raw = SMTP_SENDER or ""
    email_addr = None

    # 尝试从 "Name <email>" 格式中提取
    if '<' in raw and '>' in raw:
        start = raw.find('<') + 1
        end = raw.find('>', start)
        if end > start:
            candidate = raw[start:end].strip()
            if '@' in candidate:
                email_addr = candidate

    # 尝试直接匹配邮箱
    if not email_addr and '@' in raw:
        email_addr = raw.strip()

    # 回退到 SMTP_USER
    if not email_addr and SMTP_USER and '@' in SMTP_USER:
        email_addr = SMTP_USER.strip()

    # 最终回退
    if not email_addr:
        email_addr = 'noreply@example.com'

    # 确定显示名称
    display_name = SMTP_SENDER_NAME
    if not display_name and '<' in raw:
        name_part = raw.split('<', 1)[0].strip()
        if name_part:
            display_name = name_part

    if display_name:
        header_value = formataddr((str(Header(display_name, 'utf-8')), email_addr))
    else:
        header_value = email_addr

    return header_value, email_addr

def send_email(to_email: str, subject: str, content: str, html: Optional[str] = None, to_name: Optional[str] = None) -> bool:
    """
    发送邮件。
    
    :param to_email: 收件人邮箱
    :param subject: 邮件主题
    :param content: 纯文本内容
    :param html: HTML 内容（可选）
    :param to_name: 收件人名称（可选）
    :return: 是否成功
    """
    if not to_email:
        logger.error("收件人邮箱为空")
        return False

    logger.info(f"准备发送邮件给: {to_email}")

    msg = MIMEMultipart('alternative') if html else MIMEText(content, 'plain', 'utf-8')
    
    formatted_from, envelope_sender = _resolve_sender()
    msg['From'] = formatted_from
    
    if to_name:
        msg['To'] = formataddr((str(Header(to_name, 'utf-8')), to_email))
    else:
        msg['To'] = to_email

    msg['Subject'] = Header(subject, 'utf-8')
    msg['Date'] = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid()

    if html:
        msg.attach(MIMEText(content, 'plain', 'utf-8'))
        msg.attach(MIMEText(html, 'html', 'utf-8'))

    try:
        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.starttls() # 如果需要 TLS，请取消注释

        if SMTP_USER and SMTP_PASS:
            server.login(SMTP_USER, SMTP_PASS)
        
        failed = server.sendmail(envelope_sender, [to_email], msg.as_string())
        server.quit()
        
        if failed:
            logger.error(f"邮件发送失败，被服务器拒绝的收件人: {failed}")
            return False

        logger.info(f"邮件发送成功: {to_email}")
        return True
    except Exception as e:
        logger.error(f"邮件发送失败: {e}")
        return False

if __name__ == "__main__":
    # 测试代码
    if not SMTP_USER or not SMTP_PASS:
        logger.warning("未配置 SMTP_USER 或 SMTP_PASS，跳过发送测试。")
    else:
        # 渲染测试
        html_content = render_template(
            'register.html',
            user_name='测试用户',
            confirmation_url='https://baidu.com',
            app_name='泥邮工具人',
            support_email='help@example.com',
            current_year=2025
        )
        
        # 发送测试
        send_email(
            to_email="123@qq.com", # 替换为你的测试邮箱
            to_name="测试用户",
            subject="注册验证 - 测试邮件",
            content="请查看 HTML 版本。",
            html=html_content
        )
