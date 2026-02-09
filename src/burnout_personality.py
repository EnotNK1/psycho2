import skfuzzy as fuzz
import skfuzzy.control as ctrl
import numpy as np
import matplotlib.pyplot as plt

#входные переменные
extraversion = ctrl.Antecedent(np.arange(15, 75, 1), 'extraversion')
agreeableness = ctrl.Antecedent(np.arange(15, 75, 1), 'agreeableness')
conscientiousness = ctrl.Antecedent(np.arange(15, 75, 1), 'conscientiousness')
neuroticism = ctrl.Antecedent(np.arange(15, 75, 1), 'neuroticism')
openness = ctrl.Antecedent(np.arange(15, 75, 1), 'openness')

#выходная
burnout_probability = ctrl.Consequent(np.arange(0, 100, 1), 'burnout_probability')

#функции принадлежности входных переменных
extraversion['low'] = fuzz.trimf(extraversion.universe, [15, 15, 45])
extraversion['average'] = fuzz.trimf(extraversion.universe, [38, 45, 52])
extraversion['high'] = fuzz.trimf(extraversion.universe, [45, 75, 75])

agreeableness['low'] = fuzz.trimf(extraversion.universe, [15, 15, 45])
agreeableness['average'] = fuzz.trimf(extraversion.universe, [38, 45, 52])
agreeableness['high'] = fuzz.trimf(extraversion.universe, [45, 75, 75])

conscientiousness['low'] = fuzz.trimf(extraversion.universe, [15, 15, 45])
conscientiousness['average'] = fuzz.trimf(extraversion.universe, [38, 45, 52])
conscientiousness['high'] =fuzz.trimf(extraversion.universe, [45, 75, 75])

neuroticism['low'] = fuzz.trimf(extraversion.universe, [15, 15, 45])
neuroticism['average'] = fuzz.trimf(extraversion.universe, [38, 45, 52])
neuroticism['high'] = fuzz.trimf(extraversion.universe, [45, 75, 75])

openness['low'] = fuzz.trimf(extraversion.universe, [15, 15, 45])
openness['average'] = fuzz.trimf(extraversion.universe, [38, 45, 52])
openness['high'] = fuzz.trimf(extraversion.universe, [45, 75, 75])

#функции принадлежности выходной переменных
burnout_probability['poor'] = fuzz.trapmf(burnout_probability.universe, [0,0, 15, 50])
burnout_probability['average'] = fuzz.trapmf(burnout_probability.universe, [20,45, 55, 80])
burnout_probability['good'] = fuzz.trapmf(burnout_probability.universe, [50,85, 100, 100])

#база правил

