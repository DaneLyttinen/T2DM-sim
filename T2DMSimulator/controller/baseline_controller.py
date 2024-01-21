from collections import namedtuple
import numpy as np
from .base import Controller
from .base import Action
from statsmodels.tsa.statespace.sarimax import SARIMAX
import copy
import statsmodels.api as sm

class BaselineController(Controller):
    def __init__(self):
        self.meal_count = 0
        self.physical_activity_done = False
        self.total_daily_cho = 0  
        self.model = None
        self.all_gl_data = []
        self.last_meal_index = 0
        self.daily_averages = []
        self.max_metformin = 0
        self.administered_metformin = 0
        self.fitted_model = None

    def policy(self, observation, reward, done, **info):
        # Predict future glucose level
        if len(self.all_gl_data) <= 80:
            self.all_gl_data.append(observation.CGM)
            predicted_glucose = [observation.CGM]
        else:
            if self.model == None:
                self.model = SARIMAX(endog=self.all_gl_data,order=(4,0,0),enforce_stationarity=False)
                self.fitted_model = self.model.fit(disp=False)
            predicted_glucose = self.predict_glucose(observation.CGM)

        if len(self.all_gl_data) % 1440 == 0:
            self.meal_count = 0
            self.administered_metformin = 0
            daily_avg = np.mean(self.all_gl_data[-1440:])
            self.daily_averages.append(daily_avg)
            self.update_metformin_usage()
        # Apply rule-based logic to decide the action
        action = self.decide_action(predicted_glucose, observation, **info)
        self.update_internal_state(action)

        return action
    
    def update_metformin_usage(self):
        if len(self.daily_averages) >= 14 and not (self.daily_averages[-1] > 70 and self.daily_averages[-1] < 180) and not self.is_downtrend_in_glucose():
            self.max_metformin = 1
    
    def is_downtrend_in_glucose(self):
        x = np.arange(len(self.daily_averages[-14:]))
        y = np.array(self.daily_averages[-14:])
        x = sm.add_constant(x)

        model = sm.OLS(y, x).fit()
        slope = model.params[1]
        return slope < 0


    def predict_glucose(self, observation):
        self.all_gl_data.append(observation)
        self.fitted_model = self.fitted_model.append([observation], refit=False)
        # 30 min pred horizon
        preds = self.fitted_model.forecast(steps=6)
        return preds
    
    def decide_action(self, predicted_glucose, observation, **info):
        maximum_gl = max(predicted_glucose)
        hour_of_day = (len(self.all_gl_data) // 20) % 24 
        if self.meal_count < 3:
            meal_cho = self.calculate_meal_CHO(maximum_gl, hour_of_day)  # Calculate CHO based on predicted glucose
            self.last_meal_index = len(self.all_gl_data)
        else:
            meal_cho = 0  # No more meals if already taken 3

        physical = self.determine_physical_activity(hour_of_day)
        if meal_cho != 0:
            print("suggest to eat now")
        metformin = 0
        if self.max_metformin > 0 and self.administered_metformin < self.max_metformin and hour_of_day < 14 and hour_of_day > 6:
            metformin = 500
            self.administered_metformin += 1

        return Action(basal=0, bolus=0, meal=meal_cho, metformin=metformin, physical=physical, time=30)
    
    def determine_physical_activity(self, current_time):
        if not self.physical_activity_done and current_time >= 17:
            return 30
        return 0

    def calculate_meal_CHO(self, predicted_glucose, current_time):
        # Determine CHO content based on time of day and predicted glucose levels
        if current_time < 10 and current_time > 6:  # Breakfast
            return 45 if predicted_glucose > 100 else 60
        elif current_time < 14 and current_time > 6:  # Lunch
            return 60 if predicted_glucose > 100 else 75
        elif current_time > 6:  # Dinner
            return 30 if predicted_glucose > 100 else 45
        else:
            return 0

    def update_internal_state(self, action):
        # Update meal count and total CHO intake
        if action.meal != 0:
            self.meal_count += 1
            self.total_daily_cho += action.meal

        # Update physical activity status
        if action.physical > 0:
            self.physical_activity_done = True

    def reset(self):
        self.meal_count = 0
        self.physical_activity_done = False
        self.total_daily_cho = 0
