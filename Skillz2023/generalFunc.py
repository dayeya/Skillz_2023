from penguin_game import *
from globalsVars import *
import math

def average_distance(game, target, useables):
    valid_icebergs = filter(lambda ice: useables[ice][0], useables.keys())
    avg_d = sum(map(lambda x: x.get_turns_till_arrival(target), valid_icebergs)) / len(useables.keys())
    return avg_d

def count_s_tta(game, s_tta, updated_s_tta, temp_s_tta, s_group_save):
    s_groups = filter(lambda g: g.is_siege_group == True, game.get_all_penguin_groups())
    under_siege_bergs = filter(lambda g: g.is_under_siege == True, game.get_all_icebergs())'
    if not s_group_save and s_groups:
        s_group_save.append(s_groups[0])
        temp_s_tta = temp_s_tta + 1

    elif s_group_save != [] and updated_s_tta == False:
        # Check if the first siege group's destination is not under siege
        # and verify that it is the first ever siege group
        if s_group_save[0].destination not in under_siege_bergs and s_group_save[0] in s_groups:
            temp_s_tta = temp_s_tta + 1
        else:
            updated_s_tta = True
            s_tta = temp_s_tta
            
    return (s_tta, updated_s_tta, temp_s_tta, s_group_save)  
            


def s_sum_onw(game, ice):
    temp_groups = filter(lambda x: x.is_siege_group == True and x.destination == ice, game.get_enemy_penguin_groups())
    s_groups = filter(lambda x: x.is_siege_group == True and x.destination == ice and x.turns_till_arrival not in {0,1}, game.get_enemy_penguin_groups())
    som = 0
    if ice not in game.get_my_under_siege_icebergs() and s_groups == [] and temp_groups != []:
        s_groups = temp_groups
    for s in s_groups:
        som += int(math.ceil(s.penguin_amount * game.go_through_siege_cost))
    return som
    
def enemy_crippled(game, ice, useables, considered_s, s_tta):
    turns = ice.get_turns_till_arrival(game.get_cloneberg()) 
    bergs = game.get_enemy_icebergs()
    use = min(useables[ice][1], ice.penguin_amount) - my_siege_amount(game, ice)
    og_use = min(useables[ice][1], ice.penguin_amount)
    min_s = int(math.floor(use/game.go_through_siege_cost))
    onw_s_sum = s_sum_onw(game, ice)
    if bergs == []:
        return []
    max_s = -999999
    open_s = []
    for berg in bergs:
        if berg not in game.get_enemy_under_siege_icebergs():
            if berg.penguin_amount > max_s:
                max_s = berg.penguin_amount
            open_s.append(berg)
            if max_s >= int(math.floor(min_s * game.cloneberg_multi_factor)):
                return []
    berg_turns = []
    safe_speed = []
    close_bergs = []
    for berg in bergs:
        if berg in game.get_enemy_under_siege_icebergs():
            close_bergs.append((berg, game.siege_max_turns - berg.siege_turns))
            berg_turns.append(game.siege_max_turns - berg.siege_turns)
    min_turn = 1
    temp_cons = considered_s
    for turn in berg_turns:       
        if turn < min_turn:
            min_turn = turn
    for i in range(4):
        if i > 0:
            use = int(math.floor(use/game.acceleration_cost))
        tt_accel = int(math.ceil(1 + (turns - i+1) / (game.acceleration_factor ** i) + i-1))
        total_turns = 1 + tt_accel + ice.get_turns_till_arrival(game.get_cloneberg())//(game.acceleration_factor ** i)
        if ice.level < 4 and ice.upgrade_cost - ice.penguin_amount <= total_turns * ice.penguins_per_turn:
            continue
        if og_use >= int(math.floor(use * game.cloneberg_multi_factor)) - onw_s_sum:
            continue
        if total_turns <= min_turn + s_tta and open_s == []:
            safe_speed.append(i)
            continue
        overpowered = False
        for berg in open_s:
            b_s = int(math.ceil((berg.penguin_amount + math.ceil(berg.penguins_per_turn * total_turns)) * game.go_through_siege_cost)) + onw_s_sum
            if og_use > int(math.floor(use * game.cloneberg_multi_factor)) - b_s:
                overpowered = True
                
        for berg in close_bergs:
            if total_turns <= berg[1]:
                continue
            b_s = int(math.ceil((berg[0].penguin_amount + math.ceil(berg[0].penguins_per_turn * total_turns)) * game.go_through_siege_cost)) + onw_s_sum
            if og_use > int(math.floor(use * game.cloneberg_multi_factor)) - b_s:
                overpowered = True
        if overpowered == False:
            safe_speed.append(i)
            continue
        continue        
    return safe_speed
      
