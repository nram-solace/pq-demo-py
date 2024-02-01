# pq-demo-py
# Demo Partitioned Queue in Python
# nram Feb 01, 2024
# usage:
# ▶ python bin/pq-demo-pub.py --profile test --maxmsgsize 10 --numtopics 10 --maxmsgs 100 --numkeys 10 --test-id TEST100 -v



import os, sys
import argparse
import traceback
import random, string
import threading
import pprint
import datetime, time
import signal

sys.path.append(os.getcwd()+"/lib")
import PySolConfigs 
import PySolBase 
import PySolUtils   as pt
import PySolStats

Verbose = 0
Stats = {}
Verbose = 0

class T:
    ''' return current timestamp '''
    def __str__(self):
        return f'{datetime.datetime.now()}'

#----------------------------------------------------------------------------
# TopicPublisher Class - Uses SolaceBroker Class
# runnable as a thread
#
class TopicPublisher (threading.Thread) :
    ''' Solace topic publisher implementation '''

    def __init__(self, _brokerinfo):
        ''' Constructor. '''
        #threading.Thread.__init__(self)
        super(TopicPublisher, self).__init__()
        self._stop = threading.Event()
        self.brokerinfo = _brokerinfo
        #self.topics = []

    def random_payload(self, _n=10):
        return ''.join(random.choices(string.printable + string.whitespace, 
            k = random.randint(1,_n)))
        
    def run(self):
        b = self.brokerinfo
        if r.verbose > 0:
           print ( f'{T()}: {self.name} starting thread ...')
        self.sol = PySolBase.SolaceBroker ('tcp://{}:{}'.format(b['hostname'], b['smf_port']),
                                           b['vpn'],
                                           b['client_username'],
                                           b['client_password'],
                                           self.name,
                                           Stats,
                                           r.verbose)
        try:
            self.running = True
            self.sol.connect()
            self.sol.topic_publisher()
            print (f'{T()}: {self.name} publishing max {r.maxmsgs} msg to random topics')
            for _ in range( r.maxmsgs):
                if self.running: # TODO - this will always be true - see above.
                    t = cfg.random_topic(self.name)
                    # select random key
                    k = cfg.random_publisher_key (r.test_id)                  
                    self.sol.publish(t, self.random_payload(r.maxmsgsize), k)
                    time.sleep(random.uniform(0, cfg.publisher_delay()))
        except Exception as e:
            print(f'Unexpected error in TopicPublisher\n{e} ({sys.exc_info()[0]}')
            print(traceback.format_exc())
            self.stop() # IllegalStateError is attempting to publish after stop is called.

    def stopped(self):
        return self._stop.is_set()

    def stop(self):
        if self.stopped() :
            print (f'Publisher thread {self.name} is not running')
            return
        print (f'{T()}: Stopping publisher thread {self.name} ')
        if r.verbose > 0 :
            print('Terminating publisher')
        self.sol.direct_publisher.terminate()
        self.sol.close()
        self._stop.set()
        #os.kill(os.getpid(), signal.SIGINT)

#----------------------------------------------------------------------------
# TopicSubscriber Class - Uses SolaceBroker Class
# runnable as a thread
#
class TopicSubscriber (threading.Thread) :
    ''' Solace topic subscriber implementation '''

    def __init__(self, _brokerinfo, _topics = ['test/>']):
        ''' Constructor. '''
        #threading.Thread.__init__(self)
        super(TopicSubscriber, self).__init__()
        #super().__init__()
        self._stop = threading.Event()
        self.brokerinfo = _brokerinfo
        self.topics = _topics

    def run(self):
        b = self.brokerinfo
        if Verbose > 0:
           print ( f'{T()}: {self.name} starting thread')
        self.sol = PySolBase.SolaceBroker ('tcp://{}:{}'.format(b['hostname'], b['smf_port']),
                                           b['vpn'],
                                           b['client_username'],
                                           b['client_password'],
                                           self.name,
                                           Stats,
                                           Verbose)
        try :
            self.sol.connect()
            self.sol.topic_subscriber(self.topics)
        except Exception as e:
            print(f'Unexpected error in TopicSubscriber\n{e} ({sys.exc_info()[0]}')
            print(traceback.format_exc())
            self.stop() 

    def stopped(self):
            return self._stop.is_set()

    def stop(self):
        if self.stopped() :
            print (f'Subscriber thread {self.name} is not running')
            return
        print (f'{T()}: Stopping subscriber thread {self.name}')
        if Verbose > 0 :
            print('Terminating subscriber')
        self.sol.direct_receiver.terminate()
        self.sol.close()
        self._stop.set()
        #os.kill(os.getpid(), signal.SIGINT)

