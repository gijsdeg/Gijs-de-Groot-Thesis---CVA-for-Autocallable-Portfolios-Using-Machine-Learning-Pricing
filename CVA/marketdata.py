
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#from util.data.database import DBConnection, get_database_connection_sp
from scipy.interpolate import CubicSpline
from scipy.interpolate import interp1d
from scipy.optimize import root_scalar

# Obtain cds spreads for goldman, morgan stanley, danske


# def get_marketdata():
#     conn = DBConnection(engine=get_database_connection_sp())
#     conn_market = DBConnection(engine=get_database_connection_sp(specific_db='RMMarketData'))
    
#     yield_query = '''WITH LatestObservations AS (
#                 SELECT 
#                     YieldCurveId, 
#                     ModifyDate, 
#                     RateId, 
#                     [1BD], [1WK], [1MO], [2MO], [3MO], [4MO], [5MO], [6MO], [7MO], [8MO],
#                     [9MO], [10MO], [11MO], [12MO], [18MO], [2YR], [3YR], [4YR], [5YR], [7YR],
#                     [10YR], [12YR], [15YR], [20YR], [25YR], [30YR], [40YR], [50YR],
#                     ROW_NUMBER() OVER (
#                         PARTITION BY CAST(ModifyDate AS DATE), RateId
#                         ORDER BY ModifyDate DESC
#                     ) AS RowNum
#                 FROM StructuredProducts2010.dbo.YieldCurve
#                 WHERE 
#                     (RateId = 4 AND ModifyDate BETWEEN '2014-01-01' AND '2019-10-31')
#                     OR (RateId = 56 AND ModifyDate >= '2014-01-01')
#             )

#             SELECT 
#                 YieldCurveId, 
#                 ModifyDate, 
#                 RateId, 
#                 [1BD], [1WK], [1MO], [2MO], [3MO], [4MO], [5MO], [6MO], [7MO], [8MO],
#                 [9MO], [10MO], [11MO], [12MO], [18MO], [2YR], [3YR], [4YR], [5YR], [7YR],
#                 [10YR], [12YR], [15YR], [20YR], [25YR], [30YR], [40YR], [50YR]
#             FROM LatestObservations
#             WHERE RowNum = 1
#             ORDER BY ModifyDate'''
#     yield_curves = conn.fetch(yield_query)

#     fixing_query = '''SELECT [Date]
#         ,[Fixing]
#     FROM [StructuredProducts2010].[dbo].[FixingTable]

#     where [InstrumentIdentifierType]='FundId' and
#         [InstrumentIdentifier]=250

#         order by Date'''
#     fixing_prices = conn.fetch(fixing_query)

#     sabr_query = '''SELECT [AlphaA]
#         ,[AlphaB]
#         ,[AlphaC]
#         ,[RhoA]
#         ,[RhoB]
#         ,[RhoC]
#         ,[NuA]
#         ,[NuB]
#         ,[NuC]
#         ,[Modifydatetime]
#         ,[FundId]
#         ,[RefPrice]
#         ,[AlphaMin]
#         ,[AlphaMax]
#         ,[AlphaCut]
#         ,[RhoMin]
#         ,[RhoMax]
#         ,[RhoCut]
#         ,[NuMin]
#         ,[NuMax]
#         ,[NuCut]
#         ,[Active]
#         ,[FundType]
#         ,[ActiveSCPro]
#         ,[Id]
#     FROM [StructuredProducts2010].[dbo].[SABRParametrisatie]

#     WHERE [FundId]=250

#     order by Modifydatetime'''
#     sabr_params = conn.fetch(sabr_query)

#     cds_query = '''SELECT 
#             [PriceDate],
#             MAX(CASE WHEN BBTicker = 'DANBNK CDS EUR SR 5Y D14 Corp' THEN [Price] END) AS DANBNK_Price,
#             MAX(CASE WHEN BBTicker = 'MS CDS USD SR 5Y Corp' THEN [Price] END) AS MS_Price,
#             MAX(CASE WHEN BBTicker = 'GS CDS USD SR 5Y Corp' THEN [Price] END) AS GS_Price
#         FROM 
#             [RMMarketData].[dbo].[CDS]
#         WHERE 
#             BBTicker IN ('DANBNK CDS EUR SR 5Y D14 Corp', 'MS CDS USD SR 5Y Corp', 'GS CDS USD SR 5Y Corp')
#         GROUP BY 
#             [PriceDate]
#         ORDER BY 
#             [PriceDate]
#     '''
#     cds_spreads = conn_market.fetch(cds_query)