def groups_on_ice(game, iceberg, act):
    """
    RETURNS: A list of penguin groups on a given iceberg 
             act == 0 -> enemy penguin groups
             act == 1 -> our penguin groups
             act == other -> all penguin groups
    """
    if act == 0:   groups = game.get_enemy_penguin_groups() 
    elif act == 1: groups = game.get_my_penguin_groups()
    else: groups = game.get_all_penguin_groups() 
    final_groups = filter(lambda group: group.destination == iceberg, groups)
    return final_groups

def who_takes(game, ice, amount):
    peng_groups = groups_on_ice(game, ice, 2)
    if not peng_groups:
        return (None, 0, ice.owner, 0)
    
    tta = 0
    has = ice.owner
    ice_pengs = amount
    ppt = ice.penguins_per_turn
    peng_groups = sorted(peng_groups, key = lambda peng:peng.turns_till_arrival)
    if has == game.get_neutral():
        ppt = 0
        
    for peng in peng_groups:
        ice_pengs += ppt * tta
        ice_pengs -= peng.penguin_amount
        tta = peng.turns_till_arrival
        if ice_pengs < 0:
            amount = abs(ice_pengs)
            return (peng, amount, has, tta)
        
    return (None, 0, ice.owner, 0)

def valid_for_action(game, iceberg, amount):
    '''
    RETURNS, a tuple representing the current state of icebergs.
    tuple --> (boolean, available usage of pengs (int), threat_tta (Optional), siege level (int))
    '''
    global SIEGE_TURNS
    siege_amount = 0
    worst_case = iceberg.penguin_amount
    under_siege = game.get_my_under_siege_icebergs()
    pengs_on_ice = sorted(groups_on_ice(game, iceberg, 2), key = lambda g: g.turns_till_arrival)
    siege_level = map(lambda g: g.destination == iceberg and g.is_siege_group and g.turns_till_arrival in {0, 1}, game.get_enemy_penguin_groups())
    if len(siege_level) > 0:
        siege_amount = siege_level[len(siege_level)-1] * game.go_through_siege_cost if iceberg in under_siege else 0
    
    pengs_on_ice = filter(lambda g: g.is_siege_group == False, pengs_on_ice)
    if not pengs_on_ice:
        return (True, amount, 0, siege_amount)
    
    p_amount, ice_ppt = 0, iceberg.penguins_per_turn
    tta = 0
    last_enemy_turn, last_turn = 0, 0
    total = amount
    worst_case = 99999
    #pengs_on_ice = [g for g in pengs_on_ice if not g.is_siege_group]
    
    for g in pengs_on_ice:
        #print g, "AMOUNT | TTA", g.penguin_amount, g.turns_till_arrival
        p_amount = g.penguin_amount 
        tta = g.turns_till_arrival
        
        # our group
        if g.owner == game.get_myself():
            total += p_amount
            total += ice_ppt * (tta - last_turn)
            last_turn = tta
        else:
            total -= p_amount
            total += ice_ppt * (tta - last_turn)
            last_turn = tta
        if total < worst_case:
            worst_case = total
            
        if total < 0 and g.owner == game.get_enemy():
            threat_tta = tta
            # leftover groups shall be conuted as well.
            uncounted_enemy_groups = filter(lambda g: g.owner == game.get_enemy(), pengs_on_ice)
            calc_gap = uncounted_enemy_groups.index(g)
            uncounted_enemy_groups = sorted(uncounted_enemy_groups[calc_gap + 1:], key = lambda g: g.turns_till_arrival)
            summation = sum(map(lambda z: z.penguin_amount - ice_ppt * (z.turns_till_arrival - uncounted_enemy_groups[uncounted_enemy_groups.index(z)].turns_till_arrival) if uncounted_enemy_groups.index(z) > 0 else z.penguin_amount - (ice_ppt * z.turns_till_arrival), uncounted_enemy_groups))
            
            tup = (False, abs(total) + summation, threat_tta, siege_amount) if summation > 0 else (False, abs(total), threat_tta, siege_amount)
            return tup
    
    if worst_case != 99999:        
        tup =  (True, worst_case - ice_ppt, 0, siege_amount) if amount < total else (True, worst_case - ice_ppt, 0, siege_amount)
    else:
         tup =  (True, amount, 0, siege_amount) if amount < total else (True, amount, 0, siege_amount)
    return tup

