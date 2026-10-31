import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from halloween_engine import main
CFG = {'seed': 101, 'threat': 'pumpkin', 'support': 'rope', 'bg': 'pumpkin_patch', 'skin': 'pumpkin', 'time': 15, 'fail': False, 'hook': 'THE GIANT PUMPKIN?'}
if __name__ == '__main__':
    main(CFG)
