import math
from penguin_game import *
from MaZoR import *
from generalFunc import *
from globalsVars import *
from clone import *

def use_sum(game, useables):
    som = 0
    valid_icebergs = filter(lambda ice: useables[ice][0], game.get_my_icebergs())
    for ice in valid_icebergs:
        som += useables[ice][1]
    return som

def closest_to_ice(game, ice): 
    """returns a sorted list (by distance to ice) of  all icebergs""" 
    bergs = filter(lambda berg: berg != ice, game.get_all_icebergs())
    bergs = sorted(bergs, key = lambda x: x.get_turns_till_arrival(ice))
    return bergs
    
def siege_onw_to_ice(game, ice):
    
    groups = game.get_enemy_penguin_groups() if ice.owner == game.get_myself() else game.get_my_penguin_groups()
    sgroups = filter(lambda x: x.is_siege_group == True and x.destination == ice, groups)
    if sgroups == [] or sgroups == None:
      return False
    return True


def daddy_is_home(game, useables, ice_accel, pre_steal, our, their, owning, under_s, s_tta):
    # if pre steal is equal to 0 we havent tried to steal icebergs yet, if its equal to 1 we already have. 
    # if its 0 we only check if we need to defend our cap or if we can successfully take the enemy cap 
    # target selection and target sorting 
    if pre_steal == 0:
        targets = game.get_my_icepital_icebergs() + game.get_enemy_icepital_icebergs()
    else:
        tier = []
        if game.get_cloneberg():
            tier = clone_level(game)
            tier = sorted(tier, key = lambda x: average_distance(game, x, useables))
        my_icebergs = filter(lambda x: owning[x][0] == game.get_enemy() and x not in  game.get_my_icepital_icebergs(), game.get_my_icebergs())
        my_icebergs = sorted(my_icebergs, key = lambda x: abs(owning[x][1]))
        
        enemy_icebergs = filter(lambda x: owning[x][0] != game.get_myself() and x not in  game.get_enemy_icepital_icebergs(), game.get_enemy_icebergs())
        enemy_icebergs = sorted(enemy_icebergs, key = lambda x: abs(owning[x][3]))
        
        close = closest_to_ice(game, capital)
        ne = filter(lambda x: owning[x][0] != game.get_myself(), game.get_neutral_icebergs())
        ne = sorted(ne, key = lambda x: abs(owning[x][3] +average_distance(game, x, useables) if owning[x]!= None else x.penguin_amount+average_distance(game, x, useables)))
        targets = my_icebergs + enemy_icebergs + ne
      #  print len(game.get_my_icebergs())
      #  print len(game.get_enemy_icebergs())
        if len(our) == len(their):
            if game.get_cloneberg():
                close = sorted(close, key = lambda x: x.get_turns_till_arrival(capital))
                close = filter(lambda x: x.get_turns_till_arrival(capital) == close[0].get_turns_till_arrival(capital), close)
                close = sorted(close, key = lambda x: x.get_turns_till_arrival(game.get_cloneberg()))
            if close[0] in our:
                close = ne
                targets =  my_icebergs + enemy_icebergs + ne
            else:
                close = [close[0]]
                targets =  my_icebergs + close + enemy_icebergs
    max_tta = 0
    for target in targets:
        if not target:
            continue
        if target.owner != game.get_myself():
            if max_accel_take(game, capital, capital.penguin_amount)[2] > 0:
                continue
            if target in our:
                continue
            if target.owner == game.get_neutral() and len(our)-len(their) != 0 and owning[target][0] == None:
                continue
            
            attackers = sorted(filter(lambda ice: useables[ice][0] and ice.already_acted == False and (who_takes(game, ice, ice.penguin_amount)[0] == None or who_takes(game, ice, ice.penguin_amount)[0].owner != game.get_enemy()), game.get_my_icebergs()), key = lambda x: distance(game, x, target))
            accel_tups = [] #append accel_tup tups
            som = 0
            max_turns = 0
            siege_amounts = 0
            for ice in attackers:
                if siege_onw_to_ice(game, ice) == True and target.owner == game.get_neutral():
                    continue
                accel_tup = best_accel(game, ice, target, useables, 999999, 0, -999999)
                if accel_tup != []:
                    accel_tups.append(accel_tup)
                    siege_amounts += my_siege_amount(game, accel_tup[0])
                    if accel_tup[4] > max_turns:
                        max_turns = accel_tup[4]
            ppt = target.penguins_per_turn
            if target.owner == game.get_neutral():
                ppt = 0
            nukers = []
            accel_tups = sorted(accel_tups, key = lambda x: min(useables[x[0]][1], x[0].penguin_amount), reverse = True)
            tta = 0
            t_groups = []
            enough_pengs = False
            for accel_tup in accel_tups:
                use = min(accel_tup[0].penguin_amount, useables[accel_tup[0]][1])
                siege = my_siege_amount(game, accel_tup[0])
                if siege >= use:
                    continue
                
                amount = use - siege
                for j in range(accel_tup[2]):
                    amount = int(math.floor(amount/game.acceleration_cost))
                    
                tta = accel_tup[4]
                if target.owner == game.get_neutral() and owning[target][0] != None:
                    if tta - owning[target][2].turns_till_arrival <= 1:
                        continue
                    
                nukers.append(accel_tup)
                if tta > max_tta:
                    max_tta = tta
                t_groups.append((accel_tup[4], amount, None, game.get_myself()))
                t_takes = last_takes(game, target, t_groups)
                many = abs(t_takes[1]) - 1
                if t_takes[0] == game.get_myself():
                    enough_pengs = True
                    break
            if enough_pengs == False:
                continue
            if nukers == []:
                continue
            
            tta = 0
            s_turns = s_tta
            attacking = 0
            time_line = 0
            ppt = target.penguins_per_turn
            if target.owner == game.get_neutral():
                ppt = 0
                
            sieged = False
            overkill = many
            cap = 999999
            max_turns = 0
            for nuker in nukers:
                if attacking >= cap:
                    break
                if nuker[4] > max_turns:
                    max_turns = nuker[4]
                    
                cap = abs(owning[target][3]) + ppt * max_turns + 1
                if target.owner == game.get_neutral():
                    if owning[target][2] != None and max_turns > owning[target][2].turns_till_arrival:
                        ppt = 1
                        cap = abs(owning[target][3]) + ppt * (max_turns - owning[target][2].turns_till_arrival) + 1 
                    else:
                        cap = abs(owning[target][3]) + 1
                        
                siege = my_siege_amount(game, nuker[0])
                send = cap - attacking 
                for j in range(nuker[2]):
                    send = int(math.ceil(send*game.acceleration_cost))
                    
                send += siege
                use = min(useables[nuker[0]][1], nuker[0].penguin_amount)
                temp = min(use, send)
                nuker[0].send_penguins(target, min(use, send))
                if max_tta < s_turns:
                    sieged = True
                    
                temp -= siege    
                for t in range(nuker[2]):
                    temp = int(math.floor(temp/game.acceleration_cost))
                    
                attacking += temp 
                if nuker[2] > 0:
                    ice_accel.append((nuker[0], nuker[2], target))
                if attacking >= cap:
                    break
        else:
            if target.owner == game.get_neutral():
                continue
                    
            fatal_g = None
            target_amount = owning[target]
            if not target_amount[0]:
                continue
            else:
                # Defensive mode.
                c_danger = -999999
                fatal_amount = -1
                if target == capital:
                    c_danger = max_accel_take(game, capital, capital.penguin_amount)
                    fatal_amount = c_danger[2]
                    
                s_max_tta = s_tta
                fatal_g = target_amount[2]
                if fatal_g != None and fatal_g.owner == game.get_myself() and fatal_amount == -1:
                    continue
                
                if fatal_g == None and target not in game.get_my_icepital_icebergs() and fatal_amount == -1:
                    continue
                
                fatal_s = None
                target_amount = abs(target_amount[3])
                if fatal_amount != -1:
                    target_amount = abs(fatal_amount) + s_sum_onw(game, target)
                if target.owner == game.get_myself() and fatal_amount == -1:
                    if owning[target][0] != game.get_enemy() and game.get_my_icepital_icebergs() and fatal_amount == -1:
                        continue
                if fatal_g != None:
                    how_fast = fatal_g.turns_till_arrival
                    
                if fatal_amount != -1:
                    how_fast = c_danger[1]
                target_amount = abs(target_amount) + s_sum_onw(game, target)
                if fatal_g == None and fatal_amount == -1:
                    continue
                
                pengs = use_sum(game, useables)
                defenders = sorted(
                    filter(lambda ice: useables[ice][0] and ice.already_acted == False, game.get_my_icebergs())
                    ,key = lambda x: distance(game, x, target))
                
                accel_tups = [] #append accel_tup tups
                som = 0
                max_turns = 0
                siege_amounts = 0
                for ice in defenders:
                    accel_tup = best_accel(game, ice, target, useables, how_fast, 0, -999999)
                    if accel_tup != []:
                        accel_tups.append(accel_tup)
                        siege_amounts += my_siege_amount(game, accel_tup[0])
                        if accel_tup[4] > max_turns:
                            max_turns = accel_tup[4]
                            
                tta = 0
                nukers = []
                defending = 0
                min_turns = 999999
                siege_turns = -999999
                non_nukers = accel_tups
                accel_tups = sorted(accel_tups, key = lambda x: x[4])
                siege_mount = my_siege_amount(game, target)
                if siege_mount > 0:
                    siege_turns = game.siege_max_turns - target.siege_turns
                
                prev_target_amount = target_amount
                starget = siege_mount + target_amount
                for accel_tup in accel_tups:
                    if defending >= target_amount:
                        break
                    if accel_tup[0] == target:
                        non_nukers.remove(accel_tup)
                        continue
                    use = min(useables[accel_tup[0]][1], accel_tup[0].penguin_amount)
                    siege = my_siege_amount(game, accel_tup[0])
                    if  siege >= use:
                        non_nukers.remove(accel_tup)
                        continue
                    amount = use
                    for j in range(accel_tup[2]):
                        amount = int(math.floor(amount/game.acceleration_cost))
                    prev = defending
                    ppt = target.penguins_per_turn
                    if accel_tup[4] <= how_fast:
                        defending += amount - siege
                    else:
                        defending += amount - siege - ppt * accel_tup[4]
                    if prev < defending:
                        tta = accel_tup[4]
                        if tta <= siege_turns:
                            target_amount = starget
                        nukers.append(accel_tup)
                        non_nukers.remove(accel_tup)
                        if accel_tup[4] < min_turns:
                            min_turns = accel_tup[4]
                    else:
                        defending = prev
                        
                capital = game.get_my_icepital_icebergs()                 
                if defending < target_amount and fatal_amount == -1:
                    continue
                if defending < target_amount:
                    if capital == None:
                        continue
                    elif capital[0] != target:
                        continue
                if nukers == []:
                    if capital == None:
                        continue
                    elif capital[0] != target:
                        continue
                if capital != None and capital[0] == target:
                    nukers = filter(lambda x: my_siege_amount(game, x) < x.penguin_amount and x!=target, defenders)
                    for nuker in nukers:
                        best_speed = best_accel(game, nuker, target, useables, how_fast, 1, -999999)
                        if best_speed != []:
                            best_speed = best_speed[2]
                        else:
                            best_speed = 0
                            if fatal_amount != -1:
                                continue
                        nuker.send_penguins(target, nuker.penguin_amount)
                        #print "BEST SPEED: ", best_speed
                        if best_speed>0:
                            ice_accel.append((nuker, best_speed, target))
                    nukers = []
                if nukers == []:
                    continue
                defending = 0
                for nuker in nukers:
                    if nuker[4] > siege_turns:
                        target_amount = prev_target_amount
                    if defending >= target_amount:
                        continue
                    use = min(useables[nuker[0]][1], nuker[0].penguin_amount)
                    siege = my_siege_amount(game, nuker[0])
                    send = target_amount - defending
                    tomp = send
                    for m in range(nuker[2]):
                        send = int(math.ceil(send * game.acceleration_cost))
                    send += siege
                    temp =  min(use, send)
                    nuker[0].send_penguins(target, min(use, send))
                    for t in range(nuker[2]):
                        temp = int(math.floor(temp/game.acceleration_cost))
                    defending += temp
                    if nuker[2]>0:
                        ice_accel.append((nuker[0], nuker[2], target))
                    if defending >= target_amount:
                        continue
    return 


