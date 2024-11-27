import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

filename = "data.csv"
filename = "thickdata.csv"

if filename == "data.csv":
    rows = 5
    # Initial guesses for f, fp, bp
    initial_guesses = [17, 0.1, 0.1]
    upper_bounds = [initial_guesses[0] + 5, 0.1, 0.1]  # Set upper bounds for f, fp, bp
else:
    rows = 3
    initial_guesses = [5, 0.2, 0.1]
    upper_bounds = [initial_guesses[0] + 5, 0.2, 0.2]  # Set upper bounds for f, fp, bp

# Load the CSV data
data = np.genfromtxt(filename, delimiter=",", skip_header=1)

# Parameters (replace with actual values when known)
lobj = 5.99  # - 0.03
limg = lobj
# l = 3 * 2  # Offset
f = 15.1 + 2  # Focal length
# f = 16.5

# Extract columns: o, i, M
o_data = data[:, 0]
i_data = data[:, 1]
M_data = data[:, 2]

# For the focus actual measurement
f_array = [14.2, 14.1, 14.3, 14.2, 14.2]
f = np.mean(f_array) + 3
print(f"Focus is {f} cm +- {np.std(f_array)} cm")

a = np.array([28.8, 28.5, 28.45, 28.8, 28.5, 28.75])
print(np.mean(a), np.std(a))

# Calculate mean and standard deviation for every <rows> lines
num_measurements = len(o_data) // rows
p_means = []
p_stds = []
q_means = []
q_stds = []
M_means = []
M_stds = []
q_from_M_means = []
q_from_M_stds = []

for i in range(num_measurements):
    # Extract every <rows> rows for each measurement
    o_subset = o_data[i * rows : (i + 1) * rows]
    i_subset = i_data[i * rows : (i + 1) * rows]
    M_subset = M_data[i * rows : (i + 1) * rows]

    # Calculate mean and std for o, i, and M
    o_mean = np.mean(o_subset)
    o_std = np.std(o_subset, ddof=1)  # Sample standard deviation
    i_mean = np.mean(i_subset)
    i_std = np.std(i_subset, ddof=1)  # Sample standard deviation
    M_mean = np.mean(M_subset)
    M_std = np.std(M_subset, ddof=1)  # Sample standard deviation

    # Calculate p and q with uncertainties
    p = abs(o_mean + lobj)
    q = abs(i_mean + limg)

    # Store p and q with their uncertainties
    p_means.append(p)
    p_stds.append(o_std)
    q_means.append(q)
    q_stds.append(i_std)
    M_means.append(M_mean)
    M_stds.append(M_std)

    # Calculate q = M * p and its uncertainty
    q_from_M = M_mean * p
    q_from_M_means.append(q_from_M)
    q_from_M_stds.append(abs(M_std * p))  # Propagating uncertainty from M_std

# Convert lists to numpy arrays for easy plotting
p_means = np.array(p_means)
p_stds = np.array(p_stds)
q_means = np.array(q_means)
q_stds = np.array(q_stds)
M_means = np.array(M_means)
M_stds = np.array(M_stds)
q_from_M_means = np.array(q_from_M_means)
q_from_M_stds = np.array(q_from_M_stds)


# Define the modified thin lens equation function
def modified_thin_lens(p, f, fp, bp):
    return (p - fp) * f / (p - fp - f) + bp  # since fp = bp here


# Bounds for f, fp, and bp
lower_bounds = [initial_guesses[0] - 5, 0.01, 0.01]  # Set lower bounds for f, fp, bp

# Fit the modified thin lens equation to the data
params, covariance = curve_fit(
    modified_thin_lens,
    p_means,
    q_means,
    p0=initial_guesses,
    sigma=q_stds,
    absolute_sigma=True,
    bounds=(lower_bounds, upper_bounds),
)
f_fit, fp_fit, bp_fit = params
f_std, fp_std, bp_std = np.sqrt(np.diag(covariance))

uncertainty = np.sqrt(np.diag(covariance))
dof = len(p_means) - len(params)

chisq = np.sum(((q_means - modified_thin_lens(p_means, *params)) / q_stds) ** 2) / dof

print(f"Estimated f: {f_fit} ± {f_std} cm")
# print(f"Estimated fp: {fp_fit} ± {fp_std} cm")
# print(f"Estimated bp: {bp_fit} ± {bp_std} cm")
print(f"fp and bp: {(fp_fit+bp_fit)/2} +- {0.5*np.sqrt(fp_std**2 + bp_std**2)} cm")
print("Chi Squares:", chisq)

# Create a figure with two subplots (stacked)
fig, (ax, ax_res) = plt.subplots(
    2, 1, figsize=(8, 10), gridspec_kw={"height_ratios": [2, 1]}
)

# Plot q vs. p with error bars for experimental data
ax.errorbar(
    p_means, q_means, xerr=p_stds, yerr=q_stds, fmt="o", label="Experimental Data"
)

# Generate theoretical values for q based on thin lens equation
p_range = np.linspace(min(p_means), max(p_means), 100)
q_fitted = modified_thin_lens(p_range, f_fit, fp_fit, bp_fit)

# Plot fitted modified thin lens equation
ax.plot(
    p_range,
    q_fitted,
    label=f"Thin Lens Equation Fit (f={f_fit:.2f}, fp={(fp_fit+bp_fit)/2:.2f}, bp={(fp_fit+bp_fit)/2:.2f})",
    color="blue",
)

# Plot q = M * p relationship with mean and std
ax.errorbar(
    p_means,
    q_from_M_means,
    yerr=q_from_M_stds,
    fmt="s",
    color="green",
    label="q = M * p",
)

# Add chi-squared value to top-right corner
ax.text(
    0.95,
    0.95,
    f"$\chi^2$ = {chisq:.2f}",
    transform=ax.transAxes,
    ha="right",
    va="top",
    fontsize=12,
)

# Labels and legend
ax.set_xlabel("p (object distance) [cm]")
ax.set_ylabel("q (image distance) [cm]")
ax.set_title("Comparison of Experimental, Theoretical, and Fitted q vs. p")
ax.legend()
ax.grid()
ax.set_ylim(min(q_means) * 0.9, max(q_means) * 1.1)

# Calculate residuals (difference between measured and fitted values of q)
residuals_q = q_means - modified_thin_lens(p_means, *params)
residuals_q_from_M = q_from_M_means - modified_thin_lens(p_means, *params)

# Plot residuals below the main plot
ax_res.errorbar(
    p_means,
    residuals_q,
    yerr=q_stds,
    fmt="o",
    color="red",
    label="Residuals (Image Position from Magnification)",
)
ax_res.errorbar(
    p_means,
    residuals_q_from_M,
    yerr=q_from_M_stds,
    fmt="s",
    color="purple",
    label="Residuals (Measured Image Position)",
)

ax_res.axhline(0, color="black", linewidth=0.8)
ax_res.set_xlabel("p (object distance) [cm]")
ax_res.set_ylabel("Residuals [cm]")
ax_res.legend()
ax_res.grid()

plt.tight_layout()
plt.show()
