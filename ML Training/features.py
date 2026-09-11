import pandas as pd
import numpy as np
import pickle

import sys
import os
adjacent_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'CVA'))
sys.path.append(adjacent_folder_path)

from productdata import convert_matlab_datenum

from scipy.io import loadmat
from datetime import datetime


def get_features(product_data, market_data, div_mat):
    
    product_features = pd.DataFrame()
    product_features['Date'] = pd.to_datetime(product_data['PriceCalculationDateTime']).dt.date
    product_features['Price'] = product_data['Price']
    product_features['CallBarrier'] = product_data['CallBarrier']
    product_features['CouponBarrier'] = product_data['CouponBarrier']
    product_features['ProtectionBarrier'] = product_data['ProtectionBarrier']
    product_features['CallBarrierShifted'] = product_data['CallBarrier'] - product_data['CallBarrierShift']  # Consider changing to just CallBarrierShift
    product_features['CouponBarrierShifted'] = product_data['CouponBarrierShifted']
    product_features['ProtectionBarrierShifted'] = product_data['ProtectionBarrierShifted']
    
    calldate_cols = ['Calldate 1', 'Calldate 2', 'Calldate 3', 'Calldate 4', 'Calldate 5', 'Calldate 6', 'Calldate 7']
    after_mask = product_data[calldate_cols].gt(product_data['PriceCalculationDateTime'], axis=0)
    valid_dates = product_data[calldate_cols].where(after_mask)
    next_calldate = valid_dates.min(axis=1)
    
    product_features['RemainingCalldates'] = after_mask.sum(axis=1)
    product_features['DaysTillNextCallDate'] = (next_calldate - product_data['PriceCalculationDateTime']).dt.days
    product_features['DaysToMaturity'] = (product_data['Expiration'] - product_data['PriceCalculationDateTime']).dt.days
    product_features['DaysSinceIssuing'] = (product_data['PriceCalculationDateTime'] - product_data['StartDate']).dt.days
    product_features['UnderlyingPrice'] = product_data['KoersOLW']
    product_features['Moneyness'] = product_data['KoersOLW']/product_data['Fixing']
    product_features['Memory'] = product_data['Memory']
    product_features['CouponValue'] = product_data['CouponValue']
    product_features['CouponsInMemory'] = np.where(
        product_data['CouponsInMemory'] != 0,
        product_data['CouponValue'] / product_data['CouponsInMemory'] / 100,
        0
    )  
    
    dates = convert_matlab_datenum(pd.DataFrame(div_mat['historicDiv']['Dates'][0,0]))
    divs = pd.DataFrame(div_mat['historicDiv']['Dividends'][0,0])
    div_dates = convert_matlab_datenum(pd.DataFrame(div_mat['historicDiv']['DividendDates'][0,0]))
    
    market_data['Date'] = pd.to_datetime(market_data['Date']).dt.date
    market_features = market_data[['Date', 'AlphaA', 'AlphaB', 'AlphaC', 'RhoA', 'RhoB', 'RhoC', 'NuB', 'NuC', '1BD', '1WK', '1MO', '2MO', '6MO', '12MO', '2YR', '3YR', '4YR', '5YR', '7YR']]
    
    product_data['Date'] = pd.to_datetime(product_data['PriceCalculationDateTime']).dt.date
    product_data['Calldate 1'] = pd.to_datetime(product_data['Calldate 1'])
    product_data['Calldate 2'] = pd.to_datetime(product_data['Calldate 2'])
    product_data['Calldate 3'] = pd.to_datetime(product_data['Calldate 3'])
    product_data['Calldate 4'] = pd.to_datetime(product_data['Calldate 4'])
    product_data['Calldate 5'] = pd.to_datetime(product_data['Calldate 5'])
    product_data['Calldate 6'] = pd.to_datetime(product_data['Calldate 6'])
    product_data['Calldate 7'] = pd.to_datetime(product_data['Calldate 7'])
    
    dates = dates.apply(pd.to_datetime)
    unique_dates = dates.iloc[0].dt.date.values
    product_data['column_index'] = product_data['Date'].apply(lambda x: np.where(unique_dates == x)[0][0] if x in unique_dates else np.nan)
    
    corresponding_div_dates = div_dates.iloc[product_data['column_index'].values].reset_index(drop=True)
    corresponding_divs = divs.T.iloc[product_data['column_index'].values].reset_index(drop=True)
    
    mask = corresponding_div_dates.apply(lambda row: row.isin(valid_dates.loc[row.name]), axis = 1)

    all_divs = corresponding_divs.where(mask)
    
    q = all_divs.apply(lambda row: pd.Series(row.dropna().tolist() + [0] * (7 - len(row.dropna()))), axis=1).iloc[:, :7]
    q.columns = [f'q{i+1}' for i in range(7)]
    
    product_features = pd.concat([product_features, q], axis = 1)
    #product_features['Date'] = product_features['Date'].dt.date
    
    final_features = product_features.merge(market_features, on = 'Date', how = 'left')

    return final_features


