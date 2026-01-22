# services/network_service.py

"""
NetworkService - Obsługa uwierzytelniania i dostępu do folderu sieciowego
Zapewnia dostęp do plików na serwerze z prawami edycji
"""
import subprocess
import os
from pathlib import Path
from src.config.constants import (
    SERVER_BASE, NETWORK_USER, NETWORK_PASSWORD,
    TEMPLATES_PATH, DATA_PATH
)


class NetworkService:
    """Serwis zarządzający dostępem do folderu sieciowego"""

    def __init__(self):
        self.is_connected = False
        self.server_path = str(SERVER_BASE)

    def connect(self) -> bool:
        """
        Nawiązuje połączenie z folderem sieciowym używając NET USE

        Returns:
            bool: True jeśli połączono pomyślnie
        """
        try:
            # Sprawdź czy folder już jest dostępny
            if SERVER_BASE.exists():
                self.is_connected = True
                return True

            # Próba montowania z uwierzytelnianiem
            # net use \\server\share password /user:username
            cmd = f'net use {self.server_path} /user:{NETWORK_USER} {NETWORK_PASSWORD}'

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self.is_connected = True
                print(f"✅ Połączono z {self.server_path}")
                return True
            else:
                print(f"⚠️ Błąd montowania: {result.stderr}")
                self.is_connected = False
                return False

        except Exception as e:
            print(f"❌ Błąd połączenia z serwerem: {e}")
            self.is_connected = False
            return False

    def disconnect(self) -> bool:
        """
        Rozłącza połączenie z folderem sieciowym

        Returns:
            bool: True jeśli rozłączono pomyślnie
        """
        try:
            cmd = f'net use {self.server_path} /delete'
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self.is_connected = False
                print(f"✅ Rozłączono z {self.server_path}")
                return True
            else:
                return False

        except Exception as e:
            print(f"❌ Błąd rozłączania: {e}")
            return False

    def ensure_connection(self) -> bool:
        """
        Upewnia się że połączenie jest aktywne, w razie potrzeby łączy

        Returns:
            bool: True jeśli połączenie jest dostępne
        """
        if not self.is_connected:
            return self.connect()

        # Sprawdź czy nadal mamy dostęp
        try:
            if SERVER_BASE.exists():
                return True
            else:
                # Połączenie zerwane, próbuj ponownie
                self.is_connected = False
                return self.connect()
        except:
            self.is_connected = False
            return self.connect()

    def check_write_access(self) -> bool:
        """
        Sprawdza czy mamy uprawnienia do zapisu w folderze sieciowym

        Returns:
            bool: True jeśli możemy zapisywać pliki
        """
        if not self.ensure_connection():
            return False

        try:
            # Próba zapisu testowego pliku
            test_file = DATA_PATH / ".write_test"
            test_file.write_text("test")
            test_file.unlink()  # Usuń testowy plik
            return True
        except Exception as e:
            print(f"⚠️ Brak uprawnień do zapisu: {e}")
            return False

    def get_status(self) -> dict:
        """
        Zwraca status połączenia i uprawnień

        Returns:
            dict: Informacje o statusie połączenia
        """
        connected = self.ensure_connection()
        write_access = self.check_write_access() if connected else False

        return {
            'connected': connected,
            'write_access': write_access,
            'server_path': self.server_path,
            'templates_exists': TEMPLATES_PATH.exists() if connected else False,
            'data_exists': DATA_PATH.exists() if connected else False,
        }