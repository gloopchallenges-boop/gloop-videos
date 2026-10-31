import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from halloween_engine import main
CFG = {'seed': 109, 'threat': 'hands', 'support': 'web', 'bg': 'graveyard', 'skin': 'pumpkin', 'time': 18, 'fail': False, 'hook': 'THE GRAVEYARD HANDS?'}
if __name__ == '__main__':
    main(CFG)