#     fixing_prices = fixing_prices[fixing_prices['Date'] >= '2014-01-01']
#     fixing_prices['Date'] = fixing_prices['Date'].dt.date

#     sabr_params['Date'] = sabr_params['Modifydatetime'].dt.date
#     sabr_params = sabr_params.loc[sabr_params.groupby('Date')['Modifydatetime'].idxmax()]

#     sabr_merge = pd.merge(fixing_prices, sabr_params, how = 'left', on = 'Date')
#     fill_columns = ['AlphaA', 'AlphaB', 'AlphaC', 'RhoA', 'RhoB', 'RhoC', 'NuA', 'NuB', 'NuC']
#     sabr_merge[fill_columns] = sabr_merge[fill_columns].ffill()

#     yield_curves['Date'] = yield_curves['ModifyDate'].dt.date
#     yield_merge = pd.merge(sabr_merge, yield_curves, how = 'left', on = 'Date')

#     cds_spreads['Date'] = pd.to_datetime(cds_spreads['PriceDate'], format='%Y-%d-%m').dt.date
#     total = pd.merge(yield_merge, cds_spreads, how = 'left', on = 'Date')

#     columns = ['Fixing', 'AlphaA', 'AlphaB', 'AlphaC', 'RhoA', 'RhoB', 'RhoC', 'NuB', 'NuC', '1BD', '1WK', '1MO', '2MO', '3MO', '4MO', '5MO', '6MO', '7MO', '8MO',
#                     '9MO', '10MO', '11MO', '12MO', '18MO', '2YR', '3YR', '4YR', '5YR', '7YR', '10YR', '12YR', '15YR', '20YR', '25YR', '30YR', '40YR', '50YR', 
#                     'DANBNK_Price', 'MS_Price', 'GS_Price', 'Date']
    
#     total = total[columns]  
#     # print(total.isna().any(axis=1).sum())

#     # To remove or to ffill observations with missing yields
#     # total.dropna(inplace=True)
#     total.ffill(inplace=True)

#     return total


def hazard_rate(cds_spreads):
    R = 0.4
    hazard_rates = cds_spreads/(10000*(1-R))/252

    return hazard_rates



# def discount_rates(price_points):
#     # Connect to the database
#     conn = DBConnection(engine=get_database_connection_sp())
    
#     # Query the most recent yield curve
#     curve_query = '''SELECT TOP 1  
#             [1BD], [1WK], [1MO], [2MO], [3MO], [4MO], [5MO], [6MO], [7MO], [8MO],
#             [9MO], [10MO], [11MO], [12MO], [18MO], [2YR], [3YR], [4YR], [5YR], [7YR],
#             [10YR], [12YR], [15YR], [20YR], [25YR], [30YR], [40YR], [50YR]
#         FROM StructuredProducts2010.dbo.YieldCurve
#         WHERE RateId = 56 
#         ORDER BY ModifyDate DESC'''
    
#     #AND ModifyDate = '2025-07-25'
    
#     # Fetch the yield curve data
#     recent_curve = conn.fetch(curve_query)
    
#     # Define the maturities corresponding to the yield curve data (in years)
#     maturities = np.array([1/365, 7/365, 1/12, 2/12, 3/12, 4/12, 5/12, 6/12, 
#                            7/12, 8/12, 9/12, 10/12, 11/12, 1, 1.5, 2, 3, 4, 
#                            5, 7, 10, 12, 15, 20, 25, 30, 40, 50])  
    
#     # Extract the yield curve rates (assuming the data is in the first row)
#     yield_rates = recent_curve.iloc[0].values / 100  # Convert from percentage to decimals
    
#     # Apply cubic spline interpolation
#     days = maturities * 365  # Convert maturities to days for interpolation
#     spline = CubicSpline(days, yield_rates, extrapolate=True)
    
#     # Interpolated yield rates for the given price_points (in days)
#     interpolated_yield_rates = spline(price_points)
    
#     # Convert interpolated yield rates to discount factors using continuous compounding
#     discount_factors = np.exp(-interpolated_yield_rates * (price_points / 365))
    
#     return discount_factors
    


# def default_probabilities(hazard_rates_df: pd.DataFrame,
#                           price_points) -> pd.DataFrame:
#     """
#     Computes the probability of default in each period, conditional on
#     survival to the start of that period.

