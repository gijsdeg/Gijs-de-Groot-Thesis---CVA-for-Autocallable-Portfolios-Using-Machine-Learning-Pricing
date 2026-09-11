import pandas as pd
import numpy as np
import pickle
#from util.data.database import DBConnection, get_database_connection_sp
from datetime import datetime, timedelta

def get_productdata():

    # conn = DBConnection(engine=get_database_connection_sp())

    # product_query = '''
    # WITH ExoticSelection AS (
    #     SELECT 
    #         ExoticOptionId,
    #         StartDate,
    #         Expiration,
    #         Strike, 
    #         Currency
    #     FROM 
    #         [StructuredProducts2010].[dbo].[ExoticOption]
    #     WHERE 
    #         InstrumentIdentifierType = 'FundId' 
    #         AND InstrumentIdentifier = 250 
    #         AND OptionType = 'AutoCall' 
    #         AND Exercisetype = 'European'
    #         AND ExoticOptionId IN (   
    #             SELECT 
    #                 ExoticId
    #             FROM 
    #                 [StructuredProducts2010].[dbo].[AutoCallable]
    #             GROUP BY 
    #                 ExoticId
    #             HAVING 
    #                 COUNT(DISTINCT Calllevel) = 1
    #         )
    #         AND ExoticOptionId IN (  
    #             SELECT 
    #                 ExoticId
    #             FROM (
    #                 SELECT 
    #                     ExoticId,
    #                     YEAR(Calldate) AS callYear,
    #                     COUNT(*) AS CountPerYear
    #                 FROM 
    #                     [StructuredProducts2010].[dbo].[AutoCallable]
    #                 GROUP BY 
    #                     ExoticId, YEAR(Calldate)
    #             ) AS YearlyCounts
    #             GROUP BY 
    #                 ExoticId
    #             HAVING 
    #                 MAX(CountPerYear) <= 1
    #         )
    #         AND ExoticOptionId IN (
    #             SELECT
    #                 InstrumentIdentifier
    #             FROM 
    #                 [StructuredProducts2010].[dbo].[InstrumentPricing]
    #             WHERE 
    #                 InstrumentIdentifierType = 'ExoticId'
    #             GROUP BY
    #                 InstrumentIdentifier
    #             HAVING 
    #                 COUNT(*) >= 200
    #             )
    # ),

	# InstrumentIds AS (
	#     SELECT
    #         InstrumentId,
    #         InstrumentIdentifier
    #     FROM 
    #         [StructuredProducts2010].[dbo].[InstrumentInfo]
    #     WHERE
    #         InstrumentIdentifierType = 'ExoticId'
    #         AND InstrumentIdentifier IN (SELECT ExoticOptionId FROM ExoticSelection)
	# ),

    # AutocallInfo AS (
    #     SELECT 
    #         ExoticId,
    #         MAX(Calllevel) AS CallBarrier,
    #         MAX(CouponStrike) AS CouponBarrier,
    #         MAX(Barrier) AS ProtectionBarrier,
    #         MAX(CalllevelShift) AS CallBarrierShift,
    #         MAX(CouponShiftedStrike) AS CouponBarrierShifted,
    #         MAX(ShiftedBarrier) AS ProtectionBarrierShifted,
    #         MAX(CASE WHEN CalldateRank = 1 THEN Calldate ELSE NULL END) AS "Calldate 1",
    #         MAX(CASE WHEN CalldateRank = 2 THEN Calldate ELSE NULL END) AS "Calldate 2",
    #         MAX(CASE WHEN CalldateRank = 3 THEN Calldate ELSE NULL END) AS "Calldate 3",
    #         MAX(CASE WHEN CalldateRank = 4 THEN Calldate ELSE NULL END) AS "Calldate 4",
    #         MAX(CASE WHEN CalldateRank = 5 THEN Calldate ELSE NULL END) AS "Calldate 5",
    #         MAX(CASE WHEN CalldateRank = 6 THEN Calldate ELSE NULL END) AS "Calldate 6",
    #         MAX(CASE WHEN CalldateRank = 7 THEN Calldate ELSE NULL END) AS "Calldate 7",
    #         MAX(CASE WHEN CalldateRank = 1 THEN Coupon END) AS CouponValue,
    #         MAX(Memory) AS Memory
    #     FROM (
    #         SELECT 
    #             *,
    #             ROW_NUMBER() OVER (PARTITION BY ExoticId ORDER BY Calldate) AS CalldateRank
    #         FROM 
    #             [StructuredProducts2010].[dbo].[AutoCallable]
    #         WHERE 
    #             ExoticId IN (SELECT ExoticOptionId FROM ExoticSelection)
    #     ) AS RowNumbers
    #     GROUP BY 
    #         ExoticId
    # ),

    # Prices AS (
    #     SELECT
    #         InstrumentIdentifier,
    #         PriceCalculationDateTime,
    #         Price, 
    #         KoersOLW,
    #         CouponsInMemory,
    #         ROW_NUMBER() OVER (PARTITION BY InstrumentIdentifier, CAST(PriceCalculationDateTime AS DATE) ORDER BY PriceCalculationDateTime) AS PriceRank,
    #         COUNT(*) OVER (PARTITION BY InstrumentIdentifier, CAST(PriceCalculationDateTime AS DATE)) AS NumberOfPrices
    #     FROM 
    #         [StructuredProducts2010].[dbo].[InstrumentPricing]
    #     WHERE 
    #         InstrumentIdentifierType = 'ExoticId'
    #         AND InstrumentIdentifier IN (SELECT ExoticId FROM AutocallInfo)
    #         AND PriceCalculationDateTime >= '2023-06-14'
    # ),

    # Fixing AS (
    #     SELECT 
    #         Date,
    #         Fixing
    #     FROM 
    #         [StructuredProducts2010].[dbo].[FixingTable]
    #     WHERE 
    #         InstrumentIdentifierType = 'FundId' 
    #         AND InstrumentIdentifier = 250
    # )

    # SELECT 
	#     ii.InstrumentId,
    #     es.ExoticOptionId,
    #     es.StartDate,
    #     es.Expiration,
    #     es.Strike,
    #     es.Currency,
    #     ai.CallBarrier,
    #     ai.CouponBarrier,
    #     ai.ProtectionBarrier,
    #     ai.CallBarrierShift,
    #     ai.CouponBarrierShifted,
    #     ai.ProtectionBarrierShifted,
    #     ai.[Calldate 1],
    #     ai.[Calldate 2],
    #     ai.[Calldate 3],
    #     ai.[Calldate 4],
    #     ai.[Calldate 5],
    #     ai.[Calldate 6],
    #     ai.[Calldate 7],
    #     ai.CouponValue,
    #     ai.Memory,
    #     p.PriceCalculationDateTime,
    #     p.Price,
    #     p.KoersOLW,
    #     p.CouponsInMemory,
    #     p.PriceRank,
    #     p.NumberOfPrices,
    #     f.Fixing
    # FROM 
    #     ExoticSelection es
    #     JOIN AutocallInfo ai ON es.ExoticOptionId = ai.ExoticId
    #     JOIN Prices p ON ai.ExoticId = p.InstrumentIdentifier
	# 	JOIN InstrumentIds ii ON p.InstrumentIdentifier = ii.InstrumentIdentifier
    #     JOIN Fixing f ON CAST(es.StartDate AS DATE) = CAST(f.Date AS DATE)
    # WHERE 
    #     p.PriceRank = 1 
    #     OR p.PriceRank = NumberOfPrices
    #     OR p.PriceRank = FLOOR(NumberOfPrices/2) + 1
    # ORDER BY 
    #     ExoticOptionId, PriceCalculationDateTime;
    # ''' 

    # product_data = conn.fetch(product_query)

    # return product_data
    return 



