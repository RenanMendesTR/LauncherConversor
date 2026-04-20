"""
Utilitário para gerar o token criptografado (V1) da senha do FTP.

Uso:
    python gerar_senha_cripto.py
    python gerar_senha_cripto.py "minha_nova_senha"

O token gerado deve ser colado no Gist, no JSON de credenciais, dentro do campo
"password_enc". Exemplo do JSON final no Gist:

    {
        "host": "ftp.dominiosistemas.com.br",
        "user": "supuns",
        "password_enc": "VjEf5ed41LBiizesfe9iVEGGCTT1dRM/..."
    }

Observação: este script importa o segredo de criptografia diretamente do
launcher_main.py, portanto ambos SEMPRE permanecem sincronizados — não há
risco de gerar um token incompatível com a versão do Launcher em produção.
"""

import sys
from getpass import getpass

from launcher_main import _encrypt_password, _decrypt_password


def main():
    if len(sys.argv) > 1:
        senha = sys.argv[1]
    else:
        senha = getpass("Digite a nova senha do FTP (não será exibida): ").strip()

    if not senha:
        print("ERRO: senha vazia.", file=sys.stderr)
        sys.exit(1)

    token = _encrypt_password(senha)

    verificacao = _decrypt_password(token)
    if verificacao != senha:
        print("ERRO: round-trip falhou. Abortando.", file=sys.stderr)
        sys.exit(2)

    print()
    print("Token gerado com sucesso. Cole o valor abaixo no campo")
    print('"password_enc" do JSON no Gist:')
    print()
    print(token)
    print()
    print("JSON completo de exemplo para o Gist:")
    print()
    print('{')
    print('    "host": "ftp.dominiosistemas.com.br",')
    print('    "user": "supuns",')
    print(f'    "password_enc": "{token}"')
    print('}')


if __name__ == "__main__":
    main()
