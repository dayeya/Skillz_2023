''' CURRENTLY NOT IN USE!!! '''
global first_settlement
first_settlement = False

''' CURRENTLY NOT IN USE!!! '''
global check_for_initial
check_for_initial = True

''' CURRENTLY NOT IN USE!!! '''
global first_neutral
first_neutral = True


''' CURRENTLY NOT IN USE!!! '''
global ban_capital_p_use
ban_capital_p_use = False

''' The siege groups turns till arrival constant '''
global SIEGE_TURNS 
SIEGE_TURNS = 5

"""
A dictionary contains:
keys= every penguin group (we own) that needs acceleration in the next turn
values= the number of turns left we need to accelerate the group
"""
global accel_groups
accel_groups = {}


"""
A list contains every iceberg we sent an "acceleration needed" group that doesn't exists in the current turn.
We use the list to track down the group in the next turn and accelerate it according to accel_groups.
"""
global ice_accel 
ice_accel = [] # tuple => (ice, future_speed) num of accel


"""
A list contains every enemy iceberg that we sent a siege group to it in the current turn.
(Only contains the icebergs we sent siege to, before entering the "set_siege" function)
"""
global under_s
under_s = []


''' Siege turns till arrival '''
global s_tta 
s_tta = 5

'''
False -> if we haven't updated the siege groups turns till arrival
True -> if we updated the siege groups turns till arrival
'''
global updated_s_tta
updated_s_tta = False


"""
Counter for turns till arrival for siege groups
"""
global temp_s_tta
temp_s_tta = 0

"""
A list contains THE FIRST (in the whole game) siege group
"""
global s_group_save
s_group_save = []

"""
A dictionary for every enemy iceberg that sent groups to cloneberg and 
it's groups are on the way to cloneberg or on the way back.
Keys -> Enemy icebergs that sent to cloneberg
Values -> The penguing groups from the iceberg
"""
global punish_clone
punish_clone = {}