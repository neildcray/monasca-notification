Basic testing.
Note that mini-mon is set to use smtp3.hp.com which must be used from within the HP corporate network.

# Load some notifications into the db.
- First edit the last line of test_notifications.sql to add in your email
- From the mysql vm run `mysql -uroot -ppassword mon < sample_notifications.sql`
 
# Feed alarm transition messages into kafka
- It is helpful to watch the log file, `tail -f /var/log/mon-notification/notification.log`
  - If desired edit /etc/mon/notification.yaml to change logging options.
- Then for all of the json files or just some run
  `/opt/kafka/bin/kafka-console-producer.sh --broker 192.168.10.10:9092 --topic alarm-state-transitions < *.json`
  - Note with the alarm_ttl now implemented you may need to update the timestamp in the json files.
    - `python -c "import time; print time.time()"` will give a current timestamp