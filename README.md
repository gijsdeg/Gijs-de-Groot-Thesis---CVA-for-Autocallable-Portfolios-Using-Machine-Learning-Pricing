# Gijs-de-Groot-Thesis---CVA-for-Autocallable-Portfolios-Using-Machine-Learning-Pricing
This repository contains most parts of my thesis code. The main parts are the market simulation, cva framework and machine learning models used for pricing the autocallables. Here is a short descriptions of each file.

CVA
cva.py - This contains the main cva code that calls a matlab pricing engine through the matlab engine api for python. The matlab code is excluded from this repository so the code will not be executable.\\
cva.py - Similar to cva.py but it does not call the matlab pricing engine but uses trained machine learning models instead.
exposure_and_cva_analysis.ipynb. Notebook used to generate output relevant for the thesis.
marketdata.py - In this file queries and functions are written to retrieve and process market data.
path_functions.py - This file contains functions to walk along a path of market data and create the relevant features used as input for machine learning. It also contains functions that can be used to check whether the autocallables have been called. 
sim_engine.py - This file contains a class that defines a market simulation engine.
simulation_analysis.ipynb - Notebook used to generate output relevant for the thesis.
wwr_analysis.ipynb - Notebook used to generate output related to wrong way risk.

ML Training
errors folder stores the model errors later used for analysis.
feature_files folder stores the created feature sets.
models folder stores the trained machine learning models. Gpr models are excluded since they exceeded the 100mb limit.
elasticnet.ipynb - Notebook used to train elastic net.
error_analysis.ipynb - Notebook used to generate output relevant for the thesis.
features.py - This file contains functions for feature engineering.
gpr.ipynb - Notebook used to train gaussian process regression.
nearalnet.ipynb - Notebook used to train nearal network.
productdata.py - This file contains queries to retrieve product data of the autocallables from a database.
xgboost.ipynb - Notebook used to train xgboost.

