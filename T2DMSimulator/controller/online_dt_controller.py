from .base import Controller
from .base import Action
from onlineDt.main import Experiment
from gym.envs.registration import register

class OnlineDTController(Controller):
    def __init__(self, seed=3):
        self.seed = seed
        register(
            id='T2DSimGym-v0',
            entry_point="T2DMSimulator.simulation.env.T2DSimEnv:T2DSimEnv"
        )
        decision_transformer_config = {
            "seed": 10,
            "env": "T2DSimGym-v0",
            "K": 20,
            "embed_dim": 512,
            "n_layer": 4,
            "n_head": 4,
            "activation_function": "relu",
            "dropout": 0.1,
            "eval_context_length": 5,
            "ordering": 0,
            "eval_rtg": 3600,
            "num_eval_episodes": 10,
            "init_temperature": 0.1,
            "batch_size": 256,
            "learning_rate": 1e-4,
            "weight_decay": 5e-4,
            "warmup_steps": 10000,
            "max_pretrain_iters": 1,
            "num_updates_per_pretrain_iter": 5000,
            "max_online_iters": 1500,
            "online_rtg": 7200,
            "num_online_rollouts": 1,
            "replay_size": 1000,
            "num_updates_per_online_iter": 300,
            "eval_interval": 10,
            "device": "cuda",
            "log_to_tb": True,
            "save_dir": "./exp",
            "exp_name": "default"}
        self.experiment = Experiment(decision_transformer_config)
        self.experiment.pretrain()

    def policy(self, observation, reward, done, **info):

        return action
    
    def reset(self):
        '''
        Reset the controller state to inital state, must be implemented
        '''
        raise NotImplementedError