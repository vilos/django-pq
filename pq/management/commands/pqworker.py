import logging
from django.core.management.base import BaseCommand
from optparse import make_option


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Starts a pq worker"
    args = "<queue queue ...>"


    option_list = BaseCommand.option_list + (
        make_option('--burst', '-b', action='store_true', dest='burst',
            default=False, help='Run in burst mode (quit after all work is done)'),
        make_option('--name', '-n', default=None, dest='name',
            help='Specify a different name'),
        make_option('--connection', '-c', action='store', default='default',
                    help='Report exceptions to this Sentry DSN'),
        make_option('--sentry-dsn', action='store', default=None, metavar='URL',
                    help='Report exceptions to this Sentry DSN'),
    )

    def handle(self, *args, **options):
        """
        The actual logic of the command. Subclasses must implement
        this method.

        """
        from django.conf import settings
        from pq.queue import Queue, SerialQueue
        from pq.worker import Worker

        sentry_dsn = options.get('sentry_dsn')
        if not sentry_dsn:
            sentry_dsn = settings.SENTRY_DSN if hasattr(settings, 'SENTRY_DSN') else None

        verbosity = int(options.get('verbosity'))
        queues = []
        for queue in args:
            q = Queue.objects.get(name=queue)
            if q.serial:
                queues.append(SerialQueue.create(name=queue))
            else:
                queues.append(Queue.create(name=queue))
        w = Worker.create(queues, name=options.get('name'), connection=options['connection'])

        # Should we configure Sentry?
        if sentry_dsn:
            from raven import Client
            from pq.contrib.sentry import register_sentry
            client = Client(sentry_dsn)
            register_sentry(client, w)

        w.work(burst=options['burst'])