def get_ml_features(product_data, market_data, div_mat):

    product_features = pd.DataFrame()
    product_features['Date'] = pd.to_datetime(product_data['PriceCalculationDateTime']).dt.date
    #product_features['Price'] = product_data['Price']
    product_features['CallBarrier'] = product_data['CallBarrier']
    product_features['CouponBarrier'] = product_data['CouponBarrier']
    product_features['ProtectionBarrier'] = product_data['ProtectionBarrier']
    product_features['CallBarrierShifted'] = product_data['CallBarrier'] - product_data['CallBarrierShift']
    product_features['CouponBarrierShifted'] = product_data['CouponBarrierShifted']
    product_features['ProtectionBarrierShifted'] = product_data['ProtectionBarrierShifted']

    calldate_cols = [f'Calldate {i}' for i in range(1, 8)]
    product_data[calldate_cols] = product_data[calldate_cols].apply(pd.to_datetime)

    after_mask = product_data[calldate_cols].gt(product_data['PriceCalculationDateTime'], axis=0)
    valid_dates = product_data[calldate_cols].where(after_mask)
    next_calldate = valid_dates.min(axis=1)

    product_features['RemainingCalldates'] = after_mask.sum(axis=1)
    product_features['DaysTillNextCallDate'] = (next_calldate - product_data['PriceCalculationDateTime']).dt.days
    product_features['DaysToMaturity'] = (product_data['Expiration'] - product_data['PriceCalculationDateTime']).dt.days
    product_features['DaysSinceIssuing'] = (product_data['PriceCalculationDateTime'] - product_data['StartDate']).dt.days
    product_features['UnderlyingPrice'] = product_data['KoersOLW']
    product_features['Moneyness'] = product_data['KoersOLW'] / product_data['Fixing']
    product_features['Memory'] = product_data['Memory']
    product_features['CouponValue'] = product_data['CouponValue']
    product_features['CouponsInMemory'] = np.where(
        product_data['CouponsInMemory'] != 0,
        product_data['CouponValue'] / product_data['CouponsInMemory'] / 100,
        0
    )
    
    stored_date = convert_matlab_datenum(pd.DataFrame(div_mat['averageDiv']['Dates'][0,0]))
    diff = (product_data['PriceCalculationDateTime'] - stored_date.values[0]).dt.days

    dates = convert_matlab_datenum(pd.DataFrame(div_mat['averageDiv']['Dates'][0,0]) + diff.values[0])
    divs = pd.DataFrame(div_mat['averageDiv']['Dividends'][0, 0])
    div_dates = convert_matlab_datenum(pd.DataFrame(div_mat['averageDiv']['DividendDates'][0, 0]) + diff.values[0])

    market_data['Date'] = pd.to_datetime(market_data['Date']).dt.date
    market_features = market_data[['Date', 'AlphaA', 'AlphaB', 'AlphaC', 'RhoA', 'RhoB', 'RhoC', 'NuB', 'NuC',
                                   '1BD', '1WK', '1MO', '2MO', '6MO', '12MO', '2YR', '3YR', '4YR', '5YR', '7YR']]

    product_data['Date'] = pd.to_datetime(product_data['PriceCalculationDateTime']).dt.date

    dates = dates.apply(pd.to_datetime)
    unique_dates = dates.iloc[0].dt.date.values
    product_data['column_index'] = product_data['Date'].apply(lambda x: np.where(unique_dates == x)[0][0] if x in unique_dates else np.nan)

    corresponding_div_dates = div_dates.iloc[product_data['column_index'].values].reset_index(drop=True)
    corresponding_divs = divs.T.iloc[product_data['column_index'].values].reset_index(drop=True)

    mask = corresponding_div_dates.apply(lambda row: row.isin(valid_dates.loc[row.name]), axis = 1)

    all_divs = corresponding_divs.where(mask)

    q = all_divs.apply(lambda row: pd.Series(row.dropna().tolist() + [0] * (7 - len(row.dropna()))), axis=1).iloc[:, :7]
    q.columns = [f'q{i+1}' for i in range(7)]

    product_features = pd.concat([product_features, q], axis=1)
    final_features = product_features.merge(market_features, on='Date', how='left')

    return final_features



