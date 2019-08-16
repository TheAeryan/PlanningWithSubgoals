from AbstractPlayer import AbstractPlayer
from Types import *

from utils.Types import LEARNING_SSO_TYPE
from planning.parser import Parser

import subprocess
import random
import numpy as np

from LearningModel import CNN

class Agent(AbstractPlayer):
    NUM_GEMS_FOR_EXIT = 9
    DESC_FILE = 'planning/problem.txt'
    OUT_FILE = 'planning/plan.txt'

    def __init__(self):
        """
        Agent constructor
        Creates a new agent and sets SSO type to JSON
        """
        AbstractPlayer.__init__(self)
        self.lastSsoType = LEARNING_SSO_TYPE.JSON

        # Attributes that store agents experience:
        # - X -> inputs of the learning model
        # - Y -> correct output values (plans lengths)

        self.X = [] # Shape = (-1, 13, 26, 9)
        self.Y = [] # Shape = (-1)

        # Variable to check if the dataset has already been saved
        self.already_saved = False

        self.current_level = 0 # Level playing right now

        # Set parser
        self.parser = Parser('planning/domain.pddl', 'planning/problem.pddl',
                self.DESC_FILE, self.OUT_FILE)

        # Create Learning Model
        self.model = CNN(writer_name="start_size=0, alfa=0.002, num_rep=4", learning_rate = 0.002)

        # Iteration of current scalar summary. Needed to store the logs and plot the losses
        self.log_it = 0

        # Load Validation Dataset in order to see validation loss change with tensorboard
        # as training progresses
        test_dataset = np.load("../../../../datasets/dataset_test.npz") 
        self.test_dataset_x = test_dataset['X']
        test_dataset_y = test_dataset['Y']
        self.test_dataset_y_resh = np.reshape(test_dataset_y, (-1, 1)) 

        # Variable that stores if the agent is exploring or exploiting:
        # True -> subgoals are chosen randomly to gather experience (exploration)
        # False -> subgoals are chosen using the model to achieve the best
        #          possible results (exploitation)
        self.is_training = True


    def init(self, sso, elapsedTimer):
        """
        * Public method to be called at the start of every level of a game.
        * Perform any level-entry initialization here.
        * @param sso Phase Observation of the current game.
        * @param elapsedTimer Timer, which is 1s by default. Modified to 1000s.
                              Check utils/CompetitionParameters.py for more info.
        """
        # Set first turn as True
        self.first_turn = True

        # Create new empty action list
        # This action list corresponds to the plan found by the planner
        self.action_list = []

        # It is true when the agent has the minimum required number of gems
        self.can_exit = False


        """
        gems = self.get_gems_positions(sso)
        chosen_gem = gems[random.randint(0, len(gems) - 1)]
        one_hot_grid = self.encode_game_state(sso.observationGrid, chosen_gem)

        prediction = self.model.predict(one_hot_grid) # Shape = (1,1)

        print("PREDICTION\n\n", prediction)
        """

    
    def act(self, sso, elapsedTimer):
        """
        Method used to determine the next move to be performed by the agent.
        This method can be used to identify the current state of the game and all
        relevant details, then to choose the desired course of action.
        
        @param sso Observation of the current state of the game to be used in deciding
                   the next action to be taken by the agent.
        @param elapsedTimer Timer, which is 40ms by default. Modified to 500s.
                            Check utils/CompetitionParameters.py for more info.
        @return The action to be performed by the agent.
        """

        """grid  = sso.observationGrid

        print(grid[4][1][0].itype)""" # [x][y][elem_pos]


        """
        all_elems = set() # 6 different itypes, without counting empty tiles, bats and scorpions
                          # one-hot encoding -> length of 8 (empty tiles are not encoded as such)

        grid = sso.observationGrid

        for a in grid:
            for b in a:
                for c in b:
                    if c is not None:
                        this_itype = c.itype

                        if this_itype not in all_elems:
                            all_elems.add(this_itype)
        

        print(all_elems)
        print("\n")"""

        """encoded_grid = self.encode_game_state(sso.observationGrid, (0,0))

        print(encoded_grid.shape)

        print("\n\n\n")"""

        # If the plan is emtpy, get a new one
        if len(self.action_list) == 0:
            # Set level description and output file names
            out_description = 'MyAgent/problem.txt'
            output_file = 'MyAgent/out.txt'

            # If the agent already has 11 gems, he plans to exit the level
            keys = sso.avatarResources.keys()

            if len(keys) > 0: # He has at least one gem
                # gem_key = keys[0] # Python 2
                gem_key = list(sso.avatarResources)[0] # Python 3

                num_gems = sso.avatarResources[gem_key]

                if num_gems >= self.NUM_GEMS_FOR_EXIT:
                    # Plan to exit the level
                    self.can_exit = True

                    exit = sso.portalsPositions[0][0]
                    exit_pos = (int(exit.position.x // sso.blockSize), int(exit.position.y // sso.blockSize))

                    # Save current observation for dataset
                    one_hot_grid = self.encode_game_state(sso.observationGrid, exit_pos)
 
                    self.action_list = self.search_plan(sso, exit_pos)

                    # Save plan length as current metric
                    plan_metric = len(self.action_list)

                    self.X.append(one_hot_grid.tolist()) # tolist() to transform from numpy array to normal python array
                    self.Y.append(plan_metric)

            # Only plan for next gem if it is needed
            if not self.can_exit:
                # Obtain gems positions
                gems = self.get_gems_positions(sso)
                
                # <Choose next subgoal>

                if self.is_training: # Choose a random gem if the agent is training
                    chosen_gem = gems[random.randint(0, len(gems) - 1)] # Choose a random gem as next objective
                else: # Choose best gem if the agent is on validation time
                    chosen_gem = self.choose_next_subgoal(sso.observationGrid, gems)

                # Avoid error of picking a gem which is at the agent's position
                while (chosen_gem[0] == int(sso.avatarPosition[0] // sso.blockSize) and
                       chosen_gem[1] == int(sso.avatarPosition[1] // sso.blockSize)):
                    chosen_gem = gems[random.randint(0, len(gems) - 1)]

                # Save current observation for dataset
                one_hot_grid = self.encode_game_state(sso.observationGrid, chosen_gem)

                # Search for a plan to chosen_gem
                self.action_list = self.search_plan(sso, chosen_gem)

                # Save plan length as current metric
                plan_metric = len(self.action_list)
                
                # <Append sample to dataset>
                self.X.append(one_hot_grid.tolist())
                self.Y.append(plan_metric)

                """
                # Obtain a plan to every possible gem to collect data for training the model
                for gem in gems:
                    if ((gem[0] != int(sso.avatarPosition[0] // sso.blockSize) or
                       gem[1] != int(sso.avatarPosition[1] // sso.blockSize)) and 
                       gem != chosen_gem):
                        
                        # Save current observation for dataset
                        one_hot_grid = self.encode_game_state(sso.observationGrid, gem)

                        # Search for a plan
                        this_plan = self.search_plan(sso, gem)

                        # Save plan length as current metric
                        plan_metric = len(this_plan)
                        
                        self.X.append(one_hot_grid.tolist())
                        self.Y.append(plan_metric)
                """        

            # --- Train the model ---

            num_samples = len(self.X)

            batch_size = 16
            start_size = 16 # Min number of samples to start training the model
            num_rep = 4

            if num_samples >= start_size:
                # Execute num_rep iterations of learning. Each one with a different batch
                for _ in range(num_rep):
                    # Randomly choose sample
                    bottom_ind = random.randint(0, num_samples - batch_size + 1)
                    top_ind = bottom_ind + batch_size

                    batch_x = np.array(self.X[bottom_ind:top_ind])
                    batch_y = self.Y[bottom_ind:top_ind]
                    batch_y = np.reshape(batch_y, (-1, 1))

                    # Execute one training step
                    self.model.train(batch_x, batch_y)

                # Save Logs
                self.model.save_logs(batch_x, batch_y, self.test_dataset_x, self.test_dataset_y_resh, self.log_it)
                self.log_it += 1

                print("\n\nDATASET SIZE = {}\n\n".format(len(self.X)))


        # If a plan has been found, return the first action
        if len(self.action_list) > 0:
            return self.action_list.pop(0)
        else:
            return 'ACTION_NIL'


    def get_gems_positions(self, sso):
        # Retrieve gems from current state observation
        gems = sso.resourcesPositions[0] 
        pos = []

        for gem in gems:
            gem_x = int(gem.position.x // sso.blockSize) # Convert from pixel to grid positions
            gem_y = int(gem.position.y // sso.blockSize)

            pos.append((gem_x, gem_y))

        return pos

    def encode_game_state(self, obs_grid, goal_pos):
        """
        Transforms the game state (sso) from a matrix of observations to a matrix in which each
        position is one-hot encoded. If there are more than one observations at the same position,
        both are encoded. If there are no observations at a position, the resulting encoding
        is an array full of zeroes

        @param obs_grid Matrix of observations
        @param goal_pos (x, y) position (not as pixels but as grid) of the selected goal  
        """

        # 0, 1, 4, 5, 6, 7, 10, 11

        # Dictionary that maps itype (key) to one-hot array position to write a 1
        # e.g. 4 : 2 = [0 0 1 0 0 0 0 0 0]
        # None (empty tiles) objects are assigned an array full of zeroes
        encode_dict = {
            0 : 0,
            1 : 1,
            4 : 2,
            5 : 3,
            6 : 4,
            7 : 5,
            10 : 6,
            11 : 7
        }

        num_cols = len(obs_grid)
        num_rows = len(obs_grid[0])

        one_hot_length = 8 + 1 # 1 extra position to represent the objective (the last 1)

        # The image representation is by rows and columns, instead of (x, y) pos of each pixel
        # Row -> y
        # Col -> x
        one_hot_grid = np.zeros((num_rows, num_cols, one_hot_length), np.int8)

        # Encode the grid
        for x in range(num_cols):
            for y in range(num_rows):
                for obs in obs_grid[x][y]:
                    if obs is not None and obs.itype != 3: # Ignore Empty Tiles and pickage images (those that correspond to ACTION_USE)
                        this_pos = encode_dict[obs.itype]
                        one_hot_grid[y][x][this_pos] = 1

        # Encode the goal position within that grid
        one_hot_grid[goal_pos[1]][goal_pos[0]][one_hot_length-1] = 1

        return one_hot_grid

    def choose_next_subgoal(self, obs_grid, possible_subgoals):
        """
        Uses the learnt model to choose the best subgoal to plan for among all the
        possible subgoals, from the current state of the game.
        The chosen subgoal is the subgoal in "possible_subgoals" which has the smallest
        predicted value by the network.

        @param obs_grid Matrix of observations representing the current state of the game
        @param possible_subgoals List of possible subgoals to choose from. Each element
                                 corresponds to a (pos_x, pos_y) pair.
        """

        best_plan_length = 1000000.0
        best_subgoal = (-1, -1)

        for curr_subgoal in possible_subgoals:
            # Encode input for the network using current state and curr_subgoal
            one_hot_matrix = self.encode_game_state(obs_grid, curr_subgoal)

            # Use the model to predict plan length for curr_subgoal
            plan_length = self.model.predict(one_hot_matrix)

            # See if this is the best plan up to this point
            if plan_length < best_plan_length:
                best_plan_length = plan_length
                best_subgoal = curr_subgoal

        return best_subgoal


    def search_plan(self, sso, goal):
        """
        Method used to search for a plan given a description. Writes the resulting
        plan in the output file.

        Change: now returns the plan instead of assigning it to self.action_list

        @param sso State observation.
        @param goal Goal position to be reached. It's given as a (x, y) tuple.        
        """

        action_list = []

        # Parse the current game state
        self.parse_game_state(sso, goal)

        # Call the parser/planner
        self.parser.plan_and_parse()

        # Process the output file to get the plan
        with open(self.OUT_FILE) as plan:
            for action in plan:
                # Remove the \n character at the end and add actions to list
                action_list.append(action.replace('\n', ''))

        return action_list


    def parse_game_state(self, sso, goal):
        """
        Method used to parse a game state. Writes the output in a file to be later
        processed.

        @param sso State observation.
        @param goal Goal position to be reached. It's given as a (x, y) tuple.
        """
        # Get player orientation and parse it
        orientation = sso.avatarOrientation

        if orientation[0] == 1.0:
            orientation_str = 'ORIENTATION:right\n'
        elif orientation[0] == -1.0:
            orientation_str = 'ORIENTATION:left\n'
        elif orientation[1] == 1.0:
            orientation_str = 'ORIENTATION:down\n'
        elif orientation[1] == -1.0:
            orientation_str = 'ORIENTATION:up\n'

        # Get maximum number of rows and columns
        X_MAX = sso.observationGridNum
        Y_MAX = sso.observationGridMaxRow

        # Create a new empty game map
        game_map = []

        # Parse the State observation
        for y in range(Y_MAX):
            # Create new empty row to be written
            row = ''

            for x in range(X_MAX):
                # Get observation
                obs = sso.observationGrid[x][y][0]

                # Process the observation and append it to the row
                if obs == None:
                    row += '-'
                elif obs.itype == 0:
                    row += 'w'
                elif obs.itype == 1:
                    row += 'A'
                elif obs.itype == 4:
                    row += '.'
                elif obs.itype == 5:
                    row += 'e'
                    
                    if (x, y) == goal:
                        goal_str = 'EXIT-LEVEL\n'
                elif obs.itype == 6:
                    row += 'x'
                    
                    if (x, y) == goal:
                        goal_str = 'GET-GEM:{},{}\n'.format(x, y)
                elif obs.itype == 7:
                    row += 'o'
                elif obs.itype == 10:
                    row += 'c'
                elif obs.itype == 11:
                    row += 'b'

            # Add a new line character and add the row to the map
            row += '\n'
            game_map.append(row)


        # Write output in the file
        with open(self.DESC_FILE, 'w') as desc:
            desc.write(orientation_str)
            desc.write(goal_str)
            
            for line in game_map:
                desc.write(line)

        pass

    def result(self, sso, elapsedTimer):
        print("Nivel terminado")

        # Save dataset if it contains at least min_elem elements

        """
        min_elem = 5000
        file_name = 'dataset_train_3.npz'

        dataset_X = np.array(self.X, dtype=np.bool)
        dataset_Y = np.array(self.Y, dtype=np.int32)

        if not self.already_saved and len(self.Y) >= min_elem:
            print("\n\n<<<GUARDANDO DATASET>>>\n\n")

            np.savez(file_name, X=dataset_X, Y=dataset_Y)

            self.already_saved = True # Don't save again
        """
        
        #return random.randint(0, 2)

        # Play levels 0-2 in order
        self.current_level = (self.current_level + 1) % 3

        return self.current_level


