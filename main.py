import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

print("Libraries are working!")

# create a fake price series
prices = pd.Series(np.random.randn(100).cumsum())

# plot
prices.plot(title="Fake Price Data")
plt.show()
