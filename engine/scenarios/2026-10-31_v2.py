import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from halloween_engine import main
CFG = {'seed': 102, 'threat': 'cauldron', 'support': 'broom', 'bg': 'witch_hut', 'skin': 'witch', 'time': 14, 'fail': True, 'fail_left': 2.4, 'hook': "THE WITCH'S CAULDRON?"}
if __name__ == '__main__':
    main(CFG)