def save_features(data, name='features_saved_on'):
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    folder_name = 'feature_files'
    filename = f"{name}_{current_date}.pkl"  # Save as .pkl instead of .csv

    current_dir = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(current_dir, folder_name)
    
    os.makedirs(folder_path, exist_ok=True)

    file_path = os.path.join(folder_path, filename)
    
    # Save DataFrame as a pickle file
    with open(file_path, 'wb') as f:
        pickle.dump(data, f)



## TEST CASE 1
 
# product_data34 = get_productdata()
# market_data34 = get_marketdata()
# divs34 = loadmat(r"C:\Users\UGGROO\OneDrive - Van Lanschot Kempen\Documents\MSc Thesis\3. Repos\spil-utilities\spil-core\MainFiles\StoredMarketdataFiles\historicDiv_2025-05-14.mat")

# output34 = get_features(product_data34, market_data34, divs34)



### TEST CASE 2

# adjacent_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'CVA'))
# sys.path.append(adjacent_folder_path)

# from sim_engine import SimMarket


# product_data = get_product_selection([1733], "2025-05-14")


# NUM_STEPS = 52*5*7+2

# sim_market = SimMarket(number_of_pcs = 5)
# sim_market.transform_market_data()
# sim_market.pca()
# sim_market.set_arima_model('PC1', (1, 1, 1))
# sim_market.set_arima_model('PC2', (1, 0, 0))
# sim_market.set_arima_model('PC3', (2, 0, 0))
# sim_market.set_arima_model('PC4', (1, 0, 0))
# sim_market.set_arima_model('PC5', (1, 0, 0))
# sim_market.fit_best_distribution()
# sim_market.fit_gaussian_copula()

# sim_market.simulate(num_timesteps=NUM_STEPS) 
# sim_market.reverse_transform()
# sim_market.clean_sim_market()

# market = sim_market.sim_market.iloc[:, :-3]

# column_names = [
#     'Fixing', 'AlphaA', 'AlphaB', 'AlphaC', 'RhoA', 'RhoB', 'RhoC', 'NuB', 'NuC',
#     '1BD', '1WK', '1MO', '2MO', '3MO', '4MO', '5MO', '6MO', '7MO', '8MO',
#     '9MO', '10MO', '11MO', '12MO', '18MO', '2YR', '3YR', '4YR', '5YR', '7YR',
#     '10YR', '12YR', '15YR', '20YR', '25YR', '30YR', '40YR', '50YR',
#     'Euribor3m', 'Euribor6m', 'Euribor12m', 'Date'
# ]

# # Generate business days
# business_days = pd.bdate_range(start=product_data['PriceCalculationDateTime'].min(), periods=len(market))

# # Set correct column names and add business days as 'Date'
# market_data = market.copy()
# market_data['Date'] = business_days
# market_data.columns = column_names

# divs = loadmat(r"C:\Users\UGGROO\OneDrive - Van Lanschot Kempen\Documents\MSc Thesis\3. Repos\spil-utilities\spil-core\MainFiles\StoredMarketdataFiles\averageDiv_2025-05-09.mat")