#----------------------------------------------------------------------------
# Main class - wrapper for convinence 
#
class Main:
    def __init__(self):
        self.threads = []

    def start_subscribers(self, b) :
        print (f"{T()}: Starting subscribers")
        # start a wild-card topic subscriber
        if r.wildcardsubscriber :
            print (f"{T()}: Adding Wildcard topic subscriber")
            sub0 = TopicSubscriber(b, ['{}/>'.format(cfg.root_topic())] )
            #sub0.setName('Subscriber-0')
            sub0.name = 'sub/0'
            sub0.start()
            self.threads.append(sub0)
            time.sleep(cfg.thread_delay())

        # start another subscriber with some topics
        for i in range (cfg.num_sub_threads()):
            sub1 = TopicSubscriber(b, cfg.random_topics())
            #sub1.setName('Subscriber-{}'.format(i+1))
            if Verbose:
                print (f"{T()}: Adding sub/{i+1}")
            sub1.name = 'sub/{}'.format(i+1)
            sub1.start()
            self.threads.append(sub1)
            time.sleep(cfg.thread_delay())

    def start_publishers(self, b) :
        print (f"{T()}: Starting {cfg.num_pub_threads()} publishers")
        for i in range(cfg.num_pub_threads()):
            if Verbose:
                print (f"{T()}: Adding pub/{i+1}")
            pub = TopicPublisher(b)
            #pub.setName('Publisher-{}'.format(i+1))
            pub.name = 'pub/{}'.format(i+1)
            pub.start()
            self.threads.append(pub)
            time.sleep(cfg.thread_delay())

    def stop_threads(self) :
        print (f"{T()}: Stopping all threads")
        for t in self.threads:
            t.stop()
            #t.join()


    def num_threads(self) :
        return len(self.threads)

#----------------------------------------------------------------------------
# main function
#          
def main(argv):
    global r, cfg, pp, Stats, Verbose

    pp = pprint.PrettyPrinter()
    p = argparse.ArgumentParser()
    p.add_argument('--configfile', action='store', default='config/default.json', 
        help='Config JSON file name. (Default: config/default.json)')

    p.add_argument('--profile', action='store', 
        help='Solace broker profile name for connect info from config file')
    p.add_argument('--test-id', action='store', default='default',
        help='Test ID string for logging (Default: default)')
    p.add_argument('--maxmsgs', action='store', type=int, default=10,
        help='Max number of message to publish. (Default: 10)')
    p.add_argument('--numtopics', action='store', type=int, default=3, 
        help='Number of random topics to generate for publish and subscribe. (Default: 3)')
    p.add_argument('--numkeys', action='store', type=int, default=3, 
        help='Number of keys (Default: 3)')
    p.add_argument('--maxmsgsize', action='store', type=int, default=10, 
        help='Max payload size. A random size between 1 - this number will be used. (Default: 10)')
    p.add_argument('--template', action='store', default='default',
        help='Template name to use for topic naming (from JSON config). (Default: default)')    
    p.add_argument('-w','--wildcardsubscriber', action='store_true', default=False,
        help='Add a wild-card subscriber for top level. (Default: no)')
    p.add_argument('--naptime', action='store', type=int, 
        help='Program sleep time in seconds. (Default: auto)')
    p.add_argument('--statsfile', action='store',
       help='View previously generated Stats file')
    p.add_argument('-v','--verbose', action="count", default=0, 
        help='Turn on verbose logging. use -vvv for debug logs (Default: Off)')
    r = p.parse_args()

    Verbose = r.verbose
    if Verbose:
        print (f'Verbose level {Verbose}')

    if r.statsfile:
        Stats = PySolStats.Stats()
        Stats.read(r.statsfile)
        Stats.prints()
        sys.exit(0)

    try:

        if not r.profile:
            raise pt.ArgError ("Required arg --profile missing")

        # object to keep track of publish and subscribe stats by topic, client, etc.
        Stats = PySolStats.Stats()

        m = Main()
        print (f'{T()}: Reading config file {r.configfile}')
        cfg = PySolConfigs.Configs(r.configfile, Verbose)
        cfg.create_topics(r.template, r.numtopics) # create some random topic names
        cfg.create_publisher_keys(r.template, r.numkeys) # create some random topic names

        if Verbose > 2 :
            cfg.dump()
        b = cfg.get(r.profile)


        #m.start_subscribers(b)
        m.start_publishers(b)

        s = r.naptime if r.naptime else cfg.nap_time(int(r.maxmsgs/2)+1)
        print (f"{T()}: {m.num_threads()} threads started. will nap {s} seconds")
        time.sleep(s)
        m.stop_threads()

        time.sleep(cfg.thread_delay())
        print (f'{T()}: Terminating main thread')
        os.kill(os.getpid(), signal.SIGINT)
        sys.exit(0)

    except KeyboardInterrupt:
        print('\nExiting on Keyboard interrupt')
        m.stop_threads()
        os.kill(os.getpid(), signal.SIGINT)
        sys.exit(1)
    except (pt.ArgError, FileNotFoundError) as e:
        print(e)
        sys.exit(1)
    except Exception as e:
        print(f'\nUnexpected error in Main\n{e} ({sys.exc_info()[0]}')
        print(traceback.format_exc())
        m.stop_threads()
        sys.exit(2)
    finally:
        if Verbose > 2:
            Stats.dump()
        if Verbose > 0:
            Stats.prints()
        Stats.save()
        #print ("kill program")
        sys.exit(0)
        #os.kill(os.getpid(), signal.SIGINT)

#----------------------------------------------------------------------------
# program entry point
#
if __name__ == "__main__":
   main(sys.argv[1:])
