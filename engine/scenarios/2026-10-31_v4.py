import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from halloween_engine import main
CFG = {'seed': 104, 'threat': 'ghost', 'support': 'bubble', 'bg': 'haunted_house', 'skin': 'cat', 'time': 14, 'fail': False, 'hook': 'THE HAUNTED GHOST?'}
if __name__ == '__main__':
    main(CFG)
