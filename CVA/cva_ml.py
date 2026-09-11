"""
Minimal modifications to allow multiple ML pricing models while keeping
original structure intact. Each model now gets its own CVA series and full
exposure paths saved to disk via pickle. Nothing else has changed.
"""
import tensorflow as tf
import pandas as pd
import numpy as np

import joblib
import pickle
from datetime import datetime
from marketdata import default_probabilities
from sim_engine import SimMarket
from itertools import chain
from path_functions import generate_feature_path
from scipy.io import loadmat

import sys
import os
adjacent_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ML Training'))
sys.path.append(adjacent_folder_path)




# -------------------- CONSTANTS --------------------
R = 0.4
NUM_SIMS = 2
NUM_STEPS = 52 * 5 * 7 + 2  # +2 for two leap years the coming 7 years
RUN_DATE = "2025-07-21"


# -------------------- ML MODELS --------------------
# Add or remove models here – only existing files are loaded.
MODEL_PATHS = {
    "en":  r"C:\Users\14gij\OneDrive\Documenten\1 Master\Thesis\thesis code\ML Training\models\elasticnet_full_model_retuned.pkl",
    "xgb": r"C:\Users\14gij\OneDrive\Documenten\1 Master\Thesis\thesis code\ML Training\models\xgb_full_model_retuned.pkl",
    "nn":  r"C:\Users\14gij\OneDrive\Documenten\1 Master\Thesis\thesis code\ML Training\models\nn_full_model_retuned_3.keras",
    "gpr": r"C:\Users\14gij\OneDrive\Documenten\1 Master\Thesis\thesis code\ML Training\models\gpr_full_model_tuned2.pkl",
}
models = {}
nn_scaler = joblib.load(r"C:\Users\14gij\OneDrive\Documenten\1 Master\Thesis\thesis code\ML Training\models\scaler_retuned_3.pkl")

for name, path in MODEL_PATHS.items():
    try:
        if name == 'nn':
            models[name] = tf.keras.models.load_model(path)
        else:    
            with open(path, "rb") as f:
                models[name] = pickle.load(f)
    
        print(f"Loaded ML model '{name}' from {path}")
    except (FileNotFoundError, IOError):
        print(f"Model '{name}' not found – skipped.")
if not models:
    raise RuntimeError("No ML models could be loaded – aborting.")





# -------------------- PRODUCTS --------------------
# Prepare containers for CVA and exposure paths per model
container_ids = {
    'DANSKE': [17779, 17532, 24619, 24508, 22609],   # 22609 was 23036 before
    'MS':     [24132, 23701, 24177, 24465, 20177],   # 24465 was 22922 or something
    'GS':     [13479, 24440, 23458, 21465, 24123]    
}
all_ids = list(chain.from_iterable(container_ids.values()))

cva = {m: pd.DataFrame(np.full((NUM_SIMS, len(container_ids)), np.nan),
                       columns=container_ids.keys()) for m in models}
exposure_paths = {m: [] for m in models}
pd_paths = []
ml_features = []





# -------------------- PRICE POINTS --------------------
PRICE_POINTS = []
workdays_per_quarter = (365*4+1)/7*5/4/4  # +1 leap day every four years
i = 1
while True:
    t = round(workdays_per_quarter * i)
    if t >= NUM_STEPS:
        break
    PRICE_POINTS.append(t)
    i += 1
PRICE_POINTS = np.array(PRICE_POINTS)
NUM_PRICES = len(PRICE_POINTS)

# Mapping matrix product→container
mapping = pd.DataFrame(0, index=all_ids, columns=container_ids.keys())
for grp, ids in container_ids.items():
    mapping.loc[ids, grp] = 1
mapping.index = mapping.index.astype(str)





# -------------------- PRODUCT DATA --------------------
# product_data = get_product_selection(all_ids, RUN_DATE)
# product_data["InstrumentId"] = pd.Categorical(
#     product_data["InstrumentId"].astype(int), categories=all_ids, ordered=True
# )
# product_data = product_data.sort_values("InstrumentId").reset_index(drop=True)
# product_data['InstrumentId'] = product_data['InstrumentId'].astype(int)

with open(r"C:\Users\14gij\OneDrive\Documenten\1 Master\Thesis\thesis code\CVA\exposure_and_cva_files\productdatadata.pkl", "rb") as fh:
        product_data = pickle.load(fh)


