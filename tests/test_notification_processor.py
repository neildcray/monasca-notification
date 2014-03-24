"""Tests NotificationProcessor"""

import mock
import multiprocessing
import time
import unittest

from mon_notification.notification import Notification
from mon_notification.processors import notification_processor


class TestStateTracker(unittest.TestCase):

    def setUp(self):
        self.notification_queue = multiprocessing.Queue(10)
        self.sent_notification_queue = multiprocessing.Queue(10)
        self.finished_queue = multiprocessing.Queue(10)
        self.log_queue = multiprocessing.Queue(10)
        self.email_config = {'server': 'my.smtp.server',
                             'port': 25,
                             'user': None,
                             'password': None,
                             'timeout': 60,
                             'from_addr': 'hpcs.mon@hp.com'}

    @mock.patch('mon_notification.processors.notification_processor.smtplib')
    @mock.patch('mon_notification.processors.notification_processor.log')
    def _start_processor(self, mock_log, mock_smtp):
        """Start the processor with the proper mocks
        """
        # Since the log runs in another thread I can mock it directly, instead change the methods to put to a queue
        mock_log.warn = self.log_queue.put
        mock_log.error = self.log_queue.put

        self.mock_log = mock_log
        self.mock_smtp = mock_smtp

        nprocessor = notification_processor.NotificationProcessor(
            self.notification_queue, self.sent_notification_queue, self.finished_queue, self.email_config
        )
        self.processor = multiprocessing.Process(target=nprocessor.run)
        self.processor.start()

    def test_invalid_notification(self):
        """Verify invalid notification type is rejected.
        """
        alarm_dict = {"tenantId": "0", "alarmId": "0", "alarmName": "test Alarm", "oldState": "OK", "newState": "ALARM",
                      "stateChangeReason": "I am alarming!", "timestamp": time.time()}
        invalid_notification = Notification('invalid', 0, 1, 'test notification', 'me@here.com', alarm_dict)

        self.notification_queue.put([invalid_notification])
        self._start_processor()
        finished = self.finished_queue.get(timeout=2)
        log_msg = self.log_queue.get(timeout=1)
        self.processor.terminate()

        self.assertTrue(finished == (0, 1))
        self.assertTrue(log_msg == 'Notification type invalid is not a valid type')