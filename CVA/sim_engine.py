import numpy as np
import scipy.stats as stats
import warnings
import pmdarima as pm
import statsmodels.api as sm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import os

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from marketdata import hazard_rate
from statsmodels.distributions.copula.api import GaussianCopula, StudentTCopula
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
from scipy.stats import norm, t
from scipy.optimize import minimize
from scipy.linalg import cholesky, solve_triangular
from copulae import StudentCopula, pseudo_obs
from scipy.stats import skew, kurtosis



class SimMarket:
    """
    A class to perform PCA and simulate market data

    Attributes
    ----------
    market_data : pd.DataFrame
        A class variable that holds market data.

    Methods
    -------
    __init__():
        Initializes the MarketSimulator instance.
    display_market_data():
        Prints the market data.
    """

    path = r"C:\Users\14gij\OneDrive\Documenten\1 Master\Thesis\thesis code\CVA\exposure_and_cva_files\marketdatadata.pkl"
    with open(path, "rb") as fh:
        markt = pickle.load(fh)
    
    # Set class variables
    market_data = markt


    def __init__(self, number_of_pcs = None):
        self.transformed_market_data = pd.DataFrame()
        self.number_of_pcs = number_of_pcs
        self.scaler = StandardScaler()
        self.pc_object = None
        self.pcs = pd.DataFrame()
        self.models = pd.Series()
        self.errors = pd.DataFrame()
        self.error_distributions = pd.Series()
        self.uniform_errors = pd.DataFrame()
        self.gaussian_params = None
        self.student_t_params = None
        self.sim_pcs = pd.DataFrame()
        self.sim_market = pd.DataFrame()
        self.sims = None
        self.raw_sims = None


    def transform_market_data(self, hazard = True, log_returns = True, sabr_diff = False, yield_diff = False, log_hazard_return = True):
        market_copy = self.market_data.copy(deep=True)
        
        if hazard:
            market_copy.iloc[:, 37:40] = market_copy.iloc[:, 37:40].apply(hazard_rate)
            market_copy.rename(columns={'DANBNK_Price': 'DANBNK_Hazard'}, inplace=True)
            market_copy.rename(columns={'MS_Price': 'MS_Hazard'}, inplace=True)
            market_copy.rename(columns={'GS_Price': 'GS_Hazard'}, inplace=True)

        if log_returns:
            market_copy['Fixing'] = np.log(market_copy['Fixing'] / market_copy['Fixing'].shift(1)) 
            # market_copy['Fixing'] = (market_copy['Fixing'] - market_copy['Fixing'].shift(1)) / market_copy['Fixing'].shift(1) * 100
            # market_copy['Fixing'] = np.log(market_copy['Fixing'])

        if sabr_diff:
            market_copy.iloc[:, 1:9] = market_copy.iloc[:, 1:9].diff()

        if yield_diff:
            market_copy.iloc[:, 9:37] = market_copy.iloc[:, 9:37].diff()

        if log_hazard_return:
            market_copy.iloc[:, 37:40] = np.log(market_copy.iloc[:, 37:40] / market_copy.iloc[:, 37:40].shift(1))

        if log_returns | sabr_diff | yield_diff | log_hazard_return:
            market_copy.drop(index = 0, inplace=True)

        self.transformed_market_data = market_copy.iloc[:, 0:40]

      
    def pca(self):
        """
        Performs PCA on the market data.
        
        Returns:
        pca_df (pd.DataFrame): The DataFrame containing the principal components.
        explained_variance_ratio (List): The explained variance ratio of each principal component.
        """

        # Standardize the data
        if not self.transformed_market_data.empty:
            scaled_data = self.scaler.fit_transform(self.transformed_market_data)
        else:
            raise ValueError("Data has not been transformed yet")

        # Perform PCA
        if self.number_of_pcs is not None: 
            self.pc_object = PCA(n_components=self.number_of_pcs)
        else:
            self.pc_object = PCA()

        principal_components = self.pc_object.fit_transform(scaled_data)
        
        # Create a DataFrame with the principal components
        pca_df = pd.DataFrame(data=principal_components, 
                            columns=[f'PC{i+1}' for i in range(principal_components.shape[1])])
        
        self.pcs = pca_df
 

    def elbow_plot(self):
        """
        Plots the explained variance ratio to help determine the optimal number of principal components.
        Also prints the number of components required to explain at least 95% of the variance.
        """
        if self.pc_object is None:
            raise ValueError("PCA has not been performed. Please run the pca() method first.")

        # Explained variance and cumulative explained variance
        explained_var = self.pc_object.explained_variance_ratio_
        cumulative_var = explained_var.cumsum()

        # Find number of components needed to explain at least 90% variance
        num_components_90 = next(i + 1 for i, total_var in enumerate(cumulative_var) if total_var >= 0.89)
        print(f"Number of principal components to explain at least 90% variance: {num_components_90}")

        # Plot the explained variance ratio
        plt.figure(figsize=(10, 6))
        plt.plot(range(1, len(explained_var) + 1), explained_var, marker='o', linestyle='--')
        plt.title('Explained Variance Ratio by Principal Components')
        plt.xlabel('Number of Principal Components')
        plt.ylabel('Explained Variance Ratio')
        plt.xticks(range(1, len(explained_var) + 1))
        plt.grid(True)
        plt.show()

    def pc_tsa(self, pc):
        """
        Analyzes the best ARIMA order for the i-th principal component.

        Parameters:
        pc: The name of the principal component, for example PC1 or PC5 etc.
        """

        # Get the i-th principal component
        pc_series = self.pcs[pc]

        # Determine the degree of differencing (d) using the Augmented Dickey-Fuller test
        def determine_differencing(series):
            d = 0
            adf_result = adfuller(series)
            print(adf_result[1])
            while adf_result[1] > 0.05:
                series = series.diff().dropna()
                d += 1
                adf_result = adfuller(series)
            return d, series

        d, differenced_series = determine_differencing(pc_series)
        print(f"Determined degree of differencing: {d}")

        # Plot ACF and PACF of the differenced series
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        plot_acf(differenced_series, ax=axes[0])
        plot_pacf(differenced_series, ax=axes[1])
        plt.show()

        # Fit ARIMA models with different orders and compare AIC and BIC
        best_aic = float('inf')
        best_bic = float('inf')
        best_order = None

        # Define the range of p and q to try
        p_range = range(0, 2)
        q_range = range(0, 2)

        warnings.filterwarnings("ignore")

        for p in p_range:
            for q in q_range:
                try:
                    model = ARIMA(pc_series, order=(p, d, q))
                    results = model.fit()
                    aic = results.aic
                    bic = results.bic
                    if aic < best_aic:
                        best_aic = aic
                        best_bic = bic
                        best_order = (p, d, q)
                except:
                    continue

        print(f"Best ARIMA order: {best_order}")
        print(f"Best AIC: {best_aic}")
        print(f"Best BIC: {best_bic}")


    def set_arima_model(self, pc, order):
        model = sm.tsa.ARIMA(self.pcs[pc], order=order)
        fitted_model = model.fit()

        self.models[pc] = fitted_model
        self.errors[pc] = fitted_model.resid
        

    def fit_best_arima_model(self):
        """
        Automatically fits the best ARIMA model to each pc.
        
        Returns:
        models (List): The fitted ARIMA models.
        errors (pd.DataFrame) : Errors of the fitted model
        """
        for pc in self.pcs.columns:
            # Use pm.auto_arima to find the best ARIMA model
            auto_model = pm.auto_arima(self.pcs[pc], seasonal=False, stepwise=True, trace=True)
            order = auto_model.order

            # Fit a statsmodels ARIMA model using the extracted order
            model = sm.tsa.ARIMA(self.pcs[pc], order=order)
            fitted_model = model.fit()
            
            self.models[pc] = fitted_model 
            self.errors[pc] = fitted_model.resid


    def fit_best_distribution(self):
        """
        Automatically fits the best distribution to each column of the error dataframe,
        stores the best-fitting frozen distributions, and adds transformed columns
        to the dataframe, mapping the errors to standard uniform values.
        """
        # List of distributions to check
        DISTRIBUTIONS = [
            stats.norm, stats.expon, stats.gamma, stats.beta, stats.lognorm, stats.t, stats.jf_skew_t
        ]

        for column in self.errors.columns:
            column_errors = self.errors[column].dropna()  # Handle missing data
            best_distribution = None
            best_aic = np.inf
            best_params = None
            
            for distribution in DISTRIBUTIONS:
                try:
                    # Fit the distribution to the data
                    with warnings.catch_warnings():
                        warnings.filterwarnings('ignore')
                        params = distribution.fit(column_errors)
                    
                    # Calculate the AIC
                    log_likelihood = np.sum(distribution.logpdf(column_errors, *params))
                    k = len(params)
                    aic = 2 * k - 2 * log_likelihood
                    
                    # Update the best fit if this distribution has a lower AIC
                    if aic < best_aic:
                        best_aic = aic
                        best_distribution = distribution
                        best_params = params
                        
                except Exception as e:
                    print(f"Could not fit {distribution.name}: {e}")

            # If a best distribution was found, freeze it, store it, and transform errors
            if best_distribution and best_params:
                print(best_distribution.name)
                frozen_distribution = best_distribution(*best_params)  # Create frozen distribution
                self.error_distributions[column] = (frozen_distribution)

                # Transform errors to standard uniform using the CDF
                uniform_transformed = frozen_distribution.cdf(self.errors[column])
                self.uniform_errors[column] = uniform_transformed


    def fit_gaussian_copula(self):
        """
        Fits the gaussian copula to the uniform-transformed errors in self.uniform_errors_df.
        """
        # Apply inverse CDF of standard normal to get normal marginals
        normal_marginals = norm.ppf(self.uniform_errors)

        # Estimate the correlation matrix for the Gaussian copula
        self.gaussian_params = np.corrcoef(normal_marginals, rowvar=False)




    def fit_student_t_copula(self):
        """
        Fits a Student's t copula to the uniform-transformed errors in self.uniform_errors.
        Uses the copulae package to estimate both the correlation matrix and degrees of freedom (nu).
        """
        # Step 1: Clip values to avoid edge cases
        u = np.clip(self.uniform_errors, 1e-6, 1 - 1e-6)

        # Step 2: Fit the Student t copula
        cop = StudentCopula(dim=u.shape[1])
        cop.fit(u)

        # Step 3: Extract parameters from the fitted copula
        param_tuple = cop.params  # tuple: (df, *flattened_correlation_values)
        df = param_tuple[0]
        dim = cop.dim
        corr_flat = param_tuple[1:]

        # Step 4: Reconstruct the correlation matrix
        corr_matrix = np.eye(dim)
        tril_indices = np.tril_indices(dim, -1)
        corr_matrix[tril_indices] = corr_flat
        corr_matrix = corr_matrix + corr_matrix.T - np.diag(corr_matrix.diagonal())

        def nearest_psd(A, epsilon=1e-8):
            """Return the nearest positive semidefinite matrix to A."""
            # Symmetrize
            A = (A + A.T) / 2
            # Eigen-decomposition
            eigvals, eigvecs = np.linalg.eigh(A)
            # Clip negative eigenvalues
            eigvals[eigvals < epsilon] = epsilon
            # Reconstruct
            return eigvecs @ np.diag(eigvals) @ eigvecs.T

        corr_matrix = nearest_psd(corr_matrix)

        # Step 5: Store parameters
        self.student_t_params = {
            'correlation_matrix': corr_matrix,
            'df': df
        }


    def simulate(self, num_timesteps):
        """
        Simulates synthetic data based on the fitted copula, marginals, and ARIMA models.

        Parameters:
        num_timesteps (int): The number of timesteps or simulations to generate.

        Returns:
        simulated_pcs (pd.DataFrame): Simulated principal component values for the given timesteps.
        """
        if self.models.empty:
            raise ValueError("No ARIMA models fitted. Fit the ARIMA models first using fit_best_arima_model().")
        
        if self.error_distributions.empty:
            raise ValueError("No distributions fitted. Fit the marginals first using fit_best_distribution().")
        

        if not self.gaussian_params is None:
            copula = GaussianCopula(corr=self.gaussian_params)
        elif not self.student_t_params is None:
            copula = StudentTCopula(corr=self.student_t_params['correlation_matrix'], df = self.student_t_params['df'])
        else:
            raise ValueError("No copula fitted. Fit the copula first using fit_best_copula(), or one of the other two copula functions.")

        simulated_uniforms = copula.rvs(num_timesteps)
        simulated_uniforms = pd.DataFrame(simulated_uniforms, columns=self.uniform_errors.columns)

        # Step 2: Transform uniform errors to the original error space using inverse CDF (PPF) of the marginals
        simulated_errors = pd.DataFrame()
        for col, dist in zip(simulated_uniforms.columns, self.error_distributions):
            simulated_errors[col] = dist.ppf(simulated_uniforms[col])
            #print(dist.dist.name)


        # Step 3: Simulate ARIMA process for each principal component using simulated errors as measurement shocks
        simulated_pcs = pd.DataFrame()
        for i, model in enumerate(self.models):
            pc_name = self.pcs.columns[i]

            # Extract the simulated errors for this principal component
            input_errors = simulated_errors[pc_name].values

            # Simulate ARIMA process using the errors as measurement shocks
            arima_simulation = model.simulate(nsimulations=num_timesteps, anchor='end', measurement_shocks=input_errors)

            # Store the simulated principal component
            simulated_pcs[pc_name] = arima_simulation

        self.sim_pcs = simulated_pcs    
    

    def reverse_transform(self, log_returns=True, sabr_diff=False, yield_diff=False, log_hazard_return=True):
        reverse_market = pd.DataFrame(self.scaler.inverse_transform(self.pc_object.inverse_transform(self.sim_pcs)))
        reverse_market.iloc[:, 0] = reverse_market.iloc[:, 0].clip(-1, 1) - 0.00025

        if not self.transformed_market_data.empty:
            if log_returns:
                reverse_market.iloc[:, 0] = np.exp(reverse_market.iloc[:, 0]).cumprod() * self.market_data.iloc[-1, 0] 
                # reverse_market.iloc[:, 0] = (reverse_market.iloc[:, 0]/100 + 1).cumprod() * self.market_data.iloc[-1, 0] 

            if sabr_diff:
                reverse_market.iloc[:, 1:9] = reverse_market.iloc[:, 1:9].cumsum() + self.market_data.iloc[-1, 1:9].values

            if yield_diff:
                reverse_market.iloc[:, 9:37] = reverse_market.iloc[:, 9:37].cumsum() + self.market_data.iloc[-1, 9:37].values

            if log_hazard_return:
                reverse_market.iloc[:, 37:40] = np.exp(reverse_market.iloc[:, 37:40].astype(float)).cumprod() * self.market_data.iloc[-1, 37:40].apply(hazard_rate).astype(float).values

        self.sim_market = reverse_market



    def clean_sim_market(self):
        # Clean yield curves
        yield_mask = (self.sim_market.iloc[:, 9:37] < -2) | (self.sim_market.iloc[:, 9:37] > 15)
        self.sim_market.iloc[:, 9:37] = self.sim_market.iloc[:, 9:37].mask(yield_mask.any(axis=1), np.nan)
        self.sim_market.iloc[:, 9:37] = self.sim_market.iloc[:, 9:37].ffill()

        # Clean underlying path
        fixing_mask = (self.sim_market.iloc[:, 0] < 0) | (self.sim_market.iloc[:, 0] > 1000000)
        self.sim_market.iloc[fixing_mask, 0] = np.nan
        self.sim_market.iloc[:, 0] = self.sim_market.iloc[:, 0].ffill()

        # Clean SABR
        self.sim_market.iloc[:, 1] = self.sim_market.iloc[:, 1].clip(-0.1, 0.15)
        self.sim_market.iloc[:, 2] = self.sim_market.iloc[:, 2].clip(-1, 0.3)
        self.sim_market.iloc[:, 3] = self.sim_market.iloc[:, 3].clip(0, 1.5)
        self.sim_market.iloc[:, 4] = self.sim_market.iloc[:, 4].clip(-0.3, 1.5)
        self.sim_market.iloc[:, 5] = self.sim_market.iloc[:, 5].clip(-2, 1.5)
        self.sim_market.iloc[:, 6] = self.sim_market.iloc[:, 6].clip(-2, 0.5)
        self.sim_market.iloc[:, 7] = self.sim_market.iloc[:, 7].clip(0, 2)
        self.sim_market.iloc[:, 8] = self.sim_market.iloc[:, 8].clip(-0.5, 0.5)




    def complete_simulation_run(self, n_sims, n_steps):
        self.sims = np.empty((n_steps, self.transformed_market_data.shape[1], n_sims))
         
        for i in range(n_sims):
            self.simulate(num_timesteps=n_steps)
            self.reverse_transform()
            self.clean_sim_market()
            self.sims[:, :, i] = self.sim_market



    def pdf_comparison(self, n_sims, n_steps):
        self.raw_sims = np.empty((n_steps, n_sims))

        for i in range(n_sims):
            self.simulate(num_timesteps=n_steps)
            self.reverse_transform(log_returns=False, sabr_diff=False, yield_diff=False, log_hazard_return=False)
            self.raw_sims[:, i] = self.sim_market.iloc[:, 0]

        sim_returns = self.raw_sims.flatten()
        historic_returns = self.transformed_market_data.iloc[:, 0]
        
        print('sim statistics:')
        print(pd.DataFrame(sim_returns, columns=['Values']).describe())
        print(f"skewness : {skew(sim_returns):10.5f}")
        print(f"kurtosis : {kurtosis(sim_returns, fisher= False):10.5f}")

        print('historic statistics:')
        print(historic_returns.describe())
        print(f"skewness : {skew(historic_returns):10.5f}")
        print(f"kurtosis : {kurtosis(historic_returns, fisher= False):10.5f}")

        plt.figure(figsize=(10, 6))
        sns.kdeplot(historic_returns, bw_adjust=0.5, fill=True, label='Historic Returns')
        sns.kdeplot(sim_returns, bw_adjust=0.5, fill=True, label='Simulated Returns')
        plt.title('Empirical PDF of historic and simulated returns')
        plt.xlabel('Value')
        plt.ylabel('Density')
        plt.legend()
        plt.grid(True)
        plt.show()




    def sim_yield_plot(self):
        maturities = np.array([1/365, 7/365, 1/12, 2/12, 3/12, 4/12, 5/12, 6/12, 7/12, 8/12, 9/12, 10/12, 11/12, 1, 1.5, 2, 3, 4, 5, 7, 10, 12, 15, 20, 25, 30, 40, 50])

        data = self.sim_market.iloc[:, 9:37]

        num_rows = len(data)

        # Create a date range
        date_range = pd.date_range(start='2025-01-21', periods=num_rows, freq='D')
        data.index = date_range
        data.columns = maturities

        # Convert the index to datetime if it's not already
        # data.index = pd.to_datetime(data.index)

        # Create a meshgrid for plotting
        X, Y = np.meshgrid(data.columns, data.index.map(pd.Timestamp.toordinal))
        Z = data.values

        # Convert dates to numerical format for plotting
        X = X.astype(float)
        Y = Y.astype(float)

        fig = plt.figure(figsize=(10, 7))
        ax = fig.add_subplot(111, projection='3d')

        # Plot the surface
        surf = ax.plot_surface(X, Y, Z, cmap='viridis')

        # Add labels
        ax.set_xlabel('Maturity (Years)')
        ax.set_ylabel('Date')
        ax.set_zlabel('Yield (%)')

        # Find the first available date in each year
        first_dates_each_year = data.index.to_series().groupby(data.index.year).first()
        year_ticks = first_dates_each_year.map(pd.Timestamp.toordinal).values
        year_labels = first_dates_each_year.index

        # Set major ticks to the first available date in each year
        ax.set_yticks(year_ticks)
        ax.set_yticklabels(year_labels)

        # Add a color bar
        # fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)

        plt.show()

    def sim_yield_plot_2d(self):
        """
        Draw a 'fan' of yield curves (one curve per chosen date) in 2-D.
        Fixes OutOfBoundsDatetime in the colour-bar by normalising 0--1.
        """
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd
        import matplotlib as mpl

        maturities = np.array([1/365, 7/365, 1/12, 2/12, 3/12, 4/12, 5/12,
                            6/12, 7/12, 8/12, 9/12, 10/12, 11/12, 1, 1.5,
                            2, 3, 4, 5, 7, 10, 12, 15, 20, 25, 30, 40, 50])

        data = self.sim_market.iloc[:, 9:37]
        data.index = pd.date_range('2025-01-21', periods=len(data), freq='D')
        data.columns = maturities

        # pick one curve per month (adapt as you wish)
        curves = data.resample('BMS').first()
        n_curves = len(curves)

        # colour map -------------------------------------------------------------
        cmap   = plt.get_cmap('viridis')
        norm   = mpl.colors.Normalize(vmin=0, vmax=n_curves-1)
        colours = cmap(norm(np.arange(n_curves)))

        # figure -----------------------------------------------------------------
        fig, ax = plt.subplots(figsize=(10, 6))

        for i, (idx, row) in enumerate(curves.iterrows()):
            ax.plot(maturities, row.values,
                    color=colours[i],
                    linewidth=1.4)

            # annotate every January curve
            if idx.month == 1:
                ax.text(maturities[-1] + 0.2, row.values[-1],
                        idx.strftime('%Y-%m'),
                        va='center', fontsize=8, color=colours[i])

        # axes & grid ------------------------------------------------------------
        ax.set_title('Simulated Yield Curves')
        ax.set_xlabel('Maturity (years)')
        ax.set_ylabel('Yield (%)')
        ax.set_xlim(left=0)
        ax.grid(alpha=.3)

        ax.set_xticks([1/12, 0.5, 1, 2, 3, 5, 7, 10, 30])
        ax.set_xticklabels(['1M','6M','1Y','2Y','3Y','5Y','7Y','10Y','30Y'])

        # colour bar -------------------------------------------------------------
        sm = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])

        cbar = fig.colorbar(sm, ax=ax, pad=0.02)
        cbar.set_label('Date')

        # show 5 evenly–spaced labels
        tick_pos   = np.linspace(0, n_curves-1, 5)
        tick_dates = curves.index[np.round(tick_pos).astype(int)]
        cbar.set_ticks(tick_pos)
        cbar.set_ticklabels([d.strftime('%Y-%m-%d') for d in tick_dates])

        plt.tight_layout()
        plt.show()