def last_takes(game, ice, t_groups):
    clones = []
    if game.get_cloneberg():
        clones = filter(lambda g: g.source == ice and g.destination == game.get_cloneberg() and g.is_siege_group == False, game.get_all_penguin_groups())
        if ice == game.get_cloneberg():
            return (None, 0, None, 0, 0)
        
    peng_groups = groups_on_ice(game, ice, 2)
    if not peng_groups and clones == [] and t_groups == []:
        if ice.owner == game.get_neutral():
            return (None, ice.penguin_amount, None, ice.penguin_amount, 0)
        else:
            return (ice.owner, ice.penguin_amount, None, ice.penguin_amount, 0)
        
    peng_groups = sorted([g for g in game.get_all_penguin_groups() if g.destination == ice and g.is_siege_group == False], key = lambda g: g.turns_till_arrival)
    if not peng_groups and clones == [] and t_groups == []:
        if ice.owner == game.get_neutral():
            return (None, ice.penguin_amount, None, ice.penguin_amount, 0)
        else:
            return (ice.owner, ice.penguin_amount, None, ice.penguin_amount, 0)
    
    ice_pengs = ice.penguin_amount
    last_peng = None
    left = 0
    prev = left
    count = 0
    has = None
    tta = 0
    ppt = 1
    peng_tuples = []
    if game.get_cloneberg():
        for c in clones:
            speed = c.current_speed
            if speed == 1:
                speed = 0
            elif speed == 2:
                speed = 1
            elif speed == 4:
                speed = 2 
            elif speed == 8:
                speed = 3
            c_turns = c.turns_till_arrival + 1 + distance(game, game.get_cloneberg(), c.source)//(game.acceleration_factor)**speed
            c_amount = int(c.penguin_amount * game.cloneberg_multi_factor)
            c_tup = (c_turns, c_amount, c, c.owner)
            peng_tuples.append(c_tup)
               
    for peng in peng_groups:
        p_tup = (peng.turns_till_arrival, peng.penguin_amount, peng, peng.owner)
        peng_tuples.append(p_tup)
        
    for t in t_groups:
        peng_tuples.append(t)
        
    peng_tuples = sorted(peng_tuples, key = lambda g: g[0])
    if ice.owner in {game.get_myself(), game.get_enemy()}:
        ppt = ice.level
        left = ice.penguin_amount
        has = ice.owner
        if ice.owner == game.get_enemy():
            left = left* (-1)
            has = game.get_enemy()
        prev_left = left

    elif peng_tuples:
        for peng in peng_tuples:
            if ice_pengs >= 0:
                ice_pengs -= peng[1]
                left = ice_pengs
                last_peng = peng[2]
                tta += peng[0] - tta
                count += 1
                if ice_pengs < 0:
                    if peng[3] == game.get_enemy():
                        has = game.get_enemy()
                        left = ice_pengs
                    else:
                        has = game.get_myself()
                        left =- ice_pengs
        peng_tuples = peng_tuples[count:len(peng_tuples)]
        prev_left = left
        ppt = 1
        
    if not peng_tuples:
        return (has, left,last_peng, left, tta)
    
    for peng in peng_tuples:
        if has == game.get_enemy():
            left -= (peng[0] - tta) * ppt
        else:
            left += (peng[0] - tta) * ppt
            
        if peng[3] == game.get_myself():
            left += peng[1]
        else: 
            left -= peng[1]
            
        if left < 0:
            if prev_left > 0:
                prev_left = left
                last_peng = peng[2]
                has = game.get_enemy()
            if prev_left == 0 and peng[3] != has:
                prev_left = left
                last_peng = peng[2]
                has = game.get_enemy()
        elif left > 0: 
            if prev_left < 0:
                prev_left = left
                last_peng = peng[2]
                has = game.get_myself()
            if prev_left == 0 and peng[3] != has:
                prev_left = left
                last_peng = peng[2]
                has = game.get_myself()
        tta += peng[0] - tta
        
    return (has, prev_left,last_peng, left, tta)
    