def get_product_selection(exotic_ids, price_date):

    # if not exotic_ids:
    #     raise ValueError("The exotic_ids list cannot be empty.")
    # if not price_date:
    #     raise ValueError("A valid price_date must be provided.")

    # # Format the exotic IDs into a SQL-compatible string
    # formatted_ids = ', '.join(str(int(eid)) for eid in exotic_ids)

    # # Format the date to ensure it's in 'YYYY-MM-DD' string format
    # from datetime import datetime
    # if isinstance(price_date, datetime):
    #     price_date = price_date.strftime('%Y-%m-%d')
    # elif isinstance(price_date, (str, )):
    #     try:
    #         datetime.strptime(price_date, '%Y-%m-%d')
    #     except ValueError:
    #         raise ValueError("price_date must be in 'YYYY-MM-DD' format.")
    # else:
    #     raise TypeError("price_date must be a string or datetime object.")

    # conn = DBConnection(engine=get_database_connection_sp())

    # product_query = f'''
    #     WITH InstrumentIds AS(
    #     SELECT
    #         InstrumentId,
    #         InstrumentIdentifier
    #     FROM 
    #         [StructuredProducts2010].[dbo].[InstrumentInfo]
    #     WHERE
    #         InstrumentIdentifierType = 'ExoticId'
    #         AND InstrumentId IN ({formatted_ids})
    # ),
	
	# ExoticSelection AS (
    #     SELECT
    #         ExoticOptionId,
    #         StartDate,
    #         Expiration,
    #         Strike,
    #         Currency
    #     FROM
    #         [StructuredProducts2010].[dbo].[ExoticOption]
    #     WHERE
    #         InstrumentIdentifierType = 'FundId'
    #         AND InstrumentIdentifier = 250
    #         AND OptionType = 'AutoCall'
    #         AND Exercisetype = 'European'
    #         AND ExoticOptionId IN (
    #             SELECT
    #                 ExoticId
    #             FROM
    #                 [StructuredProducts2010].[dbo].[AutoCallable]
    #             GROUP BY
    #                 ExoticId
    #             HAVING
    #                 COUNT(DISTINCT Calllevel) = 1
    #         )
    #         AND ExoticOptionId IN (SELECT InstrumentIdentifier FROM InstrumentIds)
    # ),

    # AutocallInfo AS (
    #     SELECT
    #         ExoticId,
    #         MAX(Calllevel) AS CallBarrier,
    #         MAX(CouponStrike) AS CouponBarrier,
    #         MAX(Barrier) AS ProtectionBarrier,
    #         MAX(CalllevelShift) AS CallBarrierShift,
    #         MAX(CouponShiftedStrike) AS CouponBarrierShifted,
    #         MAX(ShiftedBarrier) AS ProtectionBarrierShifted,
    #         MAX(CASE WHEN CalldateRank = 1 THEN Calldate ELSE NULL END) AS "Calldate 1",
    #         MAX(CASE WHEN CalldateRank = 2 THEN Calldate ELSE NULL END) AS "Calldate 2",
    #         MAX(CASE WHEN CalldateRank = 3 THEN Calldate ELSE NULL END) AS "Calldate 3",
    #         MAX(CASE WHEN CalldateRank = 4 THEN Calldate ELSE NULL END) AS "Calldate 4",
    #         MAX(CASE WHEN CalldateRank = 5 THEN Calldate ELSE NULL END) AS "Calldate 5",
    #         MAX(CASE WHEN CalldateRank = 6 THEN Calldate ELSE NULL END) AS "Calldate 6",
    #         MAX(CASE WHEN CalldateRank = 7 THEN Calldate ELSE NULL END) AS "Calldate 7",
    #         MAX(CASE WHEN CalldateRank = 1 THEN Coupon END) AS CouponValue,
    #         MAX(Memory) AS Memory
    #     FROM (
    #         SELECT
    #             *,
    #             ROW_NUMBER() OVER (PARTITION BY ExoticId ORDER BY Calldate) AS CalldateRank
    #         FROM
    #             [StructuredProducts2010].[dbo].[AutoCallable]
    #         WHERE
    #             ExoticId IN (SELECT ExoticOptionId FROM ExoticSelection)
    #     ) AS RowNumbers
    #     GROUP BY
    #         ExoticId
    # ),

    # Prices AS (
    #     SELECT *
    #     FROM (
    #         SELECT
    #             InstrumentIdentifier,
    #             PriceCalculationDateTime,
    #             Price,
    #             KoersOLW,
    #             CouponsInMemory,
    #             ROW_NUMBER() OVER (
    #                 PARTITION BY InstrumentIdentifier
    #                 ORDER BY PriceCalculationDateTime DESC
    #             ) AS rn
    #         FROM
    #             [StructuredProducts2010].[dbo].[InstrumentPricing]
    #         WHERE
    #             InstrumentIdentifierType = 'ExoticId'
    #             AND InstrumentIdentifier IN (SELECT ExoticId FROM AutocallInfo)
    #             AND CAST(PriceCalculationDateTime as DATE) = '{price_date}'
    #     ) AS RankedPrices
    #     WHERE rn = 1
    # ),

    # Fixing AS (
    #     SELECT
    #         Date,
    #         Fixing
    #     FROM
    #         [StructuredProducts2010].[dbo].[FixingTable]
    #     WHERE
    #         InstrumentIdentifierType = 'FundId'
    #         AND InstrumentIdentifier = 250
    # )

    # SELECT
	#     ii.InstrumentId,
    #     es.ExoticOptionId,
    #     es.StartDate,
    #     es.Expiration,
    #     es.Strike,
    #     es.Currency,
    #     ai.CallBarrier,
    #     ai.CouponBarrier,
    #     ai.ProtectionBarrier,
    #     ai.CallBarrierShift,
    #     ai.CouponBarrierShifted,
    #     ai.ProtectionBarrierShifted,
    #     ai.[Calldate 1],
    #     ai.[Calldate 2],
    #     ai.[Calldate 3],
    #     ai.[Calldate 4],
    #     ai.[Calldate 5],
    #     ai.[Calldate 6],
    #     ai.[Calldate 7],
    #     ai.CouponValue,
    #     ai.Memory,
    #     p.PriceCalculationDateTime,
    #     p.Price,
    #     p.KoersOLW,
    #     p.CouponsInMemory,
    #     f.Fixing
    # FROM
    #     ExoticSelection es
    # JOIN AutocallInfo ai ON es.ExoticOptionId = ai.ExoticId
    # JOIN Prices p ON ai.ExoticId = p.InstrumentIdentifier
    # JOIN InstrumentIds ii ON p.InstrumentIdentifier = ii.InstrumentIdentifier
    # JOIN Fixing f ON CAST(es.StartDate AS DATE) = CAST(f.Date AS DATE);'''
    # # ORDER BY
    # #     es.ExoticOptionId, p.PriceCalculationDateTime;'''

    # product_data = conn.fetch(product_query)

    # return product_data
    return