#    if euribor_diff:
#         reverse_market.iloc[:, 37:40] = reverse_market.iloc[:, 37:40].cumsum() + self.market_data.iloc[-1, 37:40].values

# # Create a Series with the explained variance ratio
# explained_variance_ratio = pd.Series(pca.explained_variance_ratio_, 
#                                     index=[f'PC{i+1}' for i in range(len(pca.explained_variance_ratio_))])

# # Create a DataFrame with the factor loadings
# loadings_df = pd.DataFrame(pca.components_.T, 
#                         columns=[f'PC{i+1}' for i in range(pca.components_.shape[0])],
#                         index=self.market_data.columns)


# self.explained_variance_ratio = explained_variance_ratio
# self.loadings = loadings_df






# def fit_best_copula(self):
#     """
#     Fits the best copula model to the uniform-transformed errors in self.uniform_errors_df
#     by evaluating the log-likelihood for different copulas, including t-copula.
#     """
#     if self.uniform_errors.empty:
#         raise ValueError("Uniform errors dataframe is empty. Fit distributions first.")

#     # List of copulas to evaluate
#     COPULAS = [GaussianCopula, StudentTCopula]
#     best_log_likelihood = -np.inf
#     best_copula = None

#     # Fit each copula and evaluate the log-likelihood
#     for copula in COPULAS:
#         try:
#             copula.fit(self.uniform_errors)
#             log_likelihood = copula.log_likelihood(self.uniform_errors)

#             # Update the best copula if this one has a higher log-likelihood
#             if log_likelihood > best_log_likelihood:
#                 best_log_likelihood = log_likelihood
#                 best_copula = copula
#         except Exception as e:
#             print(f"Could not fit {copula._class.name_} copula: {e}")

#     self.copula = best_copula


    # def retain_pcs(self, n):
    #     """
    #     Adjusts the instance variables to only retain the first N principal components.

    #     Parameters:
    #     n (int): The number of principal components to retain.
    #     """
    #     if n > len(self.pc_object.explained_variance_ratio_):
    #         raise ValueError(f"Cannot retain {n} principal components. The PCA model only has {len(self.pc_object.explained_variance_ratio_)} components.")

    #     # Retain the first N principal components
    #     self.pcs = self.pcs.iloc[:, :n]
    #     self.explained_variance_ratio = self.explained_variance_ratio.iloc[:n]
    #     self.loadings = self.loadings.iloc[:, :n]
    #     self.number_of_pcs = n
    #     self.models = pd.Series() #None, index=[f'PC{i+1}' for i in range(n)]
    