def steal(game, useables, ice_accel, owning):
    # The purpose of this function it to identify future enemy icebergs and steal them. 
    # usually its cheaper to steal an iceberg than it is to claim an untouched neutral iceberg
    # stealing a neutral iceberg is also valuable because we gain another iceberg and the enemy loses one of the icebergs that they were going to claim in the future
    # its harder to defend a neutral iceberg since it doesnt create any penguins while its owner is neutral
    capital = game.get_my_icepital_icebergs()[0]
    steals = {n: groups_on_ice(game, n, 2) for n in game.get_neutral_icebergs()}
    steals = {n: steals[n] for n in steals.keys() if steals[n] != []}
    for n in steals:
        last_state = owning[n]
        fatal_g = last_state[2]
        if not last_state[0]:
            continue
        if fatal_g == None:
            continue
        if last_state[0] != game.get_enemy(): 
            continue 
        took = False
        n_ppt = 0 if n in game.get_neutral_icebergs() else n.penguins_per_turn 
        who_steal = sorted(game.get_my_icebergs(), key = lambda ice: ice.get_turns_till_arrival(n))
        for ice in who_steal:
            use = min(useables[ice][1], ice.penguin_amount)
            state, i_tta = useables[ice], ice.get_turns_till_arrival(n)
            if not state[0] or i_tta <= fatal_g.turns_till_arrival:
                continue
            if not last_state[0] or last_state[0] == game.get_myself():
                return None

            c_danger = False
            pre_steal_state = abs(last_state[3]) + (i_tta - fatal_g.turns_till_arrival)
            amount = pre_steal_state + 1 + my_siege_amount(game, ice)
            close = closest_to_ice(game, capital)
            close = sorted(close, key = lambda x: x.get_turns_till_arrival(capital))
            close = filter(lambda x: x.get_turns_till_arrival(capital) == close[0].get_turns_till_arrival(capital), close)

            if ice == capital:
                for c in close:
                    if c.owner == game.get_enemy():
                        c_danger = True
                        break
                    c_danger = False
                    
            if amount <= use and not ice.already_acted and amount <= n.penguin_amount + 1:
                siege_sum = sum([g.penguin_amount for g in game.get_enemy_penguin_groups() if g.is_siege_group]) * game.go_through_siege_cost - my_siege_amount(game, ice)
                if siege_onw_to_ice(game, ice) and siege_sum + amount > use and c_danger == False: 
                    amount = min(use,  amount + siege_sum + amount - use)
                ice.send_penguins(n, amount)
                took = True
                break
            else:
                took = send_accelerated_group(game, ice, n, useables, ice_accel, owning, c_danger)
                if took:
                    break
                
