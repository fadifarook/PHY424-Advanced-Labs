import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Load the CSV data
data = np.genfromtxt("data.csv", delimiter=",", skip_header=1)

# Parameters (replace with actual values when known)
l = 3 * 2  # Offset
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

# Calculate mean and standard deviation for every 5 lines
num_measurements = len(o_data) // 5
p_means = []
p_stds = []
q_means = []
q_stds = []
M_means = []
M_stds = []
q_from_M_means = []
q_from_M_stds = []

for i in range(num_measurements):
    # Extract every 5 rows for each measurement
    o_subset = o_data[i * 5 : (i + 1) * 5]
    i_subset = i_data[i * 5 : (i + 1) * 5]
    M_subset = M_data[i * 5 : (i + 1) * 5]

    # Calculate mean and std for o, i, and M
    o_mean = np.mean(o_subset)
    o_std = np.std(o_subset, ddof=1)  # Sample standard deviation
    i_mean = np.mean(i_subset)
    i_std = np.std(i_subset, ddof=1)  # Sample standard deviation
    M_mean = np.mean(M_subset)
    M_std = np.std(M_subset, ddof=1)  # Sample standard deviation

    # Calculate p and q with uncertainties
    p = abs(o_mean + l)
    q = abs(i_mean + l)

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


# Initial guesses for f, fp, bp
initial_guesses = [17, 0.1, 0.1]

# Bounds for f, fp, and bp
lower_bounds = [10, 0.01, 0.01]  # Set lower bounds for f, fp, bp
upper_bounds = [25, 0.2, 0.2]  # Set upper bounds for f, fp, bp

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

print(f"Estimated f: {f_fit} ± {f_std} cm")
print(f"Estimated fp: {fp_fit} ± {fp_std} cm")
print(f"Estimated bp: {bp_fit} ± {bp_std} cm")

# Plot q vs. p with error bars for experimental data
plt.errorbar(
    p_means, q_means, xerr=p_stds, yerr=q_stds, fmt="o", label="Experimental Data"
)

# Generate theoretical values for q based on thin lens equation
p_range = np.linspace(min(p_means), max(p_means), 100)
q_theoretical = (p_range * f) / (p_range - f)

# Plot theoretical relationship
# plt.plot(p_range, q_theoretical, label=f"Theoretical (f = {f})", color="red")

# Plot q = M * p relationship with mean and std
plt.errorbar(
    p_means,
    q_from_M_means,
    yerr=q_from_M_stds,
    fmt="s",
    color="green",
    label="q = M * p",
)

# Plot fitted modified thin lens equation
q_fitted = modified_thin_lens(p_range, f_fit, fp_fit, bp_fit)
plt.plot(
    p_range,
    q_fitted,
    label=f"Fitted (f={f_fit:.2f}, fp={fp_fit:.2f}, bp={bp_fit:.2f})",
    color="blue",
)

# Labels and legend
plt.xlabel("p (object distance) [cm]")
plt.ylabel("q (image distance) [cm]")
plt.title("Comparison of Experimental, Theoretical, and Fitted q vs. p")
plt.legend()
plt.grid()
plt.ylim(0, 100)
plt.show()
