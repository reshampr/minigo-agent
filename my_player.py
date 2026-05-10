import copy
from collections import deque
from turtledemo.penrose import start

import numpy as np
import os
import time

grid_size = 5
black = 1
white = 2
KOMI = grid_size / 2
INPUT_FILE_NAME = "/Applications/Code's/Game agent HW2/resource/asnlib/public/myplayer_play/init/input.txt"
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
STEP_FILE = os.path.join(BASE_DIR, "step.txt")
DIRECTIONS = [[1, 0], [0, 1], [-1, 0], [0, -1]]  # down,right,up,left


hashMap = {}
class Go_agent:
    def __init__(self, turn, previous_state, current_state):
        self.turn = turn
        self.previous_state = previous_state
        self.current_state = current_state

    # Returns move made by opponent in previous state
    def move_by_opponent(self):

        if np.array_equal(self.previous_state, self.current_state):
            return -1,-1

        for i in range(grid_size):
                for j in range(grid_size):
                    if self.current_state[i][j] != self.previous_state[i][j] and self.previous_state[i][j] == 0 and self.current_state[i][j] != 0:
                        return i, j

        return None

    def opp_side(self, turn):
        if turn == black:
            return white
        else:
            return black


    def has_lib(self,x,y,current_state,turn):

        queue = deque([(x,y)])
        visited = set()

        while queue:
            x,y = queue.popleft()
            visited.add((x,y))

            for direction in DIRECTIONS:
                new_x, new_y = x + direction[0], y + direction[1]
                if 0 <= new_x < grid_size and 0 <= new_y < grid_size:
                    if current_state[new_x][new_y] == 0:
                        return True
                    elif current_state[new_x][new_y] == turn and (new_x, new_y) not in visited:
                        queue.append((new_x, new_y))


        return False


    def valid_liberties(self,x,y,current_state,turn):
        copy_of_state = copy.deepcopy(current_state)
        copy_of_state[x][y] = turn
        opponent = self.opp_side(turn)

        for direction in DIRECTIONS:
            new_x, new_y = x + direction[0], y + direction[1]
            if 0 <= new_x < grid_size and 0 <= new_y < grid_size:
                if copy_of_state[new_x][new_y] == opponent:
                    if not self.has_lib(new_x,new_y,copy_of_state,opponent):
                        return True

        if self.has_lib(x,y,copy_of_state,turn):
            return True
        return False


    def legal_moves(self, current_state, turn):

        legit_moves = []
        # opponent = self.opp_side(turn)
        for i in range(grid_size):
            for j in range(grid_size):
                if current_state[i][j] == 0:
                    if self.valid_liberties(i, j, current_state,turn) and not self.ko_check(i,j):  ##############
                        legit_moves.append((i,j))
        legit_moves.append((-1, -1))

        return legit_moves

    def ko_check(self, x, y):
        """
         (x,y) is the position where a stone is being placed
         If placing the stone results in prev state == curr state ==> KO(True)
        """
        turn = self.turn
        copy_of_current_state,_ = self.make_move(self.current_state, turn, (x, y))
        return np.array_equal(copy_of_current_state, self.previous_state)

    def make_move(self, current_state, turn, move):
        copy_of_current_state = copy.deepcopy(current_state)
        if move == (-1, -1):
            return copy_of_current_state,0
        x, y = move[0], move[1]

        captured_stones_before = np.sum(copy_of_current_state == self.opp_side(turn))

        if copy_of_current_state[x][y] != 0:
            return current_state,0
        else:
            copy_of_current_state[x][y] = turn
        opp_stone = self.opp_side(turn)
        for direction in DIRECTIONS:
            new_x, new_y = x + direction[0], y + direction[1]
            if 0 <= new_x < grid_size and 0 <= new_y < grid_size:
                if not self.has_lib(new_x, new_y, copy_of_current_state,opp_stone):
                    copy_of_current_state = self.capture(copy_of_current_state, new_x, new_y, opp_stone)

        captured_stones_after = np.sum(copy_of_current_state == self.opp_side(turn))
        captureCount = captured_stones_before - captured_stones_after
        if not self.has_lib(x, y, copy_of_current_state, turn): return current_state,0
        return copy_of_current_state,captureCount

    def capture(self, current_state, x, y, turn):
        """
        'turn' will be captured
        This is only called when there is NO LIBERTY,so they can be captured
        we do not have to check for liberties again
        """
        copy_of_current_state = copy.deepcopy(current_state)
        queue = deque([(x, y)])
        visited = set()

        while queue:
            x, y = queue.popleft()
            visited.add((x, y))
            copy_of_current_state[x][y] = 0
            for direction in DIRECTIONS:
                new_x, new_y = x + direction[0], y + direction[1]
                if (new_x, new_y) in visited:
                    continue
                if 0 <= new_x < grid_size and 0 <= new_y < grid_size:
                    if current_state[new_x][new_y] == turn:
                        if (new_x, new_y) not in visited:
                            queue.append((new_x, new_y))

        return copy_of_current_state

    def ordered_moves(self,current_state,turn,legal_moves):
        other_moves = []
        power_move = []

        for move in legal_moves:
            if move == (-1, -1):
                other_moves.append(move)
            else:
                new_state,cap_count = self.make_move(copy.deepcopy(current_state), turn, move)
                influence_of_move = self.influence(new_state,turn,move)
                score = 1 * cap_count + 1 * influence_of_move
                power_move.append((move,score))
                # power_move.append((move,cap_count,influence_of_move))

        # power_move.sort(key = lambda x:(x[1],x[2]))
        power_move.sort(key = lambda x:x[1])
        power_move = [x[0] for x in power_move]
        return power_move + other_moves



    def number_of_stones(self, current_state, turn):
        opponent = self.opp_side(turn)
        turn_stones = np.sum(current_state == turn)
        opponent_stones = np.sum(current_state == opponent)
        return turn_stones, opponent_stones

    def number_of_liberties(self, current_state, turn):

        liberties = set()
        for i in range(grid_size):
            for j in range(grid_size):
                if current_state[i][j] == turn:
                    for direction in DIRECTIONS:
                        new_x, new_y = i + direction[0], j + direction[1]
                        if 0 <= new_x < grid_size and 0 <= new_y < grid_size:
                            if current_state[new_x][new_y] == 0:
                                liberties.add((new_x, new_y))

        return len(liberties)

    def edge_center(self, current_state, turn):
        opponent = self.opp_side(turn)
        turn_edge = 0
        opponent_edge = 0
        turn_center = 0
        opponent_center = 0
        unoccupied = 0
        for i in range(grid_size):
            for j in range(grid_size):
                if (i == 0 or i == grid_size - 1 or j == 0 or j == grid_size - 1):
                    if current_state[i][j] == turn:
                        turn_edge += 1
                    elif current_state[i][j] == opponent:
                        opponent_edge += 1
                else:
                    if current_state[i][j] == turn:
                        turn_center += 1
                    elif current_state[i][j] == opponent:
                        opponent_center += 1
                    else:
                        unoccupied += 1
        return turn_edge,turn_center, opponent_edge, opponent_center,unoccupied

    def territory(self,current_state, turn):
        visited = set()
        turn_territory = 0
        opponent_territory = 0
        opponent = self.opp_side(turn)

        def dfs(x,y):
            queue = deque([(x,y)])
            region = set()
            controller = set()
            visited.add((x,y))

            while queue:
                x, y = queue.popleft()
                region.add((x,y))
                for direction in DIRECTIONS:
                    new_x, new_y = x + direction[0], y + direction[1]
                    if 0 <= new_x < grid_size and 0 <= new_y < grid_size:
                        if (new_x, new_y) not in visited:
                            if current_state[new_x][new_y] == 0:
                                queue.append((new_x, new_y))
                                visited.add((new_x, new_y))
                            if current_state[new_x][new_y] != 0:
                                controller.add(current_state[new_x][new_y])
            return region, controller

        for i in range(grid_size):
            for j in range(grid_size):
                if (i,j) not in visited and current_state[i][j] == 0:
                    region, controller = dfs(i,j)

                    if len(controller) == 1:
                        stone = next(iter(controller))
                        if stone == turn:
                            turn_territory += len(region)
                        elif stone == opponent:
                            opponent_territory += len(region)
        return turn_territory, opponent_territory

    def influence(self, current_state, turn,move):
        empty_board = np.zeros((grid_size, grid_size), dtype=int)
        new_state,_ = self.make_move(copy.deepcopy(current_state), turn, move)
        for i in range(grid_size):
            for j in range(grid_size):
                if new_state[i][j] == turn:
                    for direction in DIRECTIONS:
                        for k in range(1,4):
                            new_x, new_y = i + k * direction[0], j + k * direction[1]
                            if 0 <= new_x < grid_size and 0 <= new_y < grid_size:
                                if new_state[new_x][new_y] == turn:
                                    empty_board[new_x][new_y] += 1 / k
        influence = np.sum(empty_board)
        return influence

    def influence(self, current_state, turn,move):
        empty_board = np.zeros((grid_size, grid_size), dtype=int)
        new_state,_ = self.make_move(copy.deepcopy(current_state), turn, move)
        for i in range(grid_size):
            for j in range(grid_size):
                if new_state[i][j] == turn:
                    for direction in DIRECTIONS:
                        for k in range(1,4):
                            new_x, new_y = i + k * direction[0], j + k * direction[1]
                            if 0 <= new_x < grid_size and 0 <= new_y < grid_size:
                                if new_state[new_x][new_y] == turn:
                                    empty_board[new_x][new_y] += 1 / k
        influence = np.sum(empty_board)
        return influence

    def shape_analysis(self, current_state, turn):
        score = 0
        opponent = self.opp_side(turn)
        for i in range(grid_size):
            for j in range(grid_size):
                if self.tiger(i,j,current_state,turn):
                    score += 4
                elif self.bamboo(i, j,current_state,turn):
                    score += 3
                elif self.eye(i, j,current_state,turn):
                    score += 6
                elif self.table_shape(i, j,current_state,turn):
                    score += 5
                elif self.triangle(i, j,current_state,turn):
                    score -=2

                for direction in DIRECTIONS:
                    new_x, new_y = i + direction[0], j + direction[1]
                    if 0 <= new_x < grid_size and 0 <= new_y < grid_size:
                        if current_state[new_x][new_y] == opponent:
                            score -= 1
        return score

    def tiger(self,x,y,current_state,turn):
        if x >= grid_size - 1 or y >= grid_size - 1:
            return False

        if (current_state[x][y] == turn and current_state[x + 1][y] == 0 and
         current_state[x][y + 1] == 0 and  current_state[x + 1][y + 1] == turn) or (
        current_state[x][y] == 0 and current_state[x + 1][y] == turn and
        current_state[x][y + 1] == turn and current_state[x + 1][y + 1] == 0):
            return True
        else:
            return False

    def bamboo(self,x,y,current_state,turn):
        if x >= grid_size - 1 or y >= grid_size - 1:
            return False

        if (current_state[x][y] == turn and current_state[x + 1][y + 1] == turn and
            current_state[x][y + 1] == 0 and current_state[x + 1][y] == 0):
            return True
        else:
            return False

    def eye(self,x,y,current_state,turn):
        if current_state[x][y] != 0:
            return False

        opponent = self.opp_side(turn)
        opp_counter = 0
        friendly_counter = 0

        for direction in DIRECTIONS:
            new_x, new_y = x + direction[0], y + direction[1]
            if 0 <= new_x < grid_size and 0 <= new_y < grid_size:
                if current_state[new_x][new_y] == turn:
                    friendly_counter += 1
        diagonals = [(-1,-1),(1,-1),(-1,1),(1,1)]
        for diagonal in diagonals:
            new_x, new_y = x + diagonal[0], y + diagonal[1]
            if 0 <= new_x < grid_size and 0 <= new_y < grid_size:
                if current_state[new_x][new_y] == opponent:
                    opp_counter += 1


        if friendly_counter == 4:
            return True
        elif friendly_counter == 3 and (x == 0 or x == grid_size - 1 or y == 0 or y == grid_size - 1):
            return True
        elif friendly_counter == 2 and (x == grid_size - 1) and (y == 0 or y == grid_size - 1) and opp_counter == 0:
            return True
        elif opp_counter >= 2:
            return False
        return False

    def table_shape(self,x,y,current_state,turn):
        if x < 1 or  x >= grid_size - 2 or y < 1 or y >= grid_size - 2:
            return False

        if (current_state[x][y] == turn and current_state[x][y + 2] == turn and
        current_state[x + 1][y + 1] == turn and current_state[x + 2][y] == turn and
        current_state[x + 2][y + 2] == turn):
            return True
        else:
            return False

    def triangle(self,x,y,current_state,turn):
        if x >= grid_size - 1 or y >= grid_size - 1:
            return False

        if (current_state[x][y] == turn and current_state[x + 1][y + 1] == 0
            and current_state[x][y + 1] == turn and current_state[x + 1][y] == 0):
            return True
        else:
            return False

    def evaluation_func(self, current_state, turn,prev_move):

        opponent = self.opp_side(turn)
        turn_stones, opponent_stones = self.number_of_stones(current_state, turn)
        turn_liberties = self.number_of_liberties(current_state, turn)
        opponent_liberties = self.number_of_liberties(current_state, opponent)
        edge_stones, center_stones, opponent_edge_stones, opponent_center_stones, center_unoccupied = self.edge_center(current_state, turn)
        eulerNo = self.euler(current_state, turn)
        turn_area, opponent_area = self.territory(current_state, turn)
        influence = self.influence(current_state, turn,prev_move)

        shape_score = self.shape_analysis(current_state, turn)

        evaluation = (
            (7 * (turn_stones + turn_area) - 5 * (opponent_stones)) +
            (min(max(turn_liberties - opponent_liberties,-3),3)) +
            (4* influence) +
            (5 * eulerNo) +
            (3* shape_score) -
            (5 * edge_stones * (center_unoccupied / max(1,center_stones)))
        )

        return evaluation

    def euler(self,current_state,turn):
        opponent = self.opp_side(turn)
        copy_of_current_state = copy.deepcopy(current_state)

        e1,e2,e3 = 0,0,0
        e1_opp,e2_opp,e3_opp = 0,0,0
        for i in range(grid_size -1):
            for j in range(grid_size - 1):
                subpart = copy_of_current_state[i:i+2,j:j+2]
                e1 += self.e1_calc(subpart,turn)
                e2 += self.e2_calc(subpart,turn)
                e3 += self.e3_calc(subpart,turn)
                e1_opp = self.e1_calc(subpart,opponent)
                e2_opp = self.e2_calc(subpart,opponent)
                e3_opp = self.e3_calc(subpart,opponent)

        res = (e1 - e3 + 2 * e2 - (e1_opp - e3_opp + 2 * e2_opp)) / 4
        return res

    def e1_calc(self,subpart,turn):
        boolVal = (subpart[0][0] == turn and subpart[0][1] != turn and subpart[1][0] != turn and subpart[1][1] != turn) or (
                subpart[0][0] != turn and subpart[0][1] == turn and subpart[1][0] != turn and subpart[1][1] != turn
        ) or (subpart[0][0] != turn and subpart[0][1] != turn and subpart[1][0] == turn and subpart[1][1] != turn) or (
                subpart[0][0] != turn and subpart[0][1] != turn and subpart[1][0] != turn and subpart[1][1] == turn
        )
        if boolVal:
            return 1
        else:
            return 0

    def e2_calc(self,subpart,turn):
        boolVal = (subpart[0][0] == turn and subpart[0][1] != turn and subpart[1][0] != turn and subpart[1][1] == turn) or (
                subpart[0][0] != turn and subpart[0][1] == turn and subpart[1][0] == turn and subpart[1][1] != turn
        )
        if boolVal:
            return 1
        else:
            return 0

    def e3_calc(self,subpart,turn):
        boolVal = (subpart[0][0] != turn and subpart[0][1] == turn and subpart[1][0] == turn and subpart[1][1] == turn) or (
                subpart[0][0] == turn and subpart[0][1] != turn and subpart[1][0] == turn and subpart[1][1] == turn
        ) or (subpart[0][0] == turn and subpart[0][1] == turn and subpart[1][0] != turn and subpart[1][1] == turn) or (
                subpart[0][0] == turn and subpart[0][1] == turn and subpart[1][0] == turn and subpart[1][1] != turn
        )
        if boolVal:
            return 1
        else:
            return 0


    def minimax(self, current_state, turn, step_number, depth, target_depth, branching_factor, isMaximizing, prev_move,
                secondPass, alpha, beta):

        Key = (tuple(map(tuple, current_state)),depth,isMaximizing)

        if Key in hashMap:
            return hashMap[Key]

        # Base cases
        if depth == target_depth or step_number >= 2 * grid_size * grid_size or secondPass:
            return None, self.evaluation_func(current_state, turn,prev_move)

        valid_moves = self.legal_moves(current_state, turn)
        valid_moves = self.ordered_moves(current_state,turn,valid_moves)


        if prev_move == (-1, -1) and valid_moves[0] == (-1,-1):
            secondPass = True
        opponent = self.opp_side(turn)
        if isMaximizing:

            max_value = float('-inf')
            bestMove = (-1, -1)
            for move in valid_moves[:branching_factor]:

                copy_of_current_state,cap_count = self.make_move(current_state, turn, move)
                if np.array_equal(copy_of_current_state, current_state):
                    continue
                _, max_eval = self.minimax(
                    copy_of_current_state, opponent,
                    step_number + 1, depth + 1, target_depth, branching_factor,
                    False, move, secondPass,
                    alpha, beta
                )
                max_eval += 2 * cap_count

                if max_eval > max_value:
                    max_value = max_eval
                    bestMove = move

                alpha = max(max_value, alpha)
                if alpha >= beta:
                    break
            hashMap[Key] = bestMove,max_value
            return bestMove, max_value
        else:
            min_value = float('inf')
            bestMove = (-1, -1)
            for move in valid_moves[:branching_factor]:

                copy_of_current_state,cap_count = self.make_move(current_state, opponent, move)
                if np.array_equal(copy_of_current_state, current_state):
                    continue
                best_min, min_eval = self.minimax(
                    copy_of_current_state, turn,
                    step_number + 1, depth + 1, target_depth, branching_factor,
                    True, move, secondPass,
                    alpha, beta
                )

                min_eval += 2 * cap_count
                if min_eval < min_value:
                    min_value = min_eval
                    bestMove = move

                beta = min(min_value, beta)
                if alpha >= beta:
                    break
            hashMap[Key] = bestMove, min_value
            return bestMove, min_value