def send_accelerated_group(game, ice, n, useables, ice_accel,owning, c_danger):
    took = False
    state, i_tta = useables[ice], ice.get_turns_till_arrival(n)
    fatal_g = owning[n][2]
    use = min(useables[ice][1], ice.penguin_amount)
    for i in range(1, 4):
        last_state = owning[n]
        turns = distance(game, ice, n)
        tt_accel = int(math.ceil(1 + (turns - i+1) / (game.acceleration_factor ** i) + i-1))
        if fatal_g.turns_till_arrival > tt_accel:
            break
        pre_steal_state = abs(last_state[3]) + tt_accel - fatal_g.turns_till_arrival + 1
        amount = pre_steal_state + 1
        for l in range(0, i):
            amount = int(math.ceil(amount * game.acceleration_cost))
        if amount + my_siege_amount(game,ice) <= use and not ice.already_acted and fatal_g.turns_till_arrival - tt_accel < 0:
            accel_brg =  int(amount) + my_siege_amount(game,ice)
            mount=accel_brg
            for l in range(0, i):
                mount = int(math.floor(mount / game.acceleration_cost))
            siege_sum = sum([g.penguin_amount for g in game.get_enemy_penguin_groups() if g.is_siege_group]) * game.go_through_siege_cost - my_siege_amount(game, ice)
            if siege_onw_to_ice(game, ice) and siege_sum + accel_brg > use and c_danger == False: 
                accel_brg = min(use,  accel_brg + siege_sum + accel_brg - use)
            ice.send_penguins(n, accel_brg)
            pengs = filter(lambda peng: peng.source == ice, game.get_my_penguin_groups())
            ice_accel.append((ice, i, n)) 
            took = True
            break 
    return took