def renewed_speed(speed):
    new_speed = 0
    if speed == 1:
        new_speed = 0
    elif speed == 2: 
        new_speed = 1
    elif speed == 4: 
        new_speed = 2
    elif speed == 8:
        new_speed = 3
    return new_speed

def check_value(game, p, clone, siege_TURNS):
    
    """
    RETURNS: Boolean if G is set for BLOCKING its value.
    check its value based on the destination.
    """
    print p, "TO!!!", p.destination, "SPEED: ", p.current_speed
    
    # CHECK WITH CEILING.
    src = p.source
    dst = p.destination
    distance = 0
    speed = renewed_speed(p.current_speed)
        
    turns = 0
    if p.destination == clone:
        distance = src.get_turns_till_arrival(dst)
        turns = p.turns_till_arrival + distance / (game.acceleration_factor ** speed) + game.cloneberg_max_pause_turns
    else:
        #distance = src.get_turns_till_arrival(dst)
        turns = p.turns_till_arrival
    print "CALCULATEEEE TURNS: ", p, turns
    
    # check for siege.
    if turns >= 5: return [True, turns]
    return [False, turns]

def input_clone(game, useables, punish_clone, clone, siege_TURNS):
    if not clone:
        return None
    for ice, p_dict in punish_clone.items():

        #updating cloners
        cloners = [p for p in game.get_enemy_penguin_groups() if p.source == ice and p.destination == clone]
        cloners += [p for p in game.get_enemy_penguin_groups() if p.destination == ice and p.source == clone]
        print "CLONERS BEFORE: ", cloners 

        #LAMBDA for clone as cell[1][1] represents the TOTAL turns (To clone & to dst)
        filter_lambda = lambda element: element != None
        value_lambda = lambda p: (p, check_value(game, p, clone, siege_TURNS))
        validate_cell_lambda = lambda cell: (cell[0], cell[1][1]) if cell[1][0] else None

        cloners = map(value_lambda, cloners)
        cloners = filter(validate_cell_lambda, cloners)
        cloners = sorted(filter(filter_lambda, cloners), key=lambda p_TUPLE: p_TUPLE[1])
        if not cloners: continue

        print "CLONERS AFTER: ", cloners

        for p in cloners:
            if p[0] not in punish_clone[ice].keys():
                
                # Determine dst.
                dst = "CLONE" if p[0].destination == clone else "SOURCE"
                print "Updating: ", punish_clone[ice]
                print "Updating PUNISH: ", {p[0]: [dst, p[1]]}

                punish_clone[ice].update({p[0]: [dst, p[1]]})
    
def my_siege_amount(game, iceberg):
    
    '''
    RETURNS: The current sieges level on <iceberg>
    '''
    
    under_siege = game.get_my_under_siege_icebergs()
    if iceberg not in under_siege: return 0
    print "Under siege icebergs TYOMKINNNNNN: ", under_siege
    siege_level = [g.penguin_amount for g in game.get_enemy_penguin_groups() if g.destination == iceberg and g.is_siege_group and g.turns_till_arrival in {0, 1}]
    print "GROUPPPPPS: ", iceberg, siege_level
    if not len(siege_level) > 0:
        s_groups = filter(lambda x: x.is_siege_group == True, game.get_enemy_penguin_groups())
        print "SIEEGEGEGEGEGEGEGE"
        if not len(s_groups) > 0:
            return 0
        else:
            return int(math.ceil(s_groups[0].penguin_amount * game.go_through_siege_cost))
    print "GROUPPPPPS: ", iceberg, siege_level
    siege_amount = int(math.ceil(siege_level[len(siege_level) - 1] * game.go_through_siege_cost))
    return siege_amount
    
