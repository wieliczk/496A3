EMPTY = 0
BLACK = 1
WHITE = 2
BORDER = 3
FLOODFILL = 4
import numpy as np
from pattern import pat3set
import sys
import random
import gtp_connection

class GoBoardUtil(object):
    
    @staticmethod       
    def playGame(board, color, **kwargs):
        komi = kwargs.pop('komi', 0)
        limit = kwargs.pop('limit', 1000)
        check_selfatari = kwargs.pop('selfatari', True)
        pattern = kwargs.pop('pattern', True)
        if kwargs:
            raise TypeError('Unexpected **kwargs: %r' % kwargs)
        numPass = 0
        for _ in range(limit):
            move = GoBoardUtil.generate_move_with_filter(board,pattern,check_selfatari)
            if move != None:
                isLegalMove = board.move(move,color)
                assert isLegalMove
                numPass = 0
            else:
                board.move(move,color)
                numPass += 1
                if numPass == 2:
                    break
            color = GoBoardUtil.opponent(color)
        winner = board.get_winner(komi)
        return winner
    
    @staticmethod
    def generate_legal_moves(board, color):
        """
        generate a list of legal moves

        Arguments
        ---------
        board : np.array
            a SIZExSIZE array representing the board
        color : {'b','w'}
            the color to generate the move for.
        """
        empty = board.get_empty_points()
        legal_moves = []
        for move in empty:
            if board.check_legal(move, color):
                legal_moves.append(move)
        return legal_moves

    @staticmethod
    def sorted_point_string(points, ns):
        result = []
        for point in points:
            x, y = GoBoardUtil.point_to_coord(point, ns)
            result.append(GoBoardUtil.format_point((x, y)))

        return ' '.join(sorted(result))

    @staticmethod
    def generate_pattern_moves(board):
        color = board.current_player
        pattern_checking_set = board.last_moves_empty_neighbors()
        moves = []
        for p in pattern_checking_set:
            if (board.neighborhood_33(p) in pat3set):
                assert p not in moves
                assert board.board[p] == EMPTY
                moves.append(p)
        return moves

    # BW code
    """
        Filer's moves properly 
    """
    @staticmethod
    def new_filters_for_moves(board):
        color = board.current_player
        moves = GoBoardUtil.generate_random_moves(board)
        good_moves = []
        for m in moves:
            first_filter = GoBoardUtil.filleye_filter(board, m, color)
            if not first_filter:
                second_filter = GoBoardUtil.selfatari_filter(board, m, color)
                if not second_filter:
                    good_moves.append(m)
        return good_moves



    @staticmethod
    def find_neighbours(board, move, neigh_list, prev_points, c_d=0):
        """
        Finds all the neighbours and stores them into a list
        """
        nbr = board._neighbors(move)
        prev_points.append(move)
        op_color = board.board[move] # Gets correct color
        if op_color == BLACK:
            color = WHITE
        else:
            color = BLACK
        for n in nbr:
            neigh_list.append(n)
            if board.board[n] == op_color:
                if n not in prev_points:
                    GoBoardUtil.find_neighbours(board, n, neigh_list, prev_points, c_d)
            # Gets current players stones
            if c_d != 0:
                if board.board[n] == color:
                    if n not in prev_points and n not in neigh_list:
                        GoBoardUtil.find_neighbours(board, n, neigh_list, prev_points, c_d)


    @staticmethod
    def gather_libs(board, a_list):
        """
        Finds the number of liberties for a group of stones
        Returns, the ammount of liberties as well as each liberty point
        """
        libs = 0
        moves = []
        for n in a_list:
            if board.board[n] == 0:
                libs += 1
                moves.append(n)
        return libs, moves

    @staticmethod
    def convert_point_to_move(move):
        cords = GoBoardUtil.point_to_coord(move)
        cord = GoBoardUtil.format_point(cords)
        return cord

    @staticmethod
    def all_points_for_defense(board):
        color = board.current_player
        moves = []
        for x in range(1,board.size+1):
            for y in range(1,board.size+1):
                point = board._coord_to_point(x,y)
                if board.get_color(point) == color:
                    moves.append(point)
        return moves

    @staticmethod
    def generate_capture_move(board):
        """
            # BW Code
            This portion of code is for the capture move
        """
        empty_return = []
        testing = GoBoardUtil.new_filters_for_moves(board)
        try:
            n_list = []
            checked_points = []
            last_played = board.last_move
            GoBoardUtil.find_neighbours(board, last_played, n_list, checked_points)
            libs, capture_point = GoBoardUtil.gather_libs(board, n_list)
            if libs == 1:
                if capture_point[0] in testing:
                    return capture_point              
        except:
            do_nothing = 1
            return empty_return

    @staticmethod
    def generate_defend_moves(board):
        empty_return = []
        testing = GoBoardUtil.new_filters_for_moves(board)
        try:
            # Gets all stones of player on board
            defend_moves = []
            d_checked = []
            d_list = []
            d_last_played = board.last_move
            color = board.current_player
            if color == WHITE:
                op_color = BLACK
            else:
                op_color = WHITE
            #GoBoardUtil.find_neighbours(board, d_last_played, d_list, d_checked, 2)
            d_list = board._neighbors(d_last_played)
            """
                op_moves = all the neighbours of the opponents moves
                our_moves = all of our moves (stones) affected by op_moves
                if an board.board[op_moves] 
                    a neighbour of an opponent move is our color we find the neighbours of that stone which are our color
                we then find the liberties of this new list of our_moves
                if our_moves only has 1 liberty
            """
            capture_defend = []
            our_moves_checked = []
            for op_moves in d_list:
                our_moves = []
                if board.board[op_moves] == color:
                    GoBoardUtil.find_neighbours(board, op_moves, our_moves, our_moves_checked)
                    libs, defend_point = GoBoardUtil.gather_libs(board, our_moves)
                    if libs == 1:
                        capture_defend.append(our_moves)
                        extra_check = []
                        extra_list = []
                        checking = defend_point[0]
                        GoBoardUtil.find_neighbours(board, checking, extra_list, extra_check)
                        n_libs, useless = GoBoardUtil.gather_libs(board, extra_list)
                        if n_libs > 1 and defend_point[0] in testing and defend_point[0] not in defend_moves: 
                            defend_moves.append(defend_point[0])

            # Capture_defend is a set of neighbours to our stone set that only have a single liberty 
            opp_stone_sets = []
            for a_list in capture_defend:
                a_checked_list = []
                for a_nbr in a_list:
                    opp_stones = []
                    if board.board[a_nbr] == op_color:
                        GoBoardUtil.find_neighbours(board, a_nbr, opp_stones, a_checked_list, 2)
                        opp_stone_sets.append(opp_stones)
            # Take sets of stones around atari and see if any can be captured
            for set_stones in opp_stone_sets:
                s_libs, s_points = GoBoardUtil.gather_libs(board, set_stones)
                if s_libs == 1 and s_points[0] in testing and s_points[0] not in defend_moves:
                    defend_moves.append(s_points[0])
        except:
            do_nothing = 1
            return empty_return
        if len(defend_moves) > 0:
            return defend_moves
        else:
            return empty_return

    @staticmethod
    def generate_all_policy_moves(board,pattern,check_selfatari):
        """
            generate a list of policy moves on board for board.current_player.
            Use in UI only. For playing, use generate_move_with_filter
            which is more efficient
        """
        capture_move = GoBoardUtil.generate_capture_move(board)
        if capture_move != None:
            if len(capture_move) > 0:
                return capture_move, "AtariCapture"

        defend_moves = GoBoardUtil.generate_defend_moves(board)
        if defend_moves != None:
            if len(defend_moves) > 0:
                return defend_moves, "AtariDefense"

        pattern_moves = GoBoardUtil.generate_pattern_moves(board)
        pattern_moves = GoBoardUtil.filter_moves(board, pattern_moves, check_selfatari)
        if len(pattern_moves) > 0:
            return pattern_moves, "Pattern"
        return GoBoardUtil.generate_random_moves(board), "Random"

    @staticmethod
    def generate_random_moves(board):
        empty_points = board.get_empty_points()
        color = board.current_player
        moves = []
        for move in empty_points:
            if board.check_legal(move, color) and not board.is_eye(move, color):
                moves.append(move)
        return moves

    @staticmethod
    def generate_random_move(board):
        color = board.current_player
        moves = board.get_empty_points()
        while len(moves) > 0:
            index = random.randint(0,len(moves) - 1)
            move = moves[index]
            if board.check_legal(move, color) and not board.is_eye(move, color):
                return move
            else:
                # delete moves[index] by overwriting with last in list
                lastIndex = len(moves) - 1
                if index < lastIndex:
                    moves[index] = moves[lastIndex]
                moves.pop()
        return None

    @staticmethod
    def filter_moves(board, moves, check_selfatari):
        color = board.current_player
        good_moves = []
        for move in moves:
            if not GoBoardUtil.filter(board,move,color,check_selfatari):
                good_moves.append(move)
        return good_moves

    # return True if move should be filtered
    @staticmethod
    def filleye_filter(board, move, color):
        assert move != None
        return not board.check_legal(move, color) or board.is_eye(move, color)
    
    # return True if move should be filtered
    @staticmethod
    def selfatari_filter(board, move, color):
        return (  GoBoardUtil.filleye_filter(board, move, color)
               or GoBoardUtil.selfatari(board, move, color)
               )

    # return True if move should be filtered
    @staticmethod
    def filter(board, move, color, check_selfatari):
        if check_selfatari:
            return GoBoardUtil.selfatari_filter(board, move, color)
        else:
            return GoBoardUtil.filleye_filter(board, move, color)

    @staticmethod 
    def filter_moves_and_generate(board, moves, check_selfatari):
        color = board.current_player
        while len(moves) > 0:
            candidate = random.choice(moves)
            if GoBoardUtil.filter(board, candidate, color, check_selfatari):
                moves.remove(candidate)
            else:
                return candidate
        return None
        
    @staticmethod
    def generate_move_with_filter(board, use_pattern, check_selfatari):
        """
            Arguments
            ---------
            check_selfatari: filter selfatari moves?
                Note that even if True, this filter only applies to pattern moves
            use_pattern: Use pattern policy?
        """
        move = None
        if use_pattern:
            moves = GoBoardUtil.generate_pattern_moves(board)
            move = GoBoardUtil.filter_moves_and_generate(board, moves, 
                                                         check_selfatari)
        if move == None:
            move = GoBoardUtil.generate_random_move(board)
        return move 
    
    @staticmethod
    def selfatari(board, move, color):
        max_old_liberty = GoBoardUtil.blocks_max_liberty(board, move, color, 2)
        if max_old_liberty > 2:
            return False
        cboard = board.copy()
        # swap out true board for simulation board, and try to play the move
        isLegal = cboard.move(move, color) 
        if isLegal:               
            new_liberty = cboard._liberty(move,color)
            if new_liberty==1:
                return True 
        return False

    @staticmethod
    def blocks_max_liberty(board, point, color, limit):
        assert board.board[point] == EMPTY
        max_lib = -1 # will return this value if this point is a bwnew block
        neighbors = board._neighbors(point)
        for n in neighbors:
            if board.board[n] == color:
                num_lib = board._liberty(n,color) 
                if num_lib > limit:
                    return num_lib
                if num_lib > max_lib:
                    max_lib = num_lib
        return max_lib
        
    @staticmethod
    def format_point(move):
        """
        Return coordinates as a string like 'a1', or 'pass'.

        Arguments
        ---------
        move : (row, col), or None for pass

        Returns
        -------
        The move converted from a tuple to a Go position (e.g. d4)
        """
        column_letters = "abcdefghjklmnopqrstuvwxyz"
        if move is None:
            return "pass"
        row, col = move
        if not 0 <= row < 25 or not 0 <= col < 25:
            raise ValueError
        return    column_letters[col - 1] + str(row) 
        
    @staticmethod
    def move_to_coord(point, board_size):
        """
        Interpret a string representing a point, as specified by GTP.

        Arguments
        ---------
        point : str
            the point to convert to a tuple
        board_size : int
            size of the board

        Returns
        -------
        a pair of coordinates (row, col) in range(1, board_size+1)

        Raises
        ------
        ValueError : 'point' isn't a valid GTP point specification for a board of size 'board_size'.
        """
        if not 0 < board_size <= 25:
            raise ValueError("board_size out of range")
        try:
            s = point.lower()
        except Exception:
            raise ValueError("invalid point")
        if s == "pass":
            return None
        try:
            col_c = s[0]
            if (not "a" <= col_c <= "z") or col_c == "i":
                raise ValueError
            if col_c > "i":
                col = ord(col_c) - ord("a")
            else:
                col = ord(col_c) - ord("a") + 1
            row = int(s[1:])
            if row < 1:
                raise ValueError
        except (IndexError, ValueError):
            raise ValueError("wrong coordinate")
        if not (col <= board_size and row <= board_size):
            raise ValueError("wrong coordinate")
        return row, col
    
    @staticmethod
    def opponent(color):
        opponent = {WHITE:BLACK, BLACK:WHITE} 
        try:
            return opponent[color]    
        except:
            raise ValueError("Wrong color provided for opponent function")
            
    @staticmethod
    def color_to_int(c):
        """convert character representing player color to the appropriate number"""
        color_to_int = {"b": BLACK , "w": WHITE, "e":EMPTY, "BORDER":BORDER, "FLOODFILL":FLOODFILL}
        try:
            return color_to_int[c] 
        except:
            raise ValueError("wrong color")
    
    @staticmethod
    def int_to_color(i):
        """convert number representing player color to the appropriate character """
        int_to_color = {BLACK:"b", WHITE:"w", EMPTY:"e", BORDER:"BORDER", FLOODFILL:"FLOODFILL"}
        try:
            return int_to_color[i] 
        except:
            raise ValueError("Provided integer value for color is invalid")
         
    @staticmethod
    def copyb2b(board, copy_board):
        """Return an independent copy of this Board."""
        copy_board.board = np.copy(board.board)
        copy_board.suicide = board.suicide  # checking for suicide move
        copy_board.winner = board.winner 
        copy_board.NS = board.NS
        copy_board.WE = board.WE
        copy_board._is_empty = board._is_empty
        copy_board.passes_black = board.passes_black
        copy_board.passes_white = board.passes_white
        copy_board.current_player = board.current_player
        copy_board.ko_constraint =  board.ko_constraint 
        copy_board.white_captures = board.white_captures
        copy_board.black_captures = board.black_captures 

        
    @staticmethod
    def point_to_coord(point, ns):
        """
        Transform one dimensional point presentation to two dimensional.

        Arguments
        ---------
        point

        Returns
        -------
        x , y : int
                coordinates of the point  1 <= x, y <= size
        """
        if point is None:
            return 'pass'
        row, col = divmod(point, ns)
        return row,col