# Functions from older versions, Before github :(

# --------------------- SET TARGETS ---------------------
def set_targets(game, useables) -> list:
    """A dictionary contains average distance for every icberg the ENEMY own"""
    apt = {ice: average_distance(game, ice, useables) for ice in set(game.get_enemy_icebergs())}
    return sorted(apt.keys() ,key = lambda x: apt[x])
    
# ----------------------- FINAL STATE -------------------------

# RETURNS: the number of penguins when x sends to target.
def final_state(game, tta, target):
    return target.penguin_amount + tta * target.penguins_per_turn if target not in game.get_neutral_icebergs() else target.penguin_amount

# --------------------- INITIALIZE ATTACK ---------------------
def initialize_attack(game, units, useables):
    global ban_capital_p_use
    # check acceleration on capital
    
    targets_available = set_targets(game, useables)
    if not targets_available:
        return None
    #target = targets_available[0]
    
    if game.get_enemy_icebergs() and len(game.get_enemy_icebergs())>1 and game.get_neutral_icebergs() and len(game.get_neutral_icebergs()):
        enemy_bergs=sorted([g for g in game.get_enemy_icebergs() if g != game.get_enemy_icepital_icebergs()[0]], key = lambda g: average(game,g))
        max_distance=average(game,enemy_bergs[len(enemy_bergs)-1])
        targets_available=filter(lambda ice: max_distance >average(game,ice), targets_available)
    if not targets_available:
        return None
    
    for target in targets_available:
        
        
        # CHECK FOR EXISTING GROUPS
        active_attack = map(lambda g: (g, g.turns_till_arrival, g.penguin_amount), groups_on_ice(game, target, 1))
        if active_attack:
            a_res, captured = target.penguin_amount, False
            for g_stats in active_attack:
                if a_res < 0:
                    captured = True
                    break
                a_res = a_res + target.penguins_per_turn * g_stats[1] - g_stats[2]
            if not captured:
                continue
            
        # CHECK FOR GROUPS THAT WILL CAPTURE WITH ACCELERATION.
        
        accel_groups = filter(lambda g: g.penguin_amount < final_state(game, g.turns_till_arrival, target), groups_on_ice(game, target, 1))
        print "needs accelerate", accel_groups
        for g in accel_groups:
            #if g.penguin_amount / game.acceleration_cost > final_state(game, g.turns_till_arrival/2, target):
              #  g.accelerate()
        
        #print "STATES:", useables
        att =  sorted(filter(lambda x: x not in units and x.already_acted == False and useables[x][0] and useables[x][1] > 0, useables.keys()), key = lambda x: x.get_turns_till_arrival(target))
        print "ATTACKERS", att
        att_export = {i: 0 for i in att}
        barrage, valid_att, before_group = 0, [], False
        for ice in att:
            
            final_state_per_target = final_state(game, ice.get_turns_till_arrival(target), target)
            #print ice, 'On: ', target, "Comparing: ", useables[ice][1], final_state_per_target
            #if useables[ice][1] < final_state_per_target:
            barrage += useables[ice][1]
            att_export[ice] = useables[ice][1]
            valid_att.append(ice)
            
            if barrage > final_state_per_target:
                #print "Attackers:", valid_att
                for att in valid_att:
                    last_takes_on_t = last_takes(game, target)
                    
                    if last_takes_on_t[0] == game.get_myself():
                        break
                    
                    final_state_per_target = last_takes_on_t[1] if last_takes_on_t[0] == game.get_enemy() else target.penguin_amount
                    single_brg = att_export[att] if att_export[att] < final_state_per_target else final_state_per_target + 1
                    enemy_reinforcement = sorted(groups_on_ice(game, target, 0), key = lambda x: x.turns_till_arrival)  # 0 is enemy groups
                    siege_g = my_siege_amount(game, att)
                    
                    single_brg += siege_g
                    
                       #single_berg+=siege_g.penguin_amount
                    if not enemy_reinforcement and single_brg < useables[att][1]:
                       print "SINGLEBRG: ", single_brg
                       valid_after = useables[ice]
                       if valid_after[0] and valid_after[1] > single_brg and single_brg > 0:
                            att.send_penguins(target, single_brg)
                            continue
                    
                    for g in enemy_reinforcement:
                        t_ppt = target.penguins_per_turn if target not in game.get_neutral_icebergs() else 0
                        att_tta = att.get_turns_till_arrival(target) # attackers turns till arrival
                        g_tta = g.turns_till_arrival # group turns till arrival
                        if g_tta > att_tta:
                            single_brg += (g_tta - att_tta) * t_ppt - g.penguin_amount
                            if single_brg <= 0: break
                            #print "group: ", g, "TTA:", g_tta, "attBERG: ", att_tta, "so singleBRG is: ", single_brg
                            if valid_for_action(game, target, att.penguin_amount - single_brg)[0]:
                                #single_brg = single_brg + 1 if single_brg == target.penguin_amount else single_brg
                                #print att,"SENDS", single_brg, "TO", target
                                valid_after = useables[ice]
                                if valid_after[0]:
                                    print "SINGLE1: ", single_brg
                                    att.send_penguins(target, single_brg)
                                break
                            
                            # the group will get before.
                        ice_amount_after_reinforcement = target.penguin_amount + g.penguin_amount + t_ppt * (att_tta)
                        if ice_amount_after_reinforcement < single_brg and valid_for_action(game, att, single_brg - ice_amount_after_reinforcement)[0]:
                           # print att,"SENDS", single_brg, "TO", target
                            #single_brg = single_brg + 1 if single_brg == target.penguin_amount else single_brg
                            valid_after = useables[ice]
                            if valid_after[0]:
                                print "SINGLE2: ", single_brg
                                att.send_penguins(target, single_brg)
                            break
                #map(lambda x: x.send_penguins(target, useables[x][1]) if x.can_send_penguins(target, useables[x][1]) and valid_for_action(game, x, x.penguin_amount - useables[x][1]) else None, valid_att)
                break


