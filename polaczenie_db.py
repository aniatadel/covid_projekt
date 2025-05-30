import psycopg2
from azure.identity import DefaultAzureCredential
from sqlalchemy import create_engine

def get_engine():
    """
    Tworzy i zwraca silnik połączenia SQLAlchemy do bazy danych PostgreSQL
    hostowanej na platformie Azure z wykorzystaniem uwierzytelniania AAD (Azure Active Directory).
    :return: Obiekt SQLAlchemy Engine umożliwiający komunikację z bazą danych PostgreSQL.
    """
    server = "bazacovid.postgres.database.azure.com"  # Adres serwera bazy danych
    database = "bazacovid19"                          # Nazwa bazy danych
    aad_principal = "273776@student.pwr.edu.pl"       # Użytkownik AAD uprawniony do połączenia

    # Pobranie tokenu AAD dla dostępu do PostgreSQL w Azure
    credential = DefaultAzureCredential()
    token = credential.get_token("https://ossrdbms-aad.database.windows.net")

    # Funkcja pomocnicza tworząca połączenie przy użyciu tokenu AAD
    def creator():
        return psycopg2.connect(
            host=server,
            dbname=database,
            user=aad_principal,
            password=token.token,
            sslmode="require",  # Wymuszona komunikacja szyfrowana SSL
            port=5432
        )

    # Utworzenie silnika SQLAlchemy z funkcją creator
    engine = create_engine("postgresql+psycopg2://", creator=creator)
    return engine