# --------------------- DISTANCE ---------------------
def distance(game, ice1, ice2):
    ''' RETURNS: The number of turns between 2 icebergs '''
    return ice1.get_turns_till_arrival(ice2)

# --------------------- NEAREST ---------------------
def nearest(game, from_iceberg):
    """
    RETURNS: The closest SINGLE iceberg to the given iceberg -> (from_iceberg)
    """
    
    ''' A tuple contains every iceberg we have except the given iceberg -> (from_iceberg)'''
    checking_icebergs = tuple(x for x in game.get_my_icebergs() if x != from_iceberg)
    
    ''' If we don't have any other icebergs -> Exit the function '''
    if not checking_icebergs:
        return None
        
    ''' The closest SINGLE iceberg by turns to the give iceberg -> (from_iceberg) '''
    closest_iceberg = min(checking_icebergs, key = lambda iceberg: from_iceberg.get_turns_till_arrival(iceberg))
    
    ''' Returns the closest single iceberg '''
    return closest_iceberg 


def nearest_TUPLE(game, from_iceberg):
    """
    RETURNS: A sorted TUPLE of our icebergs, sorted by least turns to most turns from the given iceberg -> (from_iceberg)
             (the list does not contain the given iceberg (from_iceberg))
    """
    
    ''' A tuple contains every iceberg we have except the given iceberg -> (from_iceberg)'''
    checking_icebergs = tuple(x for x in game.get_my_icebergs() if x != from_iceberg)
    
    ''' If we don't have any other icebergs -> Exit the function '''
    if not checking_icebergs:
        return None
        
    ''' A sorted tuple by turns (from least to most) of our icebergs'''
    closest_iceberg = sorted(checking_icebergs, key = lambda iceberg: from_iceberg.get_turns_till_arrival(iceberg))
    
    ''' Returns the sorted tuple '''
    return closest_iceberg

def d_day(game, accel_groups):

    c_danger = max_accel_take(game, game.get_my_icepital_icebergs()[0], game.get_my_icepital_icebergs()[0].penguin_amount)
    print "MAX ACCEL TAKE ", c_danger
    if c_danger[2] != -1:
        pengs = filter(lambda g: g.is_siege_group == False and g.destination == game.get_enemy_icepital_icebergs()[0] and g not in accel_groups.keys() and g.current_speed < 3, game.get_my_penguin_groups())
        for peng in pengs:
            peng.accelerate()
        return True
    return False

def amount_when(game, ice, tta):
    tta = tta + 1
    time_line = 0
    groups = send_before_all(game, ice, tta)
    groups = sorted(groups, key = lambda x: x.turns_till_arrival)
    som = 0
    ppt = ice.penguins_per_turn
    if groups == []:
        return 0
    for g in groups:
        som += ppt * time_line
        amount = g.penguin_amount
        if g.owner == game.get_enemy():
            amount = amount * -1
        som = som + amount
        time_line = g.turns_till_arrival
    return som  
    
def max_accel_take(game, ice, amount):
    pengs = filter(lambda x: x.destination == ice and x.is_siege_group == False, game.get_enemy_penguin_groups())
    pengs = sorted(pengs, key = lambda g: g.turns_till_arrival)
    som = 0
    fatal_amount = -1
    fatal_tta = 0
    t_amount = ice.penguin_amount
    for peng in pengs:
        p_amount = peng.penguin_amount
        tta = 0
        tt_accel = peng.turns_till_arrival
        speed = peng.current_speed
        if speed == 1:
            speed = 0
        elif speed == 2:
            speed = 1 
        elif speed == 4:
            speed = 2 
        elif speed == 8:
            speed = 3
        turns = peng.turns_till_arrival
        for i in range(speed + 1, 4):
            temp = int(math.floor(p_amount/game.acceleration_cost))
            tomp = int(math.floor(1 + (turns - i-speed+1) / (game.acceleration_factor ** i) + i+speed-1)) - 1
            if temp > 0:
                p_amount = temp
                tt_accel = tomp
        som_com = amount_when(game, ice, tt_accel)
        #print "SOM COM ", som_com
        temp_som = som - ice.penguins_per_turn * tt_accel + p_amount
        #print "TEMP SOm ", temp_som
        if temp_som > som:
            som = temp_som
        if fatal_tta == 0 and som > amount + som_com:
            fatal_tta = tt_accel
            fatal_amount = abs(som - (amount + som_com))
    return (som, fatal_tta, fatal_amount)            

