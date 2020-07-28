from AbstractPlayer import AbstractPlayer
from Types import *

from planning.Translator import Translator
from planning.Planning import Planning

from utils.Types import LEARNING_SSO_TYPE
from planning.parser import Parser

import subprocess
import random
import pickle
import sys


class Agent(AbstractPlayer):

    def __init__(self):
        """
        Agent constructor
        Creates a new agent and sets SSO type to JSON
        """
        AbstractPlayer.__init__(self)
        self.lastSsoType = LEARNING_SSO_TYPE.JSON

        self.config_file = "config/ice-and-fire.yaml"
        self.planning = Planning(self.config_file)


    def init(self, sso, elapsedTimer):
        """
        * Public method to be called at the start of every level of a game.
        * Perform any level-entry initialization here.
        * @param sso Phase Observation of the current game.
        * @param elapsedTimer Timer, which is 1s by default. Modified to 1000s.
                              Check utils/CompetitionParameters.py for more info.
        """
        self.translator = Translator(sso, self.config_file)


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

        plan = self.search_plan(sso, 14, 1, ["(has-ice-boots)", "(has-fire-boots)"])
        
        return 'ACTION_NIL'


    def search_plan(self, sso, x_goal, y_goal, other_predicates):
        """
        Method used to search a plan to a goal.

        @param sso State observation.
        @param x_goal X-axis coordinate of the goal to be reached.
        @param y_goal Y-axis coordinate of the goal to be reached.
        @param other_predicates List of predicates to be appended to the ones
                                of the current state.
        @return Returns a plan to the current goal.
        """
        pddl_predicates, pddl_objects = self.translator.translate_game_state_to_PDDL(sso, other_predicates)
        goal_predicate = self.translator.generate_goal_predicate(x_goal, y_goal)

        self.planning.generate_problem_file(pddl_predicates, pddl_objects, goal_predicate)
        planner_output = self.planning.call_planner()

        plan = self.translator.translate_planner_output(planner_output)

        return plan





