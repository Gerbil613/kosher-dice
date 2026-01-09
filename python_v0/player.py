'''
Simple example pokerbot, written in Python.
'''
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
        


class Player(Bot):
    '''
    A pokerbot.
    '''

    @staticmethod
    def score_pair(a, b):
        '''
        Docstring for score_pair
        
        :param a: First card
        :param b: Second card

        Evaluates strength of pair of cards based on lecture note picture
        '''
        # The raw data extracted from the image grid (Row by Row: A -> 2)
        rank_to_index = {'AKQJT98765432'[i]: i for i in range(13)}
        data = [
            # A           K     Q     J     T     9     8     7     6     5     4     3     2
            [9.95, 3.96, 2.90, 2.32, 1.97, 1.53, 1.35, 1.23, 1.06, 1.16, 1.05, 0.95, 0.85], # A Row
            [3.19, 8.17, 2.07, 1.73, 1.52, 1.14, 0.91, 0.81, 0.71, 0.60, 0.52, 0.45, 0.39], # K Row
            [2.06, 1.29, 6.58, 1.53, 1.38, 1.05, 0.78, 0.53, 0.46, 0.39, 0.34, 0.27, 0.22], # Q Row
            [1.49, 0.94, 0.80, 5.21, 1.34, 1.02, 0.79, 0.51, 0.29, 0.25, 0.21, 0.19, 0.16], # J Row
            [1.13, 0.73, 0.63, 0.63, 4.08, 1.03, 0.85, 0.58, 0.33, 0.20, 0.18, 0.16, 0.13], # T Row
            [0.70, 0.37, 0.33, 0.33, 0.36, 3.15, 0.89, 0.68, 0.44, 0.19, 0.13, 0.11, 0.08], # 9 Row
            [0.53, 0.27, 0.22, 0.22, 0.25, 0.26, 2.43, 0.77, 0.59, 0.32, 0.14, 0.07, 0.05], # 8 Row
            [0.41, 0.22, 0.13, 0.13, 0.16, 0.18, 0.19, 1.86, 0.66, 0.43, 0.20, 0.09, 0.01], # 7 Row
            [0.33, 0.16, 0.08, 0.04, 0.07, 0.09, 0.11, 0.14, 1.49, 0.57, 0.37, 0.13, 0.03], # 6 Row
            [0.33, 0.12, 0.05, 0.02, 0.00, 0.01, 0.03, 0.07, 0.09, 1.19, 0.53, 0.32, 0.08], # 5 Row
            [0.28, 0.08, 0.03, 0.00, 0.00, 0.00, 0.00, 0.00, 0.03, 0.06, 0.97, 0.23, 0.06], # 4 Row
            [0.25, 0.05, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.78, 0.02], # 3 Row
            [0.20, 0.02, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.61]  # 2 Row
        ]
        if a[0] == b[0]: # same rank
            rank = a[0]
            index = rank_to_index[rank]
            return data[index][index]
        
        # different ranks
        score1 = data[rank_to_index[a[0]]][rank_to_index[b[0]]]
        score2 = data[rank_to_index[b[0]]][rank_to_index[a[0]]]
        higher = max(score1, score2)
        lower = min(score1, score2)
        if a[1] == b[1]: # same suit
            return higher
        
        return lower

    def __init__(self):
        '''
        Called when a new game starts. Called exactly once.

        Arguments:
        Nothing.

        Returns:
        Nothing.
        '''
        pass

    def handle_new_round(self, game_state, round_state, active):
        '''
        Called when a new round starts. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        my_bankroll = game_state.bankroll  # the total number of chips you've gained or lost from the beginning of the game to the start of this round
        # the total number of seconds your bot has left to play this game
        game_clock = game_state.game_clock
        round_num = game_state.round_num  # the round number from 1 to NUM_ROUNDS
        my_cards = round_state.hands[active]  # your cards
        big_blind = bool(active)  # True if you are the big blind
        pass

    def handle_round_over(self, game_state, terminal_state, active):
        '''
        Called when a round ends. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        terminal_state: the TerminalState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        my_delta = terminal_state.deltas[active]  # your bankroll change from this round
        previous_state = terminal_state.previous_state  # RoundState before payoffs
        street = previous_state.street  # 0,2,3,4,5,6 representing when this round ended
        my_cards = previous_state.hands[active]  # your cards
        # opponent's cards or [] if not revealed
        opp_cards = previous_state.hands[1-active]
        pass

    def get_action(self, game_state, round_state, active):
        '''
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Your action.
        '''
        legal_actions = round_state.legal_actions()  # the actions you are allowed to take
        # 0, 3, 4, or 5 representing pre-flop, flop, turn, or river respectively
        street = round_state.street
        my_cards = round_state.hands[active]  # your cards
        board_cards = round_state.board  # the board cards
        # the number of chips you have contributed to the pot this round of betting
        my_pip = round_state.pips[active]
        # the number of chips your opponent has contributed to the pot this round of betting
        opp_pip = round_state.pips[1-active]
        # the number of chips you have remaining
        my_stack = round_state.stacks[active]
        # the number of chips your opponent has remaining
        opp_stack = round_state.stacks[1-active]
        continue_cost = opp_pip - my_pip  # the number of chips needed to stay in the pot
        # the number of chips you have contributed to the pot
        my_contribution = STARTING_STACK - my_stack
        # the number of chips your opponent has contributed to the pot
        opp_contribution = STARTING_STACK - opp_stack

        # Only use DiscardAction if it's in legal_actions (which already checks street)
        # use intelligent dropping strategy
        if DiscardAction in legal_actions:
            return eval_discard(my_cards, board_cards)
            
        strong_cards = "TJQKA"

        if RaiseAction in legal_actions:
            # the smallest and largest numbers of chips for a legal bet/raise
            min_raise, max_raise = round_state.raise_bounds()
            min_cost = min_raise - my_pip  # the cost of a minimum bet/raise
            max_cost = max_raise - my_pip  # the cost of a maximum bet/raise

            Player.score_pair(my_cards[0], my_cards[1])

            # if we have strong hole cards, let's raise a lot
            is_strong = Player.score_pair(my_cards[0], my_cards[1]) > 0.6
            # for card in my_cards: # Th
            #     if not (card[0] in strong_cards):
            #         is_strong = False
            #         break

            if is_strong:
                return RaiseAction(min(min_raise * 10, max_raise))
            
            else:
                if random.random() < 0.5:
                    return RaiseAction(min_raise)
                
        if CheckAction in legal_actions:  # check-call
            return CheckAction()
        if random.random() < 0.25:
            return FoldAction()
        return CallAction()


if __name__ == '__main__':
    run_bot(Player(), parse_args())
