from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Cria um superusuário usando variáveis de ambiente'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username para o superusuário'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email para o superusuário'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password para o superusuário'
        )

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Usar argumentos da linha de comando ou variáveis de ambiente
        username = (
            options.get('username') or 
            os.getenv("DJANGO_SUPERUSER_USERNAME")
        )
        email = (
            options.get('email') or 
            os.getenv("DJANGO_SUPERUSER_EMAIL")
        )
        password = (
            options.get('password') or 
            os.getenv("DJANGO_SUPERUSER_PASSWORD")
        )
        
        if not username:
            self.stdout.write(
                self.style.ERROR(
                    'Username é obrigatório. Use --username ou '
                    'defina DJANGO_SUPERUSER_USERNAME'
                )
            )
            return
        
        if not password:
            self.stdout.write(
                self.style.ERROR(
                    'Password é obrigatório. Use --password ou '
                    'defina DJANGO_SUPERUSER_PASSWORD'
                )
            )
            return

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email=email or '',
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f"Superusuário '{username}' criado com sucesso!")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"Superusuário '{username}' já existe.")
            )