# output = get_ml_features(product_data, market_data, divs)

# print(output)




















# class Features:

#     def __init__(self):
#         self.product_data = get_productdata()
#         self.market_data = get_marketdata()
#         self.product_features = pd.DataFrame()
#         self.market_features = pd.DataFrame()
#         self.div_dates = pd.DataFrame()
#         self.divs = pd.DataFrame()
#         self.final_features = pd.DataFrame()

#     def get_product_features(self):
#         self.product_features['Date'] = pd.to_datetime(self.product_data['PriceCalculationDateTime'])
#         self.product_features['CallBarrier'] = self.product_data['CallBarrier']
#         self.product_features['CouponBarrier'] = self.product_data['CouponBarrier']
#         self.product_features['ProtectionBarrier'] = self.product_data['ProtectionBarrier']
#         self.product_features['CallBarrierShifted'] = self.product_data['CallBarrier'] - self.product_data['CallBarrierShift']
#         self.product_features['CouponBarrierShifted'] = self.product_data['CouponBarrierShifted']
#         self.product_features['ProtectionBarrierShifted'] = self.product_data['ProtectionBarrierShifted']

#         calldate_cols = ['Calldate 1', 'Calldate 2', 'Calldate 3', 'Calldate 4', 'Calldate 5', 'Calldate 6', 'Calldate 7']
#         after_mask = self.product_data[calldate_cols].gt(self.product_data['PriceCalculationDateTime'], axis=0)
#         valid_dates = self.product_data[calldate_cols].where(after_mask)
#         next_calldate = valid_dates.min(axis=1)

#         self.product_features['RemainingCalldates'] = after_mask.sum(axis=1)
#         self.product_features['DaysTillNextCallDate'] = (next_calldate - self.product_data['PriceCalculationDateTime']).dt.days
#         self.product_features['DaysToMaturity'] = (self.product_data['Expiration'] - self.product_data['PriceCalculationDateTime']).dt.days
#         self.product_features['DaysSinceIssuing'] = (self.product_data['PriceCalculationDateTime'] - self.product_data['StartDate']).dt.days
#         self.product_features['UnderlyingPrice'] = self.product_data['KoersOLW']
#         self.product_features['Moneyness'] = self.product_data['KoersOLW'] / self.product_data['Fixing']
#         self.product_features['Memory'] = self.product_data['Memory']
#         self.product_features['CouponValue'] = self.product_data['CouponValue']

#     def get_market_features(self):
#         div_data = loadmat(r"C:\Users\UGGROO\OneDrive - Van Lanschot Kempen\Documents\MSc Thesis\3. Repos\spil-utilities\spil-core\MainFiles\StoredMarketdataFiles\historicDiv_2025-02-25.mat")
        
#         self.dates = pd.to_datetime(np.array(div_data['historicDiv']['DateStrings'][0,0]).flatten())
#         self.divs = pd.DataFrame(np.array(div_data['historicDiv']['Dividends'][0,0]))
#         self.div_dates = pd.DataFrame(pd.to_datetime(np.array(div_data['historicDiv']['DividendDateStrings'][0,0]).flatten()))

#         self.market_features = self.market_data[['Date', 'AlphaA', 'AlphaB', 'AlphaC', 'RhoA', 'RhoB', 'RhoC', 'NuB', 'NuC', '1BD', '1WK', '1MO', '2MO', '6MO', '12MO', '2YR', '3YR', '4YR', '5YR', '7YR']]
#         self.market_features.loc[:, 'Date'] = pd.to_datetime(self.market_features['Date'])

#     def main_features(self):
#         self.product_data['Date'] = pd.to_datetime(self.product_data['PriceCalculationDateTime'])
#         for i in range(1, 8):
#             self.product_data[f'Calldate {i}'] = pd.to_datetime(self.product_data[f'Calldate {i}'])

#         # Fix IndexError issue
#         main_idx = self.product_data['Date'].map(lambda x: np.where(self.dates == x)[0][0] if np.where(self.dates == x)[0].size > 0 else np.nan)
#         main_idx = main_idx.dropna().astype(int)

