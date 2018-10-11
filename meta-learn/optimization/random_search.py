'''
MIT License
Copyright (c) [2018] [Simon Franz Albert Blanke]
Email: simonblanke528481@gmail.com
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import os
import sys
import time
import random
import numpy as np
import pandas as pd
import multiprocessing


from functools import partial

from .base import BaseOptimizer


num_cores = multiprocessing.cpu_count()


class RandomSearch_Optimizer(BaseOptimizer):

	def __init__(self, ML_dict, scoring, N_pipelines=None, T_search_time=None, cv=5, verbosity=0):
		self.ML_dict = ML_dict
		self.scoring = scoring
		self.N_pipelines = N_pipelines
		self.T_search_time = T_search_time
		self.cv = cv
		self.verbosity = verbosity

		self.best_model = None
		self.model_list = []
		self.score_list = []
		self.hyperpara_dict = {}
		self.train_time = []

	def __call__(self):
		return self.best_model


			# get meta_regressor from model

			# get dataset meta features

			# put dataset meta freatures and hyperpara_dict together

			# predict score from data	

	def _random_search_v2(self, N_searches, ML_dict, X_train, meta_regressor):
		model, hyperpara_dict = self._get_random_hyperparameter(ML_dict)

		get_meta_regressor = self.get_meta_regressor(model)

		features_from_dataset = self._get_features_from_dataset(X_train)


		all_features = self._get_all_features(X_train, y_train)




		time_temp = time.time()
		prediction = get_meta_regressor.predict(all_features)
		train_time = time.time() - time_temp

		return model, prediction, hyperpara_dict, train_time


	def _random_search(self, N_searches, X_train, y_train, scoring, ML_dict, cv):
		'''
		In this function we do the random search in the hyperparameter/ML-models space given by the 'ML_dict'-dictionary.
		The goal is to find the model/hyperparameter combination with the best score. This means that we have to train every model on data and compare their scores.
		Arguments:
			- N_searches: Number of model/hyperpara. combinations searched. (int)
			- X_train: training data of features, similar to scikit-learn. (numpy array)
			- y_train: training data of targets, similar to scikit-learn. (numpy array)
			- scoring: scoring used to compare models, similar to scikit-learn. (string)
			- ML_dict: dictionary that contains models and hyperparameter + their ranges and steps for the search. Similar to Tpot package. (dictionary)
			- cv: defines the k of k-fold cross validation. (int)
		Returns:
			- ML_model: A list of model and hyperparameter combinations with best score. (list of scikit-learn objects)
			- score: A list of scores of these models. (list of floats)
		'''
		model, hyperpara_dict = self._get_random_hyperparameter(ML_dict)

		model = self._import_model(model)
		ML_model = model(**hyperpara_dict)

		score, train_time = self._train_model(ML_model, X_train, y_train, scoring, cv)

		return ML_model, score, hyperpara_dict, train_time


	def _random_search_multiprocessing(self, X_train, y_train):
		'''
		This function runs the 'random_search'-function in parallel to return a list of the models and their scores.
		After that the lists are searched to find the best model and its score.
		Arguments:
			- X_train: training data of features, similar to scikit-learn. (numpy array)
			- y_train: training data of targets, similar to scikit-learn. (numpy array)
		Returns:
			- best_model: The model and hyperparameter combination with best score. (scikit-learn object)
			- best_score: The score of this model. (float)
		'''	

		pool = multiprocessing.Pool(num_cores)
		random_search_obj = partial(self._random_search, ML_dict=self.ML_dict, X_train=X_train, y_train=y_train, scoring=self.scoring, cv=self.cv)
		
		c_time = time.time()
		models, scores, hyperpara_dict, train_time = zip(*pool.map(random_search_obj, range(0, self.N_pipelines)))
		
		self.model_list = models[:]
		self.score_list = scores[:]
		self.hyperpara_dict = hyperpara_dict[:]
		self.train_time = train_time[:]

		return models, scores


	def fit(self, X_train, y_train):
		models, scores = self._random_search_multiprocessing(X_train, y_train)

		self.best_model, best_score = self._find_best_model(models, scores)
		self.best_model.fit(X_train, y_train)