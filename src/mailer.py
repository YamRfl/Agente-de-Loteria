import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Carrega as variáveis ocultas do arquivo .env para a memória
load_dotenv()

# ==========================================
# CONFIGURAÇÕES DO GATEWAY SMTP (Gmail)
# ==========================================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Puxa as credenciais do cofre com total segurança
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
SENHA_APP = os.getenv("SENHA_APP")

def enviar_token_senha(email_destino, token_seguranca):
    """Envia um e-mail HTML profissional com o código de recuperação."""
    
    # Trava de segurança caso o .env não seja encontrado
    if not EMAIL_REMETENTE or not SENHA_APP:
        return False, "Erro de Servidor: Credenciais de e-mail não configuradas."

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🔐 Recuperação de Senha - Agente IA Loterias"
    msg["From"] = f"Suporte IA Loterias <{EMAIL_REMETENTE}>"
    msg["To"] = email_destino

    # Arquitetura do E-mail em HTML
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto;">
            <div style="border-bottom: 2px solid #2E86C1; padding-bottom: 10px; margin-bottom: 20px;">
                <h2 style="color: #2E86C1; margin: 0;">🍀 Agente de IA - Loterias</h2>
            </div>
            
            <p>Olá,</p>
            <p>Recebemos um pedido para redefinir a senha da sua conta.</p>
            <p>Seu código de segurança (Token) de 6 dígitos é:</p>
            
            <div style="background-color: #F4F6F7; padding: 20px; border-radius: 8px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #111;">
                {token_seguranca}
            </div>
            
            <p style="color: #E74C3C; font-size: 0.9em;"><i>Este código expira em 15 minutos.</i></p>
            <p>Se você não solicitou esta alteração, sua conta continua segura e você pode simplesmente ignorar este e-mail.</p>
            
            <br>
            <p style="font-size: 0.9em; color: #777;">Atenciosamente,<br><b>Equipe de Segurança - Agente IA</b></p>
        </body>
    </html>
    """
    
    parte_html = MIMEText(html, "html")
    msg.attach(parte_html)

    try:
        # Abertura do túnel seguro TLS e disparo do e-mail
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_APP)
        server.sendmail(EMAIL_REMETENTE, email_destino, msg.as_string())
        server.quit()
        return True, "Código de segurança enviado para o seu e-mail!"
    except Exception as e:
        return False, f"Falha no servidor de e-mails: {str(e)}"