#         for i in range(1, 8):
#             coupon_col = f'Calldate {i}'

#             # Fix invalid indexing with .iloc
#             obs_dates = self.div_dates.iloc[:, main_idx].values
#             div_yield_col = self.divs.iloc[:, main_idx].values

#             # Fix dimension mismatch issues
#             mask = (obs_dates.T[:, :, None] == self.product_data[coupon_col].values[:, None, None])

#             matched_dividends = np.where(mask, div_yield_col.T[:, :, None], np.nan).sum(axis=1)

#             self.product_features[f'Dividendyield{i}'] = matched_dividends[:, 0]

#         self.final_features = self.product_features.merge(self.market_features, on='Date', how='left')














# class Features:

#     def __init__(self):
#         self.product_data = get_productdata()
#         self.market_data = get_marketdata()
#         self.dates = pd.DataFrame()
#         self.div_dates = pd.DataFrame()
#         self.divs = pd.DataFrame()
#         self.product_features = pd.DataFrame()
#         self.market_features = pd.DataFrame()
#         self.final_features = pd.DataFrame()


#     def get_features(self):
#         self.product_features['Date'] = pd.to_datetime(self.product_data['PriceCalculationDateTime'])
#         self.product_features['CallBarrier'] = self.product_data['CallBarrier']
#         self.product_features['CouponBarrier'] = self.product_data['CouponBarrier']
#         self.product_features['ProtectionBarrier'] = self.product_data['ProtectionBarrier']
#         self.product_features['CallBarrierShifted'] = self.product_data['CallBarrier'] - self.product_data['CallBarrierShift']  # Consider changing to just CallBarrierShift
#         self.product_features['CouponBarrierShifted'] = self.product_data['CouponBarrierShifted']
#         self.product_features['ProtectionBarrierShifted'] = self.product_data['ProtectionBarrierShifted']


#         calldate_cols = ['Calldate 1', 'Calldate 2', 'Calldate 3', 'Calldate 4', 'Calldate 5', 'Calldate 6', 'Calldate 7']
#         after_mask = self.product_data[calldate_cols].gt(self.product_data['PriceCalculationDateTime'], axis=0)
#         valid_dates = self.product_data[calldate_cols].where(after_mask)
#         next_calldate = valid_dates.min(axis=1)

#         self.product_features['RemainingCalldates'] = after_mask.sum(axis=1)
#         self.product_features['DaysTillNextCallDate'] = (next_calldate - self.product_data['PriceCalculationDateTime']).dt.days
#         self.product_features['DaysToMaturity'] = (self.product_data['Expiration'] - self.product_data['PriceCalculationDateTime']).dt.days
#         self.product_features['DaysSinceIssuing'] = (self.product_data['PriceCalculationDateTime'] - self.product_data['StartDate']).dt.days
#         self.product_features['UnderlyingPrice'] = self.product_data['KoersOLW']
#         self.product_features['Moneyness'] = self.product_data['KoersOLW']/self.product_data['Fixing']
#         self.product_features['Memory'] = self.product_data['Memory']
#         self.product_features['CouponValue'] = self.product_data['CouponValue']

#         div_data = loadmat(r"C:\Users\UGGROO\OneDrive - Van Lanschot Kempen\Documents\MSc Thesis\3. Repos\spil-utilities\spil-core\MainFiles\StoredMarketdataFiles\historicDiv_2025-02-28.mat")
        
#         self.dates = convert_matlab_datenum(pd.DataFrame(div_data['historicDiv']['Dates'][0,0]))
#         self.divs = pd.DataFrame(div_data['historicDiv']['Dividends'][0,0])
#         self.div_dates = convert_matlab_datenum(pd.DataFrame(div_data['historicDiv']['DividendDates'][0,0])).T

