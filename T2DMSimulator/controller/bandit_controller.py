import numpy as np
from collections import namedtuple
from T2DMSimulator.models.bandit_model import CompliantBandit
# Define the action structure
Action = namedtuple('ControllerAction', ['meal', 'metformin', 'physical', 'time', 'times'])

class BanditController(object):
    def __init__(self, bandit_model, constraints, seed,transformer_model = None):
        self.bandit_model: CompliantBandit = bandit_model
        self.transformer_model = transformer_model
        self.constraints = constraints
        self.state = None
        np.random.seed(seed)

    def policy(self, observation, reward, done, **info):
        # Contextual bandit for immediate action
        immediate_action = self.bandit_model.predict(observation)

        # Decision transformer for long-term strategy
        long_term_action = self.transformer_model.predict(observation)

        # Combine and adjust actions based on constraints
        action = self._combine_and_adjust_actions(immediate_action, long_term_action)
        return action

    def _combine_and_adjust_actions(self, immediate_action, long_term_action):
        # Logic to combine actions - this is a simplified example
        combined_action = self._simple_combine(immediate_action, long_term_action)

        # Adjust the combined action to meet the constraints
        adjusted_action = self._apply_constraints(combined_action)
        return adjusted_action

    def _simple_combine(self, immediate_action, long_term_action):
        # Combine immediate and long-term actions
        # This method should be modified based on how you want to combine these actions
        # Example: averaging, prioritizing one over the other, etc.
        combined_action = ...  # Implement your logic here
        return combined_action

    def _apply_constraints(self, action):
        # Implement constraint logic
        # Ensure that actions such as meal, metformin dosage, and physical activity are within the defined constraints
        # This could involve clipping values, redistributing quantities, etc.
        constrained_action = ...  # Implement your logic here
        return constrained_action

    def reset(self):
        self.state = None