rules = []

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['high'] & openness['high'] & neuroticism['high'], burnout_probability['poor']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['high'] & openness['high'] & neuroticism['average'], burnout_probability['poor']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['high'] & openness['high'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['high'] & openness['average'] & neuroticism['high'], burnout_probability['poor']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['high'] & openness['average'] & neuroticism['average'], burnout_probability['poor']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['high'] & openness['average'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['high'] & openness['low'] & neuroticism['high'], burnout_probability['poor']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['high'] & openness['low'] & neuroticism['average'], burnout_probability['poor']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['high'] & openness['low'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['average'] & openness['high'] & neuroticism['high'], burnout_probability['poor']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['average'] & openness['high'] & neuroticism['average'], burnout_probability['poor']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['average'] & openness['high'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['average'] & openness['average'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['average'] & openness['average'] & neuroticism['average'], burnout_probability['poor']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['average'] & openness['average'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['average'] & openness['low'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['average'] & openness['low'] & neuroticism['average'], burnout_probability['poor']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['average'] & openness['low'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['low'] & openness['high'] & neuroticism['high'], burnout_probability['poor']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['low'] & openness['high'] & neuroticism['average'], burnout_probability['poor']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['low'] & openness['high'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['low'] & openness['average'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['low'] & openness['average'] & neuroticism['average'], burnout_probability['poor']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['low'] & openness['average'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['low'] & openness['low'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['low'] & openness['low'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['high'] & conscientiousness['low'] & openness['low'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['high'] & openness['high'] & neuroticism['high'], burnout_probability['poor']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['high'] & openness['high'] & neuroticism['average'], burnout_probability['poor']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['high'] & openness['high'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['high'] & openness['average'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['high'] & openness['average'] & neuroticism['average'], burnout_probability['poor']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['high'] & openness['average'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['high'] & openness['low'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['high'] & openness['low'] & neuroticism['average'], burnout_probability['poor']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['high'] & openness['low'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['average'] & openness['high'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['average'] & openness['high'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['average'] & openness['high'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['average'] & openness['average'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['average'] & openness['average'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['average'] & openness['average'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['average'] & openness['low'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['average'] & openness['low'] & neuroticism['average'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['average'] & openness['low'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['low'] & openness['high'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['low'] & openness['high'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['low'] & openness['high'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['low'] & openness['average'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['low'] & openness['average'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['low'] & openness['average'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['low'] & openness['low'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['low'] & openness['low'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['average'] & conscientiousness['low'] & openness['low'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['high'] & openness['high'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['high'] & openness['high'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['high'] & openness['high'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['high'] & openness['average'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['high'] & openness['average'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['high'] & openness['average'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['high'] & openness['low'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['high'] & openness['low'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['high'] & openness['low'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['average'] & openness['high'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['average'] & openness['high'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['average'] & openness['high'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['average'] & openness['average'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['average'] & openness['average'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['average'] & openness['average'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['average'] & openness['low'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['average'] & openness['low'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['average'] & openness['low'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['low'] & openness['high'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['low'] & openness['high'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['low'] & openness['high'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['low'] & openness['average'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['low'] & openness['average'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['low'] & openness['average'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['low'] & openness['low'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['low'] & openness['low'] & neuroticism['average'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['high'] & agreeableness['low'] & conscientiousness['low'] & openness['low'] & neuroticism['low'], burnout_probability['good']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['high'] & openness['high'] & neuroticism['high'], burnout_probability['poor']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['high'] & openness['high'] & neuroticism['average'], burnout_probability['poor']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['high'] & openness['high'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['high'] & openness['average'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['high'] & openness['average'] & neuroticism['average'], burnout_probability['poor']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['high'] & openness['average'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['high'] & openness['low'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['high'] & openness['low'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['high'] & openness['low'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['average'] & openness['high'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['average'] & openness['high'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['average'] & openness['high'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['average'] & openness['average'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['average'] & openness['average'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['average'] & openness['average'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['average'] & openness['low'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['average'] & openness['low'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['average'] & openness['low'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['low'] & openness['high'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['low'] & openness['high'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['low'] & openness['high'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['low'] & openness['average'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['low'] & openness['average'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['low'] & openness['average'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['low'] & openness['low'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['low'] & openness['low'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['high'] & conscientiousness['low'] & openness['low'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['high'] & openness['high'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['high'] & openness['high'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['high'] & openness['high'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['high'] & openness['average'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['high'] & openness['average'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['high'] & openness['average'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['high'] & openness['low'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['high'] & openness['low'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['high'] & openness['low'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['average'] & openness['high'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['average'] & openness['high'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['average'] & openness['high'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['average'] & openness['average'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['average'] & openness['average'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['average'] & openness['average'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['average'] & openness['low'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['average'] & openness['low'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['average'] & openness['low'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['low'] & openness['high'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['low'] & openness['high'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['low'] & openness['high'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['low'] & openness['average'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['low'] & openness['average'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['low'] & openness['average'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['low'] & openness['low'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['low'] & openness['low'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['average'] & conscientiousness['low'] & openness['low'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['high'] & openness['high'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['high'] & openness['high'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['high'] & openness['high'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['high'] & openness['average'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['high'] & openness['average'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['high'] & openness['average'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['high'] & openness['low'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['high'] & openness['low'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['high'] & openness['low'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['average'] & openness['high'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['average'] & openness['high'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['average'] & openness['high'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['average'] & openness['average'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['average'] & openness['average'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['average'] & openness['average'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['average'] & openness['low'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['average'] & openness['low'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['average'] & openness['low'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['low'] & openness['high'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['low'] & openness['high'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['low'] & openness['high'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['low'] & openness['average'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['low'] & openness['average'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['low'] & openness['average'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['low'] & openness['low'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['low'] & openness['low'] & neuroticism['average'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['average'] & agreeableness['low'] & conscientiousness['low'] & openness['low'] & neuroticism['low'], burnout_probability['good']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['high'] & openness['high'] & neuroticism['high'], burnout_probability['poor']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['high'] & openness['high'] & neuroticism['average'], burnout_probability['poor']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['high'] & openness['high'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['high'] & openness['average'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['high'] & openness['average'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['high'] & openness['average'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['high'] & openness['low'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['high'] & openness['low'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['high'] & openness['low'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['average'] & openness['high'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['average'] & openness['high'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['average'] & openness['high'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['average'] & openness['average'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['average'] & openness['average'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['average'] & openness['average'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['average'] & openness['low'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['average'] & openness['low'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['average'] & openness['low'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['low'] & openness['high'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['low'] & openness['high'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['low'] & openness['high'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['low'] & openness['average'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['low'] & openness['average'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['low'] & openness['average'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['low'] & openness['low'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['low'] & openness['low'] & neuroticism['average'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['high'] & conscientiousness['low'] & openness['low'] & neuroticism['low'], burnout_probability['good']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['high'] & openness['high'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['high'] & openness['high'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['high'] & openness['high'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['high'] & openness['average'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['high'] & openness['average'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['high'] & openness['average'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['high'] & openness['low'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['high'] & openness['low'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['high'] & openness['low'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['average'] & openness['high'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['average'] & openness['high'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['average'] & openness['high'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['average'] & openness['average'] & neuroticism['high'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['average'] & openness['average'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['average'] & openness['average'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['average'] & openness['low'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['average'] & openness['low'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['average'] & openness['low'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['low'] & openness['high'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['low'] & openness['high'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['low'] & openness['high'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['low'] & openness['average'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['low'] & openness['average'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['low'] & openness['average'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['low'] & openness['low'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['low'] & openness['low'] & neuroticism['average'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['average'] & conscientiousness['low'] & openness['low'] & neuroticism['low'], burnout_probability['good']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['high'] & openness['high'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['high'] & openness['high'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['high'] & openness['high'] & neuroticism['low'], burnout_probability['poor']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['high'] & openness['average'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['high'] & openness['average'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['high'] & openness['average'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['high'] & openness['low'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['high'] & openness['low'] & neuroticism['average'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['high'] & openness['low'] & neuroticism['low'], burnout_probability['good']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['average'] & openness['high'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['average'] & openness['high'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['average'] & openness['high'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['average'] & openness['average'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['average'] & openness['average'] & neuroticism['average'], burnout_probability['average']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['average'] & openness['average'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['average'] & openness['low'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['average'] & openness['low'] & neuroticism['average'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['average'] & openness['low'] & neuroticism['low'], burnout_probability['average']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['low'] & openness['high'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['low'] & openness['high'] & neuroticism['average'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['low'] & openness['high'] & neuroticism['low'], burnout_probability['good']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['low'] & openness['average'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['low'] & openness['average'] & neuroticism['average'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['low'] & openness['average'] & neuroticism['low'], burnout_probability['good']))

rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['low'] & openness['low'] & neuroticism['high'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['low'] & openness['low'] & neuroticism['average'], burnout_probability['good']))
rules.append(ctrl.Rule(extraversion['low'] & agreeableness['low'] & conscientiousness['low'] & openness['low'] & neuroticism['low'], burnout_probability['good']))

#построение машины нечеткого вывода
burnout_ctrl = ctrl.ControlSystem(rules)
res_burnout = ctrl.ControlSystemSimulation(burnout_ctrl)

def burnout_calculate(extraversion, agreeableness, conscientiousness, neuroticism, openness):

    res_burnout.input['extraversion'] = extraversion#'Экстраверсия']
    res_burnout.input['agreeableness'] = agreeableness#['Привязанность']
    res_burnout.input['conscientiousness'] = conscientiousness#['Саморегуляция']
    res_burnout.input['neuroticism'] = neuroticism#['Нейротизм']
    res_burnout.input['openness'] = openness#['Отктрытость опыту']

    res_burnout.compute()

    #выходная переменная, вернуть в API
    probability = (res_burnout.output['burnout_probability'])/100

    return probability