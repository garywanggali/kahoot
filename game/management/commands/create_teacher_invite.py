from django.core.management.base import BaseCommand

from game.models import TeacherInviteCode


class Command(BaseCommand):
    help = '创建老师注册邀请码'

    def add_arguments(self, parser):
        parser.add_argument('code', nargs='?', help='邀请码（默认随机生成）')
        parser.add_argument(
            '--max-uses', type=int, default=1, help='可使用次数（默认 1）',
        )
        parser.add_argument('--note', default='', help='备注')

    def handle(self, *args, **options):
        import secrets
        import string

        code = (options.get('code') or '').strip().upper()
        if not code:
            alphabet = string.ascii_uppercase + string.digits
            code = ''.join(secrets.choice(alphabet) for _ in range(8))

        max_uses = max(1, options['max_uses'])
        note = options.get('note') or ''

        invite, created = TeacherInviteCode.objects.get_or_create(
            code=code,
            defaults={'max_uses': max_uses, 'note': note},
        )
        if not created:
            invite.max_uses = max_uses
            invite.is_active = True
            if note:
                invite.note = note
            invite.save()
            self.stdout.write(self.style.WARNING(f'邀请码已存在，已更新：{code}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'已创建邀请码：{code}（可用 {max_uses} 次）'))
