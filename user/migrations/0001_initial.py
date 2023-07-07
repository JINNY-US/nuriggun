# Generated by Django 4.2.2 on 2023-07-06 17:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('email', models.EmailField(max_length=25, unique=True, verbose_name='email address')),
                ('password', models.CharField(max_length=200, verbose_name='비밀번호')),
                ('nickname', models.CharField(blank=True, max_length=8, null=True, verbose_name='닉네임')),
                ('interest', models.CharField(blank=True, choices=[('it/과학', 'it'), ('경제', 'economy'), ('생활/문화', 'culture'), ('스포츠', 'sport'), ('날씨', 'weather'), ('world', 'world')], max_length=15, verbose_name='관심분야')),
                ('profile_img', models.ImageField(blank=True, upload_to='profile/%Y/%m/', verbose_name='프로필 이미지')),
                ('is_admin', models.BooleanField(default=False, verbose_name='관리자')),
                ('is_active', models.BooleanField(default=False, verbose_name='활성화')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성일')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='수정일')),
                ('report_count', models.PositiveIntegerField(default=0)),
                ('subscribe', models.ManyToManyField(blank=True, related_name='subscribes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reported_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports_received', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='report_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('content', models.TextField()),
                ('image', models.ImageField(blank=True, null=True, upload_to='message_images/')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('is_read', models.BooleanField(default=False, verbose_name='읽음 표시')),
                ('receiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_messages', to=settings.AUTH_USER_MODEL)),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='EmailNotificationSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_notification', models.BooleanField(default=False, verbose_name='이메일 알림 동의')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='report',
            constraint=models.UniqueConstraint(fields=('user', 'reported_user'), name='unique_report'),
        ),
    ]
