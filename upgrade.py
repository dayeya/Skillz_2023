from penguin_game import *
from generalFunc import *

def upgrade_if_can(game, useables):
    """
    GOAL: the function upgrades every iceberg that can potentially upgrade and hasn't made a move in the currnet turn
    RETURNS: a list contains every iceberg that belong to us and upgraded in the current turn
    """ 
    future_useables = {
        x : (valid_for_action(game, x, x.penguin_amount - x.upgrade_cost) if useables[x][1] >= x.upgrade_cost else useables[x]) 
        for x in game.get_my_icebergs()}
    
    upgrades = filter(
        lambda ice: ice.level < 4 and min(useables[ice][1], ice.penguin_amount) >= ice.upgrade_cost 
                                  and future_useables[ice][0] 
                                  and who_takes(game, ice, ice.penguin_amount - ice.upgrade_cost)[2] == game.get_myself(), game.get_my_icebergs())
    
    ret_who_upgraded = [i.upgrade() for i in upgrades if not i.already_acted]
    return ret_who_upgraded