# Older version.


def big_berg_params(game, target, useables):
    som = 0
    valid_icebergs = filter(lambda ice: useables[ice][0], game.get_my_icebergs())
    siege_mount = 0
    for ice in valid_icebergs:
        som += useables[ice][1]
        siege_mount += my_siege_amount(game, ice)
    return (sum(map(lambda x: x.get_turns_till_arrival(target), valid_icebergs)) / len(game.get_my_icebergs()), som, valid_icebergs, siege_mount)



def nuke(game, useables, ice_accel):    
    tier = []
    if game.get_cloneberg():
        tier = clone_level(game)

    enemy_icebergs =filter(lambda x: x not in tier, game.get_enemy_icebergs())
    tier = filter(lambda x: last_takes(game, x)[0] != game.get_myself(), tier)
    tier = filter(lambda x: x.owner != game.get_myself(), tier)
    ne = filter(lambda x: last_takes(game, x)[0] != game.get_myself(), game.get_neutral_icebergs())
    pot_targets = game.get_enemy_icepital_icebergs() + tier + sorted(enemy_icebergs[1: len(enemy_icebergs)], key = lambda x: x.penguin_amount) + sorted(ne, key = lambda x: x.penguin_amount)
    pot_nukers = [i for i in game.get_my_icebergs() if useables[i][0]]
    for nuker in pot_nukers:
        for t in pot_targets:

            nuke_state = min_accel(game, nuker, t, useables)

            if not nuke_state or nuker.already_acted:
                continue
            print 'FOR: ', nuker, nuke_state
            print "NUKER VALID ", useables[nuker][1]
            nuker.send_penguins(t, int(math.ceil(nuke_state[3])))
            ice_accel.append(nuke_state[0:3])
            print ice_accel

 

