import pandas as pd
import numpy as np
import sys
import os


adjacent_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ML Training'))
sys.path.append(adjacent_folder_path)

from features import get_ml_features


from joblib import Parallel, delayed



def generate_feature_path(product_data, market_data, dividends, price_points, n_jobs=8):
    """
    Returns exactly the same (complete_feature_set, path_lengths) as your old function,
    but now KoersOLW is found and UnderlyingPrice / Moneyness are no longer NaN.
    """

    # 1) Prep market_data once, with a true Timestamp Date column
    column_names = [
        'Fixing','AlphaA','AlphaB','AlphaC',
        'RhoA','RhoB','RhoC','NuB','NuC',
        '1BD','1WK','1MO','2MO','3MO','4MO','5MO','6MO','7MO','8MO',
        '9MO','10MO','11MO','12MO','18MO','2YR','3YR','4YR','5YR','7YR',
        '10YR','12YR','15YR','20YR','25YR','30YR','40YR','50YR',
        'Date'
    ]
    md = market_data.copy().reset_index(drop=True)
    # business_days is a DatetimeIndex of Timestamps
    business_days = pd.bdate_range(
        start=product_data['PriceCalculationDateTime'].min() + pd.offsets.BDay(1),
        periods=len(md)
    )
    md['Date'] = business_days
    md.columns = column_names

    # 2) Precompute once all of the t-slices
    market_slices = [md.iloc[:t, :].copy() for t in price_points]

    # 3) worker for one product
    def _process(ix):
        prod_df = product_data.iloc[[ix]].copy().reset_index(drop=True)
        # ensure it's a Timestamp
        start_date = prod_df.at[0, 'PriceCalculationDateTime']
        feats = []

        for j, t in enumerate(price_points):
            slice_df = market_slices[j]  # contains a Timestamp 'Date' and a 'Fixing' column

            # stop if inactive
            if not is_active(prod_df, slice_df[['Date','Fixing']]):
                break

            # advance the calc date
            new_date = start_date + pd.offsets.BDay(t-1)
            
            prod_df.at[0, 'PriceCalculationDateTime'] = new_date

            # pick off the simulated price
            fixing = slice_df.loc[slice_df['Date'].dt.date == new_date.date(), 'Fixing']
            prod_df.at[0, 'KoersOLW'] = fixing.iat[0] if not fixing.empty else np.nan

            # build your ML features exactly as before
            f = get_ml_features(prod_df, slice_df, dividends)
            if f.loc[0, 'Memory'] == 1:
                f.at[0, 'CouponsInMemory'] = compute_couponinmemory(
                    prod_df, 
                    slice_df[['Date','Fixing']], 
                    f.at[0, 'CouponsInMemory']
                )
            feats.append(f)

        return feats
    
    # 4) parallelize over products
    all_feats = Parallel(n_jobs=n_jobs)(
        delayed(_process)(i) for i in range(len(product_data))
    )

    # 5) flatten & concat
    path_lengths = [len(lst) for lst in all_feats]
    flat = [df for sub in all_feats for df in sub]
    complete_feature_set = pd.concat(flat, ignore_index=True)

    return complete_feature_set, path_lengths



