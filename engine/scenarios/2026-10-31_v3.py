import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from halloween_engine import main
CFG = {'seed': 103, 'threat': 'hands', 'support': 'branch', 'bg': 'graveyard', 'skin': 'mummy', 'time': 16, 'fail': False, 'hook': 'THE SKELETON HANDS?'}
if __name__ == '__main__':
    main(CFG)
