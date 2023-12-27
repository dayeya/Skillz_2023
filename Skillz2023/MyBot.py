from penguin_game import *
from attackdefense import *
from upgrade import *
from transportation import *
from globalsVars import *
from clone import *
from MaZoR import *

# Skillz code 2022, Daniel Sapojnikov, Johnathan Tyomkin and Idan Chernetsky
#In honour to 'def daddy_is_home' and 'def valid_for_action'.
# We love you.

def do_turn(game):
    """Main function of the program"""
    
    global punish_clone
    global ban_capital_p_use
    global accel_groups
    global ice_accel
    global under_s
    global s_tta 
    global updated_s_tta
    global temp_s_tta
    global s_group_save

    try:
        if not game.get_my_icepital_icebergs() or not game.get_enemy_icepital_icebergs():
            return

        clone = game.get_cloneberg()
        if not clone: 
            clone = []
                   
        if not updated_s_tta:
            s_tup = count_s_tta(game, s_tta, updated_s_tta, temp_s_tta, s_group_save)
            s_tta = s_tup[0]
            updated_s_tta = s_tup[1]
            temp_s_tta = s_tup[2]
            s_group_save = s_tup[3]
        
        punish_clone = {ice: {} for ice in game.get_enemy_icebergs()}
        owning = {ice: last_takes(game, ice, []) for ice in game.get_my_icebergs() + game.get_enemy_icebergs() + game.get_neutral_icebergs()}
        useables = {ice: valid_for_action(game, ice, ice.penguin_amount) for ice in game.get_my_icebergs()}

        our_checked_bergs = [ice for ice in owning.keys() if owning[ice][0] == game.get_myself()]
        enemy_checked_bergs = [ice for ice in owning.keys() if owning[ice][0] == game.get_enemy()]

        considered_s = []
        for berg in game.get_enemy_icebergs():
            considered_s.append([berg, 0])
            
        accel_groups = input_berg(game, useables, ice_accel, accel_groups)
        d_day(game, accel_groups)
        accel_groups = stolen(game, accel_groups, owning)
        accel_groups = execute_acceleration(game, useables, accel_groups)
        ice_accel = []
        
        daddy_is_home(game, useables, ice_accel, 0, our_checked_bergs, enemy_checked_bergs, owning, under_s, s_tta)

        steal(game, useables, ice_accel, owning)
        daddy_is_home(game, useables, ice_accel, 1, our_checked_bergs, enemy_checked_bergs, owning, under_s, s_tta)
        u = upgrade_if_can(game, useables)

        if clone != []:
            input_clone(game, useables, punish_clone, clone, s_tta)
            clone_punishment(game, useables, u, punish_clone, under_s)

        set_siege(game, useables, owning, under_s, u)
        if game.get_cloneberg() != [] and game.get_cloneberg() != None:
            ice_accel = cloner(game, useables, ice_accel, considered_s, u, s_tta)
        under_s = []
        
    except: pass