def get_most_dangerous_island(game):
    attacking_islands = game.get_enemy_penguin_groups()
    if not attacking_islands: return None
    sourced_threats_amount = {g.source: 0 for g in attacking_islands}
    
    for attack in attacking_islands:
        source = attack.source
        sourced_threats_amount[source] += attack.penguin_amount
    values = sourced_threats_amount.values()
    max_threat = max(values)
    critical_island = [k for k, v in sourced_threats_amount.items() if v == max_threat]

    if critical_island and not critical_island[0].is_icepital and critical_island[0] not in game.get_my_icebergs():
        return critical_island[0]
    return None



def last_takes_enemy_neutral(game):
    if not game.get_neutral_icebergs():
        return None
    neutral= (g for g in game.get_neutral_icebergs() if last_takes(game,g)[0]==game.get_enemy())
    if not neutral:
        return None
    return neutral
   
    

def fatal_siege(game):
    #CURRENTLY DISABLED BECAUSE NOT SURE IF WORKING CORRECTLY
    return (False, 0)
    capital = game.get_my_icepital_icebergs()
    if capital == []:
        return (False, 0)
    capital = capital[0]
    if siege_onw_to_ice(game, capital) == False:
        return (False, 0)
    sgs = filter(lambda x: x.is_siege_group == True and x.destination == capital, game.get_enemy_penguin_groups())
    if len(sgs) <= 1 and capital in game.get_my_under_siege_icebergs():
        return (False, 0)
    sgroups = filter(lambda g: g.is_siege_group == True and g.destination == capital and g.turns_till_arrival not in {0, 1}, game.get_enemy_penguin_groups())
    if sgroups == []:
        return (False, 0)
    if capital in game.get_my_under_siege_icebergs():
        return (False, 0)
    s_size = math.ceil(sgroups[0].penguin_amount*game.go_through_siege_cost)
    som = sum_close(game, capital)
    if som < s_size:
        return (True, s_size - som)
    return (False, 0)

  

def all_siege_onw_to_ice(game, ice):
    sgroups = filter(lambda x: x.is_siege_group == True and x.destination == ice, game.get_all_penguin_groups())
    if sgroups == [] or sgroups == None:
      return False
    return True   

def sum_close(game, ice):
    bergs = filter(lambda x: x.owner == ice.owner and x != ice, game.get_all_icebergs())
    bergs = sorted(bergs, key = lambda x: x.get_turns_till_arrival(ice))
    som = 0
    if bergs == []:
        return 0
    if len(bergs) > 2:
        bergs = [bergs[0], bergs[1]]
    som += last_takes(game, capital)[3]
    for berg in bergs:
        som += berg.penguin_amount - my_siege_amount(game, berg)
    return som