# Read the input file
def read_file(input_file=INPUT_FILE_NAME):
    with open(input_file) as f:
        input_data = [file_line.strip() for file_line in f.readlines()]
        players_turn = int(input_data[0])
        prev_game_state = np.zeros((5, 5), int)
        curr_game_state = np.zeros((5, 5), int)

        # Previous state
        for i in range(1, 6):
            for j in range(len(input_data[i])):
                prev_game_state[i - 1][j] = int(input_data[i][j])

        # Current State
        for i in range(6, 11):
            for j in range(len(input_data[i])):
                curr_game_state[i - 6][j] = int(input_data[i][j])
        return players_turn, prev_game_state, curr_game_state


def write_file(output, best_move):
    try:
        with open(output, 'x') as f:
            if best_move == (-1, -1):
                f.write("PASS")
            else:
                f.write(f'{best_move[0]},{best_move[1]}')
    except FileExistsError:
        with open(output, 'w') as f:
            if best_move == (-1, -1):
                f.write("PASS")
            else:
                f.write(f'{best_move[0]},{best_move[1]}')


def step_calculator(prev_game_state, curr_game_state):
    prev_empty = True  # If this is true --> prev board is empty
    curr_empty = True  # If this is true --> curr board is empty

    # Check if previous game state is empty
    for i in range(len(prev_game_state)):
        if not prev_empty: break
        for j in range(len(prev_game_state[i])):
            if prev_game_state[i][j] != 0:
                prev_empty = False
                break

    # Check if current game state is empty
    for i in range(len(curr_game_state)):
        if not curr_empty: break
        for j in range(len(curr_game_state[i])):
            if curr_game_state[i][j] != 0:
                curr_empty = False
                break

    if prev_empty and curr_empty:
        step_number = 0
    elif prev_empty and not curr_empty:
        step_number = 1
    else:
        # If step files does not exist or is empty
        if not os.path.exists(STEP_FILE) or os.path.getsize(STEP_FILE) == 0:
            step_number = 2
        else:
            with open(STEP_FILE) as step_file:
                step_number = int(step_file.readline())
                step_number += 2

    with open(STEP_FILE, 'w') as step_file:
        step_file.write(f'{step_number}')
    return step_number


if __name__ == '__main__':

    turn, prev_state, curr_state = read_file()
    step_number = step_calculator(prev_state, curr_state)
    my_player = Go_agent(turn, prev_state, curr_state)

    alpha = -float('inf')
    beta = float('inf')


    # if step_number < 10:
    #     target_depth = 3
    # elif step_number < 20:
    #     target_depth = 4
    # else:
    #     target_depth = 5
    target_depth = 4
    branching_factor = 20
    Play, _ = my_player.minimax(curr_state, turn,
                                step_number, 0, target_depth, branching_factor,
                                True, None, False,
                                alpha, beta)

    write_file('output.txt', Play)