# Dividend curve
dividends = loadmat(r"C:\Users\14gij\OneDrive\Documenten\1 Master\Thesis\thesis code\CVA\exposure_and_cva_files\averageDiv_2025-07-01.mat")


# Discount factors (static)
# disc = discount_rates(PRICE_POINTS)

with open(r"C:\Users\14gij\OneDrive\Documenten\1 Master\Thesis\thesis code\CVA\exposure_and_cva_files\discount_jonge.pkl", "rb") as fh:
        disc = pickle.load(fh)



# -------------------- SIM MARKET --------------------
sim_market = SimMarket(number_of_pcs=5)
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





# -------------------- MAIN LOOP --------------------
for sim in range(NUM_SIMS):
    print(f"\n========== Simulation {sim + 1}/{NUM_SIMS} ==========")

    success = False
    while not success:
        try:
            sim_market.simulate(num_timesteps=NUM_STEPS)
            sim_market.reverse_transform()
            sim_market.clean_sim_market()

            market_data = sim_market.sim_market.iloc[:, :-3]
            hazard_rates = sim_market.sim_market.iloc[:, -3:]
            
            features, path_lengths = generate_feature_path(product_data, market_data, dividends, PRICE_POINTS)
            features = features.drop(columns=['Date'])
            
            col_idx = np.repeat(np.arange(len(all_ids)), path_lengths)
            row_idx = np.concatenate([np.arange(pl) for pl in path_lengths])

            pd_default = default_probabilities(hazard_rates, PRICE_POINTS)
            pd_paths.append(pd_default)

            price_store = []

            # --- Price & CVA for every loaded model ---
            for name, mdl in models.items():
                if name == 'nn':
                    features_scaled = nn_scaler.transform(features)
                    prices = mdl.predict(features_scaled).flatten()
                else:
                    prices = mdl.predict(features)

                price_store.append(prices)

                mtx = np.zeros((NUM_PRICES, len(all_ids)), dtype=float)
                mtx[row_idx, col_idx] = prices
                
                exposure = np.maximum(mtx.dot(mapping), 0)   
                exposure_paths[name].append(exposure)  
                cva[name].iloc[sim] = ((1 - R) * exposure * pd_default * disc[:, None]).sum(axis=0)

            price_mat  = np.column_stack(price_store) 
            price_cols = [f"price_{name}" for name in models]
            price_df   = pd.DataFrame(price_mat, columns=price_cols, index=features.index)

            sim_df = pd.concat([features, price_df], axis=1)
            sim_df["Simulation"] = sim + 1 
            ml_features.append(sim_df)

            success = True

        except Exception as e:
            print(f"Simulation failed: {e}. Retrying...")
       




# -------------------- RESULTS --------------------

current_date = datetime.now().strftime('%Y-%m-%d')

features_prices = pd.concat(ml_features, ignore_index=True)

# with open(rf"C:\Users\UGGROO\OneDrive - Van Lanschot Kempen\Documents\MSc Thesis\3. Repos\thesis code\CVA\exposure_and_cva_files\features_prices_final6_{current_date}.pkl", "wb") as fh:
#     pickle.dump(features_prices, fh)

# with open(rf"C:\Users\UGGROO\OneDrive - Van Lanschot Kempen\Documents\MSc Thesis\3. Repos\thesis code\CVA\exposure_and_cva_files\cva_final6_{current_date}.pkl", "wb") as fh:
#     pickle.dump(cva, fh)

# with open(rf"C:\Users\UGGROO\OneDrive - Van Lanschot Kempen\Documents\MSc Thesis\3. Repos\thesis code\CVA\exposure_and_cva_files\pd_final6_{current_date}.pkl", "wb") as fh:
#     pickle.dump(pd_paths, fh)

# for name, paths in exposure_paths.items():
#     with open(rf"C:\Users\UGGROO\OneDrive - Van Lanschot Kempen\Documents\MSc Thesis\3. Repos\thesis code\CVA\exposure_and_cva_files\exposures_final6_{name}_{current_date}.pkl", "wb") as fh:
#         pickle.dump(paths, fh)




# Compute & display mean CVA per model
cva_final = {name: df.mean() for name, df in cva.items()}

print("\n========== Mean CVA by model ==========")
for name, series in cva_final.items():
    print(f"\n{name}:")
    print(series)
















