import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from halloween_engine import main
CFG = {'seed': 105, 'threat': 'spider', 'support': 'web', 'bg': 'crypt', 'skin': 'vampire', 'time': 17, 'fail': True, 'fail_left': 2.0, 'hook': 'THE GIANT SPIDER?'}
if __name__ == '__main__':
    main(CFG)