#     Parameters
#     ----------
#     hazard_rates_df : pd.DataFrame
#         Daily instantaneous hazard rates (one column per counter-party).
#         The index can be integers (0, 1, 2, …) or date labels.
#     price_points : 1-D array-like
#         Labels or 0-based positions of the final day of each period,
#         in strictly increasing order.

#     Returns
#     -------
#     pd.DataFrame
#         Index : 'Period_1', … 'Period_n' (n = len(price_points))
#         Columns : same as hazard_rates_df.columns
#         Values  : P(default in that period | no default before its start).
#     """
#     if len(price_points) == 0:
#         raise ValueError("price_points must contain at least one element.")

#     # --- Ensure periods are strictly increasing -----------------------------
#     price_idx = pd.Index(price_points)
#     if not price_idx.is_monotonic_increasing:
#         raise ValueError("price_points must be strictly increasing.")

#     # --- Cumulative hazard Λ(t) ---------------------------------------------
#     cum_hazard = hazard_rates_df.cumsum()

#     # --- Λ(T_j) at each period end T_j --------------------------------------
#     if set(price_idx).issubset(cum_hazard.index):
#         Λ_T = cum_hazard.loc[price_idx]      # price_points are labels
#     else:
#         Λ_T = cum_hazard.iloc[price_idx]     # price_points are positions

#     # --- Incremental hazard ΔΛ = Λ(T_j) − Λ(T_{j-1}) -------------------------
#     ΔΛ = Λ_T.diff().fillna(Λ_T)              # first period: Λ(T₁) − 0

#     # --- Conditional default probability in each period ---------------------
#     cond_default = 1 - np.exp(-ΔΛ)           # 1 − exp(−ΔΛ)

#     # --- Tidy index labels ---------------------------------------------------
#     cond_default.index = [f"Period_{i+1}" for i in range(len(price_points))]

#     return cond_default


def default_probabilities(hazard_rates_df: pd.DataFrame,
                          price_points) -> pd.DataFrame:
    """
    Computes the **unconditional** probability of default in each period
    (i.e., the probability that default occurs in that period, not
    conditional on survival).

    Parameters
    ----------
    hazard_rates_df : pd.DataFrame
        Daily instantaneous hazard rates (one column per counter-party).
        The index can be integers (0, 1, 2, …) or date labels.
    price_points : 1-D array-like
        Labels or 0-based positions of the final day of each period,
        in strictly increasing order.

    Returns
    -------
    pd.DataFrame
        Index : 'Period_1', … 'Period_n' (n = len(price_points))
        Columns : same as hazard_rates_df.columns
        Values  : P(default in that period) = e^{-Λ_{i-1}} - e^{-Λ_i}.
    """
    if len(price_points) == 0:
        raise ValueError("price_points must contain at least one element.")

    price_idx = pd.Index(price_points)
    if not price_idx.is_monotonic_increasing:
        raise ValueError("price_points must be strictly increasing.")

    # Cumulative hazard Λ(t)
    cum_hazard = hazard_rates_df.cumsum()

    # Λ(T_i) at each period end
    if set(price_idx).issubset(cum_hazard.index):
        Lambda_T = cum_hazard.loc[price_idx]   # price_points are labels
    else:
        Lambda_T = cum_hazard.iloc[price_idx]  # price_points are positions

    # Previous period cumulative hazard Λ(T_{i-1}); Λ(T_0)=0
    Lambda_prev = Lambda_T.shift(fill_value=0.0)

    # Unconditional default increment: e^{-Λ_{i-1}} - e^{-Λ_i}
    uncond_default = np.exp(-Lambda_prev) - np.exp(-Lambda_T)

    # Tidy index labels
    uncond_default.index = [f"Period_{i+1}" for i in range(len(price_points))]

    return uncond_default




# def default_probabilities2(hazard_rates_df, price_points):
#     """
#     Computes default probabilities for each period given no earlier default.

#     Parameters:
#     - hazard_rates_df: DataFrame, daily instantaneous hazard rates for multiple counterparties (columns).
#     - price_points: NumPy array, indices marking the last day of each period.

#     Returns:
#     - DataFrame: Default probabilities for each counterparty (columns) and period (rows).
#     """

#     # Cumulative sum of hazard rates for each counterparty
#     cumulative_hazard_rates = hazard_rates_df.cumsum()

#     # Extract cumulative hazard rates at the end of each period
#     cumulative_hazard_at_periods = cumulative_hazard_rates.iloc[price_points].values