def execute_acceleration(game, useables, accel_groups):
    
    
    print "ACCEL GROUPS: ", accel_groups
    
    if not accel_groups:
        return accel_groups
        
    for peng in accel_groups.keys():
        if not peng.already_acted:
            peng.accelerate()
            accel_groups[peng] -= 1
        
    accel_groups = {peng:accel_groups[peng] for peng in accel_groups.keys() if accel_groups[peng] > 0}
    return accel_groups
    
def send_before_all(game, ice, tta):
    groups = filter(lambda x: x.turns_till_arrival < tta and x.destination == ice and x.is_siege_group == False, game.get_all_penguin_groups())
    return groups    
    
def send_before(game, ice, tta):
    groups = filter(lambda x: x.turns_till_arrival < tta and x.destination == ice and x.is_siege_group == False, game.get_my_penguin_groups())
    return groups
    
def after_send_before(game, min_tta, ice, tta):
    groups = filter(lambda x: x.turns_till_arrival > min_tta and turns_till_arrival < tta and x.destination == ice and x.is_siege_group == False, game.get_my_penguin_groups())
    return groups
    
def steal_countered(game, x):
    groups = filter(lambda g: g.destination == x and g.is_siege_group == False and g.turns_till_arrival < who_takes(game, x, x.penguin_amount)[3], game.get_my_penguin_groups())
    groups = filter(lambda g: who_takes(game, x, x.penguin_amount)[0] != None and who_takes(game, x, x.penguin_amount)[0].owner == game.get_enemy(), groups)
    if groups !=[]:
        return True
    else:
        return False
        
def stolen(game, accel_groups, owning):
    bergs = game.get_neutral_icebergs()
    if bergs == []:
        print "I ADORE OZATERO, BEST GROUP NO CAP "
        return accel_groups
    bergs = filter(lambda x: owning[x][0] == game.get_enemy() and (who_takes(game, x, x.penguin_amount)[0].owner == game.get_myself() or steal_countered(game, x) == True), bergs)
    berg_remove = []
    for x in bergs:
        ''' who_takes return (peng, amount, has, tta) '''
        ''' last_takes return (has, prev_left, last_peng, left, tta) '''
        temp = who_takes(game, x, x.penguin_amount)
        som = 0
        for g in send_before(game, x, owning[x][2].turns_till_arrival):
            mount = g.penguin_amount
            print "G CURRENT SPEED ", g.current_speed
            speed = g.current_speed
            if speed == 1:
                speed = 0
            elif speed == 2:
                speed = 1 
            elif speed == 4:
                speed = 2
            elif speed == 8:
                speed = 3
            for j in range(speed, 3):
                print "SPEED ", speed
                if int(math.floor(mount/game.acceleration_cost)) > 0:
                    mount = int(math.floor(mount/game.acceleration_cost))
            som += mount
        print "SOM ", som
        print "X PENG AMOUNT ", x.penguin_amount
        print "OWNING [x][1] ", owning[x][1]
        if som >= x.penguin_amount:
            berg_remove.append(x)
            continue
        delta = x.penguin_amount - som
        amount = abs(owning[x][1])
        if amount <= delta and who_takes(game, x, x.penguin_amount)[0].owner == game.get_myself():
            berg_remove.append(x)
            continue
    for x in berg_remove:
        bergs.remove(x)

    if bergs == []:
        print "I LOVE OZATERO "
        return accel_groups
    groups = filter(lambda g: g.destination in bergs and g.turns_till_arrival <= who_takes(game, g.destination, g.destination.penguin_amount)[3], game.get_my_penguin_groups())
    for g in groups:
        speed = g.current_speed    
        if speed == 4:
            speed = 2
        elif speed == 2:
            speed = 1
        if g in accel_groups.keys():
            accel_groups[g] =  3 - speed
        else:
            accel_groups.update({g: 3 - speed})
    print "ACCEL_GROUPS:  ", accel_groups
    return accel_groups
    
