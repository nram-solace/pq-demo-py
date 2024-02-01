#----------------------------------------------------------------------------
# PySolBase
#   Basic Python Solace API wrappers
#
# nram, Feb 3, 2021
#
import sys, os
import datetime, time

# Import Solace Python  API modules from the solace package
from solace.messaging.messaging_service import MessagingService, ReconnectionListener, ReconnectionAttemptListener, ServiceInterruptionListener, RetryStrategy, ServiceEvent
from solace.messaging.config.solace_constants import message_user_property_constants
from solace.messaging.resources.topic import Topic
from solace.messaging.publisher.direct_message_publisher import PublishFailureListener
from solace.messaging.resources.topic_subscription import TopicSubscription
from solace.messaging.receiver.message_receiver import MessageHandler, InboundMessage

sys.path.append(os.getcwd()+"/lib")
import PySolUtils   as pt

Verbose = 0

class T:
    ''' return current timestamp '''
    def __str__(self):
        return f'{datetime.datetime.now()}'


#----------------------------------------------------------------------------
# SolaceBroker Class
#
class SolaceBroker:
    ''' implements solace broker connection handling '''

    #----------------------------------------------------------------------------
    # Inner classes for message, event and error handling
    #
    class MessageHandlerImpl(MessageHandler):
        ''' async message handler callback '''

        def __init__ (self, _name):
            self.name = _name

        def on_message(self, message: InboundMessage):
            topic = message.get_destination_name()
            ss = Stats.sub_stats(self.name, topic)
            if Verbose > 0 :
               print (f'{T()}: [{self.name}] <- {topic} {ss}')
            if Verbose > 2:
                payload_str = message.get_payload_as_string
                print("\n" + f"Message Payload String: {payload_str} \n")
                print("\n" + f"Message Topic: {topic} \n")
                print("\n" + f"Message dump: {message} \n")

    class ServiceEventHandler(ReconnectionListener, ReconnectionAttemptListener, ServiceInterruptionListener):
        ''' solace event handlers '''

        def on_reconnected(self, e: ServiceEvent):
            print("\non_reconnected")
            print(f"Error cause: {e.get_cause()}")
            print(f"Message: {e.get_message()}")
        
        def on_reconnecting(self, e: "ServiceEvent"):
            print("\non_reconnecting")
            print(f"Error cause: {e.get_cause()}")
            print(f"Message: {e.get_message()}")

        def on_service_interrupted(self, e: "ServiceEvent"):
            print("\non_service_interrupted")
            print(f"Error cause: {e.get_cause()}")
            print(f"Message: {e.get_message()}")

    class PublisherErrorHandling(PublishFailureListener):
        ''' solace event handler '''

        def on_failed_publish(self, e: "FailedPublishEvent"):
            print("on_failed_publish")

        
    def __init__(self, _smfurl, _vpn, _clientusername, _clientpasswd, 
                       _name = "default", _stats = None, _verbose = False):
        global Verbose, Stats
        self.broker_props = {
            "solace.messaging.transport.host": _smfurl,
            "solace.messaging.service.vpn-name": _vpn,
            "solace.messaging.authentication.scheme.basic.username": _clientusername,
            "solace.messaging.authentication.scheme.basic.password": _clientpasswd
        }
        self.name = _name
        Stats = _stats
        Verbose = _verbose # store globally for other classes to use
        if Verbose > 2:
            print (f'broker_props: {self.broker_props}')

    def connect (self):
        print (f'{T()}: {self.name} Connecting to {self.broker_props["solace.messaging.transport.host"]} ({self.broker_props["solace.messaging.service.vpn-name"]})')
        self.messaging_service = MessagingService.builder().from_properties(self.broker_props)\
                    .with_reconnection_retry_strategy(RetryStrategy.parametrized_retry(20,3))\
                    .build()
        # Event Handeling for the messaging service
        self.service_handler = self.ServiceEventHandler()
        self.messaging_service.add_reconnection_listener(self.service_handler)
        self.messaging_service.add_reconnection_attempt_listener(self.service_handler)
        self.messaging_service.add_service_interruption_listener(self.service_handler)

        # Blocking connect thread
        self.messaging_service.connect()
        if not self.messaging_service.is_connected:
            raise pt.ServiceError (f'Messaging Service not connected')

    def topic_subscriber(self, _topics):
        print (f'{T()}: {self.name} Starting topic subscriber with {len(_topics)} topics')
        if Verbose > 1:
            print (f'Topics: {_topics})')

        # Define a Topic subscriptions 
        topics_sub = []
        for t in _topics:
            topics_sub.append(TopicSubscription.of(t))

        # Build a Receiver with the given topics and start it
        self.direct_receiver = self.messaging_service.create_direct_message_receiver_builder()\
                                .with_subscriptions(topics_sub)\
                                .build()

        self.direct_receiver.start()
        if not self.direct_receiver.is_running():
            raise pt.ServiceError(f'Topic Subscriber not running.')
        try:
            # Callback for received messages
            self.direct_receiver.receive_async(self.MessageHandlerImpl(self.name))
            while True:
               time.sleep(1)

        finally:
            print('{TS()}: {self.name} Terminating receiver')
            self.direct_receiver.terminate()
            print('Disconnecting Messaging Service')
            self.messaging_service.disconnect()

    def topic_publisher(self):
        print (f'{T()}: {self.name} Starting topic publisher')
        # Create a direct message publisher and start it
        self.direct_publisher = self.messaging_service.create_direct_message_publisher_builder().build()
        self.direct_publisher.set_publish_failure_listener(self.PublisherErrorHandling())

        # Blocking Start thread
        self.direct_publisher.start()
        if not self.direct_publisher.is_ready():
            raise pt.ServiceError(f'Topic Publisher not ready.')
        return self.direct_publisher

    def publish(self, _topicname, _payload, _key='default'):
        try:
            outbound_msg_builder = self.messaging_service.message_builder() \
                    .with_application_message_id("nram-test") \
                    .with_property("application", "pq-demo") \
                    .with_property("language", "Python") \
                    .with_property(message_user_property_constants.QUEUE_PARTITION_KEY, _key) \
 

            topic = Topic.of(_topicname)
            # Direct publish the message with dynamic headers and payload
            outbound_msg = outbound_msg_builder.build(_payload)
            self.direct_publisher.publish(destination=topic, message=outbound_msg)
            ss = Stats.pub_stats(self.name, _topicname, _key)
            #ss=""
            if Verbose > 0 :
               print (f'{T()}: {self.name} publishing to Topic: {_topicname} Key: {_key} ({len(_payload)} bytes) {ss}')


        except Exception as e:
            print(f'Unexpected error in SolaceBroker\n{e} ({sys.exc_info()[0]}')
            raise e

    def close(self):
        if Verbose > 0 :
            print('Disconnecting Messaging Service')
        self.messaging_service.disconnect()

