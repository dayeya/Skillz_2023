from penguin_game import *
from attackdefense import *
from upgrade import *
from transportation import *
from globalsVars import *
from clone import *

def siege_onw_to_ice(game, ice):
    """
    Returns: Boolean indicating the siege status of ICE (our & enemies).
    True -> there is a siege threat, False -> Free of sieges.
    """
    sgroups = filter(lambda x: x.is_siege_group and x.destination == ice and x.turns_till_arrival not in {0, 1}, game.get_all_penguin_groups())
    temp_groups = filter(lambda x: x.is_siege_group and x.destination == ice, game.get_all_penguin_groups())

    return (temp_groups and ice not in game.get_enemy_under_siege_icebergs()) or bool(sgroups)

def valid_to_set_siege(game, ice):
    """
    RETURNS: Boolean that indicates that ICE (enemy iceberg) is valid to set siege.
    """
    will_be_sieged = siege_onw_to_ice(game, ice)
    regular = not ice.is_under_siege
    infinite = (not regular) and (ice.siege_turns >= game.siege_max_turns - 5)
    return (infinite or regular) and (not will_be_sieged)

def punish_target_sort_key(target):
    return target.get_turns_till_arrival(game.get_cloneberg())

def clone_punishment(game, useables, u, punish_clone, under_s):
    clone = game.get_cloneberg()

    enemy_icepital = game.get_enemy_icepital_icebergs()
    if not enemy_icepital:
        return
    enemy_icepital = enemy_icepital[0]

    icebergs = game.get_my_icebergs()
    siegers = sorted([ice for ice in icebergs if ice not in u and useables[ice][0]], key=lambda x: min(x.penguin_amount, useables[x][1]), reverse=True)
    punish = [t for t in punish_clone.keys() if punish_clone[t] != dict({})]

    for s in siegers:
        s_amount = min(s.penguin_amount, useables[s][1])
        own_siege = my_siege_amount(game, s)

        punish_targets = sorted([t for t in punish if valid_to_set_siege(game, t) and t not in under_s], key=punish_target_sort_key)

        for target in punish_targets:
            p_target = punish_clone[target]
            cloners_sorted_by_calculation = sorted(p_target.keys(), key=lambda p: p_target[p][1])

            if not cloners_sorted_by_calculation:
                continue

            first_clone = cloners_sorted_by_calculation[0]

            if p_target[first_clone][1] > 5 and not siege_onw_to_ice(game, s):
                continue

            som_clone = int(sum([g.penguin_amount * game.cloneberg_multi_factor for g in p_target.keys() if p_target[g][0] == "CLONE"]) // 3)
            som_dst = int(sum([g.penguin_amount for g in p_target if p_target[g][0] == "SOURCE"]) // 3)

            som = som_clone + som_dst
            som = int(math.ceil(som)) if int(math.ceil(som)) <= s_amount else som

            if s.is_under_siege and own_siege > 0:
                if own_siege + som < som * 3:
                    s.send_penguins(target, own_siege)
                    s_amount -= own_siege
                else:
                    continue

            if som > s_amount or som == 0:
                som = s_amount

            s.send_penguins_to_set_siege(target, som)
            under_s.append(target)

def set_siege(game, useables, owning, under_s, u):
    """Sets siege on needed icebergs"""
    siege_turns = 6
    enemy_icepital = game.get_enemy_icepital_icebergs()

    if not enemy_icepital:
        return
    enemy_icepital = enemy_icepital[0]
    clone = game.get_cloneberg()
    if not clone:
        clone = []

    our_last_takes = set([ice for ice in owning.keys() if owning[ice][0] == game.get_myself()])
    enemy_icebergs = set(game.get_enemy_icebergs())
    potential_targets = enemy_icebergs.difference(our_last_takes)
    targets = sorted([ice for ice in potential_targets if ice not in under_s and valid_to_set_siege(game, ice)], key=punish_target_sort_key)
    icebergs = [ice for ice in set(game.get_my_icebergs()).difference(set(game.get_my_under_siege_icebergs())) if useables[ice][0]]
    siegers = sorted([ice for ice in icebergs if ice not in u], key=lambda x: x.level, reverse=True)

    for s in siegers:
        s_amount = min(s.penguin_amount, useables[s][1])
        if s_amount <= 0:
            continue

        for t in targets:
            s_amount = min(s.penguin_amount, useables[s][1])
            state = owning[t]
            owner, amount, last_peng, after_all_amount, tta = state
            if tta == 0 or not last_peng or tta < siege_turns and not s.already_acted:
                siege_M = min(s_amount, game.go_through_siege_cost)
                s.send_penguins_to_set_siege(t, siege_M)
                targets.remove(t)
                continue

            pen_min_siege_amount = int(math.ceil(last_peng.penguin_amount / game.go_through_siege_cost))
            steal_siege = min(s_amount, pen_min_siege_amount)

            if not s.already_acted:
                s.send_penguins_to_set_siege(t, steal_siege)
                targets.remove(t)