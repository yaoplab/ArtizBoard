"""Test FTP connection"""
import socket, sys

results = []
for port in [21, 22, 2222]:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    r = s.connect_ex(('77.37.37.209', port))
    results.append(f"Port {port}: {'OPEN' if r == 0 else 'CLOSED'}")
    s.close()

print('\n'.join(results))

# Try FTP explicit TLS
if results[0] == 'Port 21: OPEN':
    from ftplib import FTP_TLS
    try:
        ftp = FTP_TLS()
        ftp.connect('77.37.37.209', 21, timeout=10)
        print('FTP_TLS connected')
        ftp.login('u989105453.aristodetoonasi.com', 'Maat@-+2026')
        print('FTP login OK')
        ftp.prot_p()
        print(ftp.pwd())
        ftp.quit()
    except Exception as e:
        print(f'FTP error: {e}')