def convert_matlab_datenum(df):
    """
    Convert all MATLAB datenumbers in a DataFrame to Python datetime.

    Parameters:
        df (pd.DataFrame): DataFrame containing MATLAB datenumbers.

    Returns:
        pd.DataFrame: DataFrame with converted datetime values.
    """
    matlab_epoch = datetime(1, 1, 1)  # MATLAB starts at year 0000
    matlab_offset = timedelta(days=366)  # MATLAB's offset to Python datetime

    for col in df.columns:
        df[col] = df[col].apply(lambda x: matlab_epoch + timedelta(days=x) - matlab_offset
                                if isinstance(x, (int, float)) else x)
    return df


def load_saved_model(model_path):
    """
    Loads a previously saved sklearn model from disk using pickle.

    Parameters:
    model_path (str): Path to the saved model file.

    Returns:
    sklearn Pipeline: The loaded model.
    """
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    return model































# def get_product_selection(exotic_ids, price_date):
#     from datetime import datetime
#     if not exotic_ids:
#         raise ValueError("The exotic_ids list cannot be empty.")
#     if not price_date:
#         raise ValueError("A valid price_date must be provided.")

#     # Format the exotic IDs into a SQL-compatible string
#     formatted_ids = ', '.join(str(int(eid)) for eid in exotic_ids)

#     # Validate and format date
#     if isinstance(price_date, datetime):
#         price_date = price_date.strftime('%Y-%m-%d')
#     elif isinstance(price_date, str):
#         try:
#             datetime.strptime(price_date, '%Y-%m-%d')
#         except ValueError:
#             raise ValueError("price_date must be in 'YYYY-MM-DD' format.")
#     else:
#         raise TypeError("price_date must be a string or datetime object.")

#     # Generate CASE statement for ORDER BY
#     order_case = "CASE ii.InstrumentId\n"
#     for i, eid in enumerate(exotic_ids, start=1):
#         order_case += f"    WHEN {eid} THEN {i}\n"
#     order_case += "END"

#     conn = DBConnection(engine=get_database_connection_sp())