def input_berg(game, useables, ice_accel, accel_groups):
    
    '''
    Check the ice_accel is empty, finds the closest g in ratio with ice and appends to accel_groups ()
    '''
    
    print "ICE ACCEL: ", ice_accel
    
    if not ice_accel:
        return accel_groups
    for ice in ice_accel: # add accel in between groups, tta > fatal_tta
        pengs = filter(lambda peng: peng.source == ice[0] and peng.is_siege_group==False and peng.destination == ice[2] and distance(game, ice[0], ice[2]) - peng.turns_till_arrival == 1, game.get_my_penguin_groups())
        print "PENGERS ", pengs
        if not pengs:
            continue
        pengs = sorted(pengs, key = lambda g: distance(game, ice[0], ice[2]) - g.turns_till_arrival, reverse = True)
        print " PING PONGERS ", pengs
        if distance(game, ice[0], ice[2]) - pengs[0].turns_till_arrival == 1:
            accel_groups.update({pengs[0]: ice[1]})
    ice_accel = []
    print "ICE_ACCEL:  ", ice_accel
    return accel_groups

def best_accel(game, k, n, useables, how_fast, capital_danger, how_slow):
    accel_tup = []
    best = 99999
    k_amount = min(useables[k][1], k.penguin_amount)
    capital = game.get_my_icepital_icebergs()
    if capital_danger == 1 and capital != None and capital[0] == n:
        k_amount = k.penguin_amount
    for i in range(4):
        k_amount = int(math.floor(k_amount/game.acceleration_cost))
        #print "N AMOUNT: ", n.penguin_amount
        #print "NPPT: ", n.penguins_per_turn
        #print 'iteration of speed: ', i
        turns = distance(game, k, n)
        nuke_turns = int(math.ceil((turns - i+1) / (game.acceleration_factor ** i) + i) + 1)
        #print "if we accelerate on: ", i, 'TURNS =', nuke_turns
        #pre_steal_state = abs(last_state[1]) + tt_accel - fatal_g.turns_till_arrival + 1
        #nuke_amount = int(math.ceil((n.penguin_amount + n.penguins_per_turn * (nuke_turns + 1) + 1) * (game.acceleration_cost ** i))) + my_siege_amount(game, k)
        nuke_amount = (n.penguin_amount + n.penguins_per_turn * (nuke_turns + 1) + 1)
        if nuke_turns > how_fast or k_amount == 0 or nuke_turns < how_slow:
            continue
        for l in range(0, i):
            nuke_amount = int(math.ceil(nuke_amount * game.acceleration_cost))
        if nuke_amount <= best:
            best = nuke_amount
            accel_tup = (k, n, i, (nuke_amount)-nuke_turns*n.penguins_per_turn, nuke_turns)
    return accel_tup


"""
def min_accel(game, k, n, useables):
    #print k, 'ON', n
    accel_tup = []
    k_amount = useables[k][1]
    for i in range(4):
        #print "N AMOUNT: ", n.penguin_amount
        #print "NPPT: ", n.penguins_per_turn
        #print 'iteration of speed: ', i
        turns = distance(game, k, n)
        nuke_turns = int(math.ceil(1 + (turns - i+1) / (game.acceleration_factor ** i) + i-1))   
        #print "if we accelerate on: ", i, 'TURNS =', nuke_turns
        #pre_steal_state = abs(last_state[1]) + tt_accel - fatal_g.turns_till_arrival + 1
        #nuke_amount = int(math.ceil((n.penguin_amount + n.penguins_per_turn * (nuke_turns + 1) + 1) * (game.acceleration_cost ** i))) + my_siege_amount(game, k)
        nuke_amount = (n.penguin_amount + n.penguins_per_turn * (nuke_turns + 1) + 1)
        for l in range(0, i):
            nuke_amount = int(math.ceil(nuke_amount * game.acceleration_cost))
        nuke_amount += my_siege_amount(game, k)
        '''
        nuke_amount = (n.penguin_amount + n.penguins_per_turn * (nuke_turns + 1) + 1)
        for l in range(i):
            nuke_amount *= game.acceleration_cost
            nuke_amount = int(math.ceil(nuke_amount))
        nuke_amount += my_siege_amount(game, k)
        '''
        #print 'WE HAVE TO NUKE', n, 'WITH: ', nuke_amount
        if k.can_send_penguins(n, nuke_amount):
            if not accel_tup:
                accel_tup = [nuke_amount, nuke_turns, i]
                #print "TUPLE OF CALCS: ", accel_tup
                continue
            else:
                if accel_tup[0] // (game.acceleration_cost ** accel_tup[2]) < nuke_amount // (game.acceleration_cost ** i):
                    accel_tup = [nuke_amount, nuke_turns,  i]
                #print "TUPLE OF CALCS: ", accel_tup
    
    if not accel_tup:
        return
    if k.can_send_penguins(n, accel_tup[0]) and accel_tup[0] < useables[k][1] and not k.already_acted:
        #print "IF WE ACCELERATE FROM: ", k, "TO", n, "AMOUNT: ", nuke_amount
        return (k, accel_tup[2], n, int(math.ceil(accel_tup[0])))  
        
    return () 
"""

