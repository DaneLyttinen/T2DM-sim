from collections import namedtuple
import numpy as np
from .base import Controller
from .base import Action
from statsmodels.tsa.statespace.sarimax import SARIMAX
import statsmodels.api as sm
import random

class BaselineController(Controller):
    def __init__(self, seed=3):
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
        self._seed = seed
        self.max_heart_rate =  220 - random.randint(20,60)

    def policy(self, observation, reward, done, **info):
        # Predict future glucose level
        if len(self.all_gl_data) <= 83:
            self.all_gl_data.append(observation.CGM)
            predicted_glucose = [observation.CGM]
        else:
            if self.model == None:
                self.model = SARIMAX(endog=self.all_gl_data,order=(4,0,0),enforce_stationarity=False)
                self.fitted_model = self.model.fit(disp=False)
            predicted_glucose = self.predict_glucose(observation.CGM)

        if len(self.all_gl_data) % 288 == 0:
            self.meal_count = 0
            self.administered_metformin = 0
            daily_avg = np.mean(self.all_gl_data[-288:])
            self.daily_averages.append(daily_avg)
            self.update_metformin_usage()
        # Apply rule-based logic to decide the action
        action = self.decide_action(predicted_glucose)
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
    
    def decide_action(self, predicted_glucose):
        maximum_gl = max(predicted_glucose)
        hour_of_day = (len(self.all_gl_data) // 20) % 24 
        meal_cho = 0

        if self.meal_count < 3:
            if 6 <= hour_of_day < 10 and self.meal_count == 0:  # Breakfast
                meal_cho = self.calculate_meal_CHO(maximum_gl, hour_of_day, "breakfast")
            elif 12 <= hour_of_day < 14 and self.meal_count == 1:  # Lunch
                meal_cho = self.calculate_meal_CHO(maximum_gl, hour_of_day, "lunch")
            elif 17 <= hour_of_day < 20 and self.meal_count == 2:  # Dinner
                meal_cho = self.calculate_meal_CHO(maximum_gl, hour_of_day, "dinner")

        # Ensure the total CHO intake for the day does not exceed 130g
        if self.total_daily_cho + meal_cho > 130:
            meal_cho = max(0, 130 - self.total_daily_cho)
        times = []
        physical = self.determine_physical_activity(hour_of_day)
        
        if physical != 0:
            print("reccomending physical activity")
            times = [(18, 0),(18, 10), (18, 30), (18,40)]
        # if meal_cho != 0:
        #     print("suggest to eat now")
        metformin = 0
        if self.max_metformin > 0 and self.administered_metformin < self.max_metformin and hour_of_day < 14 and hour_of_day > 6:
            metformin = 500
            self.administered_metformin += 1

        return Action(basal=0, bolus=0, meal=meal_cho, metformin=metformin, physical=physical, time=30, times=times)
    
    def determine_physical_activity(self, current_time):
        heart_rate_increase = 0
        if not self.physical_activity_done and current_time >= 18:
            random.seed(self._seed)
            average_heart_rate = 65
            std_deviation = 15
            curr_heart_rate = np.random.normal(average_heart_rate, std_deviation, 1)[0]
            # Referencing values from https://www.semanticscholar.org/paper/Exercise-prescription-for-patients-with-type-2-of-Mendes-Sousa/091e3383140b3f08c150e53b5fad4c8d78f469bf
            heart_rate_increase = random.randint(round((64 / 100) * self.max_heart_rate), round((76 / 100) * self.max_heart_rate))
            heart_rate_increase = abs(curr_heart_rate - heart_rate_increase)
        return heart_rate_increase

    def calculate_meal_CHO(self, predicted_glucose, current_time, meal_type):
        # Meal-specific CHO calculation
        if meal_type == "breakfast":
            return 45 if predicted_glucose > 100 else 60
        elif meal_type == "lunch":
            return 60 if predicted_glucose > 100 else 75
        elif meal_type == "dinner":
            return 30 if predicted_glucose > 100 else 45

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