#     product_query = f'''
#         WITH InstrumentIds AS (
#             SELECT InstrumentId, InstrumentIdentifier
#             FROM [StructuredProducts2010].[dbo].[InstrumentInfo]
#             WHERE InstrumentIdentifierType = 'ExoticId'
#             AND InstrumentId IN ({formatted_ids})
#         ),
#         ExoticSelection AS (
#             SELECT ExoticOptionId, StartDate, Expiration, Strike, Currency
#             FROM [StructuredProducts2010].[dbo].[ExoticOption]
#             WHERE InstrumentIdentifierType = 'FundId'
#             AND InstrumentIdentifier = 250
#             AND OptionType = 'AutoCall'
#             AND Exercisetype = 'European'
#             AND ExoticOptionId IN (
#                 SELECT ExoticId
#                 FROM [StructuredProducts2010].[dbo].[AutoCallable]
#                 GROUP BY ExoticId
#                 HAVING COUNT(DISTINCT Calllevel) = 1
#             )
#             AND ExoticOptionId IN (SELECT InstrumentIdentifier FROM InstrumentIds)
#         ),
#         AutocallInfo AS (
#             SELECT ExoticId,
#                 MAX(Calllevel) AS CallBarrier,
#                 MAX(CouponStrike) AS CouponBarrier,
#                 MAX(Barrier) AS ProtectionBarrier,
#                 MAX(CalllevelShift) AS CallBarrierShift,
#                 MAX(CouponShiftedStrike) AS CouponBarrierShifted,
#                 MAX(ShiftedBarrier) AS ProtectionBarrierShifted,
#                 MAX(CASE WHEN CalldateRank = 1 THEN Calldate ELSE NULL END) AS [Calldate 1],
#                 MAX(CASE WHEN CalldateRank = 2 THEN Calldate ELSE NULL END) AS [Calldate 2],
#                 MAX(CASE WHEN CalldateRank = 3 THEN Calldate ELSE NULL END) AS [Calldate 3],
#                 MAX(CASE WHEN CalldateRank = 4 THEN Calldate ELSE NULL END) AS [Calldate 4],
#                 MAX(CASE WHEN CalldateRank = 5 THEN Calldate ELSE NULL END) AS [Calldate 5],
#                 MAX(CASE WHEN CalldateRank = 6 THEN Calldate ELSE NULL END) AS [Calldate 6],
#                 MAX(CASE WHEN CalldateRank = 7 THEN Calldate ELSE NULL END) AS [Calldate 7],
#                 MAX(CASE WHEN CalldateRank = 1 THEN Coupon END) AS CouponValue,
#                 MAX(Memory) AS Memory
#             FROM (
#                 SELECT *,
#                     ROW_NUMBER() OVER (PARTITION BY ExoticId ORDER BY Calldate) AS CalldateRank
#                 FROM [StructuredProducts2010].[dbo].[AutoCallable]
#                 WHERE ExoticId IN (SELECT ExoticOptionId FROM ExoticSelection)
#             ) AS RowNumbers
#             GROUP BY ExoticId
#         ),
#         Prices AS (
#             SELECT *
#             FROM (
#                 SELECT InstrumentIdentifier, PriceCalculationDateTime, Price, KoersOLW, CouponsInMemory,
#                     ROW_NUMBER() OVER (
#                         PARTITION BY InstrumentIdentifier
#                         ORDER BY PriceCalculationDateTime DESC
#                     ) AS rn
#                 FROM [StructuredProducts2010].[dbo].[InstrumentPricing]
#                 WHERE InstrumentIdentifierType = 'ExoticId'
#                 AND InstrumentIdentifier IN (SELECT ExoticId FROM AutocallInfo)
#                 AND CAST(PriceCalculationDateTime AS DATE) = '{price_date}'
#             ) AS RankedPrices
#             WHERE rn = 1
#         ),
#         Fixing AS (
#             SELECT Date, Fixing
#             FROM [StructuredProducts2010].[dbo].[FixingTable]
#             WHERE InstrumentIdentifierType = 'FundId'
#             AND InstrumentIdentifier = 250
#         )
#         SELECT
#             ii.InstrumentId,
#             es.ExoticOptionId,
#             es.StartDate,
#             es.Expiration,
#             es.Strike,
#             es.Currency,
#             ai.CallBarrier,
#             ai.CouponBarrier,
#             ai.ProtectionBarrier,
#             ai.CallBarrierShift,
#             ai.CouponBarrierShifted,
#             ai.ProtectionBarrierShifted,
#             ai.[Calldate 1],
#             ai.[Calldate 2],
#             ai.[Calldate 3],
#             ai.[Calldate 4],
#             ai.[Calldate 5],
#             ai.[Calldate 6],
#             ai.[Calldate 7],
#             ai.CouponValue,
#             ai.Memory,
#             p.PriceCalculationDateTime,
#             p.Price,
#             p.KoersOLW,
#             p.CouponsInMemory,
#             f.Fixing
#         FROM ExoticSelection es
#         JOIN AutocallInfo ai ON es.ExoticOptionId = ai.ExoticId
#         JOIN Prices p ON ai.ExoticId = p.InstrumentIdentifier
#         JOIN InstrumentIds ii ON p.InstrumentIdentifier = ii.InstrumentIdentifier
#         JOIN Fixing f ON CAST(es.StartDate AS DATE) = CAST(f.Date AS DATE)
#         ORDER BY
#             {order_case};
#     '''

#     product_data = conn.fetch(product_query)
#     return product_data


# def get_product_selection():

#     conn = DBConnection(engine=get_database_connection_sp())

#     product_query = '''
#     WITH ExoticSelection AS (
#         SELECT 
#             ExoticOptionId,
#             StartDate,
#             Expiration,
#             Strike, 
#             Currency
#         FROM 
#             [StructuredProducts2010].[dbo].[ExoticOption]
#         WHERE 
#             InstrumentIdentifierType = 'FundId' 
#             AND InstrumentIdentifier = 250 
#             AND OptionType = 'AutoCall' 
#             AND Exercisetype = 'European'
#             AND ExoticOptionId IN (   
#                 SELECT 
#                     ExoticId
#                 FROM 
#                     [StructuredProducts2010].[dbo].[AutoCallable]
#                 GROUP BY 
#                     ExoticId
#                 HAVING 
#                     COUNT(DISTINCT Calllevel) = 1
#             )
#             AND ExoticOptionId IN (1555, 1562, 1610)
#     ),

