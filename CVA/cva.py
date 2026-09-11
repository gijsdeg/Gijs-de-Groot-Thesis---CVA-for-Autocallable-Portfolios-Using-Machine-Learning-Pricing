
'''
Pseudo code:

write market data.mat file using matlab functions (can also just do this manually in matlab)

create marketdata object from simengine

get instrumentId for certain counterparty type function

for different counterparties 

    for i in 1:NUMSIM
        simulate one full dataset using the simengine
      
        basecase:
        1. reverse the pcs to obtain simulated market data 
        2  call the path pricing function that prices all products on the simulated dataset using the market and product data and simulated data as input
           (perhaps multiply prices with nominal value or something, don't know what the prices mean)
        3. multiply with the default probabilities derived from the simulated hazard rates also contained in the simulated data
        4. take average across paths and discount towards zero to then take average again over the averaged/aggregated path this is your cva

        machine learning
        1. walk across the path and price all products seperately using the different machine learning models 
        2. multiply the paths with the default probabilities derived from the simulated hazard rates
        3. take average across paths and discount towards zero to then take average again over the averaged/aggregated path, this is your cva
    end

end
'''

import pandas as pd
import numpy as np
import matlab.engine
import time
import pickle
from datetime import datetime
from marketdata import default_probabilities, discount_rates, plot_surface
from sim_engine import SimMarket
from itertools import chain
from path_functions import generate_feature_path, save_matlab_products
from scipy.io import loadmat


import sys
import os
adjacent_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ML Training'))
sys.path.append(adjacent_folder_path)

from productdata import get_product_selection, load_saved_model


####################################################                                                   ####################################################
####################################################                                                   ####################################################
####################################################  UNCOMMENT BOTTOM LINES TO STORE SIM FEATURE SET  ####################################################
###########################################################################################################################################################
###########################################################################################################################################################


# Define constants
R = 0.4
NUM_SIMS = 45
NUM_STEPS = 52*5*7+2  # +2 for two leap years the coming 7 years


# Create price indexes corresponding to quarterly pricing
PRICE_POINTS = []
i = 1
number_workdays_in_quarter = (365*4+1)/7*5/4/4  # +1 for leap day every four years
while True:
    t = round(number_workdays_in_quarter*i)
    if t >= NUM_STEPS:
        break
    PRICE_POINTS.append(t)
    i = i + 1
matlab_points = matlab.int32(PRICE_POINTS)
PRICE_POINTS = np.array(PRICE_POINTS)


# Define container ids and create mapping table
container_ids = {
    'DANSKE': [17779, 17532, 24619, 24508, 22609], 
    'MS': [24132, 23701, 24177, 24465, 20177],
    'GS': [13479, 24440, 23458, 21465, 24123]
}
all_ids = list(chain.from_iterable(container_ids.values()))
mapping = pd.DataFrame(0, index=all_ids, columns=container_ids.keys())
for group, cols in container_ids.items():
    mapping.loc[cols, group] = 1
mapping.index = mapping.index.astype(str)
matlab_ids = matlab.int32(all_ids)


# Get product data for specified products on current date (or other for which you want to compute cva)
product_data = get_product_selection(all_ids, "2025-07-14")
product_data["InstrumentId"] = pd.Categorical(
    product_data["InstrumentId"].astype(int),
    categories=all_ids,
    ordered=True
)
product_data = product_data.sort_values("InstrumentId").reset_index(drop=True)
product_data['InstrumentId'] = product_data['InstrumentId'].astype(int)
save_matlab_products(product_data)


# Get dividend curve
dividends = loadmat(r"C:\Users\UGGROO\OneDrive - Van Lanschot Kempen\Documents\MSc Thesis\3. Repos\spil-utilities\spil-core\MainFiles\StoredMarketdataFiles\averageDiv_2025-07-01.mat")

# Construct sim market
sim_market = SimMarket(number_of_pcs = 5)
sim_market.transform_market_data()
sim_market.pca()
sim_market.set_arima_model('PC1', (0, 1, 0))
sim_market.set_arima_model('PC2', (1, 0, 0))
sim_market.set_arima_model('PC3', (1, 0, 0))
sim_market.set_arima_model('PC4', (1, 0, 0))
sim_market.set_arima_model('PC5', (2, 0, 0))
sim_market.fit_best_distribution()
# sim_market.fit_gaussian_copula()
sim_market.fit_student_t_copula()


# Start matlab engine
eng = matlab.engine.start_matlab()

discount_rates = discount_rates(PRICE_POINTS)
cva = pd.DataFrame(np.full((NUM_SIMS, len(container_ids)), np.nan), columns=container_ids.keys())


feature_paths = []
output = None