#     # Compute cumulative default probabilities D(T) = 1 - exp(-cumulative hazard)
#     cumulative_default_probs = 1 - np.exp(-cumulative_hazard_at_periods)

#     # Shift cumulative default probabilities to get D(T-1), setting the first period to zero
#     cumulative_default_probs_shifted = np.vstack([np.zeros((1, cumulative_default_probs.shape[1])), 
#                                                   cumulative_default_probs[:-1]])

#     # Compute conditional default probabilities for each period
#     conditional_default_probs = (cumulative_default_probs - cumulative_default_probs_shifted) / \
#                                 (1 - cumulative_default_probs_shifted)

#     # Create a DataFrame for the output with appropriate labels
#     default_probs_df = pd.DataFrame(conditional_default_probs, 
#                                     index=[f'Period_{i+1}' for i in range(len(price_points))],
#                                     columns=hazard_rates_df.columns)

#     return default_probs_df



def plot_surface(data):
    # Assuming data is a 2D NumPy array of shape (2343, 227)
    num_rows, num_cols = data.shape

    # Create a meshgrid for plotting
    X, Y = np.meshgrid(np.arange(num_cols), np.arange(num_rows))
    Z = data

    # Create the plot
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')

    # Plot the surface
    surf = ax.plot_surface(X, Y, Z, cmap='viridis')

    # Add labels
    ax.set_xlabel('Column Index')
    ax.set_ylabel('Row Index')
    ax.set_zlabel('Value')

    # Add a color bar
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)

    plt.show()





























    # euribor_rates['Date'] = euribor_rates['Date'].dt.date
    # euribor_merge = pd.merge(sabr_merge, euribor_rates, how = 'left', on = 'Date')

    # cds_query = '''SELECT A.[PriceDate], A.[Price]
    #     FROM [RMMarketData].[dbo].[CDS] A
    #     LEFT JOIN [RMMarketData].[dbo].[GenericCDSMap] B
    #     ON A.BBTicker = B.BBTicker 
    #     WHERE ReferenceEntity = 'Morgan Stanley Int PLC' AND Tenor = 5
    # '''

        # cds_query = '''SELECT [PriceDate], [Price]
    #     FROM [RMMarketData].[dbo].[CDS] 
    #     WHERE BBTicker = 'DANBNK CDS EUR SR 5Y D14 Corp' 
    #     ORDER BY PriceDate
    # '''

        # euribor_query = '''SELECT [Date],
    #      [1] AS Euribor6m,
    #      [2] AS Euribor12m,
    #      [3] AS Euribor3m
    # FROM
    #     (SELECT [Date], Fixing, InstrumentIdentifier
    #     FROM [StructuredProducts2010].[dbo].[FixingTable]
    #     WHERE InstrumentIdentifierType = 'RateId'
    #     AND InstrumentIdentifier IN (1, 2, 3)) AS SourceTable
    # PIVOT
    #     (MAX(Fixing)
    #     FOR InstrumentIdentifier IN ([1], [2], [3])) AS PivotTable

    # ORDER BY [Date] ASC'''
    # euribor_rates = conn.fetch(euribor_query)



    

# def bootstrap_cds(tenors, spreads, yield_curve, freq_prem, freq_prot, recovery, num_days_in_a_year, premium_accrual):
#     """
#     Bootstraps cumulative probabilities of default (PDs) and hazard rates 
#     from CDS spreads assuming a piecewise flat hazard rate process.
#     """
#     # Initialize payment times
#     years_prem = np.arange(1, int(tenors[-1] * freq_prem) + 1) / freq_prem
#     years_prot = np.arange(1, int(tenors[-1] * freq_prot) + 1) / freq_prot

#     relevant_prem = np.concatenate(([0], years_prem))
#     relevant_prot = np.concatenate(([0], years_prot))

#     # Calculate discount bond prices
#     bond_price_prem = np.exp(-yield_curve[np.round(years_prem * num_days_in_a_year).astype(int)] * years_prem)
#     bond_price_prot = np.exp(-yield_curve[np.round(years_prot * num_days_in_a_year).astype(int)] * years_prot)

#     # Initialize variables
#     delta = np.diff([0] + list(tenors))
#     lambda_ = np.full(len(tenors), np.nan)
#     sp = np.full(len(relevant_prem), np.nan)
#     sp2 = np.full(len(relevant_prot), np.nan)
#     value_prem = np.full(len(tenors), np.nan)
#     value_prot = np.full(len(tenors), np.nan)

