import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from halloween_engine import main
CFG = {'seed': 107, 'threat': 'pumpkin', 'support': 'branch', 'bg': 'swamp', 'skin': 'witch', 'time': 16, 'fail': True, 'fail_left': 2.6, 'hook': 'THE SWAMP PUMPKIN?'}
if __name__ == '__main__':
    main(CFG)
