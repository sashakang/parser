# v.0.2
# added `get_credentials` method
from typing import Union
from sqlalchemy import create_engine, engine
import smtplib, ssl


def get_engine(
    fname: str = './.server',
    db: str = None
) -> engine.base.Engine:
    
    with open(fname, 'r') as f:
        for line in f:
            # print(f'{line=}')
            if line[0] == '#': continue

            vals = [s.strip() for s in line.split(':')]
            if vals[0] == 'server': 
                server = vals[1]
                continue
            if vals[0] == 'db' and not db: 
                db = vals[1]
                continue
            if vals[0] == 'login': 
                login = vals[1]
                continue
            if vals[0] == 'password':  
                password = vals[1]
                continue
    
    if not (server and login and password):
        raise ValueError("Server access credentials are not valid")

    db_str = f'/{db}' if db else ''

    engine = create_engine(
        f'mssql+pyodbc://{login}:{password}@{server}{db_str}'
        '?driver=ODBC Driver 17 for SQL Server'
        )
        # '?driver=SQL+Server+Native+Client+11.0'

    print(f'\n=>  {engine=}')

    return engine


def get_credentials(fname: str = './.server'):

    with open(fname, 'r') as f:
        for line in f:
            # print(f'{line=}')
            if line[0] == '#': continue

            vals = [s.strip() for s in line.split(':')]
            if vals[0] == 'server': 
                server = vals[1]
                continue
            if vals[0] == 'db':
                db = vals[1]
                continue
            if vals[0] == 'login': 
                login = vals[1]
                continue
            if vals[0] == 'password':  
                password = vals[1]
                continue
    
    return server, db, login, password


def send_mail(
    recipient: Union[str, list[str]],
    subject: str = 'test subject', 
    message: str = 'test message'
):
    sender_email = "parsing.bot.no.1@gmail.com"
    port = 465  # For SSL
    password = 'pyczfikuaygkoanb'
    
    msg = f'''Subject: {subject}\n{message}'''.encode()

    # Create a secure SSL context
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        # server.ehlo()
        server.login("parsing.bot.no.1@gmail.com", password)
        server.sendmail(sender_email, recipient, msg)
        
    print(f'Sent mail to {recipient}')


if __name__ == '__main__':
    eng = get_engine()
    print(type(eng))
    print(eng)
    
    send_mail('kan@dikart.ru')
    send_mail(['kan@dikart.ru', 'kan@dikart.ru'])