#     AutocallInfo AS (
#         SELECT 
#             ExoticId,
#             MAX(Calllevel) AS CallBarrier,
#             MAX(CouponStrike) AS CouponBarrier,
#             MAX(Barrier) AS ProtectionBarrier,
#             MAX(CalllevelShift) AS CallBarrierShift,
#             MAX(CouponShiftedStrike) AS CouponBarrierShifted,
#             MAX(ShiftedBarrier) AS ProtectionBarrierShifted,
#             MAX(CASE WHEN CalldateRank = 1 THEN Calldate ELSE NULL END) AS "Calldate 1",
#             MAX(CASE WHEN CalldateRank = 2 THEN Calldate ELSE NULL END) AS "Calldate 2",
#             MAX(CASE WHEN CalldateRank = 3 THEN Calldate ELSE NULL END) AS "Calldate 3",
#             MAX(CASE WHEN CalldateRank = 4 THEN Calldate ELSE NULL END) AS "Calldate 4",
#             MAX(CASE WHEN CalldateRank = 5 THEN Calldate ELSE NULL END) AS "Calldate 5",
#             MAX(CASE WHEN CalldateRank = 6 THEN Calldate ELSE NULL END) AS "Calldate 6",
#             MAX(CASE WHEN CalldateRank = 7 THEN Calldate ELSE NULL END) AS "Calldate 7",
#             MAX(CASE WHEN CalldateRank = 1 THEN Coupon END) AS CouponValue,
#             MAX(Memory) AS Memory
#         FROM (
#             SELECT 
#                 *,
#                 ROW_NUMBER() OVER (PARTITION BY ExoticId ORDER BY Calldate) AS CalldateRank
#             FROM 
#                 [StructuredProducts2010].[dbo].[AutoCallable]
#             WHERE 
#                 ExoticId IN (SELECT ExoticOptionId FROM ExoticSelection)
#         ) AS RowNumbers
#         GROUP BY 
#             ExoticId
#     ),

#     Prices AS (
#     SELECT *
#         FROM (
#             SELECT
#                 InstrumentIdentifier,
#                 PriceCalculationDateTime,
#                 Price, 
#                 KoersOLW,
#                 CouponsInMemory,
#                 ROW_NUMBER() OVER (
#                     PARTITION BY InstrumentIdentifier 
#                     ORDER BY PriceCalculationDateTime DESC
#                 ) AS rn
#             FROM 
#                 [StructuredProducts2010].[dbo].[InstrumentPricing]
#             WHERE 
#                 InstrumentIdentifierType = 'ExoticId'
#                 AND InstrumentIdentifier IN (SELECT ExoticId FROM AutocallInfo)
#                 AND CAST(PriceCalculationDateTime as DATE) = '2025-05-08'
#         ) AS RankedPrices
#     WHERE rn = 1
#     ),

#     Fixing AS (
#         SELECT 
#             Date,
#             Fixing
#         FROM 
#             [StructuredProducts2010].[dbo].[FixingTable]
#         WHERE 
#             InstrumentIdentifierType = 'FundId' 
#             AND InstrumentIdentifier = 250
#     )

#     SELECT 
#         es.ExoticOptionId,
#         es.StartDate,
#         es.Expiration,
#         es.Strike,
#         es.Currency,
#         ai.CallBarrier,
#         ai.CouponBarrier,
#         ai.ProtectionBarrier,
#         ai.CallBarrierShift,
#         ai.CouponBarrierShifted,
#         ai.ProtectionBarrierShifted,
#         ai.[Calldate 1],
#         ai.[Calldate 2],
#         ai.[Calldate 3],
#         ai.[Calldate 4],
#         ai.[Calldate 5],
#         ai.[Calldate 6],
#         ai.[Calldate 7],
#         ai.CouponValue,
#         ai.Memory,
#         p.PriceCalculationDateTime,
#         p.Price,
#         p.KoersOLW,
#         p.CouponsInMemory,
#         f.Fixing
#     FROM 
#         ExoticSelection es
#         JOIN AutocallInfo ai ON es.ExoticOptionId = ai.ExoticId
#         JOIN Prices p ON ai.ExoticId = p.InstrumentIdentifier
#         JOIN Fixing f ON CAST(p.PriceCalculationDateTime AS DATE) = CAST(f.Date AS DATE)
#     ORDER BY 
#         es.ExoticOptionId, p.PriceCalculationDateTime;'''

#     product_data = conn.fetch(product_query)

#     return product_data































'''
Autocallable should be:
- Vanilla autocall
- European
- FundId 250
- Yearly call dates
- After the structure adjustment
- Calllevel constant
'''


