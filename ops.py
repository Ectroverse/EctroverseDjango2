import random
import math
import numpy as np

raceb = 1.4
psychics = 3000000
rc = 159
diff = 2.4
networth = 7500000
attack = 0

def strength():
    fa = 0.4 + (1.2 / 255.0) * (np.random.randint(0, 2147483647) & 255)

    attack = fa * raceb * psychics * (1.0 + 0.005 * rc)
             
    attack /= diff

    print("attack " + str(attack))
    return(attack)


def illusions():
    eff = []
    timing = []

    eff_max_count = 0

    for i in range(10):
        attack = strength()
        illusion = 100 * (attack / networth)
        illusions = illusion * 4.5
        effect = min(50, round(illusions * (random.randint(1,20)/25)))
        time = random.randint(1,31)+32
        eff.append(effect)
        timing.append(time)
        if effect >= 50:
            eff_max_count += 1

        #print("effect " + str(effect))
        #print("time " + str(time))

    print("eff max count " + str(eff_max_count))    
    print("effect min " + str(min(eff)))
    print("effect max " + str(max(eff)))
    print("time min " + str(min(timing)))
    print("time max " + str(max(timing)))
    
def webs():
    eff = []
    timing = []

    for i in range(10):
        attack = strength()
        web = 100 * (attack / networth)
        effect = round(web * 3.5)
        time = random.randint(1,31)+24
        eff.append(effect)
        timing.append(time)
    
    print("effect min " + str(min(eff)))
    print("effect max " + str(max(eff)))
    print("time min " + str(min(timing)))
    print("time max " + str(max(timing)))
    
webs()