import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from halloween_engine import main
CFG = {'seed': 110, 'threat': 'ghost', 'support': 'broom', 'bg': 'swamp', 'skin': 'mummy', 'time': 15, 'fail': False, 'hook': 'THE SWAMP GHOST?'}
if __name__ == '__main__':
    main(CFG)