#     # Initial guess for hazard rate
#     h0 = 0.01

#     # Calculate first hazard rate
#     def objfunc(h):
#         term1 = (1 - recovery) * np.sum(
#             bond_price_prot[:freq_prot] * (
#                 np.exp(-h * relevant_prot[:freq_prot]) - np.exp(-h * relevant_prot[1:freq_prot + 1])
#             )
#         )
#         term2 = spreads[0] / 10000 * np.sum(
#             bond_price_prem[:freq_prem] / freq_prem * (
#                 np.exp(-h * relevant_prem[1:freq_prem + 1]) +
#                 premium_accrual / 2 * (
#                     np.exp(-h * relevant_prem[:freq_prem]) - np.exp(-h * relevant_prem[1:freq_prem + 1])
#                 )
#             )
#         )
#         return term1 - term2

#     result = root_scalar(objfunc, bracket=[0, 1], method='brentq')
#     lambda_[0] = result.root

#     # Calculate SPs and initial values of premium and protection legs
#     sp[:freq_prem + 1] = np.exp(-lambda_[0] * relevant_prem[:freq_prem + 1])
#     sp2[:freq_prot + 1] = np.exp(-lambda_[0] * relevant_prot[:freq_prot + 1])

#     value_prem[0] = spreads[0] / 10000 * np.sum(
#         bond_price_prem[:freq_prem] / freq_prem * (
#             sp[1:freq_prem + 1] +
#             premium_accrual / 2 * (sp[:freq_prem] - sp[1:freq_prem + 1])
#         )
#     )

#     value_prot[0] = (1 - recovery) * np.sum(
#         bond_price_prot[:freq_prot] * (sp2[:freq_prot] - sp2[1:freq_prot + 1])
#     )

#     # Bootstrap hazard rates
#     for k in range(1, len(tenors)):
#         prev_exp = -np.sum(delta[:k] * lambda_[:k])
#         low_prot = slice(freq_prot * tenors[k - 1], freq_prot * tenors[k])
#         high_prot = slice(freq_prot * tenors[k - 1] + 1, freq_prot * tenors[k] + 1)
#         low_prem = slice(freq_prem * tenors[k - 1], freq_prem * tenors[k])
#         high_prem = slice(freq_prem * tenors[k - 1] + 1, freq_prem * tenors[k] + 1)

#         def objfunc(h):
#             term1 = value_prot[k - 1] + (1 - recovery) * np.sum(
#                 bond_price_prot[low_prot] * (
#                     np.exp(prev_exp - h * (relevant_prot[low_prot] - tenors[k - 1])) -
#                     np.exp(prev_exp - h * (relevant_prot[high_prot] - tenors[k - 1]))
#                 )
#             )
#             term2 = spreads[k] * value_prem[k - 1] / spreads[k - 1]
#             term3 = spreads[k] / 10000 * np.sum(
#                 bond_price_prem[low_prem] / freq_prem * (
#                     np.exp(prev_exp - h * (relevant_prem[high_prem] - tenors[k - 1])) +
#                     premium_accrual / 2 * (
#                         np.exp(prev_exp - h * (relevant_prem[low_prem] - tenors[k - 1])) -
#                         np.exp(prev_exp - h * (relevant_prem[high_prem] - tenors[k - 1]))
#                     )
#                 )
#             )
#             return term1 - term2 - term3

#         result = root_scalar(objfunc, bracket=[0, 1], method='brentq')
#         lambda_[k] = result.root

#         # Update SPs and values
#         sp[high_prem] = np.exp(prev_exp - lambda_[k] * (relevant_prem[high_prem] - tenors[k - 1]))
#         sp2[high_prot] = np.exp(prev_exp - lambda_[k] * (relevant_prot[high_prot] - tenors[k - 1]))

#         value_prem[k] = spreads[k] * value_prem[k - 1] / spreads[k - 1] + spreads[k] / 10000 * np.sum(
#             bond_price_prem[low_prem] / freq_prem * (
#                 sp[high_prem] + premium_accrual / 2 * (sp[low_prem] - sp[high_prem])
#             )
#         )

#         value_prot[k] = value_prot[k - 1] + (1 - recovery) * np.sum(
#             bond_price_prot[low_prot] * (sp2[low_prot] - sp2[high_prot])
#         )

#     # Calculate cumulative PDs
#     cum_pd = 1 - sp[1:]

#     return years_prem, cum_pd, lambda_
