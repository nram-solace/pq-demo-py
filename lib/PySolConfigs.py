#----------------------------------------------------------------------------
# PySolConfigs
#  Configs file handling Class
#
# nram, Feb 3, 2021

import os, sys
import json
import random, string, re
import pprint
import datetime

sys.path.append(os.getcwd()+"/lib")
import PySolBase 
import PySolUtils   as pt

Verbose = 0
pp = pprint.PrettyPrinter()
Mistr = [] 

class T:
    ''' return current timestamp '''
    def __str__(self):
        return f'{datetime.datetime.now()}'

class Configs:
    ''' Process Solace configs JSON '''

    def __init__(self, _cfgfile, _verbose=False):
        global Verbose, Mistr
        self.cfgfile = _cfgfile
        Verbose = _verbose 
        self.topics = []
        self.publisher_keys = []
        with open(_cfgfile) as f:
            self.configs = json.load(f)
        if Verbose > 2 :
            print (self.configs)
        # build monotonically increasing stirng array .. len: 456,976
        # aaaa, aaab, ... zzzz
        Mistr = [ chr(i)+chr(j)+chr(k)+chr(l)   for i in range(97,123) 
                                                for j in range(97,123) 
                                                for k in range(97,123) 
                                                for l in range(97,123)]
        if Verbose > 0:
            print (f'{T()}: monotonically increasing string array with {len(Mistr)} built')

    def get(self, _id) :
        b = [ br for br in self.configs['brokers'] if br['id'] == _id]
        if len(b) > 0 :
            if Verbose > 2 :
                print (f"Got broker [{_id}] {b}")
            return b[0]
        else :
            msg = f'ID {_id} not found'
            raise pt.ArgError(msg)

    def info(self, b):

        return 'tcp://{}:{}'.format(b['hostname'], b['smf_port']), \
                                           b['vpn'], \
                                           b['client_username'], \
                                           b['client_password']



    def create_topics(self, _template, _n = 10):
        if _template not in self.configs['topic-templates']:
            s = f'Template {_template} not found in config'
            raise pt.ArgError(s)

        self.topicsc = self.configs['topic-templates'][_template]
        if Verbose > 1 :
            print(type(self.topicsc))
            pp.pprint(self.topicsc)
        self.topics = []
        for i in range(_n):
            t = '/'.join([ l[random.randint(0,len(l)-1)] for l in self.topicsc ])
            while t.find('$RANDOMSTR') > 0:
                t = t.replace('$RANDOMSTR', self.random_str(), 1)
            while t.find('$RANDOMNUM') > 0:
                t = t.replace('$RANDOMNUM', self.random_int(), 1)
            if t.find('$MINCSTR') > 0:
                t = t.replace('$MINCSTR', Mistr[i])
            if t.find('$MINCINT') > 0:
                t = t.replace('$MINCINT', '{:05d}'.format(i))
            if t.find('$TIMESTAMP') > 0 :
                t = t.replace('$TIMESTAMP', re.sub('\W','',str(T())))
            self.topics.append(t)
        print (f'{T()}: {len(self.topics)} topics created from schema in config')

    def create_publisher_keys (self, _template, _n = 10):
        if _template not in self.configs['publisher-key-templates']:
            s = f'Template {_template} not found in config'
            raise pt.ArgError(s)

        self.keysc = self.configs['publisher-key-templates'][_template]
        if Verbose > 1 :
            print(type(self.keysc))
            pp.pprint(self.keysc)
        self.publisher_keys = []
        for i in range(_n):
            t = '-'.join([ l[random.randint(0,len(l)-1)] for l in self.keysc ])
            while t.find('$RANDOMSTR') >= 0:
                t = t.replace('$RANDOMSTR', self.random_str(), 1)
            while t.find('$RANDOMNUM') >= 0:
                t = t.replace('$RANDOMNUM', self.random_int(), 1)
            if t.find('$MINCSTR') >= 0:
                t = t.replace('$MINCSTR', Mistr[i])
            if t.find('$MINCINT') >= 0:
                t = t.replace('$MINCINT', '{:05d}'.format(i))
            if t.find('$TIMESTAMP') >= 0 :
                t = t.replace('$TIMESTAMP', re.sub('\W','',str(T())))
            self.publisher_keys.append(t)
        print (f'{T()}: {len(self.publisher_keys)} topics created from schema in config')
            
    def random_str(self):
        l = self.configs['general']['randomstr-length']
        return ''.join(random.choices(string.ascii_lowercase, k = random.randint(l[0],l[1])))

    def random_int(self):
        l = self.configs['general']['randomint-length']
        return ''.join(random.choices(string.digits, k = random.randint(l[0],l[1])))

    def root_topic(self):
        return self.topicsc[0][0]

    # random topic name functions
    def create_randmom_topics(self, _n = 10, _levels = 3, _prefix = 'test'):
        for _ in range(_n):
            t = [_prefix]
            for _ in range(_levels) :
                s = ''.join(random.choices(string.ascii_lowercase, k = random.randint(3,8))) 
                t.append(s)
            self.topics.append('/'.join(t))
        print (f'{T()}: {len(self.topics)} random topics created')

    def num_topics(self):
        return len(self.topics)

    def all_topics(self):
        return self.topics

    # return a random topic - with publisher id substitution
    def random_topic(self, _pub_id = 'default'):
        t =  self.topics[random.randint(0,len(self.topics)-1)]
        return t.replace('$PUBLISHERID', _pub_id)
    
        # return a random topic - with publisher id substitution
    def random_publisher_key(self, _test_id = 'default'):
        k =  self.publisher_keys[random.randint(0,len(self.publisher_keys)-1)]
        return k.replace('$TESTID', _test_id)


    def random_topics(self, _n = -1, _pub_id='*'):
        ts = []
        n = self.configs['general']['num-subscriber-topics'] if _n < 0 else _n
        if Verbose > 1:
            print (f'{T()}: getting {n} random topics')
        for _ in range(n):
            t = self.topics[random.randint(0,len(self.topics)-1)]
            ts.append(t.replace('$PUBLISHERID', _pub_id))
        return ts
    
    def random_publisher_keys(self, _n = -1, _test_id='*'):
        ps = []
        n = self.configs['general']['num-publisher-keys'] if _n < 0 else _n
        if Verbose > 1:
            print (f'{T()}: getting {n} random publisher keys')
        for _ in range(n):
            t = self.pub_keys[random.randint(0,len(self.pub_keys)-1)]
            ps.append(t.replace('$TESTID', _test_id))
        return ps

    def publisher_delay(self):
        return self.configs['general']['max-publisher-delay-sec']

    def thread_delay(self):
            return self.configs['general']['thread-delay-sec']

    def num_pub_threads(self):
        return self.configs['general']['num-publisher-threads']

    def num_sub_threads(self):
        return self.configs['general']['num-subscriber-threads']

    def nap_time(self, _n):
        return _n*self.configs['general']['max-publisher-delay-sec']

    def dump(self):
        print ("\n===Configs ====\n")
        pp.pprint(self.configs)
        print ("--- Topics ---")
        pp.pprint(self.topics)
        
    def keys(self):
        return self.configs['general']['keys']