#         self.product_data['Date'] = pd.to_datetime(self.product_data['PriceCalculationDateTime'])
#         self.product_data['Calldate 1'] = pd.to_datetime(self.product_data['Calldate 1'])
#         self.product_data['Calldate 2'] = pd.to_datetime(self.product_data['Calldate 2'])
#         self.product_data['Calldate 3'] = pd.to_datetime(self.product_data['Calldate 3'])
#         self.product_data['Calldate 4'] = pd.to_datetime(self.product_data['Calldate 4'])
#         self.product_data['Calldate 5'] = pd.to_datetime(self.product_data['Calldate 5'])
#         self.product_data['Calldate 6'] = pd.to_datetime(self.product_data['Calldate 6'])
#         self.product_data['Calldate 7'] = pd.to_datetime(self.product_data['Calldate 7'])



#     def get_market_features(self):

#         self.market_features = self.market_data[['Date', 'AlphaA', 'AlphaB', 'AlphaC', 'RhoA', 'RhoB', 'RhoC', 'NuB', 'NuC', '1BD', '1WK', '1MO', '2MO', '6MO', '12MO', '2YR', '3YR', '4YR', '5YR', '7YR']]
#         self.market_features.loc['Date'] = pd.to_datetime(self.market_features['Date'])


#     def main_features(self):

        
#         main_idx = self.product_data['Date'].map(lambda x: np.where(self.dates == x)[0][0])

#         for i in range(1, 8):  # Assuming 2 coupon dates for simplicity
#             coupon_col = f'Calldate {i}'

#             # Get the corresponding observationdate column for each row
#             obs_dates = self.div_dates[:, main_idx]  # PxM where M = len(df)

#             # Get dividend yields column corresponding to maindate
#             div_yield_col = self.divs[:, main_idx]  # PxM matrix

#             # Find index in observationdates where coupondate matches
#             mask = (obs_dates.T[:, :, None] == self.product_data[coupon_col].values[:, None, None])  # (M, P, 1)
            
#             # Extract dividend yield values based on mask
#             matched_dividends = np.where(mask, div_yield_col.T[:, :, None], np.nan).sum(axis=1)  # Sum removes unselected values

#             # Append to DataFrame
#             self.product_features[f'Dividendyield{i}'] = matched_dividends[:, 0]

#         self.final_features = self.product_features.merge(self.market_features, on = 'Date', how = 'left')






# import pandas as pd
# import numpy as np

# def append_dividend_yields(product_data, div_dates, divs, market_features):
#     """
#     Append dividend yield values to product_data based on mapping Date to div_dates
#     and matching Calldate columns to div_dates.

#     Parameters:
#         product_data (pd.DataFrame): DataFrame with 'Date' and 'Calldate 1' to 'Calldate 7'.
#         div_dates (pd.DataFrame): PxN DataFrame of observation dates corresponding to divs.
#         divs (pd.DataFrame): PxN DataFrame of dividend yield values.
#         market_features (pd.DataFrame): DataFrame to merge with final features.

#     Returns:
#         pd.DataFrame: product_data with new 'Dividendyield1' to 'Dividendyield7' columns.
#     """

#     # Step 1: Map 'Date' in product_data to the corresponding index in div_dates
#     date_to_col_idx = {date: idx for idx, date in enumerate(div_dates.columns)}

#     # Step 2: Create new columns for dividend yields
#     product_features = product_data.copy()  # To avoid modifying original DataFrame

#     for i in range(1, 8):  # Loop over Calldate 1 to Calldate 7
#         div_yield_col = f'Dividendyield{i}'
#         coupon_col = f'Calldate {i}'

#         def get_div_yield(row):
#             maindate = row['Date']
#             coupondate = row[coupon_col]

#             if maindate in date_to_col_idx:
#                 col_idx = date_to_col_idx[maindate]
                
#                 # Get observation dates for this column
#                 obs_dates_col = div_dates.iloc[:, col_idx]
                
#                 # Find index where observation date matches coupon date
#                 match_mask = obs_dates_col == coupondate
                
#                 if match_mask.any():
#                     return divs.loc[match_mask, divs.columns[col_idx]].values[0]  # Take first match
#             return np.nan  # No match found

#         product_features[div_yield_col] = product_features.apply(get_div_yield, axis=1)

#     # Step 3: Merge with market features
#     final_features = product_features.merge(market_features, on='Date', how='left')

#     return final_features