for i in range(NUM_SIMS):
    print('ITERRRRRRRR  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
    print(i)
    
    max_retries = 10  # Maximum number of retries
    attempt = 0       # Counter for attempts
    success = False   # Flag to track success
    
    while not success and attempt < max_retries:
        try:
            sim_market.simulate(num_timesteps=NUM_STEPS) 
            sim_market.reverse_transform()
            sim_market.clean_sim_market()


            market_data = sim_market.sim_market.iloc[:, :-3]
            hazard_rates = sim_market.sim_market.iloc[:, -3:]

            # market_data.iloc[:, 0] = 4000
            
            np_market = market_data.to_numpy()
            matlab_market = matlab.double(np_market.tolist())
      
            output, ivs, lvs = eng.PathPricing(matlab_market, 'pricePoints', matlab_points, 'instrumentIds', matlab_ids, nargout = 3)
            output = pd.DataFrame({key[1:]: np.asarray(value).flatten() * 100 for key, value in output.items()})

            # ivs = np.array(ivs)
            # lvs = np.array(lvs) 
            # plot_surface(ivs)
            # plot_surface(lvs)

            # Only needed for simulated data creation
            features, path_lengths = generate_feature_path(product_data, market_data, dividends, PRICE_POINTS)
            flattened = output.values.flatten('F') 
            non_zero_values = flattened[flattened != 0]
            result_df = pd.DataFrame(non_zero_values, columns=['NonZeroValues'])
            features['Price'] = result_df['NonZeroValues']
            feature_paths.append(features)
           
            probability_of_default = default_probabilities(hazard_rates, PRICE_POINTS)
            exposure_per_counterparty = output.dot(mapping).clip(lower=0) 
            cva.iloc[i] = ((1-R) * exposure_per_counterparty.values * probability_of_default * discount_rates[:, np.newaxis]).sum(axis=0)
            
            # If the function runs successfully, set the flag to True
            success = True
        except Exception as e:
            
            attempt += 1
            print(f"Attempt {attempt} failed: {e}")
            
            # Wait before retrying if attempts remain
            if attempt < max_retries:
                time.sleep(60)  # 60 seconds sleep

    # If unsuccessful after max retries, assign nan
    if not success:
        print(f"Function failed after {max_retries} attempts. Setting result to NaN.")
        cva.iloc[i] = np.nan
 
eng.quit()


sim_feature_set = pd.concat(feature_paths, ignore_index=True)

current_date = datetime.now().strftime('%Y-%m-%d')

with open(rf"C:\Users\UGGROO\OneDrive - Van Lanschot Kempen\Documents\MSc Thesis\3. Repos\thesis code\ML Training\feature_files\sim_features_large5_{current_date}", 'wb') as f:
    pickle.dump(sim_feature_set, f)

with open(rf"C:\Users\UGGROO\OneDrive - Van Lanschot Kempen\Documents\MSc Thesis\3. Repos\thesis code\CVA\exposure_and_cva_files\cva_mc5_{current_date}.pkl", "wb") as fh:
    pickle.dump(cva, fh)


cva_final = cva.mean()


































# for i in range(NUM_SIMS):
#     print('ITERRRRRRRR  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
#     print(i)
#     sim_market.simulate(num_timesteps=NUM_STEPS) 
#     sim_market.reverse_transform()
#     sim_market.clean_sim_market()

#     market_data = sim_market.sim_market.iloc[:, :-3]
#     hazard_rates = sim_market.sim_market.iloc[:, -3:]

#     np_market = market_data.to_numpy()
#     matlab_market = matlab.double(np_market.tolist())

#     output = eng.PathPricing(matlab_market, 'pricePoints', matlab_points, 'instrumentIds', matlab_ids)
#     output = pd.DataFrame({key[1:]: np.asarray(value).flatten() for key, value in output.items()})
    
#     exposure_per_counterparty = output.dot(mapping)
#     probability_of_default = default_probabilities(hazard_rates, PRICE_POINTS)
    
#     cva.iloc[i] = (1-R)*(exposure_per_counterparty.values * probability_of_default * discount_rates[:, np.newaxis]).sum(axis=0)
   
# eng.quit()

# cva_final = cva.mean()




# Place this below output in the cva loop
# ivs = np.array(ivs)
# lvs = np.array(lvs) 
# plot_surface(ivs)
# plot_surface(lvs)






# ivs = None
# lvs = None

# price_vector, ivs, lvs = mc_pricer.PathPricing(nargout = 3)

# # print('$$$$$$$$$$$   CURRENT ITERATION    $$$$$$$$$$$$$$$$')
# # print(i)
# ivs = np.array(ivs)
# lvs = np.array(lvs)

# plot_surface(ivs)
# plot_surface(lvs)