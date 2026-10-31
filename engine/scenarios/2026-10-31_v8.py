import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from halloween_engine import main
CFG = {'seed': 108, 'threat': 'cauldron', 'support': 'bubble', 'bg': 'crypt', 'skin': 'vampire', 'time': 13, 'fail': False, 'hook': 'THE BUBBLING POTION?'}
if __name__ == '__main__':
    main(CFG)