product_data = '''
WITH ExoticSelection AS (
    SELECT 
        ExoticOptionId,
        StartDate,
        Expiration,
        Strike, 
        Currency
    FROM 
        [StructuredProducts2010].[dbo].[ExoticOption]
    WHERE 
        InstrumentIdentifierType = 'FundId' 
        AND InstrumentIdentifier = 250 
        AND OptionType = 'AutoCall' 
        AND Exercisetype = 'European'
        -- This condition only selects autocall for which the calllevel remains constant
        AND ExoticOptionId IN (   
            SELECT 
                ExoticId
            FROM 
                [StructuredProducts2010].[dbo].[AutoCallable]
            GROUP BY 
                ExoticId
            HAVING 
                COUNT(DISTINCT Calllevel) = 1)

        -- This condition makes sure to only select the autocalls with yearly calldates
        AND ExoticOptionId IN (  
            SELECT 
                ExoticId
            FROM (
                SELECT 
                    ExoticId,
                    YEAR(Calldate) AS callYear,
                    COUNT(*) AS CountPerYear
                FROM [StructuredProducts2010].[dbo].[AutoCallable]
                GROUP BY ExoticId, YEAR(Calldate)
            ) AS YearlyCounts
            GROUP BY 
                ExoticId
            HAVING MAX(CountPerYear) <= 1  -- Ensures at most one callDate per year

        -- This condition only takes instruments for which there are at least a certain amount of prices available
        AND ExoticOptionId IN (
            SELECT
                InstrumentIdentifier
            FROM 
                [StructuredProducts2010].[dbo].[InstrumentPricing]
            WHERE 
                InstrumentIdentifierType = 'ExoticId'
            GROUP BY
                InstrumentIdentifier
            HAVING 
                COUNT(*) >= 200)

        AND StartDate >= '2014-01-01'
        )
),


AutocallInfo AS (
    SELECT 
        ExoticId,
        MAX(Calllevel) AS CallBarrier,
        MAX(CouponStrike) AS CouponBarrier,
        MAX(Barrier) AS ProtectionBarrier,
        MAX(CalllevelShift) AS CallBarrierShift,
        MAX(CouponShiftedStrike) AS CouponBarrierShifted,
        MAX(ShiftedBarrier) AS ProtectionBarrierShifted,
        MAX(CASE WHEN CalldateRank = 1 THEN Calldate ELSE NULL END) AS "Calldate 1",
        MAX(CASE WHEN CalldateRank = 2 THEN Calldate ELSE NULL END) AS "Calldate 2",
        MAX(CASE WHEN CalldateRank = 3 THEN Calldate ELSE NULL END) AS "Calldate 3",
        MAX(CASE WHEN CalldateRank = 4 THEN Calldate ELSE NULL END) AS "Calldate 4",
        MAX(CASE WHEN CalldateRank = 5 THEN Calldate ELSE NULL END) AS "Calldate 5",
        MAX(CASE WHEN CalldateRank = 6 THEN Calldate ELSE NULL END) AS "Calldate 6",
        MAX(CASE WHEN CalldateRank = 7 THEN Calldate ELSE NULL END) AS "Calldate 7",
        MAX(CASE WHEN CalldateRank = 1 THEN Coupon END) AS CouponValue,
        MAX(Memory) AS Memory
    FROM (
        SELECT 
            *,
            ROW_NUMBER() OVER (PARTITION BY ExoticId ORDER BY Calldate) AS CalldateRank
        FROM [StructuredProducts2010].[dbo].[AutoCallable]
        WHERE ExoticId IN (SELECT ExoticOptionId FROM ExoticSelection)
    ) AS RowNumbers
    GROUP BY ExoticId
),


Prices AS (
    SELECT
       InstrumentIdentifier,
       PriceCalculationDateTime,
       Price, 
       KoersOLW,
       CouponsInMemory,
       ROW_NUMBER() OVER (PARTITION BY InstrumentIdentifier, CAST(PriceCalculationDateTime AS DATE) ORDER BY PriceCalculationDateTime) AS PriceRank,
       COUNT(*) OVER (PARTITION BY InstrumentIdentifier, CAST(PriceCalculationDateTime AS DATE)) AS NumberOfPrices
    FROM 
       [StructuredProducts2010].[dbo].[InstrumentPricing]
    WHERE 
       InstrumentIdentifierType = 'ExoticId'
       AND InstrumentIdentifier IN (SELECT ExoticId FROM AutocallInfo)
),

Fixing AS (
    SELECT Date,
        Fixing
    FROM [StructuredProducts2010].[dbo].[FixingTable]

    WHERE InstrumentIdentifierType = 'FundId' AND InstrumentIdentifier = 250
)

SELECT 
    es.ExoticOptionId,
    es.StartDate,
    es.Expiration,
    es.Strike,
    es.Currency,
    ai.CallBarrier,
    ai.CouponBarrier,
    ai.ProtectionBarrier,
    ai.CallBarrierShift,
    ai.CouponBarrierShifted,
    ai.ProtectionBarrierShifted,
    ai.[Calldate 1],
    ai.[Calldate 2],
    ai.[Calldate 3],
    ai.[Calldate 4],
    ai.[Calldate 5],
    ai.[Calldate 6],
    ai.[Calldate 7],
    ai.CouponValue,
    ai.Memory,
    p.PriceCalculationDateTime,
    p.Price,
    p.KoersOLW,
    p.CouponsInMemory,
    p.PriceRank,
    p.NumberOfPrices,
    f.Fixing
FROM 
    ExoticSelection es
    JOIN AutocallInfo ai ON es.ExoticOptionId = ai.ExoticId
    JOIN Prices p ON ai.ExoticId = p.InstrumentIdentifier
    JOIN Fixing f ON CAST(p.PriceCalculationDateTime AS DATE) = CAST(f.Date AS DATE)
WHERE 
    p.PriceRank = 1 
    OR p.PriceRank = NumberOfPrices
    OR p.PriceRank = FLOOR(NumberOfPrices/2) + 1;
'''



