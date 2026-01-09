from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction, DiscardAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot

import random

def get_card_rank(card):
    """Gets numeric rank of card (1-12)"""
    ranks = "23456789TJQKA" # order of ranks
    return ranks.index(card[0])

def get_card_suit(card):
    """Get suit of card"""
    return card[1].lower()

def eval_discard(my_cards, board_cards):
    """
    DiscardAction with the index of the card to discard
    
    my_cards: the 3 hole cards 
    board_cards: the current cards on the board
    """
    # check whether opponent already discarded
    opponent_discarded = (len(board_cards) == 3)
    my_ranks = [get_card_rank(c) for c in my_cards]

    # Pair Splitting Strategy
    counts = {r:my_ranks.count(r) for r in my_ranks}
    pair_rank = -1
    kicker_rank = -1
    for r,count in counts.items():
        if count == 2:
            pair_rank = r
        if count == 1:
            kicker_rank = r
    # if we have a pair AND a kicker
    if pair_rank != -1 and kicker_rank != -1:
        # If the kicker is much higher than the pair (e.g. 2,2,Ace)
        # better to toss one of the pairs to the board because maintain pair
        # and don't let opponent get high card
        if kicker_rank > pair_rank + 4: # THIS THRESHOLD CAN BE CHANGED
            for i, card in enumerate(my_cards):
                if get_card_rank(card) == pair_rank:
                    return DiscardAction(i)
                
    # Defensive Drop Evaluation
    scores = [0,0,0]

    for i in range(3):
        droppable_card = my_cards[i]
        # potential future board post drop
        future_board = board_cards + [droppable_card]
        f_ranks = [get_card_rank(c) for c in future_board]
        f_suits = [get_card_suit(c) for c in future_board]

        rank_val = get_card_rank(droppable_card)
        suit_val = get_card_suit(droppable_card)

        # Flush Danger
        # If the future board has 3+ of the same suit, we give everyone flush potential
        if f_suits.count(suit_val) >= 3:
            scores[i] += 100  # HIGH FLUSH POTENTIAL
        elif f_suits.count(suit_val) == 2:
            scores[i] += 20
        
        # Straight Danger
        sorted_ranks = sorted(list(set(f_ranks)))
        consecutive_count = 0
        for j in range(len(sorted_ranks)-1):
            if sorted_ranks[j+1] == sorted_ranks[j] + 1:
                consecutive_count += 1
            else:
                consecutive_count = 0
            if consecutive_count >= 2: # 3 cards in a row (e.g. 6,7,8)
                scores[i] += 50  # High chance of straight
        
        # High Card Danger
        scores[i] += rank_val * 1.5

        # Reacting to Opponent
        if opponent_discarded:
            opp_discard = board_cards[2]  # The 3rd card is theirs
            if get_card_rank(opp_discard) == rank_val:
                scores[i] += 25  # Do not add a pair
        # Randomization Factor
        scores[i] += random.uniform(0, 5)

    best_discard = scores.index(min(scores))
    return DiscardAction(best_discard)