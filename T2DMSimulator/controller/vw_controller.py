import vowpal_wabbit_next as vw
import random
from .base import Controller
from .base import Action
# Define the action namedtuple as per the provided base class

class VWController(Controller):
    def __init__(self, init_state):
        super(VWController, self).__init__(init_state)
        # Initialize Vowpal Wabbit for contextual bandit learning
        self.vw = vw.Workspace('--cb_explore_adf --epsilon 0.2')
        self.meals_recommended_today = 0

    def policy(self, observation, reward, done, **info):
        context = self.create_context(observation)
        action = self.select_action(context)
        
        if action is not None:
            return action
        else:
            # Return a default action if no action is selected
            return Action(basal=0, bolus=0, meal=0, metformin=0, physical=0)

    def create_context(self, observation):
        # Create a context for the bandit based on the observation
        # This is a placeholder implementation
        cgm_value = observation.CGM
        return f'|cgm_value {cgm_value}'

    def select_action(self, context):
        # Convert context to VW's example format
        vw_example = self.vw.parse(context, labelType=vw.pyvw.vw.lContextualBandit)

        # Use Vowpal Wabbit to select an action
        self.vw.learn(vw_example)
        chosen_action = vw_example.get_action_scores()
        vw_example.finish()  #
        return chosen_action