query2 = '''
WITH Container AS (
    SELECT 
        c.[ContainerId], 
        [PriceCalculationDateTime], 
        Startdate, 
        Expiration, 
        [Price], 
        [InstrumentIdentifierType], 
        ExoticId, 
        KoersOLW
    FROM (
        SELECT 
            c.[ContainerId], 
            [PriceCalculationDateTime], 
            Startdate, 
            Expiration, 
            [Price], 
            KoersOLW
        FROM 
            [StructuredProducts2010].[dbo].[Container] c
        JOIN (
            SELECT 
                ip2.[InstrumentIdentifier] AS ContainerId, 
                ip2.[PriceCalculationDateTime], 
                ip2.[Price], 
                ip2.KoersOLW
            FROM 
                [StructuredProducts2010].[dbo].[InstrumentPricing] ip2
            WHERE 
                ip2.InstrumentIdentifierType = 'ContainerId' 
                AND [InstrumentIdentifier] IN (
                    SELECT 
                        InstrumentIdentifier 
                    FROM 
                        StructuredProducts2010.dbo.InstrumentPricing
                    GROUP BY 
                        InstrumentIdentifier
                    HAVING 
                        COUNT(*) > 1000
                )
        ) AS subquery ON c.[ContainerId] = subquery.[ContainerId]
        WHERE 
            subquery.[PriceCalculationDateTime] BETWEEN '2023-07-04' AND '2024-03-01'
            AND c.[ContainerId] IN (
                SELECT 
                    [InstrumentIdentifier]
                FROM 
                    [StructuredProducts2010].[dbo].[InstrumentInfo]
                WHERE 
                    [Format] IN (5, 13) 
                    AND InstrumentIdentifierType = 'ContainerId'
            )
    ) AS c
    JOIN (
        SELECT 
            [ContainerId], 
            [InstrumentIdentifierType], 
            [InstrumentIdentifier] AS ExoticId
        FROM 
            [StructuredProducts2010].[dbo].[ContainerInstruments]
        WHERE 
            [InstrumentIdentifierType] = 'ExoticId'
    ) AS ci ON c.[ContainerId] = ci.[ContainerId]
),

AutocallableInfo AS (
    SELECT 
        ip.*
    FROM (
        SELECT 
            p.ExoticId,
            MAX(CouponStrike) AS CouponStrike,
            MAX(Barrier) AS Barrier,
            MAX(ShiftedBarrier) AS ShiftedBarrier,
            MAX(CallLevel) AS CallLevel,
            MAX(CASE WHEN rn = 1 THEN CONVERT(varchar(10), Calldate, 120) ELSE '0' END) AS calldate1,
            MAX(CASE WHEN rn = 2 THEN CONVERT(varchar(10), Calldate, 120) ELSE '0' END) AS calldate2,
            MAX(CASE WHEN rn = 3 THEN CONVERT(varchar(10), Calldate, 120) ELSE '0' END) AS calldate3,
            MAX(CASE WHEN rn = 4 THEN CONVERT(varchar(10), Calldate, 120) ELSE '0' END) AS calldate4,
            MAX(CASE WHEN rn = 5 THEN CONVERT(varchar(10), Calldate, 120) ELSE '0' END) AS calldate5,
            MAX(CASE WHEN rn = 6 THEN CONVERT(varchar(10), Calldate, 120) ELSE '0' END) AS calldate6,
            MAX(CASE WHEN rn = 7 THEN CONVERT(varchar(10), Calldate, 120) ELSE '0' END) AS calldate7,
            MAX(CASE WHEN rn = 1 THEN Coupon END) AS CouponValue,
            MAX(Memory) AS Memory,
            MAX(CalllevelShift) AS AutoCallShift,
            MAX(CouponShiftedStrike) AS CouponShift
        FROM (
            SELECT 
                a.ExoticId, 
                a.Calldate, 
                a.Calllevel, 
                a.Coupon, 
                a.Barrier, 
                a.CouponStrike,
                a.ShiftedBarrier, 
                a.Memory, 
                a.CalllevelShift, 
                a.CouponShiftedStrike,
                ROW_NUMBER() OVER (PARTITION BY a.ExoticId ORDER BY a.Calldate) AS rn
            FROM 
                StructuredProducts2010.dbo.AutoCallable a
        ) p
        INNER JOIN (
            SELECT 
                ExoticId
            FROM 
                StructuredProducts2010.dbo.AutoCallable
            GROUP BY 
                ExoticId
            HAVING 
                COUNT(DISTINCT Calllevel) = 1
        ) x ON x.ExoticId = p.ExoticId 
        GROUP BY 
            p.ExoticId
    ) ip
),

ExoticOptions AS (
    SELECT 
        eo.ExoticOptionId, 
        eo.InstrumentIdentifierType, 
        eo.InstrumentIdentifier, 
        eo.OptionType,
        eo.ExerciseType, 
        eo.Expiration, 
        eo.Strike, 
        eo.StrikeType, 
        eo.Currency, 
        eo.StartDate,
        eo.CouponBarrierType, 
        fc.RateId
    FROM 
        StructuredProducts2010.dbo.ExoticOption eo
    INNER JOIN 
        StructuredProducts2010.dbo.FundingCurve fc ON eo.FundingCurve = fc.CurveId
    WHERE 
        eo.StartDate >= '2014-01-01' 
        AND eo.AutoCallVariant = 'Autocallable' 
        AND eo.CouponBarrierType = 'European'
),

BondRate AS (
    SELECT 
        CI.[ContainerId],
        FC.[RateId] AS BondRateId
    FROM 
        [StructuredProducts2010].[dbo].[ContainerInstruments] CI
    JOIN 
        [StructuredProducts2010].[dbo].[Bond] B ON CI.[InstrumentIdentifier] = B.[BondId]
    JOIN 
        [StructuredProducts2010].[dbo].[FundingCurve] FC ON B.[FundingCurve] = FC.[CurveId]
    WHERE 
        CI.[InstrumentIdentifierType] = 'BondId'
),

TotalRowsPerDay AS (
    SELECT 
        ExoticId, 
        CAST(PriceCalculationDateTime AS DATE) AS PriceCalculationDate, 
        COUNT(*) AS TotalRows
    FROM 
        Container
    GROUP BY 
        ExoticId, 
        CAST(PriceCalculationDateTime AS DATE)
),

RankedResults AS (
    SELECT  
        cac.*, 
        eo.Currency, 
        eo.RateId, 
        eo.Strike,
        br.BondRateId,
        ROW_NUMBER() OVER (PARTITION BY cac.ExoticId, CAST(cac.PriceCalculationDateTime AS DATE) ORDER BY CAST(cac.PriceCalculationDateTime AS TIME)) AS row_num_asc,
        ROW_NUMBER() OVER (PARTITION BY cac.ExoticId, CAST(cac.PriceCalculationDateTime AS DATE) ORDER BY CAST(cac.PriceCalculationDateTime AS TIME) DESC) AS row_num_desc,
        ROW_NUMBER() OVER (PARTITION BY cac.ExoticId, CAST(cac.PriceCalculationDateTime AS DATE) ORDER BY CAST(cac.PriceCalculationDateTime AS TIME)) AS row_num,
        trpd.TotalRows
    FROM (
        SELECT 
            Container.ContainerId, 
            Container.Price, 
            Container.KoersOLW, 
            Container.PriceCalculationDateTime,
            Container.Startdate AS StartDate, 
            Container.Expiration,  
            AutocallableInfo.*
        FROM 
            Container
        JOIN 
            AutocallableInfo ON Container.ExoticId = AutocallableInfo.ExoticId
    ) AS cac
    JOIN 
        BondRate br ON br.ContainerId = cac.ContainerId
    JOIN 
        ExoticOptions eo ON cac.ExoticId = eo.ExoticOptionId
    JOIN 
        TotalRowsPerDay trpd ON cac.ExoticId = trpd.ExoticId AND CAST(cac.PriceCalculationDateTime AS DATE) = trpd.PriceCalculationDate
    WHERE 
        eo.OptionType = 'AutoCall' 
        AND eo.InstrumentIdentifier = 250
)

SELECT 
    ContainerId, 
    PriceCalculationDateTime, 
    Price, 
    KoersOLW, 
    StartDate, 
    Expiration, 
    Strike, 
    ExoticId, 
    CouponStrike,
    Barrier, 
    ShiftedBarrier, 
    CallLevel, 
    calldate1, 
    calldate2, 
    calldate3,
    calldate4, 
    calldate5, 
    calldate6, 
    calldate7, 
    CouponValue, 
    Memory,
    AutoCallShift, 
    CouponShift, 
    Currency, 
    RateId, 
    BondRateId
FROM 
    RankedResults
WHERE 
    row_num_asc = 1 
    OR row_num_desc = 1 
    OR row_num = FLOOR(TotalRows / 2) + 1
ORDER BY 
    PriceCalculationDateTime ASC;'''


