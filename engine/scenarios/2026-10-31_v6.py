import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from halloween_engine import main
CFG = {'seed': 106, 'threat': 'bats', 'support': 'rope', 'bg': 'haunted_house', 'skin': 'ghost', 'time': 15, 'fail': False, 'hook': 'THE VAMPIRE BATS?'}
if __name__ == '__main__':
    main(CFG)