"""     
def ozatero_l(game):
    global accel_groups
    if not game.get_neutral_icebergs:
        return None
    destinations = last_takes_enemy_neutral(game)
    if not destinations:
        return None
    pengs = game.get_my_penguin_groups()
    if not pengs:
        return None
    pengs = filter(lambda peng: peng.destination in destinations, pengs)
    if not pengs:
        return None
    for peng in pengs:
       # print "WHO TOOKS ", who_takes(game, peng.destination)[0].owner
       # print "YOSEF <3 "
        ozetaro_ice =  who_takes(game, peng.destination, peng.destination.penguin_amount)
       
        if not ozetaro_ice:
           continue
        if ozetaro_ice[0].owner == game.get_myself():
            amount = peng.penguin_amount
            count = 0
            while amount / game.acceleration_factor > 1:
                count += 1
                amount = amount / game.acceleration_factor
            accel_groups.update({peng: count})
    return None
    
def neutrals_we_lose(game):
    if not game.get_neutral_icebergs():
        return None
    destinations = last_takes_enemy_neutral(game)
    if not destinations:
        return None
    pengs = game.get_my_penguin_groups()
    if not pengs:
        return None
    pengs = filter(lambda peng: peng.destination in destinations, pengs)
    if not pengs:
        return None
    neutrals = {pengs[0].destination}
    for peng in pengs:
        neutrals.add(peng.destination)
    return neutrals
"""

""" 
def last_takes_enemy_neutral(game):
    
    if not game.get_neutral_icebergs():
        return None
    neutral = (g for g in game.get_neutral_icebergs() if last_takes(game, g)[0] == game.get_enemy())
    if not neutral:
        return None
    return neutral
    
def my_peng_destinations(game):
    if not game.get_my_penguin_groups():
        return None
    destinations = {game.get_my_penguin_groups()[0].destination}
    for peng in game.get_my_penguin_groups():
        destinations.add(peng.destination)
    return destinations

def enemy_clones_coming_back_destinations(game):
    if not game.get_enemy_penguin_groups():
        return None
    if not game.get_cloneberg():
        return None
    pengs=filter(lambda g: g.destination == game.get_cloneberg(), game.get_enemy_penguin_groups())
    if not pengs:
        return None
    destinations = {pengs[0].source}
    for peng in pengs:
        destinations.add(peng.source)
    return destinations
    
def enemy_clones_coming_back_amount(game, ice):
    amount = 0
    destinations = enemy_clones_coming_back_destinations(game)
    if not destinations:
        return None
    if ice not in destinations:
        return None
    pengs = filter(lambda g: g.destination == game.get_cloneberg() and g.source == ice, game.get_enemy_penguin_groups())
    if not pengs:
        return None
    groups = {(pengs[0].penguin_amount * game.cloneberg_multi_factor, pengs[0].turns_till_arrival + 1 + distance(game, ice, game.get_cloneberg()) // pengs[0].current_speed), pengs[0]}
    for peng in groups:
        groups.add((peng.penguin_amount * game.cloneberg_multi_factor, peng.turns_till_arrival + 1 + distance(game, ice, game.get_cloneberg()) // pengs.current_speed), peng)
    return list(groups)
"""
    