selectNames = '''
WITH ExoticSelection AS (
    SELECT 
        ExoticOptionId,
        StartDate,
        Expiration,
        Strike, 
        Currency
    FROM 
        [StructuredProducts2010].[dbo].[ExoticOption]
    WHERE 
        InstrumentIdentifierType = 'FundId' 
        AND InstrumentIdentifier = 250 
        AND OptionType = 'AutoCall' 
		--AND AutoCallVariant = 'Autocallable'
        AND Exercisetype = 'European'
        -- This condition only selects autocall for which the calllevel remains constant
        AND ExoticOptionId IN (   
            SELECT 
                ExoticId
            FROM 
                StructuredProducts2010.dbo.AutoCallable
            GROUP BY 
                ExoticId
            HAVING 
                COUNT(DISTINCT Calllevel) = 1)

        -- This condition makes sure to only select the autocalls with yearly calldates
        AND ExoticOptionId IN (  
            SELECT 
                ExoticId
            FROM (
                SELECT 
                    ExoticId,
                    YEAR(Calldate) AS callYear,
                    COUNT(*) AS CountPerYear
                FROM [StructuredProducts2010].[dbo].[AutoCallable]
                GROUP BY ExoticId, YEAR(Calldate)
            ) AS YearlyCounts
            GROUP BY 
                ExoticId
            HAVING MAX(CountPerYear) <= 1  -- Ensures at most one callDate per year
        AND StartDate >= '2020-01-01'
        )
),


AutocallInfo AS (
    SELECT 
        ExoticId,
        MAX(Calllevel) AS CallBarrier,
        MAX(CouponStrike) AS CouponBarrier,
        MAX(Barrier) AS ProtectionBarrier,
        MAX(CalllevelShift) AS CallBarrierShift,
        MAX(CouponShiftedStrike) AS CouponBarrierShifted,
        MAX(ShiftedBarrier) AS ProtectionBarrierShifted,
        MAX(CASE WHEN CalldateRank = 1 THEN Calldate ELSE NULL END) AS "Calldate 1",
        MAX(CASE WHEN CalldateRank = 2 THEN Calldate ELSE NULL END) AS "Calldate 2",
        MAX(CASE WHEN CalldateRank = 3 THEN Calldate ELSE NULL END) AS "Calldate 3",
        MAX(CASE WHEN CalldateRank = 4 THEN Calldate ELSE NULL END) AS "Calldate 4",
        MAX(CASE WHEN CalldateRank = 5 THEN Calldate ELSE NULL END) AS "Calldate 5",
        MAX(CASE WHEN CalldateRank = 6 THEN Calldate ELSE NULL END) AS "Calldate 6",
        MAX(CASE WHEN CalldateRank = 7 THEN Calldate ELSE NULL END) AS "Calldate 7",
        MAX(CASE WHEN CalldateRank = 1 THEN Coupon END) AS CouponValue,
        MAX(Memory) AS Memory
    FROM (
        SELECT 
            *,
            ROW_NUMBER() OVER (PARTITION BY ExoticId ORDER BY Calldate) AS CalldateRank
        FROM [StructuredProducts2010].[dbo].[AutoCallable]
        WHERE ExoticId IN (SELECT ExoticOptionId FROM ExoticSelection)
    ) AS RowNumbers
    GROUP BY ExoticId
),


Prices AS (
    SELECT
       InstrumentIdentifier,
       PriceCalculationDateTime,
       Price, 
       CouponsInMemory,
       ROW_NUMBER() OVER (PARTITION BY InstrumentIdentifier ORDER BY PriceCalculationDateTime) AS PriceRank,
       COUNT(*) OVER (PARTITION BY InstrumentIdentifier, CAST(PriceCalculationDateTime AS DATE)) AS Count
    FROM [StructuredProducts2010].[dbo].[InstrumentPricing]
    WHERE 
       InstrumentIdentifierType = 'ExoticId'
       AND InstrumentIdentifier IN (SELECT ExoticId FROM AutocallInfo)
),

SinglePrices AS (
    SELECT *
	FROM Prices
	WHERE PriceRank = 1
),

UniqueExoticOptions AS (
SELECT es.ExoticOptionId
FROM ExoticSelection es
JOIN AutocallInfo ai ON es.ExoticOptionId = ai.ExoticId
JOIN SinglePrices p ON ai.ExoticId = p.InstrumentIdentifier
)

SELECT 
    c.ContainerDescription
FROM UniqueExoticOptions ueo
JOIN [StructuredProducts2010].[dbo].[ContainerInstruments] ci 
    ON ueo.ExoticOptionId = ci.InstrumentIdentifier
    AND ci.InstrumentIdentifierType = 'ExoticId'
JOIN [StructuredProducts2010].[dbo].[Container] c 
    ON ci.ContainerId = c.ContainerId;'''
