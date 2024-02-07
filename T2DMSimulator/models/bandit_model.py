from contextualbandits.online import Bay
import random
from T2DMSimulator.models.bayesian_ts import BayesianTS

class CompliantBandit:
    def __init__(self, num_actions, seed=123,  n_samples=20, n_iter=2000):
        self.reward_model = BayesianTS(num_actions, n_samples=n_samples, n_iter=n_iter)
        self.compliance_model = BayesianTS(num_actions, n_samples=n_samples, n_iter=n_iter)
        self.num_actions = num_actions

    def train(self, context, action_taken, reward, cost, probability, action_recommended):
        # Train the reward model
        reward_example = self.format_example(context, action_taken, -reward, probability)
        self.reward_model.fit()
        self.vw_reward.learn_one(reward_example)
        
        # Train the compliance model based on action recommended and taken
        compliance_cost = 0 if action_taken == action_recommended else 1
        compliance_example = self.format_example(context, action_recommended, -compliance_cost, probability)
        self.vw_compliance.learn_one(compliance_example)

    def predict(self, context):
        # Predict reward
        reward_example = self.format_example(context)
        reward_predictions = self.vw_reward.predict_one(reward_example)
        
        # Predict compliance
        compliance_example = self.format_example(context)
        compliance_predictions = self.vw_compliance.predict_one(compliance_example)

        # Combine predictions (CompTS approach)
        combined_scores = [r * c for r, c in zip(reward_predictions, compliance_predictions)]
        chosen_action = combined_scores.index(max(combined_scores)) + 1
        return chosen_action

    def format_example(self, context, action=None, cost=None, probability=None, compliance=None):
        examples = []
        if action is not None:
            # Learning example
            for i in range(1, self.num_actions + 1):
                action_str = f" | :{i}" if i != action else f"0:{cost}:{probability} | :{i}"
                examples.append(f"shared | {context} {action_str}")
        else:
            # Prediction example
            for i in range(1, self.num_actions + 1):
                examples.append(f" | :{i}")
        return examples