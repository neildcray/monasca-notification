import kafka.client
import kafka.producer
import logging

from mon_notification.processors import BaseProcessor

log = logging.getLogger(__name__)


class SentNotificationProcessor(BaseProcessor):
    """Processes notifications which have been sent
         This involves adding them into a kafka topic for persisting by another process and adding the alarm
         to the finished queue.
    """

    def __init__(self, sent_queue, finished_queue, url, topic):
        """Init
             url, group - kafka connection details
             topic - kafka topic to publish notifications to
             finished_queue - queue written to when notifications are fully finished.
             sent_queue - the sent_notifications queue notifications are read from
        """
        self.topic = topic
        self.finished_queue = finished_queue
        self.sent_queue = sent_queue

        self.kafka = kafka.client.KafkaClient(url)
        self.producer = kafka.producer.SimpleProducer(
            self.kafka,
            async=False,
            req_acks=kafka.producer.SimpleProducer.ACK_AFTER_LOCAL_WRITE,
            ack_timeout=2000
        )

    def run(self):
        """Takes messages from the sent_queue, puts them on the kafka notification topic and then adds
             partition/offset to the finished queue
        """
        while True:
            notifications = self.sent_queue.get()
            for notification in notifications:
                responses = self.producer.send_messages(self.topic, notification.to_json())
                log.debug('Published to topic %s, message %s' % (self.topic, notification.to_json()))
                for resp in responses:
                    if resp.error != 0:
                        log.error('Error publishing to %s topic, error message %s' %
                                  (self.topic, resp.error))
            self._add_to_queue(
                self.finished_queue, 'finished', (notifications[0].src_partition, notifications[0].src_offset))