from penguin_game import *
from generalFunc import *
from globalsVars import *

def cloner(game, useables, ice_accel, considered_s, u, s_tta):
    """Cloner will define the logic for the cloning feature."""
    my_icebergs = game.get_my_icebergs()
    for berg in my_icebergs:
        if useables[berg][0] == False or berg == game.get_my_icepital_icebergs()[0] or berg in u:
            continue
        safe_speed = enemy_crippled(game, berg, useables, considered_s, s_tta)
        if safe_speed == []:
            continue
        use = min(useables[berg][1], berg.penguin_amount)
        for i in safe_speed:
            cost = game.acceleration_cost
            total_cost = use
            clone_factor = game.cloneberg_multi_factor
            amount = use
            for j in range(i):
                total_cost = int(math.ceil(total_cost*cost))
                amount = int(math.floor(amount/cost))
            amount -= my_siege_amount(game, berg)
            if amount <= 0:
                continue
            s_groups = filter(lambda x: x.is_siege_group and x.destination == berg, game.get_enemy_penguin_groups())
            for s in s_groups:
                total_cost += math.ceil(s.penguin_amount * game.go_through_siege_cost)
            if use >= amount * clone_factor:
                break
            berg.send_penguins(game.get_cloneberg(), use)
            if i > 0:
                ice_accel.append((berg, i, game.get_cloneberg()))
            break
    return ice_accel

def turns_till_cloneberg(ice):
    """
    Calcs the turns till arrival to the cloneberg.
    """
    return ice.get_turns_till_arrival(game.get_cloneberg())

def clone_level(game):
    """
    Determines the level of the cloninig iceberg.
    """
    clone_tier = sorted(game.get_all_icebergs(), key = turns_till_cloneberg)
    return clone_tier[0:4]