def is_active(product_data, underlying):
    # Extract scalar values from single-row DataFrame
    expiration = product_data['Expiration'].iloc[0]
    call_barrier = product_data['CallBarrier'].iloc[0]
    initial_fixing = product_data['Fixing'].iloc[0]

    print('~~~~~~~~~~~~~~~~~~~~~~~~~ PYTHON DATE COMPARISON:')
    print(underlying['Date'].iloc[-1])

    # Check if the product has expired
    if expiration <= underlying['Date'].iloc[-1]:
        print('ML EXPIRED ###################################')
        return False

    # Extract all call dates
    call_dates = [product_data[f'Calldate {n}'].iloc[0] for n in range(1, 8)]

    # Create mask for call dates that are present in underlying
    mask = underlying['Date'].isin(call_dates)

    # If any fixing on those dates exceeds or equals the call level, product has been called
    if (underlying.loc[mask, 'Fixing'] >= (call_barrier/100 * initial_fixing)).any():
        print('ML CALLED $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
        return False

    # Otherwise, the product is still active
    return True



# def compute_couponinmemory(product_data, underlying, initial_couponinmemory):
#     current_date = product_data['PriceCalculationDateTime'].iloc[0]
#     coupon_level = product_data['CouponBarrier'].iloc[0]
#     initial_memory = initial_couponinmemory
#     initial_fixing = product_data['Fixing'].iloc[0]

#     # Gather past or current call dates
#     call_dates = [product_data.get(f'Calldate {n}').iloc[0] for n in range(1, 8)]
#     call_dates = [d for d in call_dates if pd.notnull(d) and d <= current_date]

#     coupon_in_memory = 0
#     memory_was_reset = False

#     for call_date in sorted(call_dates):
#         fixing_row = underlying[underlying['Date'] == call_date]

#         if not fixing_row.empty:
#             fixing = fixing_row['Fixing'].values[0]

#             if fixing < (coupon_level/100 * initial_fixing):
#                 coupon_in_memory += 1
#             else:
#                 # A payout occurred — reset all memory
#                 coupon_in_memory = 0
#                 memory_was_reset = True

#     # If memory was never reset, include starting memory
#     if not memory_was_reset:
#         coupon_in_memory += initial_memory

#     return coupon_in_memory


# def compute_couponinmemory(product_data, underlying, initial_couponinmemory):
#     current_date   = product_data['PriceCalculationDateTime'].iloc[0]
#     coupon_level   = product_data['CouponBarrier'].iloc[0]
#     initial_fixing = product_data['Fixing'].iloc[0]
#     initial_memory = initial_couponinmemory

#     # 1. collect call‑dates that lie in the past (or today)
#     call_dates = [product_data.get(f'Calldate {n}').iloc[0] for n in range(1, 8)]
#     call_dates = [d for d in call_dates if pd.notnull(d) and d <= current_date]

#     coupon_in_memory = 0
#     memory_was_reset = False

#     # 2. iterate through past call‑dates
#     for call_date in sorted(call_dates):
#         # ---- single‑line fix: compare on plain date objects ------------
#         call_dt    = pd.to_datetime(call_date).date()
#         fixing_row = underlying[underlying['Date'].dt.date == call_dt]
#         # ----------------------------------------------------------------

#         if not fixing_row.empty:
#             fixing = fixing_row['Fixing'].values[0]
#             if fixing < (coupon_level / 100.0) * initial_fixing:
#                 coupon_in_memory += 1          # coupon retained in memory
#             else:
#                 coupon_in_memory = 0           # coupon paid, reset memory
#                 memory_was_reset = True

#     # 3. include starting memory if it was never wiped
#     if not memory_was_reset:
#         coupon_in_memory += initial_memory

#     return coupon_in_memory


def compute_couponinmemory(product_data, underlying, initial_couponinmemory):
    current_date   = product_data['PriceCalculationDateTime'].iloc[0]
    coupon_level   = product_data['CouponBarrier'].iloc[0]
    initial_fixing = product_data['Fixing'].iloc[0]
    init_memory    = initial_couponinmemory

    call_dates = [
        d for d in
        (product_data.get(f'Calldate {n}').iloc[0] for n in range(1, 8))
        if pd.notnull(d) and d <= current_date
    ]

    ud_dates = pd.to_datetime(underlying['Date']).dt.date   # <-- robust cast

    coupon_in_memory = 0
    reset_occurred   = False

    for cd in sorted(call_dates):
        row = underlying[ud_dates == pd.to_datetime(cd).date()]
        if not row.empty:
            fixing = row['Fixing'].iat[0]
            if fixing < (coupon_level / 100.0) * initial_fixing:
                coupon_in_memory += 1
            else:
                coupon_in_memory, reset_occurred = 0, True

    if not reset_occurred:
        coupon_in_memory += init_memory

    return coupon_in_memory


# def datetime_to_matlab_datenum(dt):
#     """Convert Python datetime to MATLAB datenum (date only)."""
#     return dt.toordinal() + 366


# def save_matlab_products(product_data):
#     """
#     Creates and saves a MATLAB 1xN struct array using a NumPy structured array.
#     """

#     file_path = r'C:\Users\UGGROO\OneDrive - Van Lanschot Kempen\Documents\MSc Thesis\3. Repos\spil-utilities\spil-core\MainFiles\StoredMarketdataFiles\autocallables.mat'

#     n = len(product_data)

#     # Define structured dtype
#     dtype = np.dtype([
#         ('instrumentId', 'O'),
#         ('callDates', 'O'),
#         ('callLevel', 'O'),
#         ('expirationDate', 'O')
#     ])

#     # Create empty structured array
#     struct_array = np.empty(n, dtype=dtype)

#     for i, (_, row) in enumerate(product_data.iterrows()):
#         instrument_id = float(row['InstrumentId'])
#         call_level = float(row['CallBarrier']) / 100 * float(row['Fixing'])
#         expiration_dn = datetime_to_matlab_datenum(pd.to_datetime(row['Expiration']).to_pydatetime())

#         call_dates = []
#         for j in range(1, 8):
#             col = f'Calldate {j}'
#             if pd.notnull(row.get(col)):
#                 dt = pd.to_datetime(row[col]).to_pydatetime()
#                 call_dates.append(datetime_to_matlab_datenum(dt))
#         call_dates = np.array(call_dates, dtype=float)

#         # Fill struct array entry
#         struct_array[i] = (instrument_id, call_dates, call_level, expiration_dn)

#     # Save as proper MATLAB struct array
#     savemat(file_path, {'autocallables': struct_array})
#     print(f"Saved MATLAB 1x{n} struct array to: {file_path}")





















# def generate_feature_path5(product_data, market_data, dividends, price_points, n_jobs=8):
#     """
#     For each product in product_data and each horizon t in price_points,
#     build the ML feature row (via get_ml_features), stopping when is_active()==False.
#     Returns: (complete_feature_set: DataFrame, path_lengths: List[int])
#     """
#     # 1) Prepare market_data once, with a Timestamp Date column
#     column_names = [
#         'Fixing','AlphaA','AlphaB','AlphaC',
#         'RhoA','RhoB','RhoC','NuB','NuC',
#         '1BD','1WK','1MO','2MO','3MO','4MO','5MO','6MO','7MO','8MO',
#         '9MO','10MO','11MO','12MO','18MO','2YR','3YR','4YR','5YR','7YR',
#         '10YR','12YR','15YR','20YR','25YR','30YR','40YR','50YR',
#         'Date'
#     ]
#     md = market_data.copy().reset_index(drop=True)
#     business_days = pd.bdate_range(
#         start=product_data['PriceCalculationDateTime'].min() + pd.offsets.BDay(1),
#         periods=len(md)
#     )
#     md['Date'] = business_days
#     md.columns = column_names

#     # 2) Precompute the market‐slices for each horizon t
#     market_slices = [md.iloc[:t, :].copy() for t in price_points]

#     # 3) Worker for a single product index
#     def _process_product(idx):
#         prod_df = product_data.iloc[[idx]].copy().reset_index(drop=True)
#         feats = []
#         for j, t in enumerate(price_points):
#             slice_df = market_slices[j]

#             # stop if product no longer active
#             if not is_active(prod_df, slice_df[['Date','Fixing']]):
#                 break

#             # grab the simulated price at horizon t
#             prod_df.at[0, 'KoersOLW'] = slice_df['Fixing'].iat[-1]

#             # build features
#             f = get_ml_features(prod_df, slice_df, dividends)
#             if f.loc[0, 'Memory'] == 1:
#                 f.at[0, 'CouponsInMemory'] = compute_couponinmemory(
#                     prod_df,
#                     slice_df[['Date','Fixing']],
#                     f.at[0, 'CouponsInMemory']
#                 )
#             feats.append(f)

#         return feats

#     # 4) Parallel execution over all products
#     all_feats = Parallel(n_jobs=n_jobs)(
#         delayed(_process_product)(i) for i in range(len(product_data))
#     )

#     # 5) Flatten and concatenate results
#     path_lengths = [len(lst) for lst in all_feats]
#     flat_feats = [df for sublist in all_feats for df in sublist]
#     complete_feature_set = pd.concat(flat_feats, ignore_index=True)

#     return complete_feature_set, path_lengths



# def generate_feature_path2(product_data, market_data, dividends, price_points):
#     column_names = [
#         'Fixing', 'AlphaA', 'AlphaB', 'AlphaC', 'RhoA', 'RhoB', 'RhoC', 'NuB', 'NuC',
#         '1BD', '1WK', '1MO', '2MO', '3MO', '4MO', '5MO', '6MO', '7MO', '8MO',
#         '9MO', '10MO', '11MO', '12MO', '18MO', '2YR', '3YR', '4YR', '5YR', '7YR',
#         '10YR', '12YR', '15YR', '20YR', '25YR', '30YR', '40YR', '50YR', 'Date'
#     ]

#     # Generate business days
#     business_days = pd.bdate_range(start=product_data['PriceCalculationDateTime'].min() + pd.offsets.BDay(1), periods=len(market_data))

#     # Set correct column names and add business days as 'Date'
#     market_data = market_data.copy()
#     market_data['Date'] = business_days
#     market_data.columns = column_names

#     complete_feature_set = []
#     path_lengths = []


#     for index in product_data.index:
#         # Single-row DataFrame to preserve types
#         product_df = product_data.loc[[index]].copy()
#         product_df.reset_index(drop=True, inplace=True)
#         start_date = product_df['PriceCalculationDateTime'].iloc[0]
#         feature_rows = []

#         for t in price_points:
#             market = market_data.iloc[0:t, :].copy()
#             path = market[['Date', 'Fixing']]

#             if not is_active(product_df, path):
#                 break

#             # Update product_df's calculation date
#             new_date = start_date.date() + pd.offsets.BDay(t-1)
#             product_df['PriceCalculationDateTime'] = new_date

#             # Lookup fixing for the new date
#             fixing_value = market.loc[market['Date'].dt.date == new_date.date(), 'Fixing']
#             koers_value = fixing_value.values[0] if not fixing_value.empty else None
#             product_df['KoersOLW'] = koers_value

#             features = get_ml_features(product_df, market, dividends)
#             if features['Memory'].iloc[0] == 1:
#                features['CouponsInMemory'] = compute_couponinmemory(product_df, path, features.get('CouponsInMemory', 0))

#             feature_rows.append(features)
        
#         path_lengths.append(len(feature_rows))
        
#         if feature_rows:
#             complete_feature_set.extend(feature_rows)
            
#     # Concatenate all feature rows
#     complete_feature_set = pd.concat(complete_feature_set, ignore_index=True)
#     return complete_feature_set, path_lengths






# def create_single_struct(product_data):
#     """Creates a single MATLAB-style struct (1x1 with vector fields)."""

#     instrument_ids = []
#     call_levels = []
#     expiration_dates = []
#     call_dates_all = []

#     for _, row in product_data.iterrows():
#         instrument_ids.append(float(row['ExoticOptionId']))

#         call_level = float(row['CallBarrier']) / 100 * float(row['Fixing'])
#         call_levels.append(call_level)

#         expiration = pd.to_datetime(row['Expiration']).to_pydatetime()
#         expiration_dn = expiration.toordinal() + 366
#         expiration_dates.append(expiration_dn)

#         call_dates = []
#         for i in range(1, 8):
#             col = f'Calldate {i}'
#             if pd.notnull(row.get(col)):
#                 dt = pd.to_datetime(row[col]).to_pydatetime()
#                 call_dates.append(dt.toordinal() + 366)
#         call_dates_all.append(np.array(call_dates, dtype=float))  # each inner array = one product

#     # Single struct with vector fields
#     matlab_struct = {
#         'instrumentId': np.array(instrument_ids, dtype=float),
#         'callLevel': np.array(call_levels, dtype=float),
#         'expirationDate': np.array(expiration_dates, dtype=float),
#         'callDates': np.array(call_dates_all, dtype=object)  # makes it a cell array in MATLAB
#     }

#     return matlab_struct















# def generate_feature_path(product_data, market_data, dividends, price_points):
#     column_names = ['Fixing', 'AlphaA', 'AlphaB', 'AlphaC', 'RhoA', 'RhoB', 'RhoC', 'NuB', 'NuC', '1BD', '1WK', '1MO', '2MO', '3MO', '4MO', '5MO', '6MO', '7MO', '8MO',
#                     '9MO', '10MO', '11MO', '12MO', '18MO', '2YR', '3YR', '4YR', '5YR', '7YR', '10YR', '12YR', '15YR', '20YR', '25YR', '30YR', '40YR', '50YR', 
#                     'Euribor3m', 'Euribor6m', 'Euribor12m', 'Date']

#     # Generate business days
#     business_days = pd.bdate_range(start=product_data['PriceCalculationDateTime'].min(), periods=len(market_data))
    
#     # Ensure market_data is a copy to avoid SettingWithCopyWarning
#     market_data = market_data.copy()
#     market_data['Date'] = business_days
#     market_data.columns = column_names

#     complete_feature_set = []

#     for index, product in product_data.iterrows():
#         start_date = product['PriceCalculationDateTime']
#         feature_rows = []

#         for t in price_points:
#             market = market_data.iloc[0:t, :].copy()  # Work with a copy to avoid warnings
#             path = market[['Date', 'Fixing']]

#             if not is_active(product, path):
#                 break

#             product['PriceCalculationDateTime'] = pd.to_datetime(start_date + pd.Timedelta(t, unit='D'))
            
#             # Safely access the 'Fixing' value
#             fixing_value = market.loc[market['Date'] == product['PriceCalculationDateTime'], 'Fixing']
#             if not fixing_value.empty:
#                 product['KoersOLW'] = fixing_value.values[0]
#             else:
#                 product['KoersOLW'] = None  # Handle the case where no matching date is found

#             print(market.dtypes)
#             print('features worden geget')
       
#             features = get_ml_features(product, market, dividends)
#             features['CouponsInMemory'] = compute_couponinmemory(product, path, features.get('CouponsInMemory', 0))

#             feature_rows.append(features)

#         if feature_rows:
#             complete_feature_set.extend(feature_rows)

#     # Concatenate the feature rows into a DataFrame
#     complete_feature_set = pd.concat(complete_feature_set, ignore_index=True)
#     return complete_feature_set




# def generate_feature_path(product_data, market_data, dividends, price_points):
#     column_names = ['Fixing', 'AlphaA', 'AlphaB', 'AlphaC', 'RhoA', 'RhoB', 'RhoC', 'NuB', 'NuC', '1BD', '1WK', '1MO', '2MO', '3MO', '4MO', '5MO', '6MO', '7MO', '8MO',
#                     '9MO', '10MO', '11MO', '12MO', '18MO', '2YR', '3YR', '4YR', '5YR', '7YR', '10YR', '12YR', '15YR', '20YR', '25YR', '30YR', '40YR', '50YR', 
#                     'Euribor3m', 'Euribor6m', 'Euribor12m', 'Date']

#     business_days = pd.bdate_range(start=product_data['PriceCalculationDateTime'].min(), periods=len(market_data))
#     market_data['Date'] = business_days
#     market_data.columns = column_names

#     complete_feature_set = []

#     for index, product in product_data.iterrows():
#         start_date = product['PriceCalculationDateTime']
#         feature_rows = []

#         for t in price_points:
#             market = market_data.iloc[0:t, :]
#             path = market[['Date', 'Fixing']]

#             if not is_active(product, path):
#                 break

#             product['PriceCalculationDateTime'] = start_date + pd.Timedelta(t, unit='D')  
#             product['KoersOLW'] = market.loc[market['Date'] == product['PriceCalculationDateTime'], 'Fixing'].values[0]

#             features = get_features(product, market, dividends)
#             features['CouponInMemory'] = compute_couponinmemory(product_data, path, features['CouponInMemory'])

#             feature_rows.append(features)

#         if feature_rows:
#             complete_feature_set.extend(feature_rows)

#     complete_feature_set = pd.concat(complete_feature_set, ignore_index=True)
#     return complete_feature_set


# def is_active(product_data, underlying):
#     # Check if the product has expired
#     if product_data['Expiration'] <= underlying['Date'].iloc[-1]:
#         return False

#     # Extract all call dates from product_data
#     call_dates = [product_data[f'Calldate {n}'] for n in range(1, 8)]

#     # Create mask for call dates that are present in underlying
#     mask = underlying['Date'].isin(call_dates)

#     # If any fixing on those dates exceeds or equals the call level, product has been called
#     if (underlying.loc[mask, 'Fixing'] >= (product_data['CallBarrier'] * product_data['Fixing'])).any():
#         return False

#     # Otherwise, the product is still active
#     return True




# def compute_couponinmemory(product_data, underlying):
#     current_date = product_data['PriceCalculationDateTime']
#     coupon_level = product_data['CouponLevel']
#     initial_memory = product_data.get('CouponInMemory', 0)

#     # Step 1: Get relevant call dates up to current date
#     call_dates = [
#         product_data.get(f'CallDate{n}') 
#         for n in range(1, 8)
#         if pd.notnull(product_data.get(f'CallDate{n}')) and product_data.get(f'CallDate{n}') <= current_date
#     ]

#     if not call_dates:
#         return initial_memory  # No call dates yet; return starting memory

#     # Step 2: Merge call dates with underlying fixings
#     call_df = pd.DataFrame({'Date': call_dates})
#     merged = call_df.merge(underlying[['Date', 'Fixing']], on='Date', how='left')

#     # Step 3: Identify last reset (where Fixing >= CouponLevel)
#     payout_mask = merged['Fixing'] >= coupon_level
#     if payout_mask.any():
#         last_payout_idx = payout_mask[::-1].idxmax()
#         unpaid_after_last_payout = (~payout_mask.iloc[last_payout_idx+1:]).sum()
#         return unpaid_after_last_payout
#     else:
#         # No payout occurred — all coupons are still in memory
#         total_unpaid = (~payout_mask).sum()
#         return initial_memory + total_unpaid
    

# import pandas as pd

# # Sample product data
# product_data = pd.Series({
#     'PriceCalculationDateTime': pd.Timestamp('2025-05-01'),
#     'CouponLevel': 100,
#     'CouponInMemory': 1,
#     'CallDate1': pd.Timestamp('2025-01-01'),
#     'CallDate2': pd.Timestamp('2025-02-01'),
#     'CallDate3': pd.Timestamp('2025-03-01'),
#     'CallDate4': pd.Timestamp('2025-04-01'),
#     'CallDate5': pd.Timestamp('2025-05-01'),
#     'CallDate6': None,
#     'CallDate7': None
# })

# # Sample underlying data
# underlying = pd.DataFrame({
#     'Date': pd.to_datetime([
#         '2025-01-01', '2025-02-01', '2025-03-01', '2025-04-01', '2025-05-01'
#     ]),
#     'Fixing': [95, 96, 97, 101, 98]  # Only the 4th date has Fixing >= CouponLevel
# })

# # Function under test (use the optimized version you approved earlier)
# coupon_in_memory = compute_couponinmemory(product_data, underlying)

# print("CouponInMemory:", coupon_in_memory)  # Expected output: 1