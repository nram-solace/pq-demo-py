
# --------------------------------------------------------------------------------
# PySolStats
#   Keep track of publish and subsribe stats  by client and by topic
#   Save stats as JSON and print them
# 
# nram - Feb 4, 2021

from collections import defaultdict 
import pprint
import time, datetime
import json


pp = pprint.PrettyPrinter()

class T:
    ''' return current timestamp '''
    def __str__(self):
        return f'{datetime.datetime.now()}'

class Stats:
    ''' keep publish and subscribe stats '''

    def __init__ (self, _verbose=0):
        self.stats = defaultdict(list)
        # init stats map
        # T - Number of messages Publish on a Topic
        # R - Number of messages received on a Topic
        # P - Number of messages Publish on a publisher
        # S - Number of messages received on a subsriber
        # G - General stats
        for s in ['T', 'K', 'R', 'P', 'S', 'G']:
            self.stats[s] = defaultdict(int)
        #pp.pprint(self.stats)

    def pub_stats (self, _p, _t, _k):
        self.stats["G"]["P"] += 1
        self.stats["T"][_t] += 1
        self.stats["K"][_k] += 1
        self.stats["P"][_p] += 1
        return [self.stats["G"]["P"], self.stats["T"][_t], self.stats["P"][_p]]
        #pp.pprint(self.stats)

    def sub_stats (self, _p, _t):
        self.stats["G"]["S"] += 1
        self.stats["R"][_t] += 1
        self.stats["S"][_p] += 1
        return [self.stats["G"]["S"], self.stats["R"][_t],  self.stats["S"][_p]]
        #pp.pprint(self.stats)

    def save (self, _file = None):
        if not self.stats :
            print ("No stats to save")
            return
        file = 'stats/stats-{}.json'.format(time.strftime("%Y%m%d%H%M%S")) if _file is None else _file 
        print (f'{T()}: Writing stats to file {file}')
        with open(file, 'w') as fh:
            json.dump(self.stats, fh)

    def read (self, _file):
        print (f'{T()}: Reading stats from file {_file}')
        with open(_file) as fh:
            self.stats = json.load(fh)
    
    def prints (self):
        l =  '-'*72
        ll = '='*72
        G = self.stats['G'] # general stats
        P = self.stats['P'] # publish client stats
        S = self.stats['S'] # subsribe client stats
        T = self.stats['T'] # publish topic stats
        K = self.stats['K'] # publish topic stats
        R = self.stats['R'] # subsribe topic stats

        if not self.is_set() :
            print ("No Stats to print")
            return 
        print ('\n{}\n{:^72}\n{}'.format(ll,'Stats',ll))
    
        # Total stats
        print ('{:<50}   {:<8}  {:<8}'.format('Total Stats', 'Publish', 'Subscribe'))
        print(l)
        print ('{:<50}   {:<8}  {:<8}'.format('Total messages', G['P'], G['S']))
        print(ll)
    
        # By client
        print ('{:<50}   {:<8}  {:<8}'.format('By Client', 'Publish', 'Subscribe'))
        print(l)
        for p in sorted(P.keys()):
            print ('{:<50} : {:<8}  {:<8}'.format(p, P[p], ''))
        print(l)
        for s in sorted(S.keys()):
            print ('{:<50} : {:<8}  {:<8}'.format(s, '', S[s]))
        print(ll)

        # By topic
        print ('{:<50}   {:<8}  {:<8}'.format('By Topic', 'Publish', 'Subscribe'))
        print(l)
        for t in sorted(T.keys()):
            print ('{:<50} : {:<8}  {:<8}'.format(t[:50], T[t], R[t] if t in R else '-'))
        print(ll)
        
        # By keys
        print ('{:<50}   {:<8}  {:<8}'.format('By Keys', 'Publish', 'Subscribe'))
        print(l)
        for k in sorted(K.keys()):
            print ('{:<50} : {:<8}  {:<8}'.format(k[:50], K[k], R[k] if t in R else '-'))
        print(ll)

    def is_set(self):
        return 'P' in self.stats['G']

    def dump (self) :
        print ("Stats")
        pp.pprint